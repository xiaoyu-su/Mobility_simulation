"""Opt-in isolation and fixed-denominator rider group contracts."""
from copy import deepcopy
import numpy as np
import pandas as pd
import pytest
from src.fleetctrl.av_product import opt_in
from tools.city_av.adoption import static_basis, fixed_groups, group_metrics, GROUPS
from tools.city_av.summary import bundle_contract


def meta(share):
    return dict(config=dict(opt_in_share=share,max_wait_seconds=480),
        output_sha256={'parameters.json':str(share),'demand/requests.csv':'same'},
        av_product=dict(opt_in_share=share,fence_zones=[1],av_count=2),
        dependencies={},fleet_size=10)


def test_opt_in_is_explicit_stratum_but_not_background_change():
    assert static_basis(meta(0)) == static_basis(meta(.3)) == static_basis(meta(1))
    assert bundle_contract(meta(0)) != bundle_contract(meta(.3))


@pytest.mark.parametrize('change',['demand','fleet','fence','patience'])
def test_opt_in_basis_rejects_other_interventions(change):
    a=meta(.3);b=deepcopy(a)
    if change=='demand':b['output_sha256']['demand/requests.csv']='changed'
    elif change=='fleet':b['av_product']['av_count']=3
    elif change=='fence':b['av_product']['fence_zones']=[1,2]
    else:b['config']['max_wait_seconds']=720
    assert static_basis(a)!=static_basis(b)


def test_fixed_groups_partition_same_requests_and_keep_zero_denominators_missing():
    c=pd.DataFrame(dict(start=[0]*100+[1],end=[0]*101),index=range(101));mapping=pd.Series({0:1,1:2})
    g=fixed_groups(c,mapping,{1});assert set(g)==set(GROUPS)
    frame=pd.DataFrame(dict(is_evaluation_request=True,product='unserved',wait_s=np.nan),index=c.index)
    rows=group_metrics(frame,g);assert sum(r['requests'] for r in rows)==101
    assert group_metrics(frame.iloc[::-1],g)==rows
    with pytest.raises(ValueError,match='request identities'):group_metrics(frame.iloc[:-1],g)
    assert all(r['completed']==0 and r['wait_mean_s'] is None for r in rows)
    empty=group_metrics(frame,g.where(g.eq(GROUPS[0]),GROUPS[1]))[-1]
    assert empty['requests']==0 and empty['completion_rate'] is None


def test_nested_opt_in_draw_is_fixed_and_respects_both_endpoints():
    c=pd.DataFrame(dict(start=[0]*1000+[0],end=[0]*1000+[1]),index=range(1001));mapping=pd.Series({0:1,1:2})
    groups=fixed_groups(c,mapping,{1});baseline=set(groups[groups.eq(GROUPS[0])].index)
    assert baseline=={r for r in range(1000) if opt_in(r,0,.3)}
    assert not any(opt_in(r,0,0) for r in c.index) and all(opt_in(r,0,1) for r in c.index)
    assert groups.loc[1000]=='outside_fence'
