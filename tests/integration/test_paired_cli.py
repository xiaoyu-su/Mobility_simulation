import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from src.misc.seeding import file_digest


ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ROOT / "studies/example_study/scenarios"


@pytest.mark.integration
@pytest.mark.parametrize("candidate,sigma", [("example_ir_only.csv", None), ("example_ir_batch.csv", None),
                                            ("example_ir_only.csv", .6), ("example_ir_batch.csv", .6)])
def test_complete_paired_experiment_has_matching_inputs_and_reproducible_reports(candidate, sigma, tmp_path):
    output = tmp_path / "experiment"
    command = [sys.executable, "-m", "tools.paired_eval",
               "--constant-config", str(SCENARIOS / "constant_config_ir.csv"),
               "--baseline-scenarios", str(SCENARIOS / "example_ir_only.csv"),
               "--candidate-scenarios", str(SCENARIOS / candidate),
               "--seeds", "3", "9", "--output", str(output)]
    if sigma is not None:
        command.extend(["--network-tt-noise-sigma", str(sigma)])
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=240,
                            env=dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"))
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "complete"
    assert len(manifest["runs"]) == 4 and len(manifest["validated_pairs"]) == 2
    assert all(run["returncode"] == 0 for run in manifest["runs"])
    assert all(pair["audit"]["demand"]["demand"]["count"] == 100 for pair in manifest["validated_pairs"])
    initial_hashes = [pair["audit"]["initial_vehicle_state_sha256"] for pair in manifest["validated_pairs"]]
    assert initial_hashes[0] != initial_hashes[1], "Changing seed should change the starting fleet"
    for filename, digest in manifest["report_sha256"].items():
        assert file_digest(output / filename) == digest
    drivers = pd.read_csv(output / "per_driver.csv")
    assert len(drivers) == 20  # five vehicles × two policies × two seeds
    assert not drivers.duplicated(["seed", "arm", "operator_id", "vehicle_id"]).any()
    assert (drivers.idle_time_s >= 0).all() and (drivers.tail_time_s >= 0).all()
    comparison = pd.read_csv(output / "paired_comparison.csv")
    if sigma is not None:
        assert manifest["runtime"]["execution_overrides"] == {"network_tt_noise_sigma": sigma}
        assert "pickup_promise_error.std_s" in set(comparison.metric)
        for seed in (3, 9):
            for arm in ("baseline", "candidate"):
                folder = output / "runs" / f"seed_{seed}" / arm
                users = pd.read_csv(folder / "1_user-stats.csv")
                served = users[users.dropoff_time.notna()]
                assert len(served) > 0 and served.promised_pickup_time.notna().all()
                assert users.promised_pickup_time.notna().sum() == len(served)
                assert (served.promise_operator_id == served.operator_id).all()
                np.testing.assert_allclose(served.pickup_error_s, served.pickup_time - served.promised_pickup_time, atol=1e-9)
                np.testing.assert_allclose(served.dropoff_error_s, served.dropoff_time - served.promised_dropoff_time, atol=1e-9)
                assert served.pickup_error_s.std() > 1
    row = comparison.set_index("metric").loc["request_count"]
    assert row["n_pairs"] == 2 and row["baseline_mean"] == row["candidate_mean"] == 100
    if candidate == "example_ir_only.csv":
        comparable = comparison[comparison.n_pairs == 2]
        assert (comparable.mean_difference == 0).all()
        assert (comparable.paired_t_pvalue == 1).all()
        assert (comparable.wilcoxon_pvalue == 1).all()
        for seed in (3, 9):
            for filename in ("1_user-stats.csv", "standard_eval.csv"):
                left = pd.read_csv(output / "runs" / f"seed_{seed}" / "baseline" / filename)
                right = pd.read_csv(output / "runs" / f"seed_{seed}" / "candidate" / filename)
                pd.testing.assert_frame_equal(left, right, check_exact=True)

    # An existing experiment is reviewable evidence, never a reusable scratch path.
    manifest_bytes = (output / "manifest.json").read_bytes()
    repeated = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=20)
    assert repeated.returncode != 0 and "Refusing to overwrite" in repeated.stderr
    assert (output / "manifest.json").read_bytes() == manifest_bytes
