"""Independent small examples for occupied-time and paired product identities."""
import pandas as pd
import pytest

from tools.city_av.mechanism import occupied_accounting, paired_accounting


def records():
    users=pd.DataFrame(dict(vehicle_id=[1,1],pickup_time=[10.,30.],dropoff_time=[40.,110.],
        alighting_end=[50.,120.],number_passenger=[1,1],is_evaluation_request=[False,True]))
    legs=pd.DataFrame(dict(vehicle_id=[1]*6,start_time=[10.,30.,40.,50.,100.,110.],
        end_time=[30.,40.,50.,100.,110.,120.],occupancy=[1,2,2,1,1,1]))
    return users,legs


@pytest.mark.parametrize('start,end,occupied,before,after',[(0,100,90,0,10),(40,70,30,10,40)])
def test_actual_union_cohorts_clipping_alighting_and_overlap_close(start,end,occupied,before,after):
    users,legs=records();r=occupied_accounting(users,legs,{1},start,end)
    assert r['occupied_vehicle_s']==pytest.approx(occupied)
    assert r['eval_before_window_passenger_s']==pytest.approx(before)
    assert r['eval_after_window_passenger_s']==pytest.approx(after)
    assert r['alighting_dwell_passenger_s']==10
    assert r['logged_overlap_passenger_s']==(20 if start==0 else 10)
    assert r['bridge_residual_s']==pytest.approx(0)


def test_actual_passenger_holding_must_match_occupancy_not_just_final_totals():
    users,legs=records();users.loc[0,'alighting_end']=49
    with pytest.raises(ValueError,match='passenger-holding exposure'):
        occupied_accounting(users,legs,{1},0,100)


def test_symmetric_decomposition_allocates_count_duration_interaction_exactly():
    users,legs=records();users['is_evaluation_request']=True
    a=occupied_accounting(users,legs,{1},0,100);b=dict(a,av_completed=1,mean_eval_passenger_s_per_booking=110)
    p=paired_accounting(a,b)
    assert p['completion_count_s']==-82.5 and p['passenger_duration_s']==82.5
    assert p['occupied_change_s']==0 and p['residual_s']==0


def test_human_only_zero_exposure_has_no_invented_av_duration():
    users,legs=records();a=occupied_accounting(users,legs,set(),0,100)
    assert a['occupied_vehicle_s']==a['av_completed']==0 and a['av_utilization'] is None
    assert a['mean_eval_in_vehicle_s'] is None
    with pytest.raises(ValueError,match='nonzero AV online'):
        paired_accounting(a,a)


def test_invalid_accounting_window_fails_before_exposure_arithmetic():
    users,legs=records()
    with pytest.raises(ValueError,match='Invalid accounting window'):
        occupied_accounting(users,legs,{1},100,100)
