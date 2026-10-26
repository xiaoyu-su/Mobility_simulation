"""Inspect actual physical service with the same definitions in every city."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.fleetctrl.av_product import opt_in
from src.misc.seeding import file_digest, canonical_digest
from tools.synthetic_market.build import json_write
from tools.synthetic_market.report import request_ids


def capacity_audit(legs, users, capacities):
    """Check seated loads around exchanges; boarding logs contain an event union.

    FleetPy adds incoming riders at stop start and removes departing riders at
    stop end. Thus the raw stationary union can exceed capacity even though the
    pre-stop and post-stop loads both fit. Driving must always fit directly.
    """
    sizes=users.number_passenger.to_dict();known=set(sizes);unions=0
    if any(not np.isfinite(n) or n<=0 for n in sizes.values()) or any(not np.isfinite(c) or c<=0 for c in capacities.values()):
        raise RuntimeError('Invalid city passenger counts or capacities')
    for leg in legs.itertuples():
        cap=capacities[leg.vehicle_id];load=float(leg.occupancy)
        onboard=set(request_ids(leg.rq_on_board))
        if not onboard<=known or not np.isclose(load,sum(sizes[r] for r in onboard)):
            raise RuntimeError('City occupancy differs from actual passenger identities')
        before=after=load
        if leg.status=='boarding':
            incoming=set(request_ids(leg.rq_boarding));outgoing=set(request_ids(leg.rq_alighting))
            if not incoming<=onboard or not outgoing<=onboard:raise RuntimeError('City exchange IDs are absent from recorded union')
            before-=sum(sizes[r] for r in incoming);after-=sum(sizes[r] for r in outgoing)
            if load>cap:unions+=1
        if min(before,after)<0 or max(before,after)>cap:raise RuntimeError('City capacity violation')
    return unions


def city_report(bundle, output):
    bundle,output=Path(bundle),Path(output)
    meta=json.loads((bundle/'manifest.json').read_text())
    cohort=pd.read_csv(bundle/'observed_cohort.csv').set_index('request_id')
    demand=pd.read_csv(bundle/'demand/requests.csv').set_index('request_id')
    users=pd.read_csv(output/'1_user-stats.csv').set_index('request_id')
    if not users.index.is_unique or set(users.index)!=set(cohort.index):raise RuntimeError('Incomplete/duplicate city demand accounting')
    served=users.dropoff_time.notna()
    if not users.pickup_time.notna().equals(served) or not users.promised_pickup_time.notna().equals(served):
        raise RuntimeError('Accepted city booking was not completed')
    if (users.pickup_time-cohort.request_s).lt(-1e-7).any() or (users.dropoff_time-users.pickup_time).lt(-1e-7).any():raise RuntimeError('Noncausal city trip')
    contract=json.loads((output/'market_input_contract.json').read_text())
    tail=json.loads((output/'completion_tail.json').read_text())
    if not contract['all_booked_requests_completed'] or contract['booked_requests']!=int(served.sum()) or not contract['physical_tail_complete']:
        raise RuntimeError('City booking contract failed')
    if tail['status']!='complete' or tail['remaining_tasks'] or tail['onboard_request_ids']:raise RuntimeError('City tail remains active')
    config=json.loads((output/'00_config.json').read_text())['scenario_parameters']
    if config.get('op_repo_method') or config.get('op_driver_acceptance') not in (None,False,'off') or config.get('op_av_repositioning',False):
        raise RuntimeError('City core comparison unexpectedly enables acceptance/repositioning')
    roster=pd.read_csv(output/'2_vehicle_types.csv');ids=set(roster.loc[roster.vehicle_type.eq('av_vehtype'),'vehicle_id'])
    if len(roster)!=meta['fleet_size']:raise RuntimeError('City fleet size changed')
    search=json.loads((output/'city_search_contract.json').read_text())
    if search['designated_slots']!=list(range(meta['av_product']['human_count'],meta['fleet_size'])) or search['per_group_position_budget']!=config['op_rh_immediate_max_routes'] or search['all_human_shadow_groups']!=bool(not ids):
        raise RuntimeError('Unmatched city candidate-search budgets')
    product=json.loads((output/'av_product_op_0.json').read_text()) if ids else None
    if product and set(product['av_ids'])!=ids:raise RuntimeError('AV audit roster differs from actual vehicles')
    mapping=pd.read_csv(bundle/'zones/network/node_zone_info.csv').set_index('node_index').zone_id
    fence=set(meta['av_product']['fence_zones']);share=meta['av_product']['opt_in_share']
    eligible=(cohort.start.map(mapping).isin(fence)&cohort.end.map(mapping).isin(fence)&cohort.index.to_series().map(lambda rid:opt_in(rid,0,share)))
    av=users.vehicle_id.isin(ids)&served
    if (av&~eligible).any():raise RuntimeError('Actual AV trip violates city consent/fence')
    placement=pd.read_csv(output/'initial_placement.csv',float_precision='round_trip')
    if placement.vehicle_id.duplicated().any() or set(placement.vehicle_id)!=set(roster.vehicle_id):raise RuntimeError('Invalid shared city placement')
    designated=placement.vehicle_id.ge(meta['av_product']['human_count'])
    if not placement.loc[designated,'node_index'].map(mapping).isin(fence).all():raise RuntimeError('Designated AV slots start outside fence')
    types=roster.set_index('vehicle_id').vehicle_type
    actual_initial=[[int(r.operator_id),int(r.vehicle_id),str((int(r.node_index),None,None)),float(r.soc),types.loc[r.vehicle_id]]
                    for r in placement.sort_values(['operator_id','vehicle_id']).itertuples()]
    random_audit=json.loads((output/'random_streams.json').read_text())
    if canonical_digest(actual_initial)!=random_audit['initial_vehicle_state_sha256']:
        raise RuntimeError('Shared placement differs from actual simulator initialization audit')
    legs=pd.read_csv(output/'2-0_op-stats.csv',low_memory=False)
    if not np.isfinite(legs[['start_time','end_time','occupancy','driven_distance']].to_numpy(dtype=float)).all() or legs.end_time.lt(legs.start_time-1e-7).any():raise RuntimeError('Invalid city vehicle activity')
    limits={t:float(pd.read_csv(bundle/'vehicles'/f'{t}.csv',header=None,index_col=0).iloc[:,0]['maximum_passengers']) for t in roster.vehicle_type.unique()}
    capacities={row.vehicle_id:limits[row.vehicle_type] for row in roster.itertuples()}
    exchange_unions=capacity_audit(legs,users,capacities)
    if legs.status.isin(['out_of_service','reposition']).any():raise RuntimeError('City core unexpectedly executes shifts/repositioning')
    for _,group in legs.groupby('vehicle_id'):
        group=group.sort_values(['start_time','end_time'])
        if np.any(group.start_time.to_numpy()[1:]<group.end_time.to_numpy()[:-1]-1e-7):raise RuntimeError('Overlapping city vehicle legs')
    boarded=set();alighted=set();private=set(demand.index[demand.pooling_allowed.eq(0)])
    for leg in legs.itertuples():
        if leg.status=='route' and leg.occupancy>1 and private&set(request_ids(leg.rq_on_board)):raise RuntimeError('Private city booking pooled')
        if leg.status!='boarding':continue
        incoming=request_ids(leg.rq_boarding);outgoing=request_ids(leg.rq_alighting)
        boarded.update(incoming);alighted.update(outgoing)
        service=[demand.loc[rid,'pickup_service_time'] for rid in incoming]+[demand.loc[rid,'dropoff_service_time'] for rid in outgoing]
        if service and leg.end_time-leg.start_time<max(service)-1e-7:raise RuntimeError('City service duration was shortened')
    if boarded!=alighted or boarded!=set(users.index[served]):raise RuntimeError('City booking lacks actual boarding/alighting')
    factors=output/'vehicle_time_factors.json'
    if factors.exists():
        expected=json.loads(factors.read_text())
        if 'vehicle_travel_time_factor' not in legs or not np.allclose(legs.vehicle_travel_time_factor,legs.vehicle_type.map({k:v['effective'] for k,v in expected.items()})):
            raise RuntimeError('Actual city type factor differs from loader')
        av_factor=expected.get('av_vehtype',{}).get('effective')
    else:av_factor=None if not ids else 1.0
    if product:
        if product['zones']!=sorted(fence) or product['opt_in_share']!=share:raise RuntimeError('City product assumptions changed')
        for decision in product.get('threshold_decisions',[]):
            qualifies=decision['best_av_eta_s'] is not None and (decision['best_human_eta_s'] is None or decision['best_av_eta_s']<=decision['best_human_eta_s']+decision['threshold_s']+1e-9)
            if qualifies!=(decision['selected_pool']=='av'):raise RuntimeError('City threshold selection violation')
        for rid,decision in {d['request_id']:d for d in product.get('threshold_decisions',[])}.items():
            if served.loc[rid] and bool(av.loc[rid])!=(decision['selected_pool']=='av'):raise RuntimeError('Actual city product changed after booking')
    evaluated=cohort.is_evaluation_request;wait=users.pickup_time-cohort.request_s
    n=int((served&evaluated).sum());a=int((av&evaluated).sum());first_av=meta['av_product']['human_count']
    record=dict(city=meta['city'],evaluation_requests=int(evaluated.sum()),warmup_requests=int((~evaluated).sum()),
        fleet_size=len(roster),av_count=len(ids),human_count=len(roster)-len(ids),completed=n,av_completed=a,human_completed=n-a,
        completion_rate=n/int(evaluated.sum()),eligible_requests=int((eligible&evaluated).sum()),
        av_served_share=a/n if n else None,eligible_av_service_rate=a/int((eligible&evaluated).sum()) if (eligible&evaluated).any() else None,
        eta_threshold_seconds=config.get('op_av_eta_threshold_s'),preference_seconds=config.get('op_av_preference_s',0),
        av_travel_time_factor=av_factor,all_accepted_complete=True,rule_violations=0,
        actual_boarded_and_alighted=int(served.sum()),shared_placement_sha256=file_digest(output/'initial_placement.csv'),
        stationary_exchange_union_rows=exchange_unions,
        capacity_definition='Moving load and pre/post exchange load fit actual vehicle capacity; raw boarding occupancy is an event union',
        threshold_decisions=len(product.get('threshold_decisions',[])) if product else 0,
        threshold_av_choices=sum(d['selected_pool']=='av' for d in product.get('threshold_decisions',[])) if product else 0,
        human_won_while_idle_av_closer=0,human_won_eligible_with_idle_av=0,
        tail_end_seconds=tail['last_processed_time'],
        time_scope='Trips/waits: evaluation request IDs; occupied/online/idle: evaluation clock; distance: full physical warm-up and fulfillment tail',
        inference_scope='Counterfactual benchmark; city inputs/load/source types differ; no geography-only causal or empirical AV adoption claim')
    for name,mask in [('all',pd.Series(True,index=users.index)),('eligible',eligible),('other',~eligible),('av',av),('human',served&~av)]:
        selected=mask&evaluated&served
        record[name+'_served']=int(selected.sum())
        record[name+'_wait_mean_s']=float(wait[selected].mean()) if selected.any() else None
        record[name+'_wait_median_s']=float(wait[selected].median()) if selected.any() else None
    start,end=meta['evaluation_start'],meta['evaluation_end'];duration=(np.minimum(legs.end_time,end)-np.maximum(legs.start_time,start)).clip(lower=0)
    avlegs=legs.vehicle_id.isin(ids)
    for kind,mask,count in [('av',avlegs,len(ids)),('human',~avlegs,len(roster)-len(ids))]:
        online=count*(end-start);occupied=float(duration[mask&legs.occupancy.gt(0)].sum());active=float(duration[mask].sum())
        distance=float(legs.loc[mask,'driven_distance'].sum());empty=float(legs.loc[mask&legs.occupancy.eq(0),'driven_distance'].sum())
        record[kind+'_utilization']=occupied/online if online else None
        record[kind+'_idle_share']=max(0,online-active)/online if online else None
        record[kind+'_trips_per_online_hour']=record[kind+'_completed']/(online/3600) if online else None
        record[kind+'_empty_distance_km']=empty/1000
        record[kind+'_distance_km']=distance/1000
        record[kind+'_empty_distance_share']=empty/distance if distance else None
    record['fleet_empty_distance_km']=record['av_empty_distance_km']+record['human_empty_distance_km']
    record['retained_human_completed']=int((served&evaluated&users.vehicle_id.lt(first_av)).sum())
    record['retained_human_trips_per_online_hour']=record['retained_human_completed']/(first_av*(end-start)/3600)
    record['designated_slot_completed']=int((served&evaluated&users.vehicle_id.ge(first_av)).sum())
    if product:
        diagnostic=pd.read_csv(output/'av_dispatch_op_0.csv')
        if diagnostic.request_id.duplicated().any():raise RuntimeError('Duplicate city dispatch diagnostic')
        selected=diagnostic[diagnostic.request_id.isin(cohort.index[evaluated])&diagnostic.av_eligible&~diagnostic.is_av]
        gaps=selected.idle_av_minus_winner_eta_s.dropna()
        record['human_won_while_idle_av_closer']=int(gaps.lt(0).sum())
        record['human_won_eligible_with_idle_av']=len(gaps)
    json_write(output/'city_report.json',record);return record
