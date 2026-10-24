from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from src.fleetctrl.acceptance.driver_acceptance import DriverAcceptance, create_driver_acceptance
from src.fleetctrl.acceptance.future_value import FutureValue, at_least_one, ENABLED, TOP_K
from src.misc.globals import G_PRQS_ACC_OFFER, VRL_STATES


def vehicle(vid, position=None, capacity=4, status=VRL_STATES.IDLE):
    return SimpleNamespace(vid=vid, pos=(vid, None, None) if position is None else position,
                           max_pax=capacity, status=status)


def request(rid=7, origin=(99, None, None), earliest=0, latest=1000, passengers=1, distance=1000):
    return SimpleNamespace(get_rid_struct=lambda: rid, get_o_stop_info=lambda: (origin, earliest, latest),
                           init_direct_td=distance, nr_pax=passengers, status=1)


class Network:
    def __init__(self, times):
        self.times = times
        self.calls = 0
    def return_travel_costs_1to1(self, position, origin):
        self.calls += 1
        time = self.times[position]
        return time, time, 100


class Acceptance:
    operator_id = 0
    override = None
    def __init__(self, probabilities):
        self.probabilities = probabilities
    def probability_at_eta(self, vid, request, eta):
        return self.probabilities[vid]


def reference(vehicles, network, acceptance, rq, now, chosen, k):
    # Independent full scan/sort: no production shortlist/cache helpers.
    origin, earliest, latest = rq.get_o_stop_info()
    candidates = []
    for v in vehicles:
        if v.vid == chosen or v.status == VRL_STATES.OUT_OF_SERVICE or v.pos is None or v.max_pax < rq.nr_pax:
            continue
        time = network.return_travel_costs_1to1(v.pos, origin)[1]
        if np.isfinite(time) and time >= 0:
            eta = max(0, time, earliest - now)
            if eta <= latest - now:
                candidates.append((eta, v.vid))
    candidates = sorted(candidates)[:k]
    fallback = 1 - np.prod([1 - acceptance.probability_at_eta(vid, rq, eta) for eta, vid in candidates])
    return tuple(candidates), float(fallback)


def test_formula_excludes_the_current_driver_and_preserves_cost_and_commitments(tmp_path):
    vehicles = [vehicle(i) for i in range(3)]
    attributes = {"op_driver_acceptance_probability": .25, "op_driver_acceptance_weight_objective": True,
                  ENABLED: True, TOP_K: 2}
    model = DriverAcceptance(attributes, {"random_seed": 17}, 0, vehicles, tmp_path)
    net = Network({v.pos: (v.vid + 1) * 10 for v in vehicles})
    rq = request()
    estimate = model.future_value.estimate(.25, 0, rq, 100, net)
    assert estimate.fallback == pytest.approx(.4375)  # 1 - .75²
    assert estimate.served_value == pytest.approx(.578125)  # .25 + .75 × .4375
    assert estimate.alternatives == ((20, 1), (30, 2))
    base = lambda *args: -1970.0  # cost 30 - 1000 for each of two requests
    base.assignment_reward_per_request = 1000
    committed = request(8)
    committed.status = G_PRQS_ACC_OFFER
    plan = SimpleNamespace(pax_info={7: [120, 200], 8: [130, 210]})
    objective = model.wrap_objective(base)
    assert objective(100, vehicles[0], plan, {7: rq, 8: committed}, net) == pytest.approx(-1548.125)
    assert not model.draws and pd.read_csv(model.path).empty


@pytest.mark.parametrize("k", [0, 1, 3, 20])
def test_exact_optimized_top_k_matches_independent_full_scan_for_every_exclusion(k):
    rng = np.random.default_rng(55)
    vehicles = [vehicle(i, position=(i // 2, None, None)) for i in range(16)]
    vehicles[4].status = VRL_STATES.OUT_OF_SERVICE
    vehicles[6].max_pax = 0
    vehicles[8].pos = None
    times = {v.pos: float(rng.integers(0, 150)) for v in vehicles if v.pos is not None}
    times[vehicles[10].pos] = np.inf
    times[vehicles[12].pos] = 1000
    probabilities = {v.vid: float(rng.random()) for v in vehicles}
    acceptance = Acceptance(probabilities)
    net = Network(times)
    scorer = FutureValue(acceptance, list(reversed(vehicles)), k)
    rq = request(earliest=40, latest=200, passengers=1)
    scorer.begin_round(100, net)
    for chosen in range(16):
        expected, fallback = reference(vehicles, Network(times), acceptance, rq, 100, chosen, k)
        actual = scorer.estimate(.3, chosen, rq, 100, net)
        assert actual.alternatives == expected
        assert actual.fallback == pytest.approx(fallback)
        assert actual.served_value == pytest.approx(.3 + .7 * fallback)
    assert scorer.counters["routing_queries"] <= len(times)
    if k:
        assert scorer.counters["candidate_queries"] == 1


def test_ties_earliest_start_and_distinct_colocated_drivers():
    vehicles = [vehicle(9, (1, None, None)), vehicle(3, (1, None, None)), vehicle(5, (2, None, None))]
    net = Network({(1, None, None): 1, (2, None, None): 5})
    scorer = FutureValue(Acceptance({3: .2, 5: .3, 9: .4}), vehicles, 2)
    estimate = scorer.estimate(.4, 9, request(earliest=110), 100, net)
    assert estimate.alternatives == ((10, 3), (10, 5))
    assert estimate.fallback == pytest.approx(.44)
    assert net.calls == 2  # one query per position, not per colocated vehicle


def test_cache_is_bound_to_explicit_round_and_refreshes_network_and_fleet_at_same_clock_time():
    vehicles = [vehicle(0), vehicle(1)]
    net = Network({vehicles[0].pos: 10, vehicles[1].pos: 20})
    scorer = FutureValue(Acceptance({0: .2, 1: .5}), vehicles, 1)
    rq = request(latest=150)
    first = scorer.estimate(.2, 0, rq, 100, net)
    for _ in range(30):
        assert scorer.estimate(.2, 0, rq, 100, net) == first
    assert net.calls == 2
    assert scorer.counters["fallback_cache_hits"] == 30
    net.times[vehicles[1].pos] = 200
    scorer.begin_round(100, net)
    assert scorer.estimate(.2, 0, rq, 100, net).fallback == 0
    vehicles[1].status = VRL_STATES.OUT_OF_SERVICE
    scorer.begin_round(100, net)
    assert scorer.estimate(.2, 0, rq, 100, net).alternatives == ()
    assert scorer.counters["rounds"] == 3


def test_deadline_and_request_geometry_changes_do_not_reuse_stale_candidates():
    vehicles = [vehicle(0), vehicle(1)]
    net = Network({vehicles[0].pos: 10, vehicles[1].pos: 20})
    scorer = FutureValue(Acceptance({0: .2, 1: .5}), vehicles, 1)
    assert scorer.estimate(.2, 0, request(latest=150), 100, net).fallback == .5
    assert scorer.estimate(.2, 0, request(latest=115), 100, net).fallback == 0
    assert scorer.counters["candidate_queries"] == 2


def test_exact_probability_boundaries_need_no_routes_or_draws():
    scorer = FutureValue(Acceptance({}), [], 0)
    assert scorer.estimate(.3, 0, request(), 100, None).served_value == .3
    scorer.top_k = 5
    assert scorer.estimate(1, 0, request(), 100, None).served_value == 1
    scorer.acceptance.override = 0
    assert scorer.estimate(0, 0, request(), 100, None).served_value == 0
    assert scorer.counters["routing_queries"] == 0


@pytest.mark.parametrize("probabilities,result", [([], 0), ([0, 0], 0), ([1], 1), ([.2, .5], .6), ([1e-15], 1e-15)])
def test_chained_probability_is_stable(probabilities, result):
    assert at_least_one(probabilities) == pytest.approx(result, abs=1e-20)


@pytest.mark.parametrize("k", [-1, True, 1.5, None])
def test_invalid_top_k_is_rejected(k):
    with pytest.raises(ValueError, match="top_k"):
        FutureValue(Acceptance({}), [], k)


def test_feature_requires_acceptance_and_weighting(tmp_path):
    with pytest.raises(ValueError, match="requires op_driver_acceptance=logistic"):
        create_driver_acceptance({ENABLED: True}, {}, 0, [], tmp_path)
    with pytest.raises(ValueError, match="weight_objective"):
        DriverAcceptance({ENABLED: True}, {"random_seed": 0}, 0, [], tmp_path)
    with pytest.raises(ValueError, match="boolean"):
        create_driver_acceptance({ENABLED: "False"}, {}, 0, [], tmp_path)


def test_selected_proposal_records_values_without_changing_actual_acceptance(tmp_path):
    vehicles = [vehicle(i) for i in range(3)]
    model = DriverAcceptance({"op_driver_acceptance_probability": .25, "op_driver_acceptance_weight_objective": True,
                              "op_driver_acceptance_max_declines": 0, ENABLED: True, TOP_K: 2},
                             {"random_seed": 17}, 0, vehicles, tmp_path)
    model.begin_matching_round(100, Network({v.pos: 10 for v in vehicles}))
    model.draws[(7, 0)] = SimpleNamespace(random=Mock(return_value=.3))
    assert not model.accept(0, request(), SimpleNamespace(pax_info={7: [120, 200]}), 100)
    record = pd.read_csv(model.future_value.decisions_path).iloc[0]
    assert record.probability == .25 and record.served_value == pytest.approx(.578125)
    assert record.fallback_probability == .4375
    assert len(pd.read_csv(model.path)) == 1  # no offers sent to the alternatives
    model.draws[(7, 0)].random.assert_called_once()


@pytest.mark.parametrize("probabilities", [[-1], [1.1], [np.nan], [1, np.nan]])
def test_invalid_chained_probabilities_are_rejected_even_after_one(probabilities):
    with pytest.raises(ValueError, match="Fallback probabilities"):
        at_least_one(probabilities)


def test_real_road_network_matches_full_scan_for_partial_edge_and_colocated_vehicles():
    from pathlib import Path
    from src.routing.road.NetworkBasicWithStore import NetworkBasicWithStore
    root = Path(__file__).resolve().parents[2]
    directory = root / "data/networks/example_network"
    network = NetworkBasicWithStore(str(directory))
    edges = pd.read_csv(directory / "base/edges.csv").head(12)
    positions = [(int(edge.from_node), int(edge.to_node), .25) for edge in edges.itertuples()]
    vehicles = [vehicle(i, positions[i // 2]) for i in range(12)]
    rq = request(origin=(int(edges.iloc[8].to_node), None, None), latest=1e9)
    acceptance = Acceptance({v.vid: .1 + .05 * v.vid for v in vehicles})
    scorer = FutureValue(acceptance, vehicles, 4)
    for chosen in range(12):
        expected, fallback = reference(vehicles, network, acceptance, rq, 100, chosen, 4)
        actual = scorer.estimate(.4, chosen, rq, 100, network)
        assert actual.alternatives == expected
        assert actual.fallback == pytest.approx(fallback)
    assert scorer.counters["candidate_queries"] == 1
    assert scorer.counters["routing_queries"] == 6


def test_scoring_and_logging_respect_disabled_file_writing(tmp_path):
    vehicles = [vehicle(0), vehicle(1)]
    model = DriverAcceptance({"op_driver_acceptance_probability": .4,
                              "op_driver_acceptance_weight_objective": True, ENABLED: True},
                             {"random_seed": 17, "skip_file_writing": 1}, 0, vehicles, tmp_path)
    net = Network({v.pos: 10 for v in vehicles})
    estimate = model.future_value.estimate(.4, 0, request(), 0, net)
    assert estimate.served_value == pytest.approx(.64)
    model.future_value.write_audit()
    assert not list(tmp_path.iterdir())
