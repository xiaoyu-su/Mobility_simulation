"""Validate actual mixed-fleet service and report fixed-cohort product tradeoffs."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.fleetctrl.av_product import opt_in
from tools.synthetic_market.report import activity_frame


def av_report(bundle, output):
    bundle,output=Path(bundle),Path(output)
    audit=json.loads((output/'av_product_op_0.json').read_text())
    ids=set(audit['av_ids']);zones=set(audit['zones'])
    mapping=pd.read_csv(bundle/'zones/network/node_zone_info.csv').set_index('node_index').zone_id
    cohort=pd.read_csv(bundle/'observed_cohort.csv').set_index('request_id')
    users=pd.read_csv(output/'1_user-stats.csv').set_index('request_id')
    assert users.index.is_unique and set(users.index)==set(cohort.index)
    eligible=(cohort.start.map(mapping).isin(zones)&cohort.end.map(mapping).isin(zones)
              &cohort.index.to_series().map(lambda rid:opt_in(rid,0,audit['opt_in_share'])))
    served=users.dropoff_time.notna();av=users.vehicle_id.isin(ids)&served
    if (av&~eligible).any():raise RuntimeError('Executed AV service violates opt-in or endpoint fence')
    if any(mapping.loc[node] not in zones for node in audit['initial_nodes'].values()):
        raise RuntimeError('AV initial position is outside the fence')
    if set(map(int,audit['initial_nodes']))!=ids:raise RuntimeError('Missing AV initial-state audit')
    legs=activity_frame(output);av_legs=legs.vehicle_id.isin(ids)
    if (av_legs&legs.status.eq('out_of_service')).any():raise RuntimeError('AV entered a human shift')
    human_audit=output/'repositioning_op_0.json'
    if human_audit.exists():
        human=json.loads(human_audit.read_text())
        if any(ids&set(r['assigned_vehicles']) for r in human['rounds']):raise RuntimeError('Human repositioning dispatched AVs')
    for round_ in audit['repositioning_rounds']:
        assigned=[a['vehicle_id'] for a in round_['assignments']]
        if len(assigned)!=len(set(assigned)) or not set(assigned)<=ids:raise RuntimeError('Invalid AV repositioning roster')
        if any(a['zone_id'] not in zones or mapping.loc[a['node_index']]!=a['zone_id'] for a in round_['assignments']):
            raise RuntimeError('AV reposition target escapes the fence')
    acceptance=output/'driver_acceptance_op_0.csv'
    if acceptance.exists():
        decisions=pd.read_csv(acceptance)
        av_decisions=decisions[decisions.vehicle_id.isin(ids)]
        if not av_decisions.probability.eq(1).all() or not av_decisions.accepted.all():
            raise RuntimeError('AV rejected a selected feasible assignment')
    config=json.loads((output/'00_config.json').read_text())['scenario_parameters']
    meta=json.loads((bundle/'manifest.json').read_text())
    start,end=meta['evaluation_start'],meta['evaluation_end']
    roster=pd.read_csv(output/'2_vehicle_types.csv')
    evaluated=cohort.is_evaluation_request;wait=users.pickup_time-cohort.request_s
    record=dict(evaluation_requests=int(evaluated.sum()),completed=int((served&evaluated).sum()),
                av_completed=int((av&evaluated).sum()),human_completed=int((served&~av&evaluated).sum()),
                eligible_requests=int((eligible&evaluated).sum()),av_count=len(ids),human_count=len(roster)-len(ids),
                preference_seconds=audit['preference_seconds'],av_repositioning=audit['repositioning'],
                rule_violations=0,all_accepted_complete=bool(users.pickup_time.notna().equals(users.dropoff_time.notna())),
                av_served_share=float((av&evaluated).sum()/max(1,(served&evaluated).sum())),
                eligible_av_service_rate=float((av&evaluated).sum()/max(1,(eligible&evaluated).sum())))
    for name,mask in [('eligible',eligible),('other',~eligible),('av',av),('human',served&~av)]:
        selected=mask&evaluated&served
        record[name+'_served']=int(selected.sum())
        record[name+'_arrival_wait_mean_s']=float(wait[selected].mean()) if selected.any() else None
        record[name+'_arrival_wait_median_s']=float(wait[selected].median()) if selected.any() else None
    duration=(np.minimum(legs.end_time,end)-np.maximum(legs.start_time,start)).clip(lower=0)
    av_idle=len(ids)*(end-start)-float(duration[av_legs].sum())
    for kind,mask,count in [('av',av_legs,len(ids)),('human',~av_legs,len(roster)-len(ids))]:
        online=count*(end-start)-float(duration[mask&legs.status.eq('out_of_service')].sum())
        occupied=float(duration[mask&legs.occupancy.gt(0)].sum())
        record[kind+'_utilization']=occupied/online if online else None
        record[kind+'_trips_per_online_hour']=record[kind+'_completed']/(online/3600) if online else None
        record[kind+'_reposition_distance_km']=float(legs.loc[mask&legs.status.eq('reposition'),'driven_distance'].sum()/1000)
    record['av_idle_share']=max(0,av_idle)/(len(ids)*(end-start)) if ids else None
    dispatch=pd.read_csv(output/'av_dispatch_op_0.csv')
    if dispatch.request_id.duplicated().any():raise RuntimeError('Duplicate AV dispatch diagnostic')
    diagnosed=dispatch[dispatch.request_id.isin(cohort.index[evaluated])&dispatch.av_eligible&~dispatch.is_av]
    gaps=diagnosed.idle_av_minus_winner_eta_s.dropna()
    record['human_won_eligible_with_idle_av']=len(gaps)
    record['nearest_idle_av_minus_winner_eta_median_s']=float(gaps.median()) if len(gaps) else None
    record['human_won_while_idle_av_closer']=int(gaps.lt(0).sum())
    record['dispatch_records']=len(dispatch)
    record['av_reposition_orders']=sum(len(r['assignments']) for r in audit['repositioning_rounds'])
    if 'eta_threshold_seconds' in audit or 'retarget_repositioning' in audit or (output/'vehicle_time_factors.json').exists():
        record.update(eta_threshold_seconds=audit.get('eta_threshold_seconds'),opt_in_share=audit['opt_in_share'],
                      retarget_repositioning=audit.get('retarget_repositioning',False),forecast_sigma=audit.get('forecast_sigma',0),
                      joint_repositioning=audit.get('joint_repositioning',False))
        factors_path=output/'vehicle_time_factors.json'
        if factors_path.exists():
            factors=json.loads(factors_path.read_text());record['av_travel_time_factor']=factors['av_vehtype']['effective']
            if 'vehicle_travel_time_factor' not in legs:raise RuntimeError('Loaded vehicle factor missing from actual leg records')
            expected=legs.vehicle_type.map({k:v['effective'] for k,v in factors.items()})
            if not np.allclose(legs.vehicle_travel_time_factor,expected):raise RuntimeError('Executed vehicle factor differs from loader audit')
        else:record['av_travel_time_factor']=1.0
        for kind,mask in [('av',av_legs),('human',~av_legs)]:
            distance=float(legs.loc[mask,'driven_distance'].sum())
            empty=float(legs.loc[mask&legs.occupancy.eq(0),'driven_distance'].sum())
            record[kind+'_empty_distance_km']=empty/1000
            record[kind+'_empty_distance_share']=empty/distance if distance else None
        decisions=audit.get('threshold_decisions',[])
        for d in decisions:
            qualifies=d['best_av_eta_s'] is not None and (d['best_human_eta_s'] is None or d['best_av_eta_s']<=d['best_human_eta_s']+d['threshold_s']+1e-9)
            if (d['selected_pool']=='av')!=qualifies:raise RuntimeError('AV threshold policy was not respected')
        for rid,d in {d['request_id']:d for d in decisions}.items():
            if rid in users.index and pd.notna(users.loc[rid,'dropoff_time']):
                if (users.loc[rid,'vehicle_id'] in ids)!=(d['selected_pool']=='av'):
                    raise RuntimeError('Executed service product differs from the accepted threshold dispatch')
        record['threshold_decisions']=len(decisions)
        record['threshold_av_choices']=sum(d['selected_pool']=='av' for d in decisions)
        record['threshold_violations']=0
        record['av_retarget_orders']=sum(a.get('retargeted',False) for r in audit['repositioning_rounds'] for a in r['assignments'])
        coverage=audit.get('human_coverage_rounds',[])
        for r in coverage:
            for z,value in r['expected_av_coverage'].items():
                if value<0 or value>r['original_demand'].get(z,0)+1e-9 or value>r['expected_av_eligible'].get(z,0)+1e-9 or value>r['available_av'].get(z,0)+1e-9:
                    raise RuntimeError('Joint AV coverage violates forecast/availability bounds')
                if not np.isclose(r['adjusted_human_demand'].get(z,0),r['original_demand'].get(z,0)-value):raise RuntimeError('Incorrect residual human demand')
        record['human_forecast_av_coverage_sum']=sum(sum(r['expected_av_coverage'].values()) for r in coverage)
        record['observed_av_trips_per_day']=None
        record['daily_benchmark_scope']='Three-hour request cohort; no extrapolated daily-trip claim'
    record['time_scope']='Evaluation clock window for utilization; request cohort for trips/waits; whole-run reposition km'
    (output/'av_report.json').write_text(json.dumps(record,indent=2,allow_nan=False)+'\n')
    return record
