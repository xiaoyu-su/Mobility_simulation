import copy
import json

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from tools.paired_eval.__main__ import validate_pair, check_policy_pair
from tools.paired_eval.metrics import per_driver_metrics, distribution_metrics, METRICS
from tools.paired_eval.statistics import paired_statistics
from src.misc.seeding import STREAM_SCHEME


@pytest.fixture
def result_directory(tmp_path):
    costs = tmp_path / "vehicles"
    costs.mkdir()
    (costs / "test.csv").write_text("per_km_cost [cent],100\ndaily_fix_cost [cent],2400\n")
    config = {"scenario_parameters": {"start_time": 0, "end_time": 3600},
              "directories": {"vehicles": str(costs)}}
    (tmp_path / "00_config.json").write_text(json.dumps(config))
    pd.DataFrame({"operator_id": [0, 0, 0], "vehicle_id": [0, 1, 2],
                  "vehicle_type": ["test"] * 3}).to_csv(tmp_path / "2_vehicle_types.csv", index=False)
    pd.DataFrame({"request_id": [0, 1], "operator_id": [0, np.nan],
                  "vehicle_id": [0, np.nan], "pickup_time": [600, np.nan],
                  "dropoff_time": [1200, np.nan], "fare": [1000, np.nan]}).to_csv(tmp_path / "1_user-stats.csv", index=False)
    pd.DataFrame({"vehicle_id": [0, 0, 1], "status": ["route", "route", "out_of_service"],
                  "start_time": [0, 600, 0], "end_time": [600, 1200, 3600],
                  "driven_distance": [1000, 1000, 0], "occupancy": [0, 1, 0],
                  "toll": [10, 0, 0]}).to_csv(tmp_path / "2-0_op-stats.csv", index=False)
    return tmp_path


def test_driver_accounting_includes_idle_and_inactive_vehicles(result_directory):
    drivers = per_driver_metrics(result_directory).set_index("vehicle_id")
    assert len(drivers) == 3
    assert drivers.loc[0, "idle_time_s"] == 2400
    assert drivers.loc[0, "driving_time_s"] == 1200
    assert drivers.loc[0, "occupied_time_s"] == 600
    assert drivers.loc[0, "gross_fare_revenue_cent"] == 1000
    assert drivers.loc[0, "distance_cost_cent"] == 200
    assert drivers.loc[0, "fixed_cost_cent"] == 100
    assert drivers.loc[0, "modeled_net_earnings_cent"] == 690
    assert drivers.loc[0, "earnings_per_online_hour_cent"] == 690
    assert drivers.loc[1, "online_time_s"] == 0
    assert np.isnan(drivers.loc[1, "earnings_per_online_hour_cent"])
    assert drivers.loc[2, "idle_time_s"] == 3600
    assert drivers.loc[2, "modeled_net_earnings_cent"] == -100


@pytest.mark.parametrize("cost", ["nan", "-1"])
def test_invalid_vehicle_cost_cannot_silently_produce_missing_earnings(result_directory, cost):
    path = result_directory / "vehicles/test.csv"
    path.write_text(f"per_km_cost [cent],{cost}\ndaily_fix_cost [cent],2400\n")
    with pytest.raises(ValueError, match="costs must be finite and nonnegative"):
        per_driver_metrics(result_directory)


def test_distribution_has_hand_checked_inequality_and_missing_counts():
    drivers = pd.DataFrame({metric: [0, 0, 100] for metric in METRICS})
    drivers["modeled_net_earnings_cent"] = [-10, 0, 100]
    drivers["earnings_per_online_hour_cent"] = [np.nan, 0, 100]
    distribution = distribution_metrics(drivers).set_index("metric")
    gross = distribution.loc["gross_fare_revenue_cent"]
    assert gross["gini"] == pytest.approx(2 / 3)
    assert gross["p10"] == 0 and gross["p50"] == 0 and gross["p90"] == 80
    assert gross["cv"] == pytest.approx(np.sqrt(2))
    assert np.isnan(distribution.loc["modeled_net_earnings_cent", "gini"])
    assert distribution.loc["earnings_per_online_hour_cent", "n_finite"] == 2


def test_finishing_work_after_end_time_is_accounted_without_dropping_fares(result_directory):
    path = result_directory / "2-0_op-stats.csv"
    legs = pd.read_csv(path)
    legs.loc[1, "end_time"] = 4200
    legs.to_csv(path, index=False)
    users_path = result_directory / "1_user-stats.csv"
    users = pd.read_csv(users_path)
    users.loc[0, "dropoff_time"] = 4200
    users.to_csv(users_path, index=False)
    drivers = per_driver_metrics(result_directory).set_index("vehicle_id")
    assert drivers.loc[0, "tail_time_s"] == 600
    assert drivers.loc[0, "online_time_s"] == 4200
    assert drivers.loc[0, "occupied_time_s"] == 3600
    assert drivers.loc[0, "gross_fare_revenue_cent"] == 1000
    assert drivers.loc[0, "fixed_cost_cent"] == pytest.approx(2400 * 4200 / 86400)
    assert drivers.loc[2, "online_time_s"] == 3600


@pytest.mark.parametrize("problem", ["overlap", "duplicate", "outside", "unknown_status", "duplicate_rider"])
def test_malformed_activity_or_rider_data_is_rejected(result_directory, problem):
    path = result_directory / "2-0_op-stats.csv"
    frame = pd.read_csv(path)
    if problem == "overlap":
        frame.loc[1, "start_time"] = 500
    elif problem == "duplicate":
        frame = pd.concat([frame, frame.iloc[:1]])
    elif problem == "outside":
        frame.loc[0, "start_time"] = -100
    elif problem == "unknown_status":
        frame.loc[0, "status"] = "unknown"
    else:
        users_path = result_directory / "1_user-stats.csv"
        users = pd.read_csv(users_path)
        pd.concat([users, users.iloc[:1]]).to_csv(users_path, index=False)
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError):
        per_driver_metrics(result_directory)


def test_paired_inference_matches_hand_computed_difference_interval():
    baseline = np.array([10, 20, 30, 40])
    candidate = baseline + np.array([1, 2, 3, 4])
    result = paired_statistics(baseline, candidate)
    assert result["mean_difference"] == 2.5
    assert result["paired_t_statistic"] == pytest.approx(3.872983346207417)
    assert result["ci95_low"] == pytest.approx(0.445739743239121)
    assert result["ci95_high"] == pytest.approx(4.554260256760879)
    assert result["wilcoxon_pvalue"] == 0.125
    assert result["status"] == "ok"


def test_identical_pairs_and_insufficient_samples_are_explicit():
    identical = paired_statistics([2, 3, 4], [2, 3, 4])
    assert identical["paired_t_pvalue"] == identical["wilcoxon_pvalue"] == 1
    assert identical["ci95_low"] == identical["ci95_high"] == 0
    assert paired_statistics([1], [2])["status"] == "insufficient_pairs"
    missing = paired_statistics([1, 2, np.nan], [2, 3, 4])
    assert missing["n_pairs"] == 2 and missing["n_omitted_pairs"] == 1
    assert missing["status"] == "constant_difference_t_test_undefined"


@pytest.mark.parametrize("key", ["demand", "network_input_sha256", "initial_vehicle_state_sha256", "master_seed"])
def test_input_mismatch_prevents_paired_inference(key):
    baseline = {"scheme": STREAM_SCHEME, "mode": "independent", "master_seed": 1,
                "demand": {"demand": {"count": 100, "loaded_sha256": "a"}},
                "network_input_sha256": {"nodes.csv": "a", "edges.csv": "b"},
                "initial_vehicle_count": 5, "initial_vehicle_state_sha256": "a"}
    candidate = copy.deepcopy(baseline)
    candidate[key] = "different"
    with pytest.raises(ValueError, match=key):
        validate_pair(baseline, candidate)


@pytest.mark.parametrize("change", [
    {"rq_file": "other.csv"}, {"op_repo_method": "PavoneFC"},
    {"op_module": "UnknownController"}, {"nr_mod_operators": 2},
])
def test_unmatched_background_or_unreviewed_workflow_is_rejected(change):
    baseline = {"op_module": "PoolingIRSOnly", "nr_mod_operators": 1, "rq_file": "demand.csv"}
    with pytest.raises(ValueError):
        check_policy_pair(baseline, dict(baseline, **change))
