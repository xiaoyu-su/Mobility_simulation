from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest

from src.fleetctrl.acceptance.driver_acceptance import DriverAcceptance, create_driver_acceptance
from src.fleetctrl.acceptance.forbid_rematch import enabled
from src.fleetctrl.pooling.batch.AlonsoMora.AlonsoMoraAssignment import AlonsoMoraAssignment
from src.misc.globals import G_PRQS_NO_OFFER, G_PRQS_ACC_OFFER


def request(rid):
    return SimpleNamespace(status=G_PRQS_NO_OFFER, get_rid_struct=lambda: rid, init_direct_td=10000)


def plan(vid, *rids):
    return SimpleNamespace(vid=vid, pax_info={rid: [300, 500] for rid in rids})


def model(tmp_path, **settings):
    attributes=dict(op_module='RidePoolingBatchAssignmentFleetcontrol',op_driver_acceptance_probability=.5,
                    op_driver_acceptance_max_declines=0,op_driver_acceptance_forbid_rematch=True,
                    op_driver_choice_model='singleton')
    attributes.update(settings)
    return DriverAcceptance(attributes,dict(random_seed=17,sim_env='BatchOfferSimulation',rq_type='BasicRequest'),
                            0,[SimpleNamespace(vid=0),SimpleNamespace(vid=1)],tmp_path)


class Optimizer:
    def __init__(self, next_solutions):
        self.next_solutions=iter(next_solutions)
        self.forbidden=set();self.required=[];self.cleared=False

    def forbid_request_vehicle(self,rid,vid):
        if (rid,vid) in self.forbidden:return None
        self.forbidden.add((rid,vid));return 1

    def reoptimise_after_driver_declines(self,required,single):
        self.required.append((dict(required),single))
        self.solutions=next(self.next_solutions)

    def get_optimisation_solution(self,vid):return self.solutions.get(vid)

    def clear_driver_acceptance_constraints(self):self.cleared=True


def controller(obj,optimizer,rids=(7,)):
    return SimpleNamespace(RPBO_Module=optimizer,rq_dict={rid:request(rid) for rid in rids},
                           sim_time=100,sim_vehicles=[SimpleNamespace(vid=0),SimpleNamespace(vid=1)],
                           _driver_declined_requests=set())


@pytest.mark.parametrize('choice',['off','singleton'])
def test_refusal_reoptimises_without_injected_plans_and_later_driver_accepts(tmp_path,choice):
    obj=model(tmp_path,op_driver_choice_model=choice)
    obj.draws[(7,0)]=SimpleNamespace(random=Mock(return_value=.9))
    obj.draws[(7,1)]=SimpleNamespace(random=Mock(return_value=.1))
    optimizer=Optimizer([{1:plan(1,7)}]);fc=controller(obj,optimizer)
    result=obj.forbid_rematch.resolve(fc,{0:plan(0,7)})
    assert result[1].pax_info=={7:[300,500]}
    assert optimizer.forbidden=={(7,0)} and optimizer.required==[({},False)] and optimizer.cleared
    assert not fc._driver_declined_requests
    rows=pd.read_csv(obj.path)
    assert list(rows.vehicle_id)==[0,1] and list(rows.attempt)==[1,2]
    assert list(rows.accepted)==[False,True] and not rows.terminal_decline.any()
    assert obj.forbid_rematch.counters['recovered_requests']==1
    assert not obj.forbid_rematch.pending_rows


def test_final_rejection_marks_last_genuine_refusal_without_extra_offer(tmp_path):
    obj=model(tmp_path,op_driver_acceptance_probability=0)
    optimizer=Optimizer([{1:plan(1,7)},{}]);fc=controller(obj,optimizer)
    assert obj.forbid_rematch.resolve(fc,{0:plan(0,7)})=={0:None,1:None}
    rows=pd.read_csv(obj.path)
    assert list(rows.attempt)==[1,2] and list(rows.terminal_decline)==[False,True]
    assert obj.draws=={} and fc._driver_declined_requests=={7}
    assert obj.forbid_rematch.counters['terminal_requests']==1


def test_previously_accepted_request_is_required_in_later_native_solutions(tmp_path):
    obj=model(tmp_path)
    for key,value in [((7,0),.1),((8,0),.9),((8,1),.1)]:
        obj.draws[key]=SimpleNamespace(random=Mock(return_value=value))
    optimizer=Optimizer([{0:plan(0,7),1:plan(1,8)}]);fc=controller(obj,optimizer,(7,8))
    obj.forbid_rematch.resolve(fc,{0:plan(0,7,8)})
    assert optimizer.required==[({7:0},False)]
    rows=pd.read_csv(obj.path)
    assert set(rows[rows.accepted].request_id)=={7,8} and not rows.terminal_decline.any()
    assert obj.draws[(7,0)].random.call_count==1


def test_losing_accepted_request_and_repeating_forbidden_edge_fail_closed(tmp_path):
    obj=model(tmp_path/'lost')
    obj.draws[(7,0)]=SimpleNamespace(random=lambda:.1)
    obj.draws[(8,0)]=SimpleNamespace(random=lambda:.9)
    optimizer=Optimizer([{}]);fc=controller(obj,optimizer,(7,8))
    with pytest.raises(RuntimeError,match='lost'):
        obj.forbid_rematch.resolve(fc,{0:plan(0,7,8)})
    assert optimizer.cleared
    obj=model(tmp_path/'repeat',op_driver_acceptance_probability=0)
    optimizer=Optimizer([{0:plan(0,7)}]);fc=controller(obj,optimizer)
    with pytest.raises(RuntimeError,match='already forbidden'):
        obj.forbid_rematch.resolve(fc,{0:plan(0,7)})
    assert optimizer.cleared


def graph():
    obj=AlonsoMoraAssignment.__new__(AlonsoMoraAssignment)
    obj.driver_forbidden_edges={};obj._driver_required_pairs={};obj._driver_single_request=False
    obj.active_requests={rid:request(rid) for rid in [7,8]}
    obj.r2v={rid:{0:1,1:1} for rid in [7,8]};obj.v2r={vid:{7:1,8:1} for vid in [0,1]}
    obj.rtv_costs={(0,7):-10,(0,8):-9,(0,7,8):-20,(1,7):-5,(1,8):-6,(1,7,8):-12}
    obj.rtv_obj={key:object() for key in obj.rtv_costs}
    obj.rtv_r={rid:{key:1 for key in obj.rtv_costs if rid in key[1:]} for rid in [7,8]}
    obj.rtv_v={vid:{key:1 for key in obj.rtv_costs if key[0]==vid} for vid in [0,1]}
    obj.rtv_tree_N_v={vid:{n:{key:1 for key in obj.rtv_costs if key[0]==vid and len(key)==n+1} for n in [1,2]} for vid in [0,1]}
    obj.current_assignments={};obj.unassigned_requests={7:1,8:1}
    obj.fleetcontrol=None;obj.solver_seed=None;obj.optimisation_cores=1;obj.optimisation_timeout=None
    obj.sim_time=0;obj.rid_to_consider_for_global_optimisation={7:1,8:1}
    obj.rid_to_mutually_exclusive_cluster_id={};obj.solver='Gurobi'
    obj.alonso_mora_parallelization_manager=None
    return obj


def test_forbid_prunes_both_graph_directions_and_every_cached_trip_and_is_idempotent():
    obj=graph()
    assert obj.forbid_request_vehicle(7,0)==2
    assert 0 not in obj.r2v[7] and 7 not in obj.v2r[0]
    assert (0,7) not in obj.rtv_costs and (0,7,8) not in obj.rtv_obj
    assert obj.forbid_request_vehicle(7,0) is None
    obj.r2v[7][0]=1;obj.v2r[0][7]=1
    assert obj._prune_driver_forbidden_edges()==0
    assert 0 not in obj.r2v[7] and 7 not in obj.v2r[0]


def test_committed_pair_cannot_be_forbidden():
    obj=graph();obj.active_requests[7].status=G_PRQS_ACC_OFFER
    with pytest.raises(ValueError,match='committed'):obj.forbid_request_vehicle(7,0)
    assert obj.driver_forbidden_edges=={} and (0,7,8) in obj.rtv_costs


def test_real_native_solver_reroutes_while_preserving_an_accepted_request():
    obj=graph();obj.forbid_request_vehicle(7,0)
    obj.reoptimise_after_driver_declines({8:0})
    assert obj.optimisation_solutions=={0:(0,8),1:(1,7)}
    obj.clear_driver_acceptance_constraints()
    assert obj._driver_required_pairs=={} and not obj._driver_single_request


def test_real_solver_logit_capacity_prevents_second_new_request_in_same_round():
    obj=graph();obj.reoptimise_after_driver_declines({7:0},single_request=True)
    assert obj.optimisation_solutions=={0:(0,7),1:(1,8)}


@pytest.mark.parametrize('settings',[
    {'op_driver_acceptance_max_declines':1},
    {'op_module':'PoolingIRSOnly'},
    {'op_solver':'CPLEX'},
    {'op_driver_acceptance_forbid_rematch':'true'},
])
def test_unsupported_settings_fail(settings,tmp_path):
    with pytest.raises(ValueError):model(tmp_path,**settings)


def test_default_off_creates_no_new_files(tmp_path):
    assert not enabled({}) and not enabled({'op_driver_acceptance_forbid_rematch':None})
    assert create_driver_acceptance({'op_driver_acceptance_forbid_rematch':False},{},0,[],tmp_path) is None
    with pytest.raises(ValueError,match='requires'):
        create_driver_acceptance({'op_driver_acceptance_forbid_rematch':True},{},0,[],tmp_path)
    assert not list(tmp_path.iterdir())


def test_output_suppression_preserves_rematching_counters(tmp_path):
    attrs=dict(op_module='RidePoolingBatchAssignmentFleetcontrol',op_driver_acceptance_probability=0,
               op_driver_acceptance_max_declines=0,op_driver_acceptance_forbid_rematch=True)
    obj=DriverAcceptance(attrs,dict(random_seed=0,sim_env='BatchOfferSimulation',skip_file_writing=True),
                         0,[SimpleNamespace(vid=0),SimpleNamespace(vid=1)],tmp_path)
    optimizer=Optimizer([{}]);fc=controller(obj,optimizer)
    obj.forbid_rematch.resolve(fc,{0:plan(0,7)});obj.forbid_rematch.write_audit()
    assert obj.forbid_rematch.counters['terminal_requests']==1 and not list(tmp_path.iterdir())
