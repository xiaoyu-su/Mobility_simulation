import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
import yaml

from tools.paired_eval.metrics import per_driver_metrics


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests/regression/run_example.py"
REFERENCES = ROOT / "tests/regression/baselines"


def run(example, parameters, output):
    config = output.with_suffix(".yaml")
    config.write_text(yaml.safe_dump(parameters))
    command = [sys.executable, str(RUNNER), example, "--source-root", str(ROOT),
               "--output", str(output), "--driver-acceptance-config", str(config)]
    if "op_driver_acceptance_probability" not in parameters:
        command.extend(["--network-tt-noise-sigma", ".3"])
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180,
                            env=dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONHASHSEED="0"))
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert (output / "final_state.csv").is_file()
    users = pd.read_csv(output / "1_user-stats.csv")
    assert len(users) == 100 and users.request_id.is_unique
    decisions = pd.read_csv(output / "driver_acceptance_op_0.csv")
    assert set(decisions[decisions.accepted].request_id) == set(users[users.dropoff_time.notna()].request_id)
    per_driver_metrics(output)
    return users


@pytest.mark.integration
@pytest.mark.parametrize("example", ["insertion", "immediate_batch", "batch"])
@pytest.mark.parametrize("mode", ["always", "k0", "logistic"])
def test_future_value_complete_examples_preserve_decisions_commitments_and_compatibility(example, mode, tmp_path):
    parameters = {"op_driver_acceptance": "logistic", "op_driver_acceptance_weight_objective": True,
                  "op_driver_acceptance_max_declines": 0, "op_driver_acceptance_future_value": True,
                  "op_driver_acceptance_future_value_top_k": 0 if mode == "k0" else 3}
    if mode == "always":
        parameters["op_driver_acceptance_probability"] = 1
    else:
        parameters.update(op_driver_acceptance_intercept=0, op_driver_acceptance_beta_eta=-.15,
                          op_driver_acceptance_beta_value=.1)
    output = tmp_path / "future"
    users = run(example, parameters, output)
    audit = json.loads((output / "future_value_op_0.json").read_text())
    scores = pd.read_csv(output / "future_value_op_0.csv")
    decisions = pd.read_csv(output / "driver_acceptance_op_0.csv")
    assert audit["enabled"] and audit["top_k"] == parameters["op_driver_acceptance_future_value_top_k"]
    assert not scores.empty and scores.request_id.is_unique
    assert len(scores) == decisions.request_id.nunique()
    assert (scores.served_value >= scores.probability).all() and (scores.served_value <= 1).all()
    np.testing.assert_allclose(scores.probability, decisions.groupby("request_id").first().loc[scores.request_id, "probability"], atol=1e-14)
    for record in scores.itertuples():
        if pd.notna(record.alternative_vehicle_ids):
            assert str(int(record.vehicle_id)) not in str(record.alternative_vehicle_ids).split(";")
    if mode == "always":
        expected = pd.read_csv(REFERENCES / example / "1_user-stats.csv")
        pd.testing.assert_frame_equal(users.sort_values("request_id").reset_index(drop=True),
                                      expected.sort_values("request_id").reset_index(drop=True), check_exact=True)
        pd.testing.assert_frame_equal(pd.read_csv(output / "standard_eval.csv"),
                                      pd.read_csv(REFERENCES / example / "standard_eval.csv"), check_exact=True)
        assert audit["counters"]["routing_queries"] == 0
        assert (scores.served_value == 1).all() and scores.fallback_probability.isna().all()
    elif mode == "k0":
        assert audit["counters"]["routing_queries"] == 0
        control = tmp_path / "phase3"
        run(example, {**parameters, "op_driver_acceptance_future_value": False}, control)
        for filename in ("1_user-stats.csv", "standard_eval.csv", "driver_acceptance_op_0.csv"):
            pd.testing.assert_frame_equal(pd.read_csv(output / filename), pd.read_csv(control / filename), check_exact=True)
        assert not (control / "future_value_op_0.csv").exists()
    else:
        assert audit["counters"]["routing_queries"] > 0
        assert audit["counters"]["fallback_cache_hits"] > 0
        assert (scores.served_value > scores.probability).any()
        np.testing.assert_allclose(scores.served_value,
                                   scores.probability + (1 - scores.probability) * scores.fallback_probability, atol=1e-14)
