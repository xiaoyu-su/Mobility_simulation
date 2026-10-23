import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from src.demand.demand import Demand
from src.misc.seeding import component_rng, derive_rng


def test_named_streams_do_not_depend_on_creation_order_or_other_draws():
    expected = derive_rng(42, "demand").integers(100000, size=30)
    derive_rng(42, "batch_optimizer/0").random(10000)
    derive_rng(42, "parcels").shuffle(np.arange(100))
    np.testing.assert_array_equal(expected, derive_rng(42, "demand").integers(100000, size=30))
    assert not np.array_equal(expected, derive_rng(43, "demand").integers(100000, size=30))
    assert not np.array_equal(expected, derive_rng(42, "parcels").integers(100000, size=30))


def test_derivation_does_not_change_global_random_state():
    np.random.seed(42)
    before = np.random.get_state()
    derive_rng(99, "demand").random(100)
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])


def test_stream_is_stable_across_python_hash_seeds():
    code = "from src.misc.seeding import derive_rng; print(derive_rng(42, 'demand').integers(100000, size=10).tolist())"
    results = [subprocess.check_output([sys.executable, "-c", code],
               env=dict(os.environ, PYTHONHASHSEED=seed), text=True) for seed in ("1", "987")]
    assert results[0] == results[1]


@pytest.mark.parametrize("seed,name", [(-1, "demand"), (1.5, "demand"), (True, "demand"), (1, "")])
def test_invalid_stream_keys_are_rejected(seed, name):
    with pytest.raises(ValueError):
        derive_rng(seed, name)


def test_default_is_legacy_and_unknown_mode_is_rejected():
    assert component_rng({}, "demand") is None
    assert component_rng({"random_stream_mode": "legacy"}, "demand") is None
    with pytest.raises(ValueError, match="random_stream_mode"):
        component_rng({"random_stream_mode": "typo"}, "demand")


class RoutingStub:
    def return_position_from_str(self, value):
        return (int(value), None, None)


def test_loaded_demand_is_unchanged_by_parcel_loading_or_optimizer_draws(tmp_path):
    demand_file = tmp_path / "demand.csv"
    pd.DataFrame({"request_id": range(40), "rq_time": range(40),
                  "start": [1] * 40, "end": [2] * 40}).to_csv(demand_file, index=False)
    parameters = {"random_seed": 17, "random_stream_mode": "independent", "user_max_decision_time": 0}

    def load(with_interference):
        demand = Demand(parameters, str(tmp_path / "unused.csv"), RoutingStub())
        if with_interference:
            np.random.random(500)
            derive_rng(17, "batch_optimizer/0").random(10000)
            demand.load_parcel_demand_file(0, 100, str(tmp_path), "demand.csv", 17,
                                          parcel_rq_type="BasicParcelRequest")
        np.random.seed(123)
        before = np.random.get_state()
        demand.load_demand_file(0, 100, str(tmp_path), "demand.csv", 17,
                               rq_type_distr={"BasicRequest": 0.5, "SlaveRequest": 0.5})
        after = np.random.get_state()
        np.testing.assert_array_equal(before[1], after[1])
        assert before[2:] == after[2:]
        return demand.input_fingerprints["demand"]

    assert load(False) == load(True)


def test_traveler_choices_are_isolated_per_request():
    from src.demand.TravelerModels import WaitingTimeSensitiveLinearDeclineRequest
    from src.simulation.Offers import TravellerOffer

    parameters = {"random_seed": 9, "random_stream_mode": "independent", "nr_mod_operators": 1,
                  "user_max_wait_time": 0, "user_max_wait_time_2": 100}
    row = pd.Series({"request_id": 7, "rq_time": 0, "start": 1, "end": 2, "latest_decision_time": 0})
    requests = [WaitingTimeSensitiveLinearDeclineRequest(row, RoutingStub(), 1, parameters) for _ in range(2)]
    outcomes = []
    for request in requests:
        request.receive_offer(0, TravellerOffer(7, 0, 50, 60, 100), 0)
        np.random.random(1234)
        derive_rng(9, "batch_optimizer/0").random(99)
        outcomes.append([request.choose_offer(parameters, 0) for _ in range(20)])
    assert outcomes[0] == outcomes[1]


def test_batch_optimizer_initialization_leaves_global_stream_untouched():
    from types import SimpleNamespace
    from src.fleetctrl.pooling.batch.BatchAssignmentAlgorithmBase import BatchAssignmentAlgorithmBase

    holder = SimpleNamespace()
    np.random.seed(42)
    before = np.random.get_state()
    BatchAssignmentAlgorithmBase.__init__(holder, None, None, 0, None,
                                         {"random_stream_mode": "independent"}, seed=9)
    after = np.random.get_state()
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]
    assert holder.rng is not None and 0 <= holder.solver_seed < 2_000_000_000
