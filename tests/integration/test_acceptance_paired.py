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
@pytest.mark.parametrize("baseline,candidate,constants", [
    ("example_ir_driver_acceptance.yaml", "example_ir_driver_acceptance.yaml", "constant_config_ir.csv"),
    ("example_ir_only.csv", "example_ir_driver_classes.yaml", "constant_config_ir.csv"),
    ("example_pool.csv", "example_batch_driver_classes.yaml", "constant_config_pool.csv"),
])
def test_paired_acceptance_audits_repeatability_and_report_pipeline(baseline, candidate, constants, tmp_path):
    output = tmp_path / "experiment"
    command = [sys.executable, "-m", "tools.paired_eval",
               "--constant-config", str(SCENARIOS / constants),
               "--baseline-scenarios", str(SCENARIOS / baseline),
               "--candidate-scenarios", str(SCENARIOS / candidate),
               "--network-tt-noise-sigma", ".3", "--seeds", "5", "11", "--output", str(output)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=240,
                            env=dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"))
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "complete" and len(manifest["validated_pairs"]) == 2
    comparison = pd.read_csv(output / "paired_comparison.csv").set_index("metric")
    assert comparison.loc["driver_declines", "candidate_mean"] > 0
    assert comparison.loc["driver_offer_attempts", "candidate_mean"] > 0
    for seed in (5, 11):
        directory = output / "runs" / f"seed_{seed}"
        users = pd.read_csv(directory / "candidate/1_user-stats.csv")
        decisions = pd.read_csv(directory / "candidate/driver_acceptance_op_0.csv")
        assert len(users) == 100 and users.request_id.is_unique
        assert set(decisions[decisions.accepted].request_id) == set(users[users.dropoff_time.notna()].request_id)
        audit = json.loads((directory / "candidate/driver_acceptance_op_0.json").read_text())
        assert audit["master_seed"] == seed and len(audit["vehicle_classes"]) == 5
        if baseline == candidate:
            for filename in ("driver_acceptance_op_0.csv", "1_user-stats.csv", "standard_eval.csv"):
                pd.testing.assert_frame_equal(pd.read_csv(directory / "baseline" / filename),
                                              pd.read_csv(directory / "candidate" / filename), check_exact=True)
            finite = comparison[comparison.n_pairs == 2]
            assert (finite.mean_difference == 0).all() and (finite.paired_t_pvalue == 1).all()
        else:
            assert not (directory / "baseline/driver_acceptance_op_0.csv").exists()
            assert set(audit["classes"]) == {"full_time", "part_time"}
            assert comparison.loc["driver_declines", "baseline_mean"] == 0
