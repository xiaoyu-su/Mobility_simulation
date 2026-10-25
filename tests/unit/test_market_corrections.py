import json
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest

from src.infra.ChargingInfrastructure import infrastructure_node_id
from src.simulation.completion_tail import completion_tail
from src.fleetctrl.planning.PlanRequest import PlanRequest
from src.fleetctrl.planning.VehiclePlan import VehiclePlan,BoardingPlanStop
from tools.synthetic_market.spatial import causal_requests,mapped_nodes,node_pools
from tools.synthetic_market.build import fit_travel
from tools.synthetic_market.records import read_records


@pytest.mark.parametrize('bad',[np.nan,np.inf,-1,1.2,'bad'])
def test_infrastructure_rejects_nonintegral_or_missing_node_ids(bad):
    with pytest.raises((ValueError,OverflowError)):infrastructure_node_id(bad)


def test_blank_charging_csv_keeps_real_node_indices_integral(tmp_path):
    path=tmp_path/'depots.csv'
    path.write_text('charging_station_id,node_index,max_nr_parking,charging_units\n0,17,8,\n')
    row=next(pd.read_csv(path).iterrows())[1]
    assert isinstance(row.node_index,np.floating)
    assert infrastructure_node_id(row.node_index)==17
    assert isinstance(infrastructure_node_id(row.node_index),int)


def test_causal_grid_keeps_last_request_and_raw_clock_patience():
    source=pd.DataFrame(dict(request_id=[0,1,2],start=[1]*3,end=[2]*3,request_s=[25200.,25201.,35999.]))
    demand=causal_requests(source,60,[300,300,300])
    assert demand.rq_time.tolist()==[25200,25260,36000]
    assert (demand.rq_time>=source.request_s).all()
    assert demand.latest_start_time.tolist()==[25500,25501,36299]
    with pytest.raises(ValueError,match='Patience'):causal_requests(source,60,[0,0,0])


def test_road_imputation_is_identity_stable_and_intrazonal_not_collocated():
    a=pd.DataFrame(dict(trip_id=['first','second'],PULocationID=[1,1],DOLocationID=[1,2]))
    pools={1:[10,11],2:[20,21]}
    x=mapped_nodes(a,pools,4,'road_nodes',{1:10,2:20})
    y=mapped_nodes(a.iloc[::-1],pools,4,'road_nodes',{1:10,2:20})
    pd.testing.assert_frame_equal(x.sort_index(),y.sort_index())
    assert x.iloc[0].start!=x.iloc[0].end


def test_polygon_crs_mismatch_fails_instead_of_guessing(tmp_path):
    path=tmp_path/'zones.json'
    path.write_text(json.dumps(dict(type='FeatureCollection',features=[dict(type='Feature',properties={'zone_id':1},
        geometry=dict(type='Polygon',coordinates=[[[0,0],[1,0],[1,1],[0,1],[0,0]]]))])))
    nodes=pd.DataFrame(dict(node_index=[0],pos_x=[500000],pos_y=[4500000]))
    mapping=pd.DataFrame(dict(node_index=[0],zone_id=[1]))
    with pytest.raises(ValueError,match='CRS'):node_pools(mapping,nodes,path,'EPSG:32618','EPSG:32618')


def test_source_events_and_pooling_flags_are_preserved_without_inventing_arrival(tmp_path):
    path=tmp_path/'trips.csv'
    path.write_text('hvfhs_license_num,request_datetime,on_scene_datetime,pickup_datetime,dropoff_datetime,PULocationID,DOLocationID,shared_request_flag,shared_match_flag\n'
        'HV0003,2019-11-05 07:00:00,2019-11-05 07:01:00,2019-11-05 07:02:00,2019-11-05 07:05:00,1,2,N,N\n'
        'HV0003,2019-11-05 07:00:00,2019-11-05 07:03:00,2019-11-05 07:02:00,2019-11-05 07:05:00,1,1,Y,Y\n')
    a,_,_=read_records([path],['2019-11-05'],{1,2},0,1,include_intrazonal=True)
    assert len(a)==2 and a.pooling_requested.tolist()==[0,1]
    assert a.observed_arrival_wait_s.iloc[0]==60 and a.observed_curb_s.iloc[0]==60
    assert pd.isna(a.observed_arrival_wait_s.iloc[1])


class Router:
    def return_node_position(self,n):return n
    def return_travel_costs_1to1(self,a,b):return (10,10,0)


def test_noise_detrending_does_not_count_bin_mean_variation_twice():
    a=pd.DataFrame(dict(PULocationID=[1]*6,DOLocationID=[2]*6,pickup_s=[0]*3+[900]*3,
        dropoff_s=[10]*3+[900+10*np.e]*3))
    factors,sigma,_=fit_travel(a,Router(),{1:0,2:1},0,1800,900,detrend=True)
    assert sigma==pytest.approx(0)
    assert factors.travel_time_factor.tolist()==pytest.approx([1,np.e])


def vehicle_and_requests():
    requests={}
    for rid,allowed in [(0,False),(1,True)]:
        rq=SimpleNamespace(get_rid_struct=lambda rid=rid:rid,nr_pax=1,rq_time=0,o_pos=(0,None,None),d_pos=(2,None,None),
            earliest_start_time=0,latest_start_time=None,max_trip_time=10000,pooling_allowed=allowed,
            pickup_service_time=94,dropoff_service_time=30)
        requests[rid]=PlanRequest(rq,Router())
    v=SimpleNamespace(vid=0,pos=(0,None,None),soc=1,pax=[],max_pax=4,max_parcels=0,
        get_nr_pax_without_currently_boarding=lambda:0,get_nr_parcels_without_currently_boarding=lambda:0,
        compute_soc_consumption=lambda distance:0,planning_requests=requests,request_service_add_time=0)
    return v


def stop(node,board=None,alight=None):
    board=board or [];alight=alight or []
    return BoardingPlanStop((node,None,None),boarding_dict={1:board,-1:alight},
        earliest_pickup_time_dict={i:0 for i in board},latest_pickup_time_dict={i:1000 for i in board},
        max_trip_time_dict={i:10000 for i in alight},change_nr_pax=len(board)-len(alight),duration=30)


def test_private_request_cannot_overlap_but_handoff_and_separate_dwell_are_valid():
    vehicle=vehicle_and_requests()
    overlapping=VehiclePlan(vehicle,0,Router(),[stop(0,[0]),stop(1,[1]),stop(2,alight=[0]),stop(3,alight=[1])])
    assert not overlapping.is_feasible()
    handoff=VehiclePlan(vehicle,0,Router(),[stop(0,[0]),stop(2,[1],[0]),stop(3,alight=[1])])
    assert handoff.is_feasible()
    assert handoff.list_plan_stops[0].get_duration_and_earliest_departure()[0]==94
    assert handoff.list_plan_stops[-1].get_duration_and_earliest_departure()[0]==30
    start,end=handoff.list_plan_stops[-1].get_planned_arrival_and_departure_time()
    assert end-start==30
    vehicle.planning_requests[0].pooling_allowed=True
    allowed=VehiclePlan(vehicle,0,Router(),[stop(0,[0]),stop(1,[1]),stop(2,alight=[0]),stop(3,alight=[1])])
    assert allowed.is_feasible()


@pytest.mark.parametrize('limit,complete',[(14400,False),(20000,True)])
def test_completion_tail_extends_long_trip_or_explicitly_fails_with_audit(tmp_path,limit,complete):
    vehicle=SimpleNamespace(assigned_route=[SimpleNamespace(status=1)],pax=[SimpleNamespace(get_rid_struct=lambda:7)])
    def update(last,next_,only_active=False):
        assert only_active
        if next_>=18000:vehicle.assigned_route=[];vehicle.pax=[]
    sim=SimpleNamespace(scenario_parameters={'completion_tail_max_seconds':limit},end_time=0,time_step=60,
        sim_vehicles={0:vehicle},charging_operator_dict={},skip_output=False,dir_names={'output':str(tmp_path)},
        update_sim_state_fleets=update,routing_engine=SimpleNamespace(update_network=lambda *a,**k:None),record_stats=lambda **k:None)
    if complete:completion_tail(sim)
    else:
        with pytest.raises(RuntimeError,match='tail exhausted'):completion_tail(sim)
    audit=json.loads((tmp_path/'completion_tail.json').read_text())
    assert audit['status']==('complete' if complete else 'incomplete')
    assert audit['onboard_request_ids']==([] if complete else [7])
