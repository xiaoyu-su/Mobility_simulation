"""Build private, fingerprinted market inputs with a held-out target day."""

from datetime import date
import importlib.metadata
import json
import math
import re
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

from src.misc.init_modules import load_routing_engine
from src.misc.seeding import file_digest
from tools.paired_eval.__main__ import ROOT,source_record
from tools.synthetic_market.records import read_records
from tools.synthetic_market.spatial import node_pools,mapped_nodes,causal_requests


def json_write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def market_dependencies():
    versions={}
    for name in ['numpy','pandas','scipy','pyyaml','gurobipy','pyarrow']:
        try:versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:versions[name]=None
    return versions


def training_dates(target,training):
    target=date.fromisoformat(target);days=[date.fromisoformat(v) for v in training]
    if not days or len(set(days))!=len(days) or target in days:
        raise ValueError('Training dates must be nonempty, unique and exclude the target date')
    if any(d.weekday()!=target.weekday() for d in days):
        raise ValueError('Forecast training dates must share the target weekday')
    if any(d>=target for d in days):raise ValueError('Forecast training dates must precede the held-out target day')
    return target.isoformat(),[d.isoformat() for d in days]


def fit_travel(training,router,centroids,start,end,resolution,detrend=False):
    rows=training.copy()
    route_cache={}
    origins=rows['start'] if 'start' in rows else rows.PULocationID.map(centroids)
    destinations=rows['end'] if 'end' in rows else rows.DOLocationID.map(centroids)
    for a,b in sorted(set(zip(origins,destinations))):
        route_cache[a,b]=router.return_travel_costs_1to1(router.return_node_position(int(a)),router.return_node_position(int(b)))[1]
    rows['base_route_s']=[route_cache[a,b] for a,b in zip(origins,destinations)]
    rows=rows[np.isfinite(rows.base_route_s) & rows.base_route_s.gt(0)].copy()
    if rows.empty:raise ValueError('No positive reachable interzonal travel-time calibration pairs')
    rows['log_ratio']=np.log((rows.dropoff_s-rows.pickup_s)/rows.base_route_s)
    rows['bin']=(rows.pickup_s//resolution*resolution).astype(int)
    overall=rows.log_ratio
    residual=rows.log_ratio-rows.groupby('bin').log_ratio.transform('mean') if detrend else overall
    sigma=float(residual.std(ddof=0))
    # Mean-one execution noise: E[ratio] = factor and log ratio mean = log(factor)-sigma²/2.
    factors=[]
    for time in range(start,end,resolution):
        values=rows.loc[rows.bin.eq(time),'log_ratio']
        if len(values)<3:values=overall
        factor=float(np.exp(values.mean()+sigma*sigma/2))
        if not math.isfinite(factor) or not 0 < factor <= 100:
            raise ValueError('Implausible/nonfinite travel factor; inspect source units and network mapping')
        factors.append(dict(simulation_time=time,travel_time_factor=factor))
    return pd.DataFrame(factors),sigma,dict(training_pairs=len(rows),excluded_zero_or_unreachable=len(training)-len(rows),
        estimation=f'log-duration/imputed-route fit; {"within-bin residual" if detrend else "global"} log sigma; per-bin log mean with global fallback below 3 pairs',
        interpretation='Observed ride duration includes non-driving effects; execution noise is a fitted proxy, not identified causal noise')


def historical_profiles(training,days,zones,start,end,resolution,utilization):
    forecasts=[];supply=[]
    for t in range(start,end,resolution):
        departures=training.loc[training.request_s.ge(t)&training.request_s.lt(t+resolution),'PULocationID'].value_counts()
        arrivals=training.loc[training.dropoff_s.ge(t)&training.dropoff_s.lt(t+resolution),'DOLocationID'].value_counts()
        for zone in zones:
            forecasts.append(dict(time=t,zone_id=zone,**{'out aggregate_o_and_d':float(departures.get(zone,0)/days),
                                                       'in aggregate_o_and_d':float(arrivals.get(zone,0)/days)}))
        occupied=np.maximum(0,np.minimum(training.dropoff_s.to_numpy(),t+resolution)-np.maximum(training.pickup_s.to_numpy(),t)).sum()
        average=float(occupied/(resolution*days))
        supply.append(dict(time=t,mean_observed_occupied_vehicles=average,modeled_active_vehicles=max(1,int(math.ceil(average/utilization)))))
    return pd.DataFrame(forecasts),pd.DataFrame(supply)


def build(args):
    output=args.output.resolve()
    if output.exists():raise ValueError(f'Refusing to overwrite market bundle: {output}')
    target,days=training_dates(args.target_date,args.training_dates)
    if args.data_kind not in ('fixture','tlc_public'):raise ValueError('Specify fixture or tlc_public provenance')
    if args.network_type not in ('NetworkBasic','NetworkBasicWithStore','NetworkTTMatrix'):raise ValueError('Unsupported market road router')
    if not 0 < args.utilization <= 1 or not 0 <= args.full_time_share <= 1:raise ValueError('Utilization/share outside valid range')
    if not 0 <= args.seed < 2**32:raise ValueError('Seed outside 0..2**32-1')
    if args.fleet_size is not None and args.fleet_size < 1:raise ValueError('Fleet size must be positive')
    if args.max_route_candidates is not None and args.max_route_candidates<1:raise ValueError('Route candidate limit must be positive')
    if args.future_value and args.driver_model=='off':raise ValueError('Future value requires a driver model')
    if args.patience_extra_seconds < 0 or args.request_time_proxy_seconds is not None and args.request_time_proxy_seconds < 0:
        raise ValueError('Patience/proxy seconds must be nonnegative')
    start,end,resolution,dt=args.start_seconds,args.end_seconds,args.resolution,args.time_step
    if not 0 <= start < end <= 86400 or dt<=0 or resolution<=0 or start%resolution or any(t%dt for t in [start,end,resolution]):
        raise ValueError('Market times/resolution must align to the positive simulation grid within one day')
    warmup=args.warmup_seconds
    if warmup<0 or warmup%resolution or start-warmup<0:raise ValueError('Warm-up must align to resolution and remain within the target day')
    sim_start=start-warmup
    if args.include_intrazonal and args.spatial_mapping!='road_nodes':raise ValueError('Intrazonal trips require road-node imputation')
    if not 0 < args.patience_quantile <= 1:raise ValueError('Patience quantile outside (0,1]')
    if any(not math.isfinite(x) or not 0<=x<86400 for x in [args.pickup_service_seconds,args.dropoff_service_seconds]):
        raise ValueError('Service durations must be finite and in 0..86400')
    if args.vehicle_capacity<1 or not 0<=args.completion_tail_max_seconds<=7*86400:raise ValueError('Invalid capacity or completion-tail bound')
    mapping=pd.read_csv(args.zone_map)
    if not {'node_index','zone_id','is_centroid'}.issubset(mapping):raise ValueError('Zone map requires node_index, zone_id and is_centroid')
    if mapping.node_index.duplicated().any() or mapping[['node_index','zone_id','is_centroid']].isna().any().any():
        raise ValueError('Node-to-zone mapping must be nonmissing and unique by node')
    for column in ['node_index','zone_id']:
        if not (mapping[column].astype(int)==mapping[column]).all():raise ValueError('Node/zone IDs must be integers')
    mapping=mapping.loc[mapping.zone_id.ge(0)].copy()
    centroids=mapping.loc[mapping.is_centroid.eq(1)].groupby('zone_id').node_index.min().astype(int).to_dict()
    if set(mapping.zone_id)!=set(centroids):raise ValueError('Every modeled zone needs a centroid')
    if len(centroids)<2:raise ValueError('At least two modeled zones are required')
    network=args.network.resolve()
    required=[network/'base/nodes.csv',network/'base/edges.csv',network/'base/crs.info']
    if args.network_type=='NetworkTTMatrix':required += [network/f'ff/tables/{name}.npy' for name in ['nn_fastest_tt','nn_fastest_distance']]
    for path in required:
        if not path.is_file():raise ValueError(f'Missing network input: {path}')
    nodes=pd.read_csv(network/'base/nodes.csv');node_ids=set(nodes.node_index)
    if not set(mapping.node_index).issubset(node_ids):raise ValueError('Zone map references nodes absent from the network')
    records,counts,inputs=read_records(args.trips,[target,*days],set(centroids),args.seed,args.sample_fraction,
                                      args.request_time_proxy_seconds,args.chunk_size,args.include_intrazonal)
    pools=node_pools(mapping,nodes,args.zone_polygons,args.zone_polygons_crs,(network/'base/crs.info').read_text().strip())
    records=mapped_nodes(records,pools,args.seed,args.spatial_mapping,centroids)
    measured=records.loc[records.service_date.eq(target)&records.request_s.ge(start)&records.request_s.lt(end)].copy()
    measured=measured.sort_values(['request_s','trip_id']).reset_index(drop=True)
    measured['request_id']=range(len(measured));measured['is_evaluation_request']=True
    warm=records.loc[records.service_date.eq(target)&records.request_s.ge(sim_start)&records.request_s.lt(start)].copy()
    warm=warm.sort_values(['request_s','trip_id']).reset_index(drop=True)
    warm['request_id']=np.arange(len(measured),len(measured)+len(warm));warm['is_evaluation_request']=False
    observed=pd.concat([warm,measured],ignore_index=True).sort_values(['request_s','trip_id']).reset_index(drop=True)
    context=records.loc[records.service_date.isin(days)].copy()
    training=context.loc[context.request_s.ge(sim_start)&context.request_s.lt(end+resolution)].copy()
    if observed.empty or training.empty:raise ValueError('Both target-window trips and independent training trips are required')
    if set(training.service_date)!=set(days):raise ValueError('Every declared training date must have retained trips')
    vehicle_source=ROOT/'data/vehicles/default_vehtype.csv'
    vehicle_hash=file_digest(vehicle_source)
    output.mkdir(parents=True)
    manifest=dict(status='building',data_kind=args.data_kind,target_date=target,training_dates=days,
        sampling=dict(seed=args.seed,fraction=args.sample_fraction,scheme='sha256 source-bytes/row/seed threshold v1'),
        source=source_record(),inputs=inputs,network_type=args.network_type,
        zone_map_sha256=file_digest(args.zone_map),network_sha256={str(p.relative_to(network)):file_digest(p) for p in required},
        filtered_counts=counts,target_count=len(observed),training_count=len(training),
        evaluation_count=len(measured),warmup_count=len(warm),training_context_count=len(context),
        evaluation_start=start,evaluation_end=end,simulation_start=sim_start,
        window_exclusions=dict(target=int(records.service_date.eq(target).sum()-len(observed)),
                               training=int(records.service_date.isin(days).sum()-len(training))),
        assumptions=dict(timestamp_timezone='America/New_York local wall time',
            request_time_proxy_seconds=args.request_time_proxy_seconds,patience_extra_seconds=args.patience_extra_seconds,
            target_utilization=args.utilization,full_time_share=args.full_time_share,
            driver_coefficients='illustrative existing Phase 3 values, not calibrated from TLC',
            spatial_mapping=args.spatial_mapping,within_zone_coordinates='imputed, not observed GPS',
            intrazonal_included=args.include_intrazonal,pooling_policy=args.pooling_policy,
            patience_model=args.patience_model,pickup_service_model=args.pickup_service,
            demand_universe='recorded completed trips, not all attempted/cancelled marketplace requests',
            fleet='training occupied interval proxy divided by assumed utilization; not observed driver counts'),
        dependencies=market_dependencies())
    if args.zone_polygons:
        manifest['zone_polygons_sha256']=file_digest(args.zone_polygons)
        manifest['zone_polygons_crs']=args.zone_polygons_crs
    manifest['vehicle_source_sha256']=vehicle_hash
    manifest['spatial_imputation']=dict(seed=args.seed,scheme='sha256 market-road-v1/source-row/role',
        node_counts={str(z):len(pool) for z,pool in pools.items()},polygon_constrained=args.zone_polygons is not None)
    manifest['supply_proxy_definition']='Mean ongoing recorded rides divided by assumed utilization; pooled rides may refer to the same vehicle'
    def save():json_write(output/'manifest.json',manifest)
    save()
    try:
        (output/'vehicles').mkdir();shutil.copy2(vehicle_source,output/'vehicles/default_vehtype.csv')
        vehicle_path=output/'vehicles/default_vehtype.csv'
        vehicle_text,count=re.subn(rb'(?m)^(maximum_passengers,)[^\r\n]+',lambda m:m[1]+str(args.vehicle_capacity).encode(),vehicle_path.read_bytes(),count=1)
        if count!=1:raise ValueError('Vehicle specification lacks maximum_passengers')
        vehicle_path.write_bytes(vehicle_text)
        private_vehicle_hash=file_digest(vehicle_path)
        for path in required:
            destination=output/'network'/path.relative_to(network);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,destination)
        router=load_routing_engine(args.network_type,str(output/'network'))
        private=training.loc[training.shared_matched.eq(0)]
        fitting=private if len(private)>=3 else training
        factors,sigma,fit=fit_travel(fitting,router,centroids,sim_start,end+2*resolution,resolution,detrend=True)
        fit['population']='known unshared training trips' if len(private)>=3 else 'all training trips (insufficient unshared flags)'
        factors.to_csv(output/'network/calibrated_factors.csv',index=False)
        training.to_csv(output/'training_cohort.csv',index=False)
        context.to_csv(output/'training_context.csv',index=False)
        available=training.observed_wait_s.dropna()
        if args.patience_model=='training_quantile' and available.empty:
            if args.request_time_proxy_seconds is None:raise ValueError('No training waits available for patience fitting')
            patience_base=float(args.request_time_proxy_seconds)
        else:patience_base=float(available.quantile(args.patience_quantile)) if len(available) else 0
        patience=(observed.observed_wait_s.fillna(0)+args.patience_extra_seconds if args.patience_model=='observed_replay'
                  else np.full(len(observed),math.ceil(patience_base)+args.patience_extra_seconds))
        requests=causal_requests(observed,dt,patience)
        sim_end=max(end,int(requests.rq_time.max())+dt)
        forecasts,supply=historical_profiles(context,len(days),sorted(centroids),sim_start,sim_end+resolution,resolution,args.utilization)
        forecast_dir=output/'forecasts'/str(resolution);forecast_dir.mkdir(parents=True)
        forecasts.to_csv(forecast_dir/'historical.csv',index=False)
        supply=supply.loc[supply.time.lt(sim_end)].copy()
        fleet=args.fleet_size or int(supply.loc[supply.time.ge(start)&supply.time.lt(end),'modeled_active_vehicles'].max())
        supply['share_active_fleet_size']=np.minimum(supply.modeled_active_vehicles/fleet,1)
        supply.to_csv(output/'supply_profile.csv',index=False)
        zone_dir=output/'zones/network';zone_dir.mkdir(parents=True);mapping.to_csv(zone_dir/'node_zone_info.csv',index=False)
        pd.DataFrame(dict(zone_id=sorted(centroids))).to_csv(output/'zones/general_information.csv',index=False)
        if args.pooling_policy=='source':
            observed['pooling_allowed']=observed.pooling_requested.fillna(1).astype(int)
        else:observed['pooling_allowed']=int(args.pooling_policy=='all')
        pickup_service=args.pickup_service_seconds
        if args.pickup_service=='training_curb':
            curb=training.observed_curb_s.dropna()
            if curb.empty:raise ValueError('Training curb fitting requires valid observed on-scene records')
            pickup_service=float(curb.median())
        requests['pooling_allowed']=observed.pooling_allowed
        requests['pickup_service_time']=pickup_service;requests['dropoff_service_time']=args.dropoff_service_seconds
        observed.to_csv(output/'observed_cohort.csv',index=False)
        demand_dir=output/'demand';demand_dir.mkdir();requests.to_csv(demand_dir/'requests.csv',index=False)
        fleet_dir=output/'fleetctrl/initial_vehicle_distribution/market_network';fleet_dir.mkdir(parents=True)
        initial=context.loc[context.request_s.ge(sim_start)&context.request_s.lt(sim_start+resolution),'PULocationID'].value_counts()
        if initial.empty:initial=training.PULocationID.value_counts()
        initial_rows=[]
        for zone,count in initial.items():
            pool=pools[zone] if args.spatial_mapping=='road_nodes' else [centroids[zone]]
            initial_rows.extend(dict(node_index=n,probability=count/initial.sum()/len(pool)) for n in pool)
        pd.DataFrame(initial_rows).to_csv(fleet_dir/'initial.csv',index=False)
        active=output/'fleetctrl/elastic_fleet_size';active.mkdir(parents=True);supply[['time','share_active_fleet_size']].to_csv(active/'active.csv',index=False)
        infra=output/'infra';infra.mkdir()
        pd.DataFrame([dict(charging_station_id=i,node_index=n,max_nr_parking=fleet,charging_units='') for i,n in enumerate(sorted(centroids.values()))]).to_csv(infra/'depots.csv',index=False)
        from tools.paired_eval.worker import load_parameters
        parameters=load_parameters(ROOT/'studies/example_study/scenarios/constant_config_ir.csv',ROOT/'studies/example_study/scenarios/example_ir_only.csv')
        parameters.update(study_name='market_data',scenario_name='market',network_name='market_network',demand_name='market',
            network_type=args.network_type,nw_dynamic_f='calibrated_factors.csv',rq_file='requests.csv',random_seed=args.seed,
            random_stream_mode='independent',start_time=sim_start,end_time=sim_end,time_step=dt,
            completion_tail_max_seconds=args.completion_tail_max_seconds,op_request_constraints=True,
            n_cpu_per_sim=1,record_promised_times=True,network_tt_noise_sigma=sigma,
            op_init_veh_distribution='initial.csv',op_fleet_composition={'default_vehtype':fleet},
            op_module=args.controller,op_max_wait_time=float((requests.latest_start_time-requests.rq_time).max()),
            op_reoptimisation_timestep=dt,
            op_zone_system='market_zones',op_temporal_resolution=resolution,op_fc_type='aggregate_o_and_d',
            op_forecast_f='historical.csv',op_repo_horizons=[0,resolution],op_repo_timestep=resolution,op_repo_lock=False)
        if args.controller=='RidePoolingBatchAssignmentFleetcontrol':parameters.update(sim_env='BatchOfferSimulation',op_rp_batch_optimizer='AlonsoMora')
        if args.max_route_candidates is not None:parameters['op_rh_immediate_max_routes']=args.max_route_candidates
        if args.dynamic_fleet:parameters.update(op_dyn_fs_method='TimeBasedFS',op_act_fs_file='active.csv',infra_structure_name='market_infra',op_depot_file='depots.csv')
        if args.driver_model=='classes':
            parameters.update(op_driver_acceptance='logistic',op_driver_acceptance_max_declines=0,
                op_driver_acceptance_weight_objective=True,op_driver_choice_model='singleton',
                op_driver_acceptance_classes={'full_time':dict(share=args.full_time_share,intercept=.5,beta_eta=-.1,beta_value=.1),
                                             'part_time':dict(share=1-args.full_time_share,intercept=0,beta_eta=-.2,beta_value=.15)})
        if args.future_value:
            if args.driver_model=='off':raise ValueError('Future value requires a driver model')
            parameters.update(op_driver_acceptance_future_value=True,op_driver_acceptance_future_value_top_k=3)
        json_write(output/'parameters.json',parameters)
        if file_digest(args.zone_map)!=manifest['zone_map_sha256'] or any(file_digest(network/name)!=digest for name,digest in manifest['network_sha256'].items()):
            raise RuntimeError('Source network/zone inputs changed during market build')
        if args.zone_polygons and file_digest(args.zone_polygons)!=manifest['zone_polygons_sha256']:raise RuntimeError('Zone polygons changed during build')
        if file_digest(output/'vehicles/default_vehtype.csv')!=private_vehicle_hash or file_digest(vehicle_source)!=vehicle_hash:
            raise RuntimeError('Source vehicle specifications changed during market build')
        manifest.update(status='complete',fleet_size=fleet,travel_noise_sigma=sigma,travel_fit=fit,
            simulation_end=sim_end,patience_training_quantile_s=patience_base,
            pickup_service_seconds=pickup_service,dropoff_service_seconds=args.dropoff_service_seconds,
            pooling_flag_missing_count=int(observed.pooling_requested.isna().sum()),
            observed_wait_available=bool(observed.request_observed.all()),
            output_sha256={str(p.relative_to(output)):file_digest(p) for p in output.rglob('*') if p.is_file() and p.name!='manifest.json'})
        if source_record()['code_digest']!=manifest['source']['code_digest']:raise RuntimeError('Source changed during market build')
        save();return manifest
    except BaseException as error:
        manifest.update(status='failed',error=f'{type(error).__name__}: {error}');save();raise
