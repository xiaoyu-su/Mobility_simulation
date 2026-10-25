import numpy as np
import pytest

from src.fleetctrl.repositioning.PavoneHailingHighs import integer_rebalance


def costs(zones):return {(a,b):1+abs(a-b) for a in zones for b in zones if a!=b}


def test_unique_minimum_cost_flow_and_idle_limits():
    zones=[0,1,2];c={(0,1):2,(0,2):4,(1,0):8,(1,2):9,(2,0):8,(2,1):9}
    flows,report=integer_rebalance(zones,{0:9,1:0,2:0},{0:9,1:0,2:0},set(zones),c)
    assert sorted(flows)==[(0,1)]*3+[(0,2)]*3
    assert report['objective']==18 and report['targets']=={0:3,1:3,2:3}


def test_fractional_forecast_excess_cannot_generate_infeasible_uniform_integer_targets():
    zones=[0,1,2]
    flows,report=integer_rebalance(zones,{0:1.8,1:1.8,2:.8},{0:2,1:2,2:1},set(zones),costs(zones))
    assert flows==[] and report['targets']=={0:0,1:0,2:0}
    flows,report=integer_rebalance(zones,{0:5.9,1:.9,2:.9},{0:6,1:1,2:1},set(zones),costs(zones))
    assert len(flows)==2 and set(flows)=={(0,1),(0,2)}


def test_transport_problem_above_restricted_gurobi_variable_limit_needs_no_commercial_solver():
    zones=list(range(46));idle={z:92 if z==0 else 0 for z in zones}
    flows,report=integer_rebalance(zones,idle,idle,set(zones),costs(zones))
    assert len(zones)*(len(zones)-1)>2000 and len(flows)==90
    assert all(a==0 for a,b in flows) and report['status']==0


@pytest.mark.parametrize('excess,idle',[({0:-.1},{0:1}),({0:np.inf},{0:1}),({0:2},{0:1}),({0:1},{0:1.5})])
def test_invalid_supply_is_rejected(excess,idle):
    with pytest.raises(ValueError):integer_rebalance([0],excess,idle,{0},{})


def test_empty_single_zone_and_zero_idle_do_not_invent_vehicle_moves():
    assert integer_rebalance([],{}, {},set(),{})[0]==[]
    assert integer_rebalance([0],{0:1},{0:1},{0},{})[0]==[]
    assert integer_rebalance([0,1],{0:0,1:0},{0:0,1:0},{0,1},{})[0]==[]
