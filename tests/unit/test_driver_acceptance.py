import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.fleetctrl.acceptance.driver_acceptance import DriverAcceptance, DriverClass, create_driver_acceptance, PREFIX
from src.misc.globals import G_PRQS_ACC_OFFER, G_PRQS_NO_OFFER


def model(tmp_path, **settings):
    attributes = {PREFIX + "_intercept": 0, PREFIX + "_beta_eta": -.2,
                  PREFIX + "_beta_value": .1, **{PREFIX + "_" + key: value for key, value in settings.items()}}
    return DriverAcceptance(attributes, {"random_seed": 17}, 0, [SimpleNamespace(vid=0), SimpleNamespace(vid=1)], tmp_path)


def request(rid=7, status=G_PRQS_NO_OFFER):
    return SimpleNamespace(get_rid_struct=lambda: rid, init_direct_td=10000, status=status)


def test_logistic_signs_units_and_extreme_values():
    group = DriverClass(1, 1, -.2, .1)
    assert group.probability(300, 10000) == pytest.approx(1 / (1 + np.exp(-1)))
    assert group.probability(600, 10000) < group.probability(300, 10000)
    assert group.probability(300, 20000) > group.probability(300, 10000)
    assert DriverClass(1, 1000, 0, 0).probability(0, 0) == 1
    assert DriverClass(1, -1000, 0, 0).probability(0, 0) == 0
    with pytest.raises(ValueError):
        group.probability(-1, 100)


@pytest.mark.parametrize("settings", [{"probability": -1}, {"probability": 1.1}, {"probability": np.nan},
                                     {"max_declines": -1}, {"max_declines": 1.5}, {"max_declines": True},
                                     {"intercept": np.inf}, {"beta_value": None}, {"weight_objective": "False"},
                                     {"classes": {}}, {"classes": {"full": {"share": 1}}},
                                     {"classes": {"full": {"share": .5, "intercept": 0, "beta_eta": 0, "beta_value": 0}}}])
def test_invalid_settings_are_rejected(settings, tmp_path):
    with pytest.raises(ValueError):
        model(tmp_path, **settings)


def test_off_constructs_no_stream_or_files(tmp_path):
    assert create_driver_acceptance({}, {}, 0, [], tmp_path) is None
    assert create_driver_acceptance({PREFIX: "off"}, {}, 0, [], tmp_path) is None
    assert not list(tmp_path.iterdir())


def test_bounded_retries_terminal_rejection_and_cached_decision(tmp_path):
    obj = model(tmp_path, probability=0, max_declines=2)
    rq, plan = request(), SimpleNamespace(pax_info={7: [300, 500]})
    assert not obj.accept(0, rq, plan, 100)
    assert not obj.accept(0, rq, plan, 100)
    log = pd.read_csv(obj.path)
    assert list(log.attempt) == [1, 2, 3]
    assert list(log.terminal_decline) == [False, False, True]
    assert list(log.decline_count) == [1, 2, 3]
    assert not log.accepted.any() and log.uniform_draw.isna().all()
    assert obj.draws == {}


def test_retry_can_accept_and_never_consumes_other_component_rngs(tmp_path):
    from unittest.mock import Mock
    obj = model(tmp_path, probability=.5, max_declines=2)
    obj.draws[(7, 0)] = SimpleNamespace(random=Mock(side_effect=[.9, .8, .1]))
    rq, plan = request(), SimpleNamespace(pax_info={7: [300, 500]})
    assert obj.accept(0, rq, plan, 100)
    log = pd.read_csv(obj.path)
    assert list(log.accepted) == [False, False, True]
    assert list(log.attempt) == [1, 2, 3]
    assert not log.terminal_decline.any()


def test_scoring_and_unrelated_decisions_do_not_shift_request_draws(tmp_path):
    np.random.seed(42)
    before = np.random.get_state()
    first, repeat = model(tmp_path / "first"), model(tmp_path / "repeat")
    plan = SimpleNamespace(pax_info={7: [300, 500], 8: [400, 600]})
    for _ in range(100):
        repeat.probability(0, request(), plan, 100)
    repeat.accept(1, request(8), plan, 100)
    assert first.accept(0, request(), plan, 100) == repeat.accept(0, request(), plan, 100)
    a, b = pd.read_csv(first.path), pd.read_csv(repeat.path)
    pd.testing.assert_frame_equal(a.reset_index(drop=True), b[b.request_id == 7].reset_index(drop=True))
    after = np.random.get_state()
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def test_classes_are_fixed_by_vehicle_id_and_recorded_with_coefficient_provenance(tmp_path):
    classes = {"part": {"share": .6, "intercept": 0, "beta_eta": -.1, "beta_value": .2},
               "full": {"share": .4, "intercept": 1, "beta_eta": -.2, "beta_value": .3}}
    first = model(tmp_path / "first", classes=classes)
    second = model(tmp_path / "second", classes=dict(reversed(list(classes.items()))))
    assert first.vehicle_classes == second.vehicle_classes
    audit = json.loads((tmp_path / "first/driver_acceptance_op_0.json").read_text())
    assert audit["classes"]["full"]["beta_eta"] == -.2
    assert audit["coefficient_status"] == "user-supplied, not calibrated"
    assert audit["units"]["beta_value"] == "per direct-trip kilometer"


def test_committed_riders_are_not_redrawn_or_removed_even_with_zero_acceptance(tmp_path):
    obj = model(tmp_path, probability=0)
    assert obj.accept(0, request(status=G_PRQS_ACC_OFFER), SimpleNamespace(), 100)
    assert pd.read_csv(obj.path).empty and obj.draws == {}


def test_weight_only_changes_uncommitted_request_reward_and_never_operating_cost(tmp_path):
    obj = model(tmp_path, probability=.25, weight_objective=True)
    base = lambda *args: -1970.0  # 30 cost - 1000 each for two requests
    base.assignment_reward_per_request = 1000
    objective = obj.wrap_objective(base)
    plan = SimpleNamespace(pax_info={7: [300, 500], 8: [400, 600]})
    requests = {7: request(), 8: request(8, G_PRQS_ACC_OFFER)}
    assert objective(100, SimpleNamespace(vid=0), plan, requests, None) == -1220
    assert obj.draws == {} and pd.read_csv(obj.path).empty
    obj.override = 1
    assert objective(100, SimpleNamespace(vid=0), plan, requests, None) == base()
    with pytest.raises(ValueError, match="requires distance"):
        obj.wrap_objective(lambda *args: 0)


def test_live_reduced_plan_cannot_mutate_the_optimizers_stored_committed_plan():
    from copy import deepcopy
    from unittest.mock import Mock
    from src.fleetctrl.RidePoolingBatchOptimizationFleetControlBase import RidePoolingBatchOptimizationFleetControlBase

    class Plan:
        def __init__(self, rids):
            self.pax_info = {rid: [100, 200] for rid in rids}
            self.stops = list(rids)
        def copy(self):
            return deepcopy(self)

    proposed, stored_lower = Plan([7, 8]), Plan([8])
    controller = SimpleNamespace(sim_time=0, sim_vehicles=[SimpleNamespace(vid=0)],
        rq_dict={7: request(7), 8: request(8, G_PRQS_ACC_OFFER)},
        rid_to_assigned_vid={8: 0}, _driver_declined_requests=set(), veh_plans={0: Plan([8])},
        driver_acceptance=SimpleNamespace(accept=lambda vid, rq, plan, now: rq.get_rid_struct() != 7),
        RPBO_Module=SimpleNamespace(get_optimisation_solution=lambda vid: proposed,
                                   get_vehicle_plan_without_rid=lambda *args: stored_lower),
        assign_vehicle_plan=Mock())
    RidePoolingBatchOptimizationFleetControlBase._set_new_assignments(controller)
    live = controller.assign_vehicle_plan.call_args.args[1]
    assert set(live.pax_info) == {8} and controller._driver_declined_requests == {7}
    assert controller.assign_vehicle_plan.call_args.kwargs["add_arg"] is True
    live.stops.clear()
    live.pax_info.clear()
    assert stored_lower.stops == [8] and set(stored_lower.pax_info) == {8}


def test_skip_file_writing_is_respected(tmp_path):
    obj = DriverAcceptance({PREFIX + "_probability": 1},
                           {"random_seed": 17, "skip_file_writing": 1}, 0, [SimpleNamespace(vid=0)], tmp_path)
    assert obj.accept(0, request(), SimpleNamespace(pax_info={7: [300, 500]}), 100)
    assert not list(tmp_path.iterdir())


def test_acceptance_report_counts_decisions_and_rejects_malformed_boolean_columns(tmp_path):
    from tools.paired_eval.metrics import driver_acceptance_summary
    assert driver_acceptance_summary(tmp_path)["driver_offer_attempts"] == 0
    obj = model(tmp_path, probability=0, max_declines=1)
    obj.accept(0, request(), SimpleNamespace(pax_info={7: [300, 500]}), 100)
    summary = driver_acceptance_summary(tmp_path)
    assert summary == {"driver_offer_attempts": 2, "driver_acceptances": 0, "driver_declines": 2,
                       "driver_terminal_declines": 1, "driver_offered_requests": 1}
    log = pd.read_csv(obj.path)
    log["accepted"] = 0
    log.to_csv(obj.path, index=False)
    with pytest.raises(ValueError, match="Malformed"):
        driver_acceptance_summary(tmp_path)


def test_yaml_scenarios_load_nested_class_parameters_and_merge_constants(tmp_path):
    from src.misc.config import ConstantConfig, ScenarioConfig
    import yaml
    classes = {"full": {"share": 1, "intercept": 0, "beta_eta": -.2, "beta_value": .1}}
    path = tmp_path / "scenarios.yaml"
    path.write_text(yaml.safe_dump([{PREFIX: "logistic", PREFIX + "_classes": classes, "random_seed": 9}]))
    scenarios = ScenarioConfig(str(path))
    assert len(scenarios) == 1 and isinstance(scenarios[0], ConstantConfig)
    merged = ConstantConfig({"random_seed": 1, "network_name": "test"}) + scenarios[0]
    assert merged["random_seed"] == 9 and merged["network_name"] == "test"
    assert merged[PREFIX + "_classes"] == classes


@pytest.mark.parametrize("contents", ["random_seed: 9\n", "- 9\n", ""])
def test_yaml_scenarios_reject_invalid_container_shapes(contents, tmp_path):
    from src.misc.config import ScenarioConfig
    path = tmp_path / "scenarios.yaml"
    path.write_text(contents)
    with pytest.raises(ValueError, match="list of parameter mappings"):
        ScenarioConfig(str(path))
