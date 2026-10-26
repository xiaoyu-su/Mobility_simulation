"""Prepare city-neutral, immutable inputs without inventing observed trip times."""

import importlib.util
import json
import math
from pathlib import Path
import re
import shutil

import numpy as np
import pandas as pd

from src.misc.seeding import file_digest
from src.misc.vehicle_timing import travel_time_factor
from tools.paired_eval.__main__ import ROOT, source_record
from tools.paired_eval.worker import load_parameters
from tools.synthetic_market.build import json_write, market_dependencies
from tools.synthetic_market.spatial import causal_requests


ROUTERS = {'NetworkBasicWithStore','NetworkBasicWithStoreCpp',
           'NetworkPartialPreprocessedCpp','NetworkTTMatrix'}


def safe_input(root, name):
    path=(root/name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'Missing/escaping city input: {name}')
    return path


def integer_column(values, name):
    numbers=pd.to_numeric(values,errors='raise')
    if numbers.isna().any() or not np.isfinite(numbers).all() or not numbers.eq(numbers.astype(np.int64)).all():
        raise ValueError(f'{name} must contain finite integers')
    return numbers.astype(np.int64)


def routing_runtime(router):
    if not router.endswith('Cpp'):return {}
    spec=importlib.util.find_spec('src.routing.road.cpp_router.PyNetwork')
    if spec is None:raise ValueError('Compile the FleetPy C++ router before building this city')
    paths=[Path(spec.origin),*(ROOT/'src/routing/road/cpp_router').glob('*.pyx'),
           *(ROOT/'src/routing/road/cpp_router').glob('*.pxd'),
           *(ROOT/'src/routing/road/cpp_router').glob('*.h'),
           *(ROOT/'src/routing/road/cpp_router').glob('*.cpp')]
    return {str(p.relative_to(ROOT)):file_digest(p) for p in sorted(set(paths))}


def normalize_mapping(path, nodes, overlap_policy='error'):
    mapping=pd.read_csv(path)
    if not {'node_index','zone_id'}<=set(mapping):raise ValueError('City zone map needs node_index and zone_id')
    for key in ['node_index','zone_id']:mapping[key]=integer_column(mapping[key],key)
    if overlap_policy not in {'error','lowest_zone_id'}:raise ValueError('Unknown zone overlap policy')
    duplicates=mapping[mapping.node_index.duplicated(keep=False)]
    resolution=dict(policy=overlap_policy,duplicate_nodes=int(duplicates.node_index.nunique()),
                    original_memberships=duplicates[['node_index','zone_id']].to_dict('records'))
    if len(duplicates):
        if overlap_policy=='error':raise ValueError('Duplicate mapped node')
        mapping=mapping.sort_values(['node_index','zone_id']).drop_duplicates('node_index',keep='first').copy()
    if not set(mapping.node_index)<=set(nodes.node_index):raise ValueError('Zone map references missing nodes')
    mapping=mapping[mapping.zone_id.ge(0)].copy()
    access=set(nodes.loc[nodes.is_stop_only.eq(1),'node_index']) or set(nodes.node_index)
    modeled=set(mapping.loc[mapping.node_index.isin(access),'zone_id'])
    mapping=mapping[mapping.zone_id.isin(modeled)].sort_values('node_index').reset_index(drop=True)
    if len(modeled)<2:raise ValueError('At least two mapped access zones required')
    # Some public city maps lack centroid flags. Pick an actual access node;
    # preserve a supplied centroid when it is a valid access point.
    original=mapping.get('is_centroid',pd.Series(0,index=mapping.index))
    mapping['is_centroid']=0
    for _,g in mapping.groupby('zone_id',sort=True):
        choices=g[g.node_index.isin(access)]
        flagged=choices[original.loc[choices.index].eq(1)]
        node=int((flagged if len(flagged) else choices).node_index.min())
        mapping.loc[mapping.node_index.eq(node),'is_centroid']=1
    resolution['selected_memberships']=mapping[mapping.node_index.isin(duplicates.node_index)][['node_index','zone_id']].to_dict('records')
    mapping.attrs['overlap_resolution']=resolution
    return mapping


def copy_network(source, destination, router, dynamics):
    required=['base/nodes.csv','base/edges.csv','base/crs.info']
    if router=='NetworkTTMatrix':required += ['ff/tables/nn_fastest_tt.npy','ff/tables/nn_fastest_distance.npy']
    if router=='NetworkPartialPreprocessedCpp':required += ['base/tt_matrix.npy','base/dis_matrix.npy']
    if dynamics is None and router!='NetworkTTMatrix':
        required += [str(p.relative_to(source)) for p in source.glob('[0-9]*/edges_td_att.csv')]
    elif dynamics:
        required.append(dynamics)
        frame=pd.read_csv(safe_input(source,dynamics))
        if 'travel_time_folder' in frame:
            required += [str(Path(folder)/'edges_td_att.csv') for folder in frame.travel_time_folder.astype(str).unique()]
    hashes={}
    for name in sorted(set(required)):
        path=safe_input(source,name);hashes[name]=file_digest(path)
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    return hashes


def build(config_path, data_root, output, fleet_multiplier=1):
    config_path,data_root,output=Path(config_path).resolve(),Path(data_root).resolve(),Path(output).resolve()
    if output.exists():raise ValueError('Refusing to overwrite city bundle')
    c=json.loads(config_path.read_text())
    if c.get('schema_version')!=1 or not re.fullmatch(r'[a-z][a-z0-9_-]*',c.get('city','')):
        raise ValueError('Invalid city configuration identity/version')
    start,end,warm=c['evaluation_start'],c['evaluation_end'],c['warmup_start'];dt=c.get('time_step',60)
    ref0,ref1=c['reference_start'],c['reference_end']
    if not all(type(v) is int for v in [start,end,warm,dt,ref0,ref1]) or not 0<=ref0<ref1<=warm<start<end<=86400 or dt<=0 or 900%dt or any(t%dt for t in [warm,start,end]):
        raise ValueError('Reference must precede warm-up; aligned city windows must be valid')
    if not math.isfinite(fleet_multiplier) or not 0<fleet_multiplier<=10:raise ValueError('Invalid fleet multiplier')
    fleet=max(2,int(round(c['fleet_size']*fleet_multiplier)))
    share,optin,fence=c.get('av_share',.1),c.get('opt_in_share',.3),c.get('fence_share',.3)
    if not 0<share<1 or not 0<=optin<=1 or not 0<fence<=1:raise ValueError('Invalid AV shares')
    av_count=min(fleet-1,max(1,int(round(fleet*share))));human_count=fleet-av_count
    factor=travel_time_factor(c.get('travel_time_factor',1.25))
    controller=c.get('controller','PoolingIRSOnly')
    if controller not in {'PoolingIRSOnly','PoolingIRSAssignmentBatchOptimization'}:raise ValueError('City threshold harness requires an immediate insertion controller')
    if type(c.get('max_route_candidates',30)) is not int or c.get('max_route_candidates',30)<1:raise ValueError('Positive integer route budget required')
    patience=c.get('max_wait_seconds',480)
    if not math.isfinite(patience) or patience<dt:raise ValueError('Patience must cover grid admission')
    for key in ['pickup_service_seconds','dropoff_service_seconds']:
        if not math.isfinite(c.get(key,30)) or not 0<=c.get(key,30)<86400:raise ValueError('Invalid physical service duration')
    source=source_record();parent=None
    if c['input_kind']=='market_bundle':
        parent=json.loads(safe_input(data_root,'manifest.json').read_text())
        if parent['status']!='complete' or parent['source']['code_digest']!=c['parent_code_digest']:
            raise ValueError('Unexpected parent source or incomplete parent dataset')
        if market_dependencies()!=parent['dependencies']:raise ValueError('Parent dataset dependency mismatch')
        for name,h in parent['output_sha256'].items():
            if file_digest(safe_input(data_root,name))!=h:raise ValueError('Parent dataset input hash mismatch')
        original=pd.read_csv(data_root/'observed_cohort.csv')
        if original.request_id.duplicated().any():raise ValueError('Duplicate parent request')
        if (parent['evaluation_start'],parent['evaluation_end'],parent['simulation_start'])!=(start,end,warm):
            raise ValueError('Declared city window differs from parent cohort')
        mapping_path=data_root/'zones/network/node_zone_info.csv';network=data_root/'network'
        router=parent['network_type'];dynamics=json.loads((data_root/'parameters.json').read_text()).get('nw_dynamic_f')
        reference=pd.read_csv(data_root/'training_context.csv')
        ref_counts=reference.PULocationID.value_counts().to_dict()
        initial=pd.read_csv(data_root/'fleetctrl/initial_vehicle_distribution/market_network/initial.csv')
        counts=dict(source_rows=len(original),retained=len(original),unmapped=0,outside_window=0)
        request_source=data_root/'observed_cohort.csv'
        observed=original.copy()
        observed['pooling_allowed']=original.pooling_allowed.astype(int)
        reference_description=dict(kind='prior_training_dates',dates=parent['training_dates'],rows=len(reference),source_sha256=file_digest(data_root/'training_context.csv'))
    elif c['input_kind']=='native':
        network=(data_root/c['network_path']).resolve()
        if not network.is_relative_to(data_root):raise ValueError('Network escapes dataset root')
        mapping_path=safe_input(data_root,c['zone_map']);request_source=safe_input(data_root,c['requests'])
        router=c['router'];dynamics=c.get('network_dynamics')
        original=pd.read_csv(request_source)
        for key in ['request_id','rq_time','start','end']:original[key]=integer_column(original[key],key)
        if original.request_id.duplicated().any() or original.rq_time.lt(0).any() or original.rq_time.ge(86400).any():
            raise ValueError('Native demand needs unique IDs and same-day request times')
        nodes=pd.read_csv(network/'base/nodes.csv');mapping=normalize_mapping(mapping_path,nodes,c.get('zone_overlap_policy','error'))
        mapped=set(mapping.node_index)
        valid=original.start.isin(mapped)&original.end.isin(mapped)
        retained=original[valid].copy().sort_values(['rq_time','request_id'])
        reference=retained[retained.rq_time.ge(ref0)&retained.rq_time.lt(ref1)]
        if reference.empty:raise ValueError('No independent pre-warm-up reference demand')
        node_zones=mapping.set_index('node_index').zone_id
        ref_counts=reference.start.map(node_zones).value_counts().to_dict()
        counts_by_node=reference.start.value_counts().sort_index()
        initial=pd.DataFrame(dict(node_index=counts_by_node.index,probability=counts_by_node/counts_by_node.sum()))
        observed=retained[retained.rq_time.ge(warm)&retained.rq_time.lt(end)].copy()
        observed['request_s']=observed.rq_time;observed['is_evaluation_request']=observed.rq_time.ge(start)
        observed['pooling_allowed']=1  # explicit native ride-pooling benchmark assumption, not observed consent
        counts=dict(source_rows=len(original),retained=len(observed),unmapped=int((~valid).sum()),outside_window=int(valid.sum()-len(observed)))
        reference_description=dict(kind='strictly_earlier_same_source_clock',start=ref0,end=ref1,rows=len(reference),request_ids=reference.request_id.astype(int).tolist())
    else:raise ValueError('Unsupported city input kind')
    if router not in ROUTERS:raise ValueError('Unsupported city router')
    if observed.empty or not observed.is_evaluation_request.any():raise ValueError('Empty city evaluation cohort')
    if 'nodes' not in locals():nodes=pd.read_csv(network/'base/nodes.csv')
    mapping=normalize_mapping(mapping_path,nodes,c.get('zone_overlap_policy','error'))
    zones=sorted(mapping.zone_id.unique().tolist())
    selected=sorted(sorted(zones,key=lambda z:(-ref_counts.get(z,0),z))[:max(1,math.ceil(len(zones)*fence))])
    if parent and selected!=parent['av_product']['fence_zones']:raise ValueError('Parent historical fence no longer reproduces')
    if initial.node_index.duplicated().any() or not set(initial.node_index)<=set(mapping.node_index) or not np.isfinite(initial.probability).all() or initial.probability.le(0).any() or not np.isclose(initial.probability.sum(),1):
        raise ValueError('Invalid reference-derived initial distribution')
    output.mkdir(parents=True)
    manifest=dict(status='building',data_kind='fleetpy_city_benchmark',city=c['city'],source=source,
        dependencies=market_dependencies(),config_sha256=file_digest(config_path),config=c,
        input_kind=c['input_kind'],request_source_sha256=file_digest(request_source),
        zone_source_sha256=file_digest(mapping_path),provenance=c['provenance'],
        filtered_counts=counts,reference=reference_description,
        evaluation_start=start,evaluation_end=end,simulation_start=warm,
        target_count=len(observed),evaluation_count=int(observed.is_evaluation_request.sum()),warmup_count=int((~observed.is_evaluation_request).sum()),
        fleet_size=fleet,fleet_multiplier=fleet_multiplier,network_type=router,
        shared_initialization='city-av-placement-v1',runtime_files_sha256=routing_runtime(router),
        mapping_normalization=mapping.attrs['overlap_resolution'],
        av_product=dict(av_count=av_count,human_count=human_count,requested_share=share,opt_in_share=optin,fence_zones=selected,
            fence_selection='densest 30% of mapped access zones by strictly separate reference pickups; stable zone ties',travel_time_factor=factor),
        assumptions=dict(patience_seconds=patience,pooling='native all-pooling benchmark assumption' if not parent else 'preserved TLC source consent',
            pickup_service_seconds=c.get('pickup_service_seconds',30),dropoff_service_seconds=c.get('dropoff_service_seconds',30),
            execution_noise_sigma=0,human_acceptance='off',human_repositioning='off',av_repositioning='off',
            fleet='explicit benchmark fleet, not observed online supply',opt_in='per-request assumption, not empirical rider adoption',
            reference='no evaluation or warm-up pickups used to select fence/initial distribution',
            network='provided exogenous benchmark dynamics; no claim of held-out empirical travel forecasting'))
    ambiguous=set(r['node_index'] for r in manifest['mapping_normalization']['original_memberships'])
    touches=observed.start.isin(ambiguous)|observed.end.isin(ambiguous)
    manifest['mapping_normalization'].update(affected_retained_requests=int(touches.sum()),
        affected_evaluation_requests=int((touches&observed.is_evaluation_request).sum()))
    if parent:manifest['parent_dataset']=dict(manifest_sha256=file_digest(data_root/'manifest.json'),source=parent['source'],data_kind=parent['data_kind'],changes='Rebuilt comparison: no execution noise, shared placement, constant benchmark patience/service; historical network factors and source consent retained')
    json_write(output/'manifest.json',manifest)
    try:
        manifest['network_sha256']=copy_network(network,output/'network',router,dynamics)
        (output/'zones/network').mkdir(parents=True);mapping.to_csv(output/'zones/network/node_zone_info.csv',index=False)
        pd.DataFrame(dict(zone_id=zones)).to_csv(output/'zones/general_information.csv',index=False)
        observed=observed.sort_values(['request_s','request_id']).reset_index(drop=True)
        observed.to_csv(output/'observed_cohort.csv',index=False)
        requests=causal_requests(observed,dt,np.full(len(observed),patience))
        requests['pooling_allowed']=observed.pooling_allowed
        requests['pickup_service_time']=c.get('pickup_service_seconds',30);requests['dropoff_service_time']=c.get('dropoff_service_seconds',30)
        (output/'demand').mkdir();requests.to_csv(output/'demand/requests.csv',index=False)
        initial.sort_values('node_index').to_csv(output/'initial_distribution.csv',index=False)
        (output/'vehicles').mkdir();base=(ROOT/'data/vehicles/default_vehtype.csv').read_bytes()
        (output/'vehicles/default_vehtype.csv').write_bytes(base)
        av,n=re.subn(rb'(?m)^(vtype_name_full,)[^\r\n]+',lambda m:m[1]+b'av_vehtype',base,count=1)
        if n!=1:raise ValueError('Missing vehicle type label')
        (output/'vehicles/av_vehtype.csv').write_bytes(av.rstrip(b'\r\n')+f'\ntravel_time_factor,{factor}\n'.encode())
        (output/'forecasts/900').mkdir(parents=True);(output/'fleetctrl').mkdir();(output/'infra').mkdir()
        p=load_parameters(ROOT/'studies/example_study/scenarios/constant_config_ir.csv',ROOT/'studies/example_study/scenarios/example_ir_only.csv')
        p.update(study_name='city_av',scenario_name=c['city'],network_name='city_network',demand_name='city',rq_file='requests.csv',
            network_type=router,nw_dynamic_f=dynamics,random_seed=0,random_stream_mode='independent',start_time=warm,
            end_time=max(end,int(requests.rq_time.max())+dt),time_step=dt,n_cpu_per_sim=1,
            op_module=controller,op_fleet_composition={'default_vehtype':human_count,'av_vehtype':av_count},
            op_max_wait_time=patience,op_reoptimisation_timestep=dt,op_rh_immediate_max_routes=c.get('max_route_candidates',30),
            op_const_boarding_time=30,op_request_constraints=True,record_promised_times=True,network_tt_noise_sigma=0,
            completion_tail_max_seconds=86400,op_zone_system='city_zones',op_temporal_resolution=900,
            op_av_vehicle_types=[['av_vehtype']],op_av_zones=[selected],op_av_opt_in_share=optin,
            op_av_preference_s=0,op_av_repositioning=False,op_av_repositioning_timestep=900)
        json_write(output/'parameters.json',p)
        if source_record()['code_digest']!=source['code_digest']:raise RuntimeError('Source changed during city build')
        if file_digest(config_path)!=manifest['config_sha256'] or file_digest(request_source)!=manifest['request_source_sha256'] or file_digest(mapping_path)!=manifest['zone_source_sha256']:
            raise RuntimeError('City source data changed during build')
        for name,h in manifest['network_sha256'].items():
            if file_digest(network/name)!=h:raise RuntimeError('City network source changed during build')
        manifest.update(status='complete',output_sha256={str(p.relative_to(output)):file_digest(p) for p in output.rglob('*') if p.is_file() and p.name!='manifest.json'})
        json_write(output/'manifest.json',manifest);return manifest
    except BaseException as error:
        manifest.update(status='failed',error=f'{type(error).__name__}: {error}');json_write(output/'manifest.json',manifest);raise
