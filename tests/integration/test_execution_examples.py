"""Complete legacy and noisy runs; no numerical screenshot target is assumed."""

import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from tools.paired_eval.metrics import per_driver_metrics


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests/regression/run_example.py"
REFERENCES = ROOT / "tests/regression/baselines"


@pytest.mark.integration
@pytest.mark.parametrize("example", ["insertion", "immediate_batch", "batch"])
@pytest.mark.parametrize("sigma", [0, .6])
def test_complete_example_records_promises_and_retains_delayed_committed_riders(example, sigma, tmp_path):
    output = tmp_path / "run"
    command = [sys.executable, str(RUNNER), example, "--source-root", str(ROOT),
               "--output", str(output), "--network-tt-noise-sigma", str(sigma), "--record-promised-times"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180,
                            env=dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONHASHSEED="0"))
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert (output / "final_state.csv").is_file()
    users = pd.read_csv(output / "1_user-stats.csv").set_index("request_id").sort_index()
    assert len(users) == 100 and users.index.is_unique
    served = users[users.dropoff_time.notna()]
    assert len(served) > 0
    assert (users.promised_pickup_time.notna() == users.dropoff_time.notna()).all(), "Every booked rider must finish"
    assert (served.promise_operator_id == served.operator_id).all()
    assert (served.dropoff_time >= served.pickup_time).all()
    np.testing.assert_allclose(served.pickup_error_s, served.pickup_time - served.promised_pickup_time, atol=1e-9)
    np.testing.assert_allclose(served.dropoff_error_s, served.dropoff_time - served.promised_dropoff_time, atol=1e-9)
    legs = pd.read_csv(output / "2-0_op-stats.csv")
    per_driver_metrics(output)  # validates chronological activity, status, costs, and tail accounting
    if sigma == 0:
        assert "travel_time_multiplier" not in legs
        expected = pd.read_csv(REFERENCES / example / "1_user-stats.csv").set_index("request_id").sort_index()
        pd.testing.assert_frame_equal(users[expected.columns], expected, check_exact=True)
        pd.testing.assert_frame_equal(pd.read_csv(output / "standard_eval.csv"),
                                      pd.read_csv(REFERENCES / example / "standard_eval.csv"), check_exact=True)
    else:
        assert (legs.travel_time_multiplier > 0).all()
        assert (legs.loc[legs.status == "boarding", "travel_time_multiplier"] == 1).all()
        assert legs.travel_time_multiplier.min() < 1 < legs.travel_time_multiplier.max()
        assert served.pickup_error_s.min() < 0 < served.pickup_error_s.max()
        assert ((served.pickup_time - served.rq_time) > 300).any(), "Exercise service after the original waiting deadline"
