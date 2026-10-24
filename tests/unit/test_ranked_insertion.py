import json
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest

from src.fleetctrl.acceptance.driver_acceptance import DriverAcceptance, create_driver_acceptance
from src.fleetctrl.acceptance.ranked_insertion import enabled, select_insertion_candidate
from src.misc.globals import G_PRQS_NO_OFFER, G_PRQS_ACC_OFFER


def model(tmp_path, choice="singleton", **settings):
    attributes = dict(op_module="PoolingIRSOnly", op_driver_acceptance="logistic",
                      op_driver_acceptance_probability=.5, op_driver_acceptance_max_declines=0,
                      op_driver_acceptance_ranked_fallback=True, op_driver_choice_model=choice)
    attributes.update(settings)
    return DriverAcceptance(attributes, dict(random_seed=17, sim_env="ImmediateDecisionsSimulation",
                                             rq_type="BasicRequest"),
                            0, [SimpleNamespace(vid=i) for i in range(3)], tmp_path)


def request(rid=7, status=G_PRQS_NO_OFFER):
    return SimpleNamespace(get_rid_struct=lambda: rid, init_direct_td=10000, status=status)


def candidate(vid, cost, rid=7):
    return vid, SimpleNamespace(vid=vid, pax_info={rid: [300, 500]}), cost


@pytest.mark.parametrize("choice", ["off", "singleton", "logit"])
def test_first_willing_driver_serves_and_replay_consumes_no_draws(tmp_path, choice):
    obj = model(tmp_path, choice=choice)
    obj.draws[(7, 0)] = SimpleNamespace(random=Mock(return_value=.9))
    obj.draws[(7, 1)] = SimpleNamespace(random=Mock(return_value=.1))
    obj.draws[(7, 2)] = SimpleNamespace(random=Mock(side_effect=AssertionError("Already served")))
    proposals = [candidate(2, 3), candidate(1, 2), candidate(0, 1)]
    snapshot = [(vid, plan.pax_info.copy(), cost) for vid, plan, cost in proposals]
    selected = select_insertion_candidate(obj, proposals, request(), 100)
    assert selected[0] == 1
    assert select_insertion_candidate(obj, proposals, request(), 100) == selected
    assert obj.accept(1, request(), selected[1], 100)
    assert obj.ranked_fallback.counters["offers"] == 2
    assert obj.ranked_fallback.counters["fallback_acceptances"] == 1
    decisions = pd.read_csv(obj.path)
    assert list(decisions.vehicle_id) == [0, 1]
    assert list(decisions.attempt) == [1, 2]
    assert list(decisions.accepted) == [False, True]
    assert not decisions.terminal_decline.any()
    assert obj.draws[(7, 0)].random.call_count == obj.draws[(7, 1)].random.call_count == 1
    assert obj.draws[(7, 2)].random.call_count == 0
    assert snapshot == [(vid, plan.pax_info.copy(), cost) for vid, plan, cost in proposals]
    if choice != "off":
        assert obj.choice.owners == {7: 1}
        assert obj.choice.counters["episodes"] == 2


def test_exhausted_request_has_one_terminal_decline_and_one_draw_per_distinct_driver(tmp_path):
    obj = model(tmp_path, op_driver_acceptance_probability=0)
    proposals = [candidate(0, 5), candidate(1, 2), candidate(0, 1), candidate(2, 3)]
    assert select_insertion_candidate(obj, proposals, request(), 100) is None
    assert select_insertion_candidate(obj, proposals, request(), 100) is None
    decisions = pd.read_csv(obj.path)
    assert list(decisions.vehicle_id) == [0, 1, 2]
    assert list(decisions.attempt) == list(decisions.decline_count) == [1, 2, 3]
    assert list(decisions.terminal_decline) == [False, False, True]
    assert decisions.uniform_draw.isna().all() and obj.draws == {}
    rows = pd.read_csv(obj.ranked_fallback.path)
    assert rows.candidate_count.eq(3).all()
    assert rows.iloc[0].candidate_vehicle_ids == "0;1;2"
    assert json.loads(rows.iloc[0].candidate_costs) == [1, 2, 3]
    assert obj.ranked_fallback.counters["exhausted_requests"] == 1


def test_probability_one_and_equal_costs_preserve_the_original_stable_minimum(tmp_path):
    obj = model(tmp_path, op_driver_acceptance_probability=1)
    proposals = [candidate(2, -3), candidate(0, -3), candidate(1, 9)]
    result = select_insertion_candidate(obj, proposals, request(), 100)
    assert result is proposals[0] or result == proposals[0]
    assert obj.draws == {} and obj.ranked_fallback.counters["offers"] == 1


def test_empty_candidates_and_output_suppression(tmp_path):
    attributes = dict(op_module="PoolingIRSOnly", op_driver_acceptance_probability=0,
                      op_driver_acceptance_max_declines=0, op_driver_acceptance_ranked_fallback=True)
    obj = DriverAcceptance(attributes, dict(random_seed=1, sim_env="ImmediateDecisionsSimulation",
                                            skip_file_writing=True), 0, [SimpleNamespace(vid=0)], tmp_path)
    assert select_insertion_candidate(obj, [], request(), 0) is None
    assert select_insertion_candidate(obj, [candidate(0, 0, rid=8)], request(8), 0) is None
    obj.ranked_fallback.write_audit()
    assert not list(tmp_path.iterdir())
    assert obj.ranked_fallback.counters["no_candidate_requests"] == 1
    assert obj.ranked_fallback.counters["exhausted_requests"] == 1


def test_invalid_candidates_fail_before_any_acceptance_draw(tmp_path):
    obj = model(tmp_path)
    for proposals in [[candidate(0, float("nan"))], [(1, candidate(0, 1)[1], 1)], [candidate(0, 1, rid=8)]]:
        with pytest.raises(ValueError):
            select_insertion_candidate(obj, proposals, request(), 0)
    assert obj.draws == {} and obj.ranked_fallback.counters["requests"] == 0


def test_ranking_uses_each_proposals_eta_and_driver_class(tmp_path):
    obj = model(tmp_path, op_driver_acceptance_probability=None,
                op_driver_acceptance_intercept=0, op_driver_acceptance_beta_eta=-1,
                op_driver_acceptance_beta_value=0)
    first, second = candidate(0, 1), candidate(1, 2)
    first[1].pax_info[7] = [700, 900]
    second[1].pax_info[7] = [100, 300]
    obj.draws[(7, 0)] = SimpleNamespace(random=Mock(return_value=.1))
    obj.draws[(7, 1)] = SimpleNamespace(random=Mock(return_value=.1))
    assert select_insertion_candidate(obj, [first, second], request(), 100)[0] == 1
    probabilities = pd.read_csv(obj.path).probability
    assert probabilities.iloc[0] < .001 and probabilities.iloc[1] == .5


def test_committed_request_is_not_redrawn(tmp_path):
    obj = model(tmp_path, op_driver_acceptance_probability=0)
    plan = candidate(0, 1)[1]
    assert obj.accept(0, request(status=G_PRQS_ACC_OFFER), plan, 0, final_candidate=False)
    assert obj.draws == {} and pd.read_csv(obj.path).empty


@pytest.mark.parametrize("settings", [
    {"op_driver_acceptance_max_declines": 1},
    {"op_module": "RidePoolingBatchAssignmentFleetcontrol"},
    {"op_driver_acceptance_ranked_fallback": "true"},
])
def test_unsupported_or_ambiguous_ranked_settings_fail(settings, tmp_path):
    with pytest.raises(ValueError):
        model(tmp_path, **settings)


def test_flag_requires_acceptance_and_default_off_has_no_effect(tmp_path):
    with pytest.raises(ValueError, match="requires"):
        create_driver_acceptance({"op_driver_acceptance_ranked_fallback": True}, {}, 0, [], tmp_path)
    for flag in [None, False, 0]:
        assert not enabled({"op_driver_acceptance_ranked_fallback": flag})
    assert select_insertion_candidate(None, [], request(), 0) is None
    proposals = [candidate(2, 1), candidate(0, 1)]
    assert select_insertion_candidate(None, proposals, request(), 0) is proposals[0]


def test_request_draws_are_independent_of_unrelated_fallback_episodes(tmp_path):
    a, b = model(tmp_path/'a'), model(tmp_path/'b')
    select_insertion_candidate(b, [candidate(2, 1, rid=8)], request(8), 0)
    proposals = [candidate(0, 1), candidate(1, 2)]
    left = select_insertion_candidate(a, proposals, request(), 100)
    right = select_insertion_candidate(b, proposals, request(), 100)
    assert (left[0] if left else None) == (right[0] if right else None)
    x, y = pd.read_csv(a.path), pd.read_csv(b.path)
    pd.testing.assert_frame_equal(x, y[y.request_id == 7].reset_index(drop=True), check_exact=True)


@pytest.mark.parametrize('scenario', [dict(sim_env='BatchOfferSimulation'), dict(sim_env='ImmediateDecisionsSimulation',rq_type='IndividualConstraintRequest')])
def test_ranked_rejects_delayed_or_nonbasic_travelers(tmp_path,scenario):
    attributes = dict(op_module='PoolingIRSOnly',op_driver_acceptance_probability=.5,
                      op_driver_acceptance_max_declines=0,op_driver_acceptance_ranked_fallback=True)
    with pytest.raises(ValueError,match='ImmediateDecisionsSimulation and BasicRequest'):
        DriverAcceptance(attributes,dict(random_seed=1,**scenario),0,[SimpleNamespace(vid=0)],tmp_path)
