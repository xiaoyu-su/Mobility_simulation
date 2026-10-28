"""Read-only physical accounting with explicit populations, units and clocks."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.fleetctrl.av_product import opt_in
from src.misc.globals import G_DIR_VEH
from tools.city_av.report import capacity_audit
from tools.paired_eval.metrics import per_driver_metrics,distribution_metrics,driver_acceptance_summary
from tools.synthetic_market.report import request_ids

# name: unit, desirable direction, population/time definition
CATALOG={
 'requests':('requests','contextual','All evaluation-cohort requests, including unserved'),
 'completed':('requests','higher','Evaluation requests with actual pickup and dropoff, including later fulfillment'),
 'unserved':('requests','lower','Evaluation requests without completed service'),
 'completion_rate':('fraction','higher','Completed / all evaluation-cohort requests'),
 'wait_mean_s':('s','lower','Actual boarding start minus original request time, served evaluation requests'),
 'wait_p50_s':('s','lower','Median wait among served evaluation requests'),
 'wait_p95_s':('s','lower','95th percentile wait among served evaluation requests'),
 'ride_mean_s':('s','contextual','Dropoff/alighting start minus pickup/boarding start; served evaluation requests'),
 'pickup_promise_mae_s':('s','lower','Absolute actual-minus-accepted pickup error; completed evaluation requests with promises'),
 'pickup_late_rate':('fraction','lower','Actual pickup later than accepted promise; completed evaluation requests with promises'),
 'driver_offer_attempts':('offers','contextual','Actual human offer attempts, whole physical run'),
 'reoffered_requests':('requests','contextual','Unique requests actually offered to more than one distinct human driver; whole run'),
 'repeat_driver_offer_attempts':('offers','contextual','Repeated attempts to the same request/driver pair; whole run'),
 'driver_outside_choices':('menus','contextual','Driver menus selecting the outside option; whole run; unavailable when choice disabled'),
 'driver_menu_conflicts':('offers','contextual','Selected driver offers lost to request conflicts; whole run; unavailable when choice disabled'),
 'driver_declines':('offers','contextual','Actual declined human offer attempts, whole physical run'),
 'driver_acceptances':('offers','contextual','Actual accepted human offers, whole physical run'),
 'offer_acceptance_rate':('fraction','contextual','Accepted human offer attempts / actual attempts; not request completion'),
 'terminal_declined_requests':('requests','lower','Unique request IDs with a terminal driver decline, whole physical run'),
 'utilization':('fraction','contextual','Occupied vehicle seconds / online vehicle seconds in evaluation clock'),
 'idle_share':('fraction','contextual','Unlogged or explicitly idle online seconds / online seconds in evaluation clock'),
 'empty_distance_km':('km','contextual','Occupancy-zero distance over whole physical run, including warm-up/tail'),
 'empty_distance_share':('fraction','contextual','Empty / all driven distance over the same whole physical run'),
 'av_reposition_distance_km':('km','contextual','Empty AV repositioning distance over the whole physical run'),
 'reposition_distance_km':('km','contextual','Repositioning legs over whole physical run; not all empty driving'),
 'vehicle_modeled_net_earnings_mean_cent':('cent','contextual','Per-driver modeled fare minus distance/fixed/toll cost, whole run/tail; not observed wages'),
 'human_earnings_per_online_hour_mean_cent':('cent/hour','contextual','Mean human-driver modeled net / own online hours, whole run/tail'),
 'human_earnings_cv':('ratio','contextual','Human-driver CV of modeled per-online-hour earnings; whole run/tail'),
 'human_earnings_p10_cent':('cent/hour','contextual','Human driver p10 modeled per-online-hour earnings; whole run/tail'),
 'human_earnings_p50_cent':('cent/hour','contextual','Human driver p50 modeled per-online-hour earnings; whole run/tail'),
 'human_earnings_p90_cent':('cent/hour','contextual','Human driver p90 modeled per-online-hour earnings; whole run/tail'),
 'human_earnings_gini':('fraction','lower','Human-driver modeled per-online-hour earnings Gini; unavailable with negative earnings'),
 'av_count':('vehicles','contextual','Actual loaded AV roster, not requested percentage'),
 'av_completed':('requests','contextual','Completed evaluation requests assigned to actual AV IDs'),
 'human_completed':('requests','contextual','Completed evaluation requests assigned to human IDs'),
 'av_share_served':('fraction','contextual','AV completed / all completed evaluation requests; allocation, not welfare'),
 'av_utilization':('fraction','contextual','Occupied AV seconds / actual AV online seconds in evaluation clock'),
 'av_idle_share':('fraction','contextual','Unlogged or explicitly idle AV seconds / AV online seconds in evaluation clock'),
 'eligible_av_service_rate':('fraction','contextual','AV completed / fixed AV-eligible evaluation requests'),
 'eligible_wait_mean_s':('s','lower','Served evaluation requests satisfying declared opt-in and both-endpoint fence'),
 'other_wait_mean_s':('s','lower','Served evaluation requests outside declared AV eligibility'),
 'av_empty_distance_share':('fraction','contextual','Empty / all AV driven distance, whole physical run'),
 'idle_av_closer_human_won_rate':('fraction','contextual','Eligible human-won diagnostics with idle AV closer / eligible human-won diagnostics with defined ETA gap'),
 'common_human_completed':('requests','contextual','Evaluation trips served by the same always-human prefix IDs within the input regime'),
 'common_human_trips_per_online_hour':('trips/hour','contextual','Same human-prefix evaluation trips / prefix evaluation-clock online hours'),
 'rule_violations':('violations','lower','Zero only after physical accounting, event, capacity and applicable eligibility/privacy checks pass'),
}


def catalog():
    return {k:dict(unit=v[0],preference=v[1],definition=v[2]) for k,v in CATALOG.items()}


def ratio(a,b):return float(a/b) if b else None

def mean(values):return float(values.mean()) if len(values) else None


def measure(folder,bundle=None,meta=None,cost_hashes=None,specification_directory=None):
    """Audit actual outputs without writing into the simulation or its inputs."""
    folder=Path(folder);config=json.loads((folder/'00_config.json').read_text());p=config['scenario_parameters']
    u=pd.read_csv(folder/'1_user-stats.csv').set_index('request_id')
    roster=pd.read_csv(folder/'2_vehicle_types.csv');keys=['operator_id','vehicle_id']
    if u.empty or not u.index.is_unique or roster.empty or roster.duplicated(keys).any():raise ValueError('Incomplete/duplicate request or roster accounting')
    if set(roster.operator_id)!={0} or set(roster.vehicle_id)!=set(range(len(roster))):raise ValueError('Comparison accounting supports one operator')
    audit=json.loads((folder/'random_streams.json').read_text())
    if len(u)!=sum(v['count'] for v in audit['demand'].values()):raise ValueError('Full demand accounting differs from loaded requests')
    served=u.dropoff_time.notna()
    if not u.pickup_time.notna().equals(served):raise ValueError('Picked-up booking lacks completed dropoff')
    promised='promised_pickup_time' in u
    if promised and not u.promised_pickup_time.notna().equals(served):raise ValueError('Accepted promise does not physically complete')
    if not (folder/'final_state.csv').is_file() or not (folder/'standard_eval.csv').is_file():raise ValueError('Missing final simulation/evaluation state')
    if bundle is not None:
        bundle=Path(bundle);c=pd.read_csv(bundle/'observed_cohort.csv').set_index('request_id');demand=pd.read_csv(bundle/'demand/requests.csv').set_index('request_id')
        if set(u.index)!=set(c.index) or set(u.index)!=set(demand.index):raise ValueError('Source cohort/request IDs differ')
        c=c.loc[u.index];demand=demand.loc[u.index];request=c.request_s;selected=c.is_evaluation_request.astype(bool)
        start,end=meta['evaluation_start'],meta['evaluation_end']
        if promised and (u.promised_pickup_time-demand.latest_start_time).gt(1e-6).any():raise ValueError('Offer exceeds original request-clock deadline')
    else:
        request=u.rq_time;start,end=p['start_time'],p['end_time'];selected=request.ge(start)&request.lt(end);demand=None
    if not end>start or (u.pickup_time-request).dropna().lt(-1e-6).any() or (u.dropoff_time-u.pickup_time).dropna().lt(0).any():raise ValueError('Noncausal service or invalid evaluation clock')
    for name in ['completion_tail.json','market_input_contract.json']:
        path=folder/name
        if not path.exists():continue
        x=json.loads(path.read_text())
        if name=='completion_tail.json' and (x['status']!='complete' or x['remaining_tasks'] or x['onboard_request_ids']):raise ValueError('Incomplete physical fulfillment tail')
        if name=='market_input_contract.json' and (not x['all_booked_requests_completed'] or x['booked_requests']!=int(served.sum())):raise ValueError('Incomplete accepted bookings')
    product_path=folder/'av_product_op_0.json';product=json.loads(product_path.read_text()) if product_path.exists() else None
    av_ids=set(product['av_ids']) if product else set();ids=set(roster.vehicle_id)
    if not av_ids<=ids or set(u.loc[served,'vehicle_id'])-ids:raise ValueError('Service references unknown vehicle IDs')
    if product and set(roster.loc[roster.vehicle_type.isin(product['vehicle_types']),'vehicle_id'])!=av_ids:raise ValueError('AV type audit differs from roster')
    eligible=None
    if bundle is not None and 'av_product' in meta:
        mapping=pd.read_csv(bundle/'zones/network/node_zone_info.csv').set_index('node_index').zone_id;fence=meta['av_product']['fence_zones'];share=meta['av_product']['opt_in_share']
        eligible=c.start.map(mapping).isin(fence)&c.end.map(mapping).isin(fence)&c.index.to_series().map(lambda rid:opt_in(rid,0,share))
        if (served&u.vehicle_id.isin(av_ids)&~eligible).any():raise ValueError('AV service violates opt-in or endpoint fence')
    elif product:
        # Generic scenarios can supply an audited dispatch eligibility flag, but
        # source endpoints require a city bundle for independent fence checks.
        raise ValueError('Generic AV comparisons require a city bundle for independent eligibility accounting')
    costdir=Path(specification_directory) if specification_directory else Path(config['directories'][G_DIR_VEH]);specs={}
    from src.misc.seeding import file_digest
    for kind in roster.vehicle_type.unique():
        path=costdir/f'{kind}.csv';h=file_digest(path)
        expected=meta['output_sha256'].get('vehicles/'+path.name) if meta else (cost_hashes or {}).get(path.name)
        if expected!=h:raise ValueError('Unbound or changed vehicle physical/cost specification')
        specs[kind]=float(pd.read_csv(path,header=None,index_col=0).iloc[:,0]['maximum_passengers'])
    legs=pd.read_csv(folder/'2-0_op-stats.csv',low_memory=False)
    if not set(legs.vehicle_id)<=ids or not np.isfinite(legs[['start_time','end_time','occupancy','driven_distance']]).all().all() or legs.end_time.lt(legs.start_time).any():raise ValueError('Invalid physical vehicle activity')
    for _,g in legs.groupby('vehicle_id'):
        g=g.sort_values(['start_time','end_time'])
        if np.any(g.start_time.to_numpy()[1:]<g.end_time.to_numpy()[:-1]-1e-6):raise ValueError('Overlapping vehicle chronology')
    if meta is not None:
        moving=legs[legs.status.eq('reposition')]
        if moving.occupancy.ne(0).any() or not moving.vehicle_id.isin(av_ids).all():raise ValueError('City repositioning carried passengers or moved a human')
        if not p.get('op_av_repositioning') and len(moving):raise ValueError('Disabled AV repositioning executed movement')
        if product and (product['zones']!=sorted(meta['av_product']['fence_zones']) or product['opt_in_share']!=meta['av_product']['opt_in_share']):raise ValueError('Loaded AV product differs from declared eligibility')
    if av_ids:
        factors=json.loads((folder/'vehicle_time_factors.json').read_text())
        if not np.allclose(legs.vehicle_travel_time_factor,legs.vehicle_type.map({k:v['effective'] for k,v in factors.items()})):raise ValueError('Loaded AV timing factors differ from physical execution records')
    capacities={r.vehicle_id:specs[r.vehicle_type] for r in roster.itertuples()};capacity_audit(legs,u,capacities)
    boarded={};alighted={};private=set(demand.index[demand.pooling_allowed.eq(0)]) if demand is not None else set()
    for leg in legs.itertuples():
        if leg.status=='route' and leg.occupancy>1 and private&set(request_ids(leg.rq_on_board)):raise ValueError('Private request was pooled')
        if leg.status!='boarding':continue
        if demand is not None:
            service=[demand.loc[r,'pickup_service_time'] for r in request_ids(leg.rq_boarding)]+[demand.loc[r,'dropoff_service_time'] for r in request_ids(leg.rq_alighting)]
            if service and leg.end_time-leg.start_time<max(service)-1e-6:raise ValueError('Physical passenger service duration is too short')
        for field,target,event in [('rq_boarding',boarded,'pickup_time'),('rq_alighting',alighted,'dropoff_time')]:
            for rid in request_ids(getattr(leg,field)):
                if rid in target or rid not in u.index or u.loc[rid,'vehicle_id']!=leg.vehicle_id or not np.isclose(u.loc[rid,event],leg.start_time,rtol=0,atol=1e-6):raise ValueError('Physical passenger event differs from completed user record')
                target[rid]=leg.end_time
    if set(boarded)!=set(alighted) or set(boarded)!=set(u.index[served]):raise ValueError('Rejected/unserved request has physical service or completed request lacks events')
    drivers=per_driver_metrics(folder,clip_initial_inactivity=p.get('op_dyn_fs_method')=='TimeBasedFS',specification_directory=costdir)
    humans=drivers[~drivers.vehicle_id.isin(av_ids)]
    distribution=distribution_metrics(humans).set_index('metric');earn=distribution.loc['earnings_per_online_hour_cent']
    done=served&selected;av=done&u.vehicle_id.isin(av_ids);wait=u.pickup_time-request;duration=(np.minimum(legs.end_time,end)-np.maximum(legs.start_time,start)).clip(lower=0)
    def exposure(group):
        rows=legs.vehicle_id.isin(group);online=len(group)*(end-start)-float(duration[rows&legs.status.eq('out_of_service')].sum());occupied=float(duration[rows&legs.occupancy.gt(0)].sum());logged=float(duration[rows].sum());idle=max(0,len(group)*(end-start)-logged)+float(duration[rows&legs.status.eq('idle')].sum())
        return online,ratio(occupied,online),ratio(idle,online)
    _,util,idle=exposure(ids);_,avutil,avidle=exposure(av_ids)
    distance=float(legs.driven_distance.sum());empty=float(legs.loc[legs.occupancy.eq(0),'driven_distance'].sum());avlegs=legs.vehicle_id.isin(av_ids)
    always=len(roster)-(meta.get('placement_anchor_av_count',meta['av_product']['av_count']) if meta and 'av_product' in meta else 0);common_ids=set(range(always));online,_,_=exposure(common_ids);human_count=int((done&u.vehicle_id.isin(common_ids)).sum())
    values=dict(requests=int(selected.sum()),completed=int(done.sum()),unserved=int((selected&~served).sum()),completion_rate=ratio(done.sum(),selected.sum()),wait_mean_s=mean(wait[done]),wait_p50_s=float(wait[done].median()) if done.any() else None,wait_p95_s=float(wait[done].quantile(.95)) if done.any() else None,ride_mean_s=mean((u.dropoff_time-u.pickup_time)[done]),utilization=util,idle_share=idle,empty_distance_km=empty/1000,empty_distance_share=ratio(empty,distance),reposition_distance_km=float(legs.loc[legs.status.eq('reposition'),'driven_distance'].sum()/1000),vehicle_modeled_net_earnings_mean_cent=float(drivers.modeled_net_earnings_cent.mean()),human_earnings_per_online_hour_mean_cent=float(earn['mean']),human_earnings_cv=float(earn['cv']),human_earnings_p10_cent=float(earn['p10']),human_earnings_p50_cent=float(earn['p50']),human_earnings_p90_cent=float(earn['p90']),human_earnings_gini=float(earn['gini']),av_count=len(av_ids),av_completed=int(av.sum()),human_completed=int(done.sum()-av.sum()),av_share_served=ratio(av.sum(),done.sum()),av_utilization=avutil,av_idle_share=avidle,av_empty_distance_share=ratio(legs.loc[avlegs&legs.occupancy.eq(0),'driven_distance'].sum(),legs.loc[avlegs,'driven_distance'].sum()),common_human_completed=human_count,common_human_trips_per_online_hour=ratio(human_count,online/3600),rule_violations=0)
    values.update(pickup_promise_mae_s=mean((u.pickup_time-u.promised_pickup_time)[done].abs()) if promised else None,pickup_late_rate=float((u.pickup_time-u.promised_pickup_time)[done].gt(1e-6).mean()) if promised and done.any() else None,eligible_av_service_rate=ratio(av.sum(),(eligible&selected).sum()) if eligible is not None else None,eligible_wait_mean_s=mean(wait[done&eligible]) if eligible is not None else None,other_wait_mean_s=mean(wait[done&~eligible]) if eligible is not None else None,idle_av_closer_human_won_rate=None)
    attempts=driver_acceptance_summary(folder);n=attempts['driver_offer_attempts'];values.update(driver_offer_attempts=n,driver_declines=attempts['driver_declines'],driver_acceptances=attempts['driver_acceptances'],offer_acceptance_rate=ratio(attempts['driver_acceptances'],n),terminal_declined_requests=0)
    values.update(reoffered_requests=0,repeat_driver_offer_attempts=0,driver_outside_choices=None,driver_menu_conflicts=None)
    paths=list(folder.glob('driver_acceptance_op_*.csv'))
    if paths:
        decisions=pd.concat([pd.read_csv(p) for p in paths]);values['terminal_declined_requests']=int(decisions.loc[decisions.terminal_decline,'request_id'].nunique());values['reoffered_requests']=int(decisions.groupby(['operator_id','request_id']).vehicle_id.nunique().gt(1).sum());values['repeat_driver_offer_attempts']=int(len(decisions)-len(decisions.drop_duplicates(['operator_id','request_id','vehicle_id'])))
        terminal=set(decisions.loc[decisions.terminal_decline,'request_id'])
        if terminal&set(u.index[served]):raise ValueError('Terminally declined request received physical service')
    path=folder/'av_dispatch_op_0.csv'
    if path.exists():
        diag=pd.read_csv(path);mask=diag.request_id.isin(u.index[selected])&diag.av_eligible&~diag.is_av;gap=diag.loc[mask,'idle_av_minus_winner_eta_s'].dropna();values['idle_av_closer_human_won_rate']=float(gap.lt(0).mean()) if len(gap) else None
    values['av_reposition_distance_km']=float(legs.loc[avlegs&legs.status.eq('reposition'),'driven_distance'].sum()/1000)
    choice_paths=list(folder.glob('driver_choice_op_*.json'))
    if choice_paths:
        counters=[json.loads(path.read_text())['counters'] for path in choice_paths]
        values['driver_outside_choices']=sum(c['outside_choices'] for c in counters);values['driver_menu_conflicts']=sum(c['conflict_rejections'] for c in counters)
    values={k:None if v is None or not np.isfinite(v) else float(v) for k,v in values.items()}
    frame=pd.DataFrame(dict(request_s=request,is_evaluation_request=selected,served=served,wait_s=wait,av=u.vehicle_id.isin(av_ids)),index=u.index)
    if eligible is not None:frame['eligible']=eligible
    return values,frame,dict(all_physical_checks_pass=True,source_clock='bundle original request_s' if bundle else 'native rq_time',evaluation_start=start,evaluation_end=end,full_requests=len(u),evaluation_requests=int(selected.sum()),accepted_promises_checked=promised,private_consent_checked=demand is not None,full_driver_cost_scope='whole physical horizon/tail; modeled, not observed wages')
