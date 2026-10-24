import json
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


def run(example, parameters, output, noise=.3):
    config = output.with_suffix(".yaml")
    config.write_text(yaml.safe_dump(parameters))
    command = [sys.executable, str(RUNNER), example, "--source-root", str(ROOT),
               "--output", str(output), "--driver-acceptance-config", str(config),
               "--network-tt-noise-sigma", str(noise)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180,
                            env=dict(os.environ, PYTHONHASHSEED="0", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"))
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert (output / "final_state.csv").is_file()
    users = pd.read_csv(output / "1_user-stats.csv")
    decisions = pd.read_csv(output / "driver_acceptance_op_0.csv")
    assert len(users) == 100 and users.request_id.is_unique
    assert set(decisions[decisions.accepted].request_id) == set(users[users.dropoff_time.notna()].request_id)
    assert not decisions[decisions.accepted].request_id.duplicated().any()
    if noise:
        assert (users.promised_pickup_time.notna() == users.dropoff_time.notna()).all()
    per_driver_metrics(output)
    summary = driver_acceptance_summary(output)
    assert summary["driver_acceptances"] == users.dropoff_time.notna().sum()
    return users


@pytest.mark.integration
@pytest.mark.parametrize("example", ["insertion", "immediate_batch", "batch"])
@pytest.mark.parametrize("mode", ["always", "logistic"])
def test_singleton_full_run_reproduces_phase3_including_retries(example, mode, tmp_path):
    parameters = {"op_driver_acceptance": "logistic", "op_driver_acceptance_weight_objective": True,
                  "op_driver_acceptance_max_declines": 2}
    if mode == "always":
        parameters["op_driver_acceptance_probability"] = 1
    else:
        parameters.update(op_driver_acceptance_intercept=0, op_driver_acceptance_beta_eta=-.15,
                          op_driver_acceptance_beta_value=.1)
    plain, choice = tmp_path / "plain", tmp_path / "choice"
    run(example, parameters, plain)
    run(example, {**parameters, "op_driver_choice_model": "singleton"}, choice)
    for filename in ("1_user-stats.csv", "standard_eval.csv", "driver_acceptance_op_0.csv"):
        pd.testing.assert_frame_equal(pd.read_csv(plain / filename), pd.read_csv(choice / filename), check_exact=True)
    assert not (plain / "driver_choice_op_0.csv").exists()
    records = pd.read_csv(choice / "driver_choice_op_0.csv")
    assert (records.menu_size == 1).all() and records.legacy_delegated.all()
    audit = json.loads((choice / "driver_choice_op_0.json").read_text())
    assert audit["counters"]["multi_item_episodes"] == 0


@pytest.mark.integration
@pytest.mark.parametrize("future", [False, True])
def test_actual_batch_menus_execute_only_one_new_choice_and_preserve_bookings(future, tmp_path):
    parameters = {"op_driver_acceptance": "logistic", "op_driver_acceptance_weight_objective": True,
                  "op_driver_acceptance_max_declines": 0, "op_driver_choice_model": "logit",
                  "op_driver_acceptance_intercept": 0, "op_driver_acceptance_beta_eta": -.15,
                  "op_driver_acceptance_beta_value": .1}
    if future:
        parameters.update(op_driver_acceptance_future_value=True, op_driver_acceptance_future_value_top_k=3)
    output = tmp_path / "menu"
    run("batch", parameters, output)
    records = pd.read_csv(output / "driver_choice_op_0.csv")
    audit = json.loads((output / "driver_choice_op_0.json").read_text())
    assert audit["counters"]["multi_item_episodes"] > 0
    assert records.groupby("episode").accepted.sum().le(1).all()
    assert not records[records.accepted].request_id.duplicated().any()
    assert ((records.choice_probability >= 0) & (records.choice_probability <= 1)).all()
    multi = records[~records.legacy_delegated]
    assert not multi.empty and multi.menu_size.gt(1).all()
    assert multi.groupby("episode").apply(lambda rows: np.isclose(rows.choice_probability.sum() + rows.outside_probability.iloc[0], 1), include_groups=False).all()
    selected = multi[multi.selected & multi.uniform_draw.notna()]
    assert (selected.uniform_draw >= selected.interval_start).all()
    assert (selected.uniform_draw < selected.interval_end).all()
    if future:
        assert (output / "future_value_op_0.csv").is_file()
