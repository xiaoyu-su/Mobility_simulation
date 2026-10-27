"""Cohort identity and the distinction between offered and actual deadlines."""
from copy import deepcopy
import numpy as np
import pandas as pd
import pytest
from tools.city_av.patience import static_basis,deadline_metrics
from tools.city_av.summary import bundle_contract


def meta(patience):
    return dict(config=dict(max_wait_seconds=patience,pickup_service_seconds=30),
        output_sha256={'parameters.json':str(patience),'demand/requests.csv':str(patience),'observed_cohort.csv':'same'},
        dependencies={},runtime_files_sha256={},fleet_size=10,av_product={'fence_zones':[1,2]})


def test_ordinary_summary_contract_distinguishes_patient_input_regimes():
    assert bundle_contract(meta(240))!=bundle_contract(meta(480))


def test_sensitivity_basis_permits_only_patience_and_deadline_bytes():
    assert static_basis(meta(240))==static_basis(meta(480))


@pytest.mark.parametrize('change',['service','cohort'])
def test_sensitivity_basis_retains_uncontrolled_input_changes(change):
    a=meta(240);b=deepcopy(a)
    if change=='service':b['config']['pickup_service_seconds']=60
    else:b['output_sha256']['observed_cohort.csv']='other'
    assert static_basis(a)!=static_basis(b)


def records():
    u=pd.DataFrame(dict(pickup_time=[470.,490.,np.nan],dropoff_time=[500.,520.,np.nan],promised_pickup_time=[450.,470.,np.nan]))
    c=pd.DataFrame(dict(request_s=[0.,0.,0.],is_evaluation_request=[True]*3));d=pd.DataFrame(dict(latest_start_time=[480.]*3))
    return u,c,d


def test_late_actual_pickup_is_counted_without_hiding_or_cancelling_booking():
    u,c,d=records();r=deadline_metrics(u,c,d,480)
    assert r['within_limit_completed']==1 and r['late_actual_pickups']==1 and r['late_actual_pickup_rate']==.5
    assert r['within_480s_completed']==1
    assert r['late_actual_pickup_mean_s']==r['late_actual_pickup_max_s']==10
    assert r['accepted_offer_deadline_violations']==0


def test_offer_beyond_original_clock_cutoff_fails_closed():
    u,c,d=records();u.loc[1,'promised_pickup_time']=481
    with pytest.raises(ValueError,match='Accepted offer exceeds'):deadline_metrics(u,c,d,480)
