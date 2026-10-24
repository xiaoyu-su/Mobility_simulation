import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ROOT / "studies/example_study/scenarios"


@pytest.mark.integration
@pytest.mark.parametrize("constants,baseline,candidate", [
    ("constant_config_ir.csv", "example_ir_future_value.yaml", "example_ir_future_value.yaml"),
    ("constant_config_ir.csv", "example_ir_driver_acceptance.yaml", "example_ir_future_value.yaml"),
    ("constant_config_pool.csv", "example_batch_driver_classes.yaml", "example_batch_future_value.yaml"),
])
def test_future_value_paired_runs_are_repeatable_and_keep_the_background_matched(constants, baseline, candidate, tmp_path):
    output = tmp_path / "experiment"
    command = [sys.executable, "-m", "tools.paired_eval",
               "--constant-config", str(SCENARIOS / constants), "--baseline-scenarios", str(SCENARIOS / baseline),
               "--candidate-scenarios", str(SCENARIOS / candidate), "--network-tt-noise-sigma", ".3",
               "--seeds", "5", "11", "--output", str(output)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=240,
                            env=dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"))
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "complete" and len(manifest["validated_pairs"]) == 2
    for seed in (5, 11):
        directory = output / "runs" / f"seed_{seed}"
        users = pd.read_csv(directory / "candidate/1_user-stats.csv")
        decisions = pd.read_csv(directory / "candidate/driver_acceptance_op_0.csv")
        assert len(users) == 100 and users.request_id.is_unique
        assert set(decisions[decisions.accepted].request_id) == set(users[users.dropoff_time.notna()].request_id)
        audit = json.loads((directory / "candidate/future_value_op_0.json").read_text())
        assert audit["counters"]["weight_evaluations"] > audit["counters"]["candidate_queries"] > 0
        assert audit["counters"]["fallback_cache_hits"] > 0
        if baseline == candidate:
            for filename in ("1_user-stats.csv", "standard_eval.csv", "driver_acceptance_op_0.csv", "future_value_op_0.csv"):
                pd.testing.assert_frame_equal(pd.read_csv(directory / "baseline" / filename),
                                              pd.read_csv(directory / "candidate" / filename), check_exact=True)
            left = json.loads((directory / "baseline/future_value_op_0.json").read_text())
            assert left == audit
            comparison = pd.read_csv(output / "paired_comparison.csv")
            assert (comparison.loc[comparison.n_pairs == 2, "mean_difference"] == 0).all()
        else:
            assert not (directory / "baseline/future_value_op_0.csv").exists()
