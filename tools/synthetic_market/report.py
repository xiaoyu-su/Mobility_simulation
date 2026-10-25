"""Event-aligned, fixed request-cohort diagnostics for complete market runs."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance


def request_ids(value):
    if pd.isna(value):return []
    return [int(float(v)) for v in str(value).split(';')]


def activity_frame(run):
    path=Path(run)/'2-0_op-stats.csv'
    return pd.read_csv(path) if path.exists() else pd.DataFrame(columns=[
        'vehicle_id','status','start_time','end_time','occupancy','driven_distance','rq_boarding','rq_on_board'])


def median(values):
    values=pd.Series(values).dropna()
    return float(values.median()) if len(values) else None


def error(model,source):
    return abs(median(model)-median(source)) if len(model.dropna()) and len(source.dropna()) else None


def calibration_report(bundle,users,drivers,run=None):
    observed=pd.read_csv(bundle/'observed_cohort.csv')
    if not users.request_id.is_unique or not observed.request_id.is_unique:
        raise ValueError('Duplicate user/cohort row would multiply calibration report joins')
    if set(users.request_id)!=set(observed.request_id):raise ValueError('Calibration cohort and simulation request IDs differ')
    joined=users.merge(observed,on='request_id',suffixes=('_sim','_observed'),validate='one_to_one')
    simulation_requests=len(joined)
    if 'is_evaluation_request' in joined:joined=joined[joined.is_evaluation_request].copy()
    served=joined.pickup_time.notna();complete=joined.dropoff_time.notna()
    wait=joined.loc[served,'pickup_time']-joined.loc[served,'request_s']
    early=int(wait.lt(-1e-7).sum())
    if early:raise ValueError(f'{early} simulated pickups precede actual source request time')
    source=joined.loc[served,'observed_wait_s']
    report=dict(requests=len(joined),simulation_requests=simulation_requests,warmup_requests=simulation_requests-len(joined),
        completed=int(complete.sum()),completion_rate=float(complete.mean()),
        simulated_arrival_wait_median_s=median(wait),simulated_pickup_wait_median_s=median(wait),
        legacy_simulation_grid_wait_median_s=median(joined.loc[served,'pickup_time']-joined.loc[served,'rq_time']),
        pickup_alias_definition='legacy field name; boarding-start/vehicle-arrival proxy, measured from raw source request',
        early_pickup_count=early,mean_admission_delay_s=float((joined.rq_time-joined.request_s).mean()),
        observed_pickup_wait_median_s=median(joined.observed_wait_s),observed_pickup_wait_median_served_s=median(source),
        observed_wait_count=int(joined.observed_wait_s.notna().sum()),
        simulated_ride_median_s=median(joined.loc[complete,'dropoff_time']-joined.loc[complete,'pickup_time']),
        observed_ride_median_s=median(joined.dropoff_s-joined.pickup_s),
        whole_run_simulated_utilization=float(drivers.occupied_time_s.sum()/drivers.online_time_s.sum()),
        observed_completion_rate=None,observed_utilization=None,
        unavailable_reason='Trip records omit unserved requests and fleet online exposure',
        comparison_population='Fixed evaluation request-time cohort; event comparisons use served IDs with the corresponding observed event',
        costs_scope='Whole simulated horizon including warm-up and fulfillment tail; not a three-hour cohort earnings estimate')
    if not joined.request_observed.all():report['unavailable_reason']+='; request times are proxies and observed waits are unavailable'
    if run is None:return report
    legs=activity_frame(run)
    departure={};boarding_start={};pooled=set()
    for leg in legs[legs.status.eq('boarding')].itertuples():
        for rid in request_ids(leg.rq_boarding):
            if rid in departure:raise ValueError('Request boarded more than once')
            departure[rid]=leg.end_time;boarding_start[rid]=leg.start_time
    for leg in legs[legs.status.eq('route')&legs.occupancy.ge(2)].itertuples():pooled.update(request_ids(leg.rq_on_board))
    joined['departure']=joined.request_id.map(departure)
    if not joined.loc[served,'departure'].notna().all():raise ValueError('Missing physical boarding completion')
    if not np.allclose(joined.loc[served,'pickup_time'],joined.loc[served,'request_id'].map(boarding_start)):
        raise ValueError('User pickup event does not match physical boarding start')
    departure_wait=joined.loc[served,'departure']-joined.loc[served,'request_s']
    matched=served&joined.observed_arrival_wait_s.notna()
    model_arrival=joined.loc[matched,'pickup_time']-joined.loc[matched,'request_s']
    source_arrival=joined.loc[matched,'observed_arrival_wait_s']
    valid_total=source.notna()
    report.update(simulated_departure_wait_median_s=median(departure_wait),
        total_wait_median_abs_error_s=error(departure_wait[valid_total],source[valid_total]),
        total_wait_wasserstein_s=float(wasserstein_distance(departure_wait[valid_total],source[valid_total])) if valid_total.any() else None,
        simulated_post_boarding_ride_median_s=median(joined.loc[complete,'dropoff_time']-joined.loc[complete,'departure']),
        source_arrival_available_count=int(joined.observed_arrival_wait_s.notna().sum()),arrival_comparison_count=int(matched.sum()),
        model_arrival_median_matched_s=median(model_arrival),source_arrival_median_matched_s=median(source_arrival),
        arrival_median_abs_error_s=error(model_arrival,source_arrival),
        arrival_wasserstein_s=float(wasserstein_distance(model_arrival,source_arrival)) if matched.any() else None,
        model_pooled_share_served=float(joined.loc[served,'request_id'].isin(pooled).mean()) if served.any() else None,
        source_shared_match_count=int(joined.shared_matched.notna().sum()),
        source_shared_match_share=None if not joined.shared_matched.notna().any() else float(joined.shared_matched.mean()),
        pooling_eligibility_violations=int(joined.loc[joined.pooling_allowed.eq(0),'request_id'].isin(pooled).sum()))
    if report['pooling_eligibility_violations']:raise ValueError('Private requests experienced overlapping-rider service')
    parameters=json.loads((bundle/'parameters.json').read_text())
    metadata=json.loads((bundle/'manifest.json').read_text())
    begin=metadata.get('evaluation_start',parameters['start_time']);end=metadata.get('evaluation_end',parameters['end_time'])
    duration=(np.minimum(legs.end_time,end)-np.maximum(legs.start_time,begin)).clip(lower=0)
    online=len(drivers)*(end-begin)-float(duration[legs.status.eq('out_of_service')].sum())
    occupied=float(duration[legs.occupancy.gt(0)&~legs.status.eq('out_of_service')].sum())
    report['simulated_utilization']=occupied/online if online else None
    report['simulated_utilization_scope']='Physical activity in evaluation clock window only'
    return report
