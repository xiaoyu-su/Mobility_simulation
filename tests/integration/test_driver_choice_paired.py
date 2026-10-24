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
@pytest.mark.parametrize("constant,baseline,candidate,equal", [
    ("constant_config_ir.csv", "example_ir_driver_acceptance.yaml", "example_ir_driver_choice.yaml", True),
    ("constant_config_pool.csv", "example_batch_driver_choice.yaml", "example_batch_driver_choice.yaml", True),
    ("constant_config_ir.csv", "example_ir_future_value.yaml", "example_ir_future_value_choice.yaml", True),
])
def test_choice_paired_experiments_are_reproducible_and_preserve_singleton_controls(constant, baseline, candidate, equal, tmp_path):
    output = tmp_path / "experiment"
    command = [sys.executable, "-m", "tools.paired_eval", "--constant-config", str(SCENARIOS / constant),
               "--baseline-scenarios", str(SCENARIOS / baseline), "--candidate-scenarios", str(SCENARIOS / candidate),
               "--network-tt-noise-sigma", ".3", "--seeds", "5", "11", "--output", str(output)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=240,
                            env=dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1"))
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "complete" and len(manifest["validated_pairs"]) == 2
    for seed in (5, 11):
        folder = output / "runs" / f"seed_{seed}"
        users = pd.read_csv(folder / "candidate/1_user-stats.csv")
        decisions = pd.read_csv(folder / "candidate/driver_acceptance_op_0.csv")
        assert len(users) == 100 and users.request_id.is_unique
        assert set(decisions[decisions.accepted].request_id) == set(users[users.dropoff_time.notna()].request_id)
        choice = pd.read_csv(folder / "candidate/driver_choice_op_0.csv")
        audit = json.loads((folder / "candidate/driver_choice_op_0.json").read_text())
        assert audit["counters"]["accepted_items"] == int(choice.accepted.sum())
        if equal:
            for filename in ("1_user-stats.csv", "standard_eval.csv", "driver_acceptance_op_0.csv"):
                pd.testing.assert_frame_equal(pd.read_csv(folder / "baseline" / filename),
                                              pd.read_csv(folder / "candidate" / filename), check_exact=True)
            comparison = pd.read_csv(output / "paired_comparison.csv")
            assert (comparison.loc[comparison.n_pairs == 2, "mean_difference"] == 0).all()
        if baseline == candidate:
            pd.testing.assert_frame_equal(pd.read_csv(folder / "baseline/driver_choice_op_0.csv"), choice, check_exact=True)
            assert json.loads((folder / "baseline/driver_choice_op_0.json").read_text()) == audit
        else:
            assert not (folder / "baseline/driver_choice_op_0.csv").exists()
        if "future_value" in baseline:
            for filename in ("future_value_op_0.csv",):
                pd.testing.assert_frame_equal(pd.read_csv(folder / "baseline" / filename),
                                              pd.read_csv(folder / "candidate" / filename), check_exact=True)
