from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.routing.road.NetworkBasic import Node,Edge
from src.routing.road.NetworkBasicWithStore import NetworkBasicWithStore
from tools.windowed_eval.snapshot import dumps,loads
from tools.windowed_eval.metrics import cohort_observations,cohort_metrics,cohort_driver_credit


def test_closures_modules_defaults_function_attributes_aliases_and_rngs_survive():
    owner=SimpleNamespace(rng=np.random.default_rng(19))
    def factory(scale):
        def objective(x=2,*,offset=3):return scale*np.sqrt(x)+offset+owner.rng.random()
        objective.assignment_reward_per_request=100
        return objective
    objective=factory(4)
    restored,restored_owner,alias=loads(dumps((objective,owner,owner)))
    assert alias is restored_owner and restored_owner is not owner
    assert restored.assignment_reward_per_request==100
    assert restored.__defaults__==objective.__defaults__ and restored.__kwdefaults__==objective.__kwdefaults__
    assert restored()==objective()
    assert restored(9,offset=1)==objective(9,offset=1)


def test_flat_network_preserves_topology_edge_identity_adjacency_orders_and_cache():
    network=NetworkBasicWithStore.__new__(NetworkBasicWithStore)
    nodes=[Node(i,False,i,i) for i in range(3)]
    for origin,destination in [(1,2),(0,2),(0,1)]:
        edge=Edge((nodes[origin],nodes[destination]),10+origin+destination,4.5)
        nodes[origin].add_next_edge_to(nodes[destination],edge)
        nodes[destination].add_prev_edge_from(nodes[origin],edge)
    nodes[2].prev=nodes[1];nodes[0].next=nodes[2]
    nodes[2].cost=(9,10,11);nodes[2].settled=18
    network.nodes=pd.Series(nodes);network.current_dijkstra_number=19
    network.travel_time_infos={(0,2):(4.5,4.5,12)}
    restored=loads(dumps(network))
    assert [n.node_index for n in restored.nodes[0].edges_to]==[2,1]
    assert [n.node_index for n in restored.nodes[2].edges_from]==[1,0]
    assert restored.nodes[0].edges_to[restored.nodes[2]] is restored.nodes[2].edges_from[restored.nodes[0]]
    assert restored.nodes[2].prev is restored.nodes[1] and restored.nodes[0].next is restored.nodes[2]
    assert restored.nodes[2].cost==(9,10,11) and restored.nodes[2].settled==18
    assert restored.travel_time_infos==network.travel_time_infos
    edge=restored.nodes[0].edges_to[restored.nodes[2]]
    assert edge.edge_index==(restored.nodes[0],restored.nodes[2])


def request(rid,time,pickup=None,dropoff=None,fare=100):
    data=dict(request_id=str(rid),rq_time=time,pickup_time=pickup,dropoff_time=dropoff,
              fare=fare,operator_id=0,vehicle_id=1,promised_pickup_time=10,promised_dropoff_time=20)
    return SimpleNamespace(record_data=lambda:dict(data))


def test_request_time_membership_is_disjoint_and_cutoff_events_are_censored():
    requests={1:request(1,0,10,30),2:request(2,20,29,40),3:request(3,30),4:request(4,39)}
    events={'accepted':{1:0,2:20},'rejected':{3:40,4:39}}
    a=cohort_observations(requests,events,0,20,30)
    b=cohort_observations(requests,events,20,40,40)
    assert set(a.request_id).isdisjoint(set(b.request_id))
    assert a.status.tolist()==['picked_up_censored'] and a.dropoff_time.isna().all()
    assert b.set_index('request_id').status.to_dict()=={'2':'picked_up_censored','3':'unresolved_censored','4':'rejected'}
    assert b.fare.isna().all() and cohort_metrics(b)['completed_requests']==0
    assert cohort_metrics(b)['censored_requests']==2


def test_observed_driver_credit_never_prorates_unfinished_fares_or_mileage():
    rows=cohort_observations({1:request(1,0,10,20),2:request(2,1,15,100)},
                             {'accepted':{1:0,2:1},'rejected':{}},0,30,30)
    credit=cohort_driver_credit(rows,pd.DataFrame({'operator_id':[0,0],'vehicle_id':[0,1]}))
    assert credit.completed_cohort_trips.tolist()==[0,1]
    assert credit.completed_cohort_gross_fare_cent.tolist()==[0,100]
    assert cohort_metrics(rows)['completed_gross_fare_cent']==100


def test_empty_cohort_has_explicit_zero_counts_and_undefined_conditional_means():
    rows=cohort_observations({1:request(1,50)},{'accepted':{},'rejected':{}},0,10,10)
    summary=cohort_metrics(rows)
    assert summary['request_count']==summary['completed_requests']==summary['censored_requests']==0
    assert np.isnan(summary['completion_rate']) and np.isnan(summary['observed_wait_mean_s'])
    credit=cohort_driver_credit(rows,pd.DataFrame({'operator_id':[0],'vehicle_id':[1]}))
    assert credit.completed_cohort_trips.iloc[0]==0
