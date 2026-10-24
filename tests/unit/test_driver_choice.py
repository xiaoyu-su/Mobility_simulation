from itertools import permutations
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from src.fleetctrl.acceptance.choice_model import ChoiceOffer, MenuChoice, choose_menu, menu_distribution
from src.fleetctrl.acceptance.conflict_resolution import resolve_choices
from src.fleetctrl.acceptance.driver_acceptance import DriverAcceptance, create_driver_acceptance
from src.fleetctrl.acceptance.driver_choice import choice_mode
from src.misc.globals import G_PRQS_ACC_OFFER


def request(rid=7, status=1):
    return SimpleNamespace(get_rid_struct=lambda: rid, init_direct_td=1000, status=status)


def model(path, mode="logit", **kwargs):
    attributes = {"op_driver_acceptance_probability": .5, "op_driver_acceptance_max_declines": 0,
                  "op_driver_choice_model": mode, **kwargs}
    return DriverAcceptance(attributes, {"random_seed": 17}, 0, [SimpleNamespace(vid=0)], path)


def test_logit_menu_has_an_outside_option_and_uses_odds_not_raw_probabilities():
    offers, probabilities, outside = menu_distribution(0, [ChoiceOffer(7, 0, .25), ChoiceOffer(8, 0, .75)])
    assert [offer.request_id for offer in offers] == [7, 8]
    np.testing.assert_allclose(probabilities, [1/13, 9/13], rtol=0, atol=1e-15)
    assert outside == pytest.approx(3/13)
    assert sum(probabilities) + outside == pytest.approx(1)


@pytest.mark.parametrize("probability", [0, .01, .37, .5, .99, 1])
def test_one_item_distribution_is_bit_exact_bernoulli(probability):
    offer = ChoiceOffer(7, 0, probability)
    assert menu_distribution(0, [offer]) == ((offer,), (probability,), 1 - probability)
    for value in (0, .2, .37, .9, .999999):
        result = choose_menu(0, [offer], SimpleNamespace(random=lambda: value))
        assert (result.selected is not None) == (value < probability)


def test_menu_sampling_does_not_depend_on_input_order():
    offers = [ChoiceOffer(8, 0, .4), ChoiceOffer(7, 0, .2), ChoiceOffer(9, 0, .6)]
    choices = [choose_menu(0, order, SimpleNamespace(random=lambda: .5)) for order in permutations(offers)]
    assert all(choice == choices[0] for choice in choices)


def test_empty_zero_and_single_certain_menus_do_not_draw():
    rng = Mock()
    assert choose_menu(0, [], rng).selected is None
    assert choose_menu(0, [ChoiceOffer(7, 0, 0), ChoiceOffer(8, 0, 0)], rng).selected is None
    assert choose_menu(0, [ChoiceOffer(7, 0, 1), ChoiceOffer(8, 0, .5)], rng).selected.request_id == 7
    rng.random.assert_not_called()


def test_multiple_certain_items_share_mass_and_extreme_finite_odds_remain_stable():
    _, probabilities, outside = menu_distribution(0, [ChoiceOffer(7, 0, 1), ChoiceOffer(8, 0, 1), ChoiceOffer(9, 0, 0)])
    assert probabilities == (.5, .5, 0) and outside == 0
    result = choose_menu(0, [ChoiceOffer(7, 0, 1), ChoiceOffer(8, 0, 1)], SimpleNamespace(random=lambda: .9))
    assert result.selected.request_id == 8
    _, probabilities, outside = menu_distribution(0, [ChoiceOffer(7, 0, 1 - 1e-15), ChoiceOffer(8, 0, 1e-300)])
    assert np.isfinite(probabilities).all() and outside > 0
    assert sum(probabilities) + outside == pytest.approx(1)
    tail = choose_menu(0, [ChoiceOffer(i, 0, 1) for i in range(6)],
                       SimpleNamespace(random=lambda: np.nextafter(1.0, 0)))
    assert tail.selected.request_id == 5 and tail.outside_probability == 0


def test_probability_one_tail_interval_is_recorded_correctly_before_zero_items(monkeypatch, tmp_path):
    obj = model(tmp_path)
    obj.probability = lambda vid, rq, plan, now: 1 if rq.get_rid_struct() < 6 else 0
    monkeypatch.setattr("src.fleetctrl.acceptance.driver_choice.derive_rng",
                        lambda *args: SimpleNamespace(random=lambda: np.nextafter(1.0, 0)))
    requests = {rid: request(rid) for rid in range(7)}
    plan = SimpleNamespace(pax_info={rid: [200, 300] for rid in range(7)})
    obj.choice.prepare_batch({0: plan}, requests, 100)
    log = pd.read_csv(obj.choice.path).set_index("request_id")
    assert log.loc[5, "accepted"] and log.loc[5, "interval_end"] == 1
    assert log.loc[6, "interval_start"] == log.loc[6, "interval_end"] == 1


@pytest.mark.parametrize("probability", [-.1, 1.1, np.inf, np.nan])
def test_invalid_probabilities_are_rejected(probability):
    with pytest.raises(ValueError):
        ChoiceOffer(7, 0, probability)


def test_mixed_drivers_duplicate_requests_and_invalid_draws_are_rejected():
    with pytest.raises(ValueError, match="driver's offers"):
        menu_distribution(0, [ChoiceOffer(7, 1, .5)])
    with pytest.raises(ValueError, match="Duplicate request"):
        menu_distribution(0, [ChoiceOffer(7, 0, .5), ChoiceOffer(7, 0, .6)])
    with pytest.raises(ValueError, match="Choice draw"):
        choose_menu(0, [ChoiceOffer(7, 0, .5)], SimpleNamespace(random=lambda: 1))


def test_greedy_conflicts_are_deterministic_and_never_double_serve():
    a = choose_menu(0, [ChoiceOffer(7, 0, 1, priority=2)], None)
    b = choose_menu(1, [ChoiceOffer(7, 1, 1, priority=1)], None)
    c = choose_menu(2, [ChoiceOffer(8, 2, 1)], None)
    for order in permutations([a, b, c]):
        resolution = resolve_choices(order)
        assert {(offer.request_id, offer.vehicle_id) for offer in resolution.accepted} == {(7, 1), (8, 2)}
        assert resolution.rejected == ((a.selected, "request_conflict"),)
        assert len({offer.request_id for offer in resolution.accepted}) == len(resolution.accepted)


def test_conflict_ties_and_protected_commitments():
    a = choose_menu(0, [ChoiceOffer(7, 0, 1)], None)
    b = choose_menu(1, [ChoiceOffer(7, 1, 1)], None)
    assert resolve_choices([b, a]).accepted == (a.selected,)
    assert resolve_choices([a, b], protected_requests={7}).accepted == ()
    assert resolve_choices([a], unavailable_vehicles={0}).rejected == ((a.selected, "vehicle_unavailable"),)
    with pytest.raises(ValueError, match="one menu choice"):
        resolve_choices([a, a])


def test_singleton_compatibility_preserves_phase3_draws_retries_and_files(tmp_path):
    plain = model(tmp_path / "plain", "off", op_driver_acceptance_max_declines=2)
    single = model(tmp_path / "single", "singleton", op_driver_acceptance_max_declines=2)
    plan = SimpleNamespace(pax_info={rid: [200, 300] for rid in range(30)})
    np.random.seed(123)
    before = np.random.get_state()
    for rid in range(30):
        assert plain.accept(0, request(rid), plan, 100) == single.accept(0, request(rid), plan, 100)
    pd.testing.assert_frame_equal(pd.read_csv(plain.path), pd.read_csv(single.path), check_exact=True)
    after = np.random.get_state()
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]
    assert not (tmp_path / "plain/driver_choice_op_0.csv").exists()


def test_multi_item_menu_records_one_categorical_decision_without_bernoulli_redraw(monkeypatch, tmp_path):
    obj = model(tmp_path)
    rng = SimpleNamespace(random=Mock(return_value=.4))
    monkeypatch.setattr("src.fleetctrl.acceptance.driver_choice.derive_rng", lambda *args: rng)
    obj.begin_matching_round(100, None)
    requests = {7: request(7), 8: request(8), 9: request(9, G_PRQS_ACC_OFFER)}
    plan = SimpleNamespace(pax_info={7: [200, 300], 8: [210, 310], 9: [100, 150]})
    obj.choice.prepare_batch({0: plan}, requests, 100)
    assert obj.outcomes == {(7, 0): False, (8, 0): True}
    assert not obj.draws  # only the categorical sampler consumed randomness
    assert not obj.accept(0, requests[7], plan, 100)
    assert obj.accept(0, requests[8], plan, 100)
    assert obj.accept(0, requests[9], plan, 100)
    obj.choice.prepare_batch({0: plan}, requests, 100)
    rng.random.assert_called_once()
    decisions = pd.read_csv(obj.path)
    assert list(decisions.accepted) == [False, True]
    np.testing.assert_allclose(decisions.probability, [1/3, 1/3])
    assert decisions.uniform_draw.isna().all()
    choices = pd.read_csv(obj.choice.path)
    assert list(choices.menu_size) == [2, 2]
    assert choices.loc[choices.accepted, "request_id"].tolist() == [8]
    assert choices.loc[choices.accepted, "interval_start"].iloc[0] < .4 < choices.loc[choices.accepted, "interval_end"].iloc[0]


def test_outside_menu_choice_rejects_all_and_duplicate_solver_assignment_fails(monkeypatch, tmp_path):
    obj = model(tmp_path)
    monkeypatch.setattr("src.fleetctrl.acceptance.driver_choice.derive_rng",
                        lambda *args: SimpleNamespace(random=lambda: .99))
    plan = SimpleNamespace(pax_info={7: [200, 300], 8: [210, 310]})
    requests = {7: request(7), 8: request(8)}
    obj.choice.prepare_batch({0: plan}, requests, 100)
    assert not any(obj.outcomes.values())
    assert obj.choice.counters["outside_choices"] == 1
    assert set(pd.read_csv(obj.choice.path).reason) == {"outside"}
    with pytest.raises(ValueError, match="multiple vehicles"):
        obj.choice.prepare_batch({0: plan, 1: plan}, requests, 100)


def test_configuration_and_output_suppression(tmp_path):
    with pytest.raises(ValueError, match="requires op_driver_acceptance"):
        create_driver_acceptance({"op_driver_choice_model": "logit"}, {}, 0, [], tmp_path)
    with pytest.raises(ValueError, match="must be off"):
        model(tmp_path, "invalid")
    with pytest.raises(ValueError, match="max_declines=0"):
        model(tmp_path, "logit", op_driver_acceptance_max_declines=1)
    with pytest.raises(ValueError, match="BasicRequest"):
        DriverAcceptance({"op_driver_acceptance_probability": 1, "op_driver_choice_model": "singleton"},
                         {"random_seed": 17, "rq_type": "WaitingTimeSensitiveLinearDeclineRequest"},
                         0, [SimpleNamespace(vid=0)], tmp_path)
    directory = tmp_path / "suppressed"
    obj = DriverAcceptance({"op_driver_acceptance_probability": 1, "op_driver_choice_model": "singleton"},
                           {"random_seed": 17, "skip_file_writing": 1}, 0, [SimpleNamespace(vid=0)], directory)
    assert obj.accept(0, request(), SimpleNamespace(pax_info={7: [200, 300]}), 100)
    obj.choice.write_audit()
    assert not directory.exists()


def test_separate_episodes_cannot_accept_the_same_uncommitted_request_twice(tmp_path):
    obj = DriverAcceptance({"op_driver_acceptance_probability": 1, "op_driver_choice_model": "singleton"},
                           {"random_seed": 17}, 0, [SimpleNamespace(vid=0), SimpleNamespace(vid=1)], tmp_path)
    rq = request()
    plan = SimpleNamespace(pax_info={7: [200, 300]})
    assert obj.accept(0, rq, plan, 100)
    with pytest.raises(ValueError, match="already accepted"):
        obj.accept(1, rq, plan, 100)
    rq.status = G_PRQS_ACC_OFFER  # later operator reassignment retains the booking
    assert obj.accept(1, rq, plan, 200)
    assert len(pd.read_csv(obj.path)) == 1


@pytest.mark.parametrize("extension", ["yaml", "csv"])
def test_explicit_off_survives_actual_yaml_and_csv_decoding(extension, tmp_path):
    from src.misc.config import ScenarioConfig
    path = tmp_path / f"off.{extension}"
    path.write_text("- op_driver_acceptance: off\n  op_driver_choice_model: off\n" if extension == "yaml"
                    else "op_driver_acceptance,op_driver_choice_model\noff,off\n")
    parameters = ScenarioConfig(str(path))[0]
    assert choice_mode(parameters) == "off"
    assert create_driver_acceptance(parameters, {}, 0, [], tmp_path) is None
    parameters.update(op_driver_acceptance="logistic", op_driver_acceptance_probability=1, op_module="PoolingIRSOnly")
    obj = create_driver_acceptance(parameters, {"random_seed": 17, "sim_env": "ImmediateDecisionsSimulation"},
                                   0, [SimpleNamespace(vid=0)], tmp_path)
    assert obj.choice is None
    assert obj.accept(0, request(), SimpleNamespace(pax_info={7: [200, 300]}), 100)
    assert not (tmp_path / "driver_choice_op_0.csv").exists()
