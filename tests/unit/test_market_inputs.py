from argparse import Namespace
import json

import numpy as np
import pandas as pd
import pytest

from tools.synthetic_market.build import training_dates,historical_profiles,fit_travel
from tools.synthetic_market.records import read_records,stable_fraction
from tools.synthetic_market.run import calibration_report


def records():
    return pd.DataFrame([dict(hvfhs_license_num='HV0003',request_datetime=f'2019-11-05 07:0{i}:00',
        pickup_datetime=f'2019-11-05 07:0{i}:30',dropoff_datetime=f'2019-11-05 07:0{i+1}:30',
        PULocationID=1,DOLocationID=2) for i in range(6)])


def test_csv_and_parquet_read_actual_schemas_without_loading_entire_file(tmp_path):
    data=records();a=tmp_path/'records.csv';b=tmp_path/'records.parquet'
    data.to_csv(a,index=False);data.to_parquet(b,index=False)
    x,c,_=read_records([a],['2019-11-05'],{1,2},3,1,chunk_size=2)
    y,d,_=read_records([b],['2019-11-05'],{1,2},3,1,chunk_size=4)
    pd.testing.assert_frame_equal(x.drop(columns='trip_id').sort_values('request_s').reset_index(drop=True),
                                 y.drop(columns='trip_id').sort_values('request_s').reset_index(drop=True))
    assert c==d and c['retained']==6 and c['raw_rows']==6
    assert x.observed_wait_s.eq(30).all()


def test_sampling_is_nested_and_invariant_to_chunk_size(tmp_path):
    path=tmp_path/'trips.csv';records().to_csv(path,index=False)
    a,_,_=read_records([path],['2019-11-05'],{1,2},3,1,chunk_size=1)
    b,_,_=read_records([path],['2019-11-05'],{1,2},3,1,chunk_size=5)
    pd.testing.assert_frame_equal(a,b)
    assert all(stable_fraction(3,i)==stable_fraction(3,i) for i in a.trip_id)
    assert {i for i in a.trip_id if stable_fraction(3,i)<.2}<={i for i in a.trip_id if stable_fraction(3,i)<.7}


def test_missing_request_time_requires_explicit_proxy_and_cannot_create_observed_wait(tmp_path):
    path=tmp_path/'trips.csv';records().drop(columns='request_datetime').to_csv(path,index=False)
    with pytest.raises(ValueError,match='proxy'):read_records([path],['2019-11-05'],{1,2},0,1)
    rows,_,_=read_records([path],['2019-11-05'],{1,2},0,1,proxy_seconds=120)
    assert rows.observed_wait_s.isna().all() and not rows.request_observed.any()
    assert (rows.pickup_s-rows.request_s).eq(120).all()


def test_invalid_rows_are_disjointly_counted_and_identical_valid_rides_keep_source_identity(tmp_path):
    data=records();data.loc[0,'dropoff_datetime']='bad';data.loc[1,'PULocationID']=999
    data.loc[2,'DOLocationID']=1;data=pd.concat([data,data.iloc[[5]]],ignore_index=True)
    path=tmp_path/'trips.csv';data.to_csv(path,index=False)
    rows,counts,_=read_records([path],['2019-11-05'],{1,2},0,1)
    assert counts['invalid_time']==counts['invalid_zone']==counts['intrazonal_unrepresented']==1
    assert len(rows)==4 and rows.trip_id.is_unique
    with pytest.raises(ValueError,match='same source'):read_records([path,path],['2019-11-05'],{1,2},0,1)


@pytest.mark.parametrize('target,days',[
    ('2019-11-26',['2019-11-26']),('2019-11-26',['2019-11-25']),
    ('2019-11-26',['2019-12-03']),('2019-11-26',['2019-11-05','2019-11-05']),('2019-11-26',[]),
])
def test_training_split_rejects_leakage_and_wrong_weekdays(target,days):
    with pytest.raises(ValueError):training_dates(target,days)


def test_forecasts_average_training_days_and_supply_integrates_partial_intervals():
    frame=pd.DataFrame(dict(request_s=[0,600],pickup_s=[0,600],dropoff_s=[1200,900],PULocationID=[1,1],DOLocationID=[2,2]))
    forecast,supply=historical_profiles(frame,2,[1,2],0,1800,900,.5)
    assert forecast.loc[(forecast.time==0)&(forecast.zone_id==1),'out aggregate_o_and_d'].iloc[0]==1
    assert forecast.loc[(forecast.time==900)&(forecast.zone_id==2),'in aggregate_o_and_d'].iloc[0]==1
    assert supply.mean_observed_occupied_vehicles.iloc[0]==1200/1800
    assert supply.modeled_active_vehicles.iloc[0]==2


def test_factor_and_mean_one_noise_fit_known_log_ratios():
    class Router:
        def return_node_position(self,x):return x
        def return_travel_costs_1to1(self,a,b):return 100,100,100
    logs=np.array([0.,.2,.4,.6])
    frame=pd.DataFrame(dict(PULocationID=[1]*4,DOLocationID=[2]*4,request_s=[0]*4,pickup_s=[0]*4,
                            dropoff_s=100*np.exp(logs)))
    factors,sigma,fit=fit_travel(frame,Router(),{1:0,2:1},0,1800,900)
    assert sigma==pytest.approx(logs.std())
    assert factors.travel_time_factor.eq(np.exp(logs.mean()+logs.var()/2)).all()
    assert fit['training_pairs']==4


def test_calibration_merge_rejects_even_fully_duplicated_user_rows(tmp_path):
    pd.DataFrame(dict(request_id=[1],observed_wait_s=[None])).to_csv(tmp_path/'observed_cohort.csv',index=False)
    with pytest.raises(ValueError,match='Duplicate'):
        calibration_report(tmp_path,pd.DataFrame(dict(request_id=[1,1])),pd.DataFrame())
