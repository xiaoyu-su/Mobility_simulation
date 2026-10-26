import json
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from src.misc.vehicle_timing import travel_time_factor
from src.misc.globals import *
from src.simulation.Vehicles import SimulationVehicle
from src.simulation.Legs import VehicleRouteLeg
from src.fleetctrl.planning.VehiclePlan import VehiclePlan,BoardingPlanStop
from src.fleetctrl.av_product import AVProduct
from src.fleetctrl.acceptance.future_value import FutureValue
from tools.av_eval.__main__ import policy_profiles
from tests.unit.test_execution_noise import LineNetwork


@pytest.mark.parametrize('value',[0,.5,-1,11,None,True,float('nan'),float('inf'),'bad'])
def test_invalid_vehicle_time_factor_rejected(value):
    with pytest.raises(ValueError,match='travel_time_factor'):travel_time_factor(value)


def car(noise=0):
    attributes={G_VTYPE_NAME:'test',G_VTYPE_MAX_PAX:4,G_VTYPE_FIX_COST:0,G_VTYPE_DIST_COST:1,
                G_VTYPE_BATTERY_SIZE:1,G_VTYPE_RANGE:100,'travel_time_factor':1.25}
    v=SimulationVehicle(0,0,attributes,LineNetwork(),{},[],True,True,{'random_seed':17,'network_tt_noise_sigma':noise})
    v.pos=(1,None,None);v.soc=1
    return v


@pytest.mark.parametrize('noise_multiplier',[None,.5,2])
def test_type_factor_scales_execution_replay_and_not_stationary_service(noise_multiplier):
    v=car(.3 if noise_multiplier is not None else 0)
    if noise_multiplier is not None:
        v._execution_rng=Mock();v._execution_rng.lognormal.return_value=noise_multiplier
    v.assign_vehicle_plan([VehicleRouteLeg(VRL_STATES.ROUTE,(2,None,None),{}),
                           VehicleRouteLeg(VRL_STATES.BOARDING,(2,None,None),{},duration=5)],100)
    v.update_veh_state(100,107);v.update_veh_state(107,140)
    route,service=v.op_output;arrival=100+12.5*(noise_multiplier or 1)
    assert route['end_time']==arrival and service['end_time']==arrival+5
    assert route['driven_distance']==pytest.approx(100)
    assert v.soc==pytest.approx(1-100/100000)
    assert route['vehicle_travel_time_factor']==1.25
    assert [float(x.split(':')[1]) for x in route['trajectory'].split(';')]==[100,arrival]
    if noise_multiplier is not None:v._execution_rng.lognormal.assert_called_once()


def test_type_factor_scales_planned_arrival_and_intermediary_state_once():
    v=car()
    pickup=BoardingPlanStop((2,None,None),boarding_dict={1:[7]},duration=5,change_nr_pax=1,
                           earliest_pickup_time_dict={7:100},latest_pickup_time_dict={7:200})
    dropoff=BoardingPlanStop((3,None,None),boarding_dict={-1:[7]},duration=7,change_nr_pax=-1,max_trip_time_dict={7:1000})
    plan=VehiclePlan(v,100,v.routing_engine,[pickup,dropoff])
    assert plan.pax_info[7]==[112.5,130]
    state=plan.return_intermediary_plan_state(v,100,v.routing_engine,0)
    assert state['c_time']==117.5
    assert plan.update_tt_and_check_plan(v,100,v.routing_engine,init_plan_state=state)
    assert plan.pax_info[7]==[112.5,130]


def test_threshold_is_eta_bound_with_human_fallback_and_no_human_case():
    product=object.__new__(AVProduct);product.av_ids={1};product.threshold_decisions=[];product.threshold_products={}
    request=SimpleNamespace(get_rid_struct=lambda:7)
    human=(0,SimpleNamespace(pax_info={7:[300,400]}),-100)
    av=(1,SimpleNamespace(pax_info={7:[420,500]}),0)
    product.threshold=120
    assert product.threshold_candidates([human,av],request,100)==[av]
    product.threshold=119
    assert product.threshold_candidates([human,av],request,100)==[human]
    assert product.threshold_candidates([av],request,100)==[av]
    product.threshold=None
    candidates=[human,av];assert product.threshold_candidates(candidates,request,100) is candidates


def test_threshold_commitment_preserves_product_during_native_reoptimization():
    p=object.__new__(AVProduct);p.threshold=120;p.threshold_products={7:True};p.requests={7:SimpleNamespace(status=0)}
    p.eligible=lambda request:True
    plan=SimpleNamespace(list_plan_stops=[SimpleNamespace(get_list_boarding_rids=lambda:[7])])
    human=SimpleNamespace(is_av=False);av=SimpleNamespace(is_av=True)
    assert p.allows_plan(human,plan)  # candidate evaluation precedes product commitment
    p.requests[7].status=G_PRQS_ACC_OFFER
    assert not p.allows_plan(human,plan) and p.allows_plan(av,plan)
    p.threshold_products[7]=False
    assert p.allows_plan(human,plan) and not p.allows_plan(av,plan)


def test_future_candidates_use_vehicle_speed_and_exclude_ineligible_av():
    cars=[SimpleNamespace(vid=0,pos=(1,None,None),max_pax=4,status=0,travel_time_factor=1.25),
          SimpleNamespace(vid=1,pos=(2,None,None),max_pax=4,status=0,travel_time_factor=1),
          SimpleNamespace(vid=2,pos=(0,None,None),max_pax=4,status=0,is_av=True,av_product=SimpleNamespace(eligible=lambda q:False))]
    f=FutureValue(SimpleNamespace(operator_id=0,seed=17),cars,top_k=2)
    router=SimpleNamespace(return_travel_costs_1to1=lambda a,b:(10 if a[0]==1 else 11,10 if a[0]==1 else 11,100))
    f.begin_round(0,router)
    request=SimpleNamespace(get_o_stop_info=lambda:((3,None,None),0,100),nr_pax=1)
    assert f._nearest(request,0)==((11,1),(12.5,0))


def forecast_product(sigma=0):
    p=object.__new__(AVProduct);p.zones={10};p.forecast_resolution=60;p.forecast_sigma=sigma;p.share=.3;p.seed=17;p.operator_id=0
    p.forecasts=pd.DataFrame({'time':[0,60],'zone_id':[10,10],'out aggregate_o_and_d':[100.,200.]})
    p.eligible_forecasts=p.forecasts.copy()
    return p


def test_forecast_interpolation_noise_is_repeatable_shared_and_isolated():
    p=forecast_product();assert p.forecast_weights(30)[0]=={10:150.0}
    before=np.random.get_state();p.forecast_sigma=.5
    a,factors=p.forecast_weights(30);b,again=p.forecast_weights(30)
    assert a==b and factors==again
    eligible,_=p.forecast_weights(30,eligible=True)
    assert eligible[10]==pytest.approx(a[10]*.3)
    after=np.random.get_state();np.testing.assert_array_equal(before[1],after[1]);assert before[2:]==after[2:]


def test_joint_coverage_is_bounded_by_available_av_and_eligible_forecast():
    p=forecast_product();p.joint=True;p.node_zones={1:10};p.coverage_rounds=[]
    p.fleetctrl=SimpleNamespace(sim_vehicles=[SimpleNamespace(vid=0,is_av=True,pos=(1,None,None)),
                                             SimpleNamespace(vid=1,is_av=False,pos=(1,None,None))],
                                 veh_plans={0:SimpleNamespace(list_plan_stops=[])})
    demand={10:20.,20:5.}
    residual,audit=p.human_forecast(demand,0,60)
    assert residual=={10:19.,20:5.} and audit['expected_av_coverage']=={10:1}
    assert demand=={10:20.,20:5.}


@pytest.mark.parametrize('profile',[{'name':'../escape'},{'name':'bad','unknown':1},
                                    {'name':'bad','eta_threshold_seconds':float('nan')},
                                    {'name':'bad','eta_threshold_seconds':10,'preference_seconds':5}])
def test_invalid_policy_grid_fails_before_running(profile,tmp_path):
    path=tmp_path/'grid.json';path.write_text(json.dumps([profile]))
    with pytest.raises(ValueError):policy_profiles(SimpleNamespace(policy_grid=path))


@pytest.mark.parametrize('overrides,match',[
    ({'op_module':'RidePoolingBatchAssignmentFleetcontrol','op_av_eta_threshold_s':120},'immediate insertion'),
    ({'op_av_eta_threshold_s':120,'op_av_preference_s':10},'alternative policies'),
    ({'op_driver_choice_model':'logit'},'multi-item'),
])
def test_unsupported_av_policy_combinations_fail_before_loading_inputs(overrides,match):
    attrs=dict(op_module='PoolingIRSOnly',op_vr_control_func_dict={'func_key':'distance_and_user_times_with_walk','vot':.5},
               op_av_vehicle_types=['av'],op_av_zones=[10],**{})
    attrs.update(overrides)
    scenario=dict(random_stream_mode='independent',n_cpu_per_sim=1,sim_env='ImmediateDecisionsSimulation',rq_type='BasicRequest')
    with pytest.raises(ValueError,match=match):AVProduct(SimpleNamespace(op_id=0),attrs,scenario,{})
