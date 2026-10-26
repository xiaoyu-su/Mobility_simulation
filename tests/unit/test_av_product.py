from types import SimpleNamespace

import pytest

from src.fleetctrl.av_product import AVProduct,integer_targets,opt_in,create_av_product
from src.fleetctrl.acceptance.driver_acceptance import DriverAcceptance
from src.fleetctrl.pooling.objectives import return_pooling_objective_function


def test_opt_in_is_nested_fixed_and_does_not_depend_on_iteration_order():
    lower={rid for rid in range(1000) if opt_in(rid,0,.3)}
    higher={rid for rid in reversed(range(1000)) if opt_in(rid,0,.7)}
    assert lower<higher
    assert not any(opt_in(r,0,0) for r in range(100))
    assert all(opt_in(r,0,1) for r in range(100))


def test_targets_conserve_fleet_and_reject_invalid_forecasts():
    assert integer_targets({2:1,1:1,3:1},5)=={1:2,2:2,3:1}
    assert integer_targets({1:0},5)=={}
    with pytest.raises(ValueError):integer_targets({1:float('nan')},4)
    with pytest.raises(ValueError):integer_targets({1:-1},4)


def test_eligibility_requires_both_endpoints_and_opt_in():
    p=object.__new__(AVProduct);p.node_zones={0:10,1:10,2:20};p.zones={10};p.share=1;p.operator_id=0
    def rq(a,b):return SimpleNamespace(get_rid=lambda:1,get_o_stop_info=lambda:((a,None,None),0,100),get_d_stop_info=lambda:((b,None,None),100,100))
    assert p.eligible(rq(0,1))
    assert not p.eligible(rq(0,2)) and not p.eligible(rq(2,0))
    p.share=0;assert not p.eligible(rq(0,1))


def test_preference_uses_rider_seconds_and_cancels_for_existing_av_riders():
    f=return_pooling_objective_function({'func_key':'distance_and_user_times_with_walk','vot':.5})
    plan=SimpleNamespace(pax_info={1:[5,25]},list_plan_stops=[])
    requests={1:SimpleNamespace(rq_time=0,walking_time_end=0)}
    vehicle=SimpleNamespace(pos=(0,None,None),distance_cost=0,is_av=False)
    base=f(0,vehicle,plan,requests,None)
    vehicle.is_av=True;vehicle.av_product=SimpleNamespace(preference=120)
    assert f(0,vehicle,plan,requests,None)==base-60
    vehicle.av_product.preference=-120
    assert f(0,vehicle,plan,requests,None)==base+60


def test_av_accepts_even_when_human_probability_override_is_zero(tmp_path):
    a=DriverAcceptance({'op_driver_acceptance_probability':0},{'random_seed':3},0,
                       [SimpleNamespace(vid=0,is_av=False),SimpleNamespace(vid=1,is_av=True)],tmp_path)
    assert a.probability_at_eta(0,None,100)==0
    assert a.probability_at_eta(1,None,100)==1
    assert a.vehicle_classes[1]=='av'
    request=SimpleNamespace(status=0,get_rid_struct=lambda:7,init_direct_td=1000)
    plan=SimpleNamespace(pax_info={7:[100,300]})
    assert a.accept(1,request,plan,0)


def test_unused_av_policy_rejected_instead_of_silently_ignored():
    assert create_av_product(None,{},None,None) is None
    with pytest.raises(ValueError,match='require'):create_av_product(None,{'op_av_preference_s':10},None,None)


def test_initial_position_distribution_is_conditioned_on_fence_without_new_draws():
    p=object.__new__(AVProduct);p.nodes={1,2}
    assert p.initial_distribution({0:.5,1:.3,2:.2})=={1:.6,2:.4}
    assert p.initial_distribution({0:1})=={1:.5,2:.5}
