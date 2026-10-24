"""Detect changes to all evaluation cells and individual rider outcomes."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[2]
REFERENCES = Path(__file__).with_name("baselines")
RUNNER = Path(__file__).with_name("run_example.py")


@pytest.mark.integration
@pytest.mark.parametrize("example", ["insertion", "immediate_batch", "batch"])
def test_example_matches_upstream(example, tmp_path):
    manifest = json.loads((REFERENCES / "manifest.json").read_text())
    assert manifest["upstream_commit"] == "c813728b6d188df8dd7fd5d3d36dcb0a55c898a2"
    output = tmp_path / "results"
    environment = dict(os.environ, PYTHONHASHSEED="0", MPLBACKEND="Agg",
                       MPLCONFIGDIR=str(tmp_path / "matplotlib"),
                       OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                       MKL_NUM_THREADS="1")
    result = subprocess.run(
        [sys.executable, str(RUNNER), example, "--source-root", str(ROOT),
         "--output", str(output)],
        cwd=ROOT, env=environment, capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert (output / "final_state.csv").is_file(), "Simulation did not finish"

    actual_eval = pd.read_csv(output / "standard_eval.csv", index_col=0)
    expected_eval = pd.read_csv(REFERENCES / example / "standard_eval.csv", index_col=0)
    assert not actual_eval.empty, "No evaluation metrics executed"
    pd.testing.assert_frame_equal(actual_eval, expected_eval, check_exact=True)

    actual_users = pd.read_csv(output / "1_user-stats.csv", index_col="request_id").sort_index()
    expected_users = pd.read_csv(REFERENCES / example / "1_user-stats.csv", index_col="request_id").sort_index()
    assert len(actual_users) == 100, "Bundled demand did not execute in full"
    assert actual_users.index.is_unique, "Duplicate rider output"
    pd.testing.assert_frame_equal(actual_users, expected_users, check_exact=True)
