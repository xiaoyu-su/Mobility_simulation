"""Run real insertions/Alonso-Mora assignments with acceptance enabled."""

import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
import yaml

from tools.paired_eval.metrics import per_driver_metrics, driver_acceptance_summary


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests/regression/run_example.py"
REFERENCES = ROOT / "tests/regression/baselines"


@pytest.mark.integration
@pytest.mark.parametrize("example", ["insertion", "immediate_batch", "batch"])
@pytest.mark.parametrize("mode", ["always", "never", "logistic"])
def test_acceptance_executes_only_accepted_rides_and_preserves_committed_plans(example, mode, tmp_path):
    output = tmp_path / "run"
    config = {"op_driver_acceptance": "logistic", "op_driver_acceptance_max_declines": 1}
    if mode == "logistic":
        config.update(op_driver_acceptance_intercept=0, op_driver_acceptance_beta_eta=-.15,
                      op_driver_acceptance_beta_value=.1, op_driver_acceptance_weight_objective=True)
    else:
        config.update(op_driver_acceptance_probability=1 if mode == "always" else 0,
                      op_driver_acceptance_weight_objective=mode == "always")
    config_path = tmp_path / "acceptance.yaml"
    config_path.write_text(yaml.safe_dump(config))
    command = [sys.executable, str(RUNNER), example, "--source-root", str(ROOT),
               "--output", str(output), "--driver-acceptance-config", str(config_path)]
    if mode == "logistic":
        command.extend(["--network-tt-noise-sigma", "0.3"])
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180,
                            env=dict(os.environ, PYTHONHASHSEED="0", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"))
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert (output / "final_state.csv").is_file()
    users = pd.read_csv(output / "1_user-stats.csv").set_index("request_id").sort_index()
    assert len(users) == 100 and users.index.is_unique
    served = users[users.dropoff_time.notna()]
    decisions = pd.read_csv(output / "driver_acceptance_op_0.csv")
    assert not decisions.empty
    assert not decisions.duplicated(["request_id", "attempt"]).any()
    assert decisions.groupby("request_id").attempt.max().max() <= 2
    accepted = decisions[decisions.accepted].set_index("request_id")
    declined = decisions[decisions.terminal_decline]
    assert set(served.index) == set(accepted.index), "No booked riders abandoned and no declined riders served"
    assert set(served.index).isdisjoint(set(declined.request_id))
    assert accepted.index.is_unique
    summary = driver_acceptance_summary(output)
    assert summary["driver_offer_attempts"] == len(decisions)
    assert summary["driver_acceptances"] == len(served)
    assert summary["driver_declines"] == (~decisions.accepted).sum()
    if mode == "always":
        expected = pd.read_csv(REFERENCES / example / "1_user-stats.csv").set_index("request_id").sort_index()
        pd.testing.assert_frame_equal(users, expected, check_exact=True)
        pd.testing.assert_frame_equal(pd.read_csv(output / "standard_eval.csv"),
                                      pd.read_csv(REFERENCES / example / "standard_eval.csv"), check_exact=True)
        assert summary["driver_declines"] == 0
        assert decisions.uniform_draw.isna().all()
    elif mode == "never":
        assert len(served) == 0
        assert not decisions.accepted.any()
        assert decisions.groupby("request_id").size().eq(2).all()
        assert decisions.groupby("request_id").terminal_decline.sum().eq(1).all()
        assert users.offers.str.contains("driver_declined").any()
    else:
        assert 0 < len(served) < 100
        assert (~decisions.accepted).any()
        assert users.promised_pickup_time.notna().sum() == len(served)
        assert np.isfinite(served.pickup_error_s).all()
    per_driver_metrics(output)
