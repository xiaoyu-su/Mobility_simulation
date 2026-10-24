"""Request-time cohorts with explicit right censoring at an observation horizon."""

import numpy as np
import pandas as pd


def cohort_observations(requests, events, start, end, horizon):
    rows = []
    for rid, request in requests.items():
        data = request.record_data()
        if not start <= data['rq_time'] < end:
            continue
        def seen(value):
            return value if value is not None and pd.notna(value) and value < horizon else None
        pickup, dropoff = seen(data.get('pickup_time')), seen(data.get('dropoff_time'))
        booked = seen(events['accepted'].get(rid))
        rejected = seen(events['rejected'].get(rid))
        status = ('completed' if dropoff is not None else 'picked_up_censored' if pickup is not None
                  else 'rejected' if rejected is not None else 'accepted_censored' if booked is not None
                  else 'unresolved_censored')
        rows.append(dict(request_id=str(data['request_id']),rq_time=data['rq_time'],
                         status=status,accepted_time=booked,rejected_time=rejected,
                         pickup_time=pickup,dropoff_time=dropoff,
                         operator_id=data.get('operator_id') if pickup is not None else None,
                         vehicle_id=data.get('vehicle_id') if pickup is not None else None,
                         fare=data.get('fare') if dropoff is not None else None,
                         wait_s=pickup-data['rq_time'] if pickup is not None else None,
                         ride_s=dropoff-pickup if dropoff is not None else None,
                         pickup_error_s=pickup-data['promised_pickup_time'] if pickup is not None and data.get('promised_pickup_time') is not None else None,
                         dropoff_error_s=dropoff-data['promised_dropoff_time'] if dropoff is not None and data.get('promised_dropoff_time') is not None else None))
    columns=['request_id','rq_time','status','accepted_time','rejected_time','pickup_time','dropoff_time',
             'operator_id','vehicle_id','fare','wait_s','ride_s','pickup_error_s','dropoff_error_s']
    result=pd.DataFrame(rows,columns=columns).sort_values('request_id',kind='stable').reset_index(drop=True)
    if result.request_id.duplicated().any():
        raise ValueError('Duplicate request identity in a window cohort')
    return result


def cohort_metrics(rows):
    n=len(rows)
    completed=rows.status.eq('completed')
    rejected=rows.status.eq('rejected')
    censored=~(completed|rejected)
    def mean(column):
        values=pd.to_numeric(rows[column],errors='coerce').dropna()
        return float(values.mean()) if len(values) else np.nan
    return dict(request_count=float(n),completed_requests=float(completed.sum()),
                completion_rate=float(completed.mean()) if n else np.nan,
                picked_up_requests=float(rows.pickup_time.notna().sum()),
                rejected_requests=float(rejected.sum()),censored_requests=float(censored.sum()),
                accepted_censored_requests=float(rows.status.eq('accepted_censored').sum()),
                picked_up_censored_requests=float(rows.status.eq('picked_up_censored').sum()),
                unresolved_censored_requests=float(rows.status.eq('unresolved_censored').sum()),
                observed_wait_mean_s=mean('wait_s'),observed_ride_mean_s=mean('ride_s'),
                pickup_error_mean_s=mean('pickup_error_s'),dropoff_error_mean_s=mean('dropoff_error_s'),
                completed_gross_fare_cent=float(pd.to_numeric(rows.loc[completed,'fare'],errors='coerce').sum()))


def cohort_driver_credit(rows, roster):
    completed=rows[rows.status.eq('completed')]
    credits=completed.groupby(['operator_id','vehicle_id'],dropna=False).agg(
        completed_cohort_trips=('request_id','size'),completed_cohort_gross_fare_cent=('fare','sum')).reset_index()
    result=roster[['operator_id','vehicle_id']].merge(credits,how='left',on=['operator_id','vehicle_id'])
    for column in ['completed_cohort_trips','completed_cohort_gross_fare_cent']:
        result[column]=pd.to_numeric(result[column]).fillna(0)
    return result
