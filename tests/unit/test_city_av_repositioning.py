import json

import pandas as pd
import pytest

from tests.integration.test_city_av_examples import city_fixture
from tools.city_av.build import build
from tools.city_av.reposition import MODE, reference_weights
from tools.synthetic_market.worker import verify_bundle


def test_stationary_av_weights_use_separate_eligible_od_not_evaluation_or_warmup(tmp_path):
    cfg,c=city_fixture(tmp_path/'source');c['av_repositioning_forecast']=MODE;cfg.write_text(json.dumps(c))
    a=tmp_path/'first';build(cfg,cfg.parent,a)
    rows=pd.read_csv(cfg.parent/'requests.csv');rows.loc[rows.rq_time.ge(900),'start']=2;rows.loc[rows.rq_time.ge(900),'end']=0
    rows.to_csv(cfg.parent/'requests.csv',index=False);b=tmp_path/'second';build(cfg,cfg.parent,b)
    for name in ['forecasts/900/city_av_reference.csv','repositioning_reference.csv','initial_distribution.csv']:
        assert (a/name).read_bytes()==(b/name).read_bytes()
    m=json.loads((a/'manifest.json').read_text());reference=m['av_repositioning_reference']
    assert reference['reference_rows']==6 and reference['eligible_reference_rows']==2
    assert reference['positive_origin_zones']==1
    f=pd.read_csv(a/reference['file']);assert f['out aggregate_o_and_d'].eq(2).all() and set(f.zone_id)=={10}
    d=pd.read_csv(a/'repositioning_reference.csv');assert d.reference_time.lt(900).all()
    assert set(d.reference_id).isdisjoint(set(pd.read_csv(a/'demand/requests.csv').request_id))


@pytest.mark.parametrize('problem',['no_eligible_od','unknown_method','future_date','unapproved_date'])
def test_repositioning_forecast_rejects_missing_or_future_training_information(tmp_path,problem):
    cfg,c=city_fixture(tmp_path/'source');c['av_repositioning_forecast']=MODE
    if problem=='unknown_method':
        c['av_repositioning_forecast']='target_day_peeking';cfg.write_text(json.dumps(c))
        with pytest.raises(ValueError,match='Unknown'):build(cfg,cfg.parent,tmp_path/'bad')
        return
    if problem=='no_eligible_od':
        d=pd.read_csv(cfg.parent/'requests.csv');d.loc[d.rq_time.lt(900),'end']=2;d.to_csv(cfg.parent/'requests.csv',index=False);cfg.write_text(json.dumps(c))
        with pytest.raises(ValueError,match='No independent AV-eligible'):build(cfg,cfg.parent,tmp_path/'bad')
        return
    mapping=pd.DataFrame(dict(node_index=[0,1,2],zone_id=[10,10,20]))
    reference=pd.DataFrame(dict(trip_id=['a'],request_s=[100],start=[0],end=[1],service_date=['2019-11-26' if problem=='future_date' else '2019-11-18']))
    parent=dict(target_date='2019-11-26',training_dates=['2019-11-19'])
    with pytest.raises(ValueError,match='unapproved/future'):reference_weights(reference,c,mapping,[10],parent)


@pytest.mark.parametrize('name',['forecasts/900/city_av_reference.csv','repositioning_reference.csv'])
def test_city_reference_and_consumed_forecast_are_immutable_bundle_inputs(tmp_path,name):
    cfg,c=city_fixture(tmp_path/'source');c['av_repositioning_forecast']=MODE;cfg.write_text(json.dumps(c));bundle=tmp_path/'bundle';build(cfg,cfg.parent,bundle)
    assert verify_bundle(bundle)['status']=='complete'
    with (bundle/name).open('a') as f:f.write('\n')
    with pytest.raises(ValueError,match='hash mismatch'):verify_bundle(bundle)


@pytest.mark.parametrize('lock',['locked','locked_end','infeasible_locked'])
def test_service_priority_cancels_only_soft_goals_without_mutating_live_plan(lock):
    from src.fleetctrl.av_product import AVProduct
    from src.fleetctrl.planning.VehiclePlan import VehiclePlan,RoutingTargetPlanStop
    from tests.unit.test_av_round2 import car
    v=car();v.is_av=True;p=object.__new__(AVProduct);p.service_priority=True;p.threshold=None;p.requests={};v.av_product=p
    soft=RoutingTargetPlanStop((2,None,None));hard=RoutingTargetPlanStop((3,None,None),locked=lock=='locked',locked_end=lock=='locked_end')
    if lock=='infeasible_locked':hard.set_infeasible_locked(True)
    original=VehiclePlan(v,0,v.routing_engine,[soft,hard]);original.set_utility(123)
    candidate=p.service_insertion_plan(v,original,0,v.routing_engine)
    assert len(original.list_plan_stops)==2 and original.get_utility()==123
    assert len(candidate.list_plan_stops)==1 and candidate.list_plan_stops[0].get_pos()==(3,None,None)
    assert candidate.list_plan_stops[0] is not hard and candidate.get_utility() is None
    if lock=='infeasible_locked':assert candidate.list_plan_stops[0].is_infeasible_locked()


@pytest.mark.parametrize('enabled,is_av',[(False,True),(True,False)])
def test_legacy_and_human_insertion_plans_keep_identity(enabled,is_av):
    from src.fleetctrl.av_product import AVProduct
    from types import SimpleNamespace
    p=object.__new__(AVProduct);p.service_priority=enabled
    plan=SimpleNamespace(list_plan_stops=['must not be inspected'])
    assert p.service_insertion_plan(SimpleNamespace(is_av=is_av),plan,0,None) is plan
