"""Driver accounting from completed simulation outputs, in seconds and cents."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.misc.globals import G_DIR_VEH, VRL_STATES


DRIVING = {"route", "reposition", "to_charge", "to_depot", "to_reservation"}
KNOWN_STATUSES = {status.display_name for status in VRL_STATES}
METRICS = ["idle_time_s", "driving_time_s", "occupied_time_s", "online_time_s",
           "utilization", "completed_trips", "gross_fare_revenue_cent",
           "distance_cost_cent", "fixed_cost_cent", "toll_cent",
           "modeled_net_earnings_cent", "earnings_per_online_hour_cent"]


def per_driver_metrics(result_directory, clip_initial_inactivity=False, specification_directory=None):
    """Account recorded activity; optionally left-truncate initial parked time.

    An explicit specification directory reads archived cost assumptions without
    rewriting raw configuration paths; the default retains existing behavior.
    TimeBasedFS can start an initial inactive leg one grid tick before start.
    Only stationary, empty, toll-free out-of-service time may be truncated;
    moving or overlapping records remain invalid. Raw output is never changed.
    """
    root = Path(result_directory)
    config = json.loads((root / "00_config.json").read_text())
    parameters = config["scenario_parameters"]
    start, end = float(parameters["start_time"]), float(parameters["end_time"])
    horizon = end - start
    if not np.isfinite(horizon) or horizon <= 0:
        raise ValueError("Simulation horizon must be positive and finite")
    roster = pd.read_csv(root / "2_vehicle_types.csv")
    keys = ["operator_id", "vehicle_id"]
    if roster.empty or roster.duplicated(keys).any():
        raise ValueError("Vehicle roster must be nonempty and unique")
    users = pd.read_csv(root / "1_user-stats.csv")
    if users.empty or users.request_id.duplicated().any():
        raise ValueError("Rider output must be nonempty with unique request IDs")
    completed = users[users.dropoff_time.notna()].copy()
    if not completed.empty:
        if completed[keys + ["fare", "pickup_time"]].isna().any().any():
            raise ValueError("Completed rides need a driver, pickup time, and fare")
        if not np.isfinite(completed[keys + ["fare", "pickup_time", "dropoff_time"]].to_numpy(dtype=float)).all():
            raise ValueError("Nonfinite completed rider output")
        if ((completed.pickup_time < start) | (completed.dropoff_time < completed.pickup_time)).any():
            raise ValueError("Completed ride has inconsistent pickup/dropoff times")
        assigned = set(map(tuple, completed[keys].to_numpy()))
        if not assigned.issubset(set(map(tuple, roster[keys].to_numpy()))):
            raise ValueError("A completed ride references an unknown vehicle")

    cost_directory = Path(specification_directory) if specification_directory is not None else Path(config["directories"][G_DIR_VEH])
    costs = {}
    for vehicle_type in roster.vehicle_type.unique():
        specification = pd.read_csv(cost_directory / f"{vehicle_type}.csv", header=None, index_col=0).iloc[:, 0]
        costs[vehicle_type] = (float(specification["per_km_cost [cent]"]),
                               float(specification["daily_fix_cost [cent]"]))
        if not np.isfinite(costs[vehicle_type]).all() or min(costs[vehicle_type]) < 0:
            raise ValueError("Vehicle costs must be finite and nonnegative")

    logs = {}
    required = ["vehicle_id", "status", "start_time", "end_time", "driven_distance", "occupancy", "toll"]
    for operator in roster.operator_id.unique():
        path = root / f"2-{int(operator)}_op-stats.csv"
        legs = pd.read_csv(path) if path.is_file() else pd.DataFrame(columns=required)
        if not set(required).issubset(legs.columns):
            raise ValueError(f"Missing activity columns in {path}")
        if legs.duplicated().any():
            raise ValueError("Duplicate vehicle activity rows")
        if not set(legs.status).issubset(KNOWN_STATUSES):
            raise ValueError("Unknown vehicle status")
        allowed_ids = set(roster.loc[roster.operator_id == operator, "vehicle_id"])
        if not set(legs.vehicle_id).issubset(allowed_ids):
            raise ValueError("Activity references an unknown vehicle")
        logs[operator] = legs

    rows = []
    for vehicle in roster.sort_values(keys).itertuples(index=False):
        legs = logs[vehicle.operator_id]
        legs = legs[legs.vehicle_id == vehicle.vehicle_id].sort_values(["start_time", "end_time"])
        rides = completed[(completed.operator_id == vehicle.operator_id) &
                          (completed.vehicle_id == vehicle.vehicle_id)]
        if legs.empty and not rides.empty:
            raise ValueError("Completed rides have no corresponding vehicle activity")
        totals = {"logged": 0.0, "idle": 0.0, "driving": 0.0, "occupied": 0.0,
                  "out_of_service": 0.0, "distance": 0.0, "toll": 0.0}
        previous_end = start
        for leg in legs.itertuples(index=False):
            values = [leg.start_time, leg.end_time, leg.driven_distance, leg.occupancy, leg.toll]
            if not np.isfinite(np.asarray(values, dtype=float)).all():
                raise ValueError("Nonfinite vehicle activity")
            leg_start = leg.start_time
            if (clip_initial_inactivity and leg_start < start and leg.end_time >= start
                    and leg.status == "out_of_service" and leg.driven_distance == 0
                    and leg.occupancy == 0 and leg.toll == 0
                    and getattr(leg, "start_pos", None) == getattr(leg, "end_pos", None)):
                leg_start = start
            if (leg_start < start - 1e-6 or
                    leg.end_time < leg_start or leg_start < previous_end - 1e-6):
                raise ValueError("Overlapping vehicle activity or activity before simulation start")
            if leg.driven_distance < 0 or leg.occupancy < 0:
                raise ValueError("Negative distance or occupancy")
            duration = leg.end_time - leg_start
            previous_end = max(previous_end, leg.end_time)
            totals["logged"] += duration
            totals["idle"] += duration if leg.status == "idle" else 0
            totals["driving"] += duration if leg.status in DRIVING else 0
            totals["occupied"] += duration if leg.occupancy > 0 else 0
            totals["out_of_service"] += duration if leg.status == "out_of_service" else 0
            totals["distance"] += leg.driven_distance
            totals["toll"] += leg.toll

        # FleetPy drains pending assignments after end_time. Include those exact
        # recorded legs and fares; do not prorate unknown within-leg distances.
        accounting_end = max(end, previous_end)
        exposure = accounting_end - start
        per_km, daily_fixed = costs[vehicle.vehicle_type]
        gross = float(rides.fare.sum())
        distance_cost = totals["distance"] / 1000 * per_km
        fixed_cost = daily_fixed * exposure / 86400
        net = gross - distance_cost - fixed_cost - totals["toll"]
        online = max(0.0, exposure - totals["out_of_service"])
        rows.append({"operator_id": vehicle.operator_id, "vehicle_id": vehicle.vehicle_id,
                     "vehicle_type": vehicle.vehicle_type,
                     "accounting_end_time": accounting_end, "tail_time_s": accounting_end - end,
                     "idle_time_s": max(0.0, exposure - totals["logged"]) + totals["idle"],
                     "driving_time_s": totals["driving"], "occupied_time_s": totals["occupied"],
                     "online_time_s": online,
                     "utilization": totals["occupied"] / online if online else np.nan,
                     "completed_trips": len(rides), "gross_fare_revenue_cent": gross,
                     "distance_cost_cent": distance_cost, "fixed_cost_cent": fixed_cost,
                     "toll_cent": totals["toll"], "modeled_net_earnings_cent": net,
                     "earnings_per_online_hour_cent": net / (online / 3600) if online else np.nan})
    return pd.DataFrame(rows)


def distribution_metrics(drivers):
    rows = []
    for metric in METRICS:
        all_values = drivers[metric].to_numpy(dtype=float)
        values = all_values[np.isfinite(all_values)]
        row = {"metric": metric, "n_total": len(all_values), "n_finite": len(values)}
        if not len(values):
            row.update({key: np.nan for key in ("mean", "std", "cv", "p10", "p50", "p90", "gini")})
        else:
            mean, std = float(values.mean()), float(values.std(ddof=0))
            sorted_values = np.sort(values)
            if (values < 0).any():
                gini = np.nan  # Do not shift negative earnings to manufacture a Gini.
            elif values.sum() == 0:
                gini = 0.0
            else:
                weights = 2 * np.arange(1, len(values) + 1) - len(values) - 1
                gini = float(np.dot(weights, sorted_values) / (len(values) * values.sum()))
            row.update(mean=mean, std=std, cv=std / abs(mean) if mean else (0.0 if std == 0 else np.nan),
                       p10=float(np.quantile(values, .1)), p50=float(np.quantile(values, .5)),
                       p90=float(np.quantile(values, .9)), gini=gini)
        rows.append(row)
    return pd.DataFrame(rows)


def seed_summary(result_directory, drivers, distribution):
    users = pd.read_csv(Path(result_directory) / "1_user-stats.csv")
    picked_up = users.pickup_time.notna()
    completed = users.dropoff_time.notna()
    summary = {"request_count": float(len(users)), "picked_up_requests": float(picked_up.sum()),
               "completed_requests": float(completed.sum()), "completion_rate": float(completed.mean()),
               "rider_wait_mean_s": float((users.loc[picked_up, "pickup_time"] - users.loc[picked_up, "rq_time"]).mean()),
               "fleet_gross_fare_revenue_cent": float(drivers.gross_fare_revenue_cent.sum()),
               "fleet_modeled_net_earnings_cent": float(drivers.modeled_net_earnings_cent.sum())}
    for row in distribution.itertuples(index=False):
        for statistic in ("mean", "std", "cv", "p10", "p50", "p90", "gini"):
            summary[f"{row.metric}.{statistic}"] = float(getattr(row, statistic))
    if "promised_pickup_time" in users.columns:
        summary.update(promise_error_summary(users))
    summary.update(driver_acceptance_summary(result_directory))
    return summary


def driver_acceptance_summary(result_directory):
    paths = sorted(Path(result_directory).glob("driver_acceptance_op_*.csv"))
    summary = {"driver_offer_attempts": 0.0, "driver_acceptances": 0.0,
               "driver_declines": 0.0, "driver_terminal_declines": 0.0, "driver_offered_requests": 0.0}
    if not paths:
        return summary
    decisions = pd.concat([pd.read_csv(path) for path in paths], ignore_index=True)
    if decisions.empty:
        return summary
    if (decisions.duplicated(["operator_id", "request_id", "attempt"]).any()
            or not pd.api.types.is_bool_dtype(decisions.accepted)
            or not pd.api.types.is_bool_dtype(decisions.terminal_decline)
            or not decisions.accepted.isin([True, False]).all()
            or not decisions.terminal_decline.isin([True, False]).all()
            or not np.isfinite(decisions.probability).all()
            or not decisions.probability.between(0, 1).all()
            or (decisions.accepted & decisions.terminal_decline).any()):
        raise ValueError("Malformed driver-acceptance decision log")
    summary.update(driver_offer_attempts=float(len(decisions)),
                   driver_acceptances=float(decisions.accepted.sum()),
                   driver_declines=float((~decisions.accepted).sum()),
                   driver_terminal_declines=float(decisions.terminal_decline.sum()),
                   driver_offered_requests=float(len(decisions.drop_duplicates(["operator_id", "request_id"]))))
    return summary


def promise_error_summary(users):
    """Signed actual-minus-accepted-promise errors; missing service is counted.

    Service/completion counts must accompany these conditional error metrics:
    unserved requests are never silently converted into zero timing error.
    """
    summary = {"promised_requests": float(users.promise_operator_id.notna().sum())}
    for event in ("pickup", "dropoff"):
        actual, promised = users[f"{event}_time"], users[f"promised_{event}_time"]
        valid = actual.notna() & promised.notna()
        error = actual[valid] - promised[valid]
        if not np.isfinite(error.to_numpy(dtype=float)).all():
            raise ValueError("Nonfinite actual/promise error")
        prefix = f"{event}_promise_error"
        summary.update({f"{prefix}.count": float(len(error)),
                        f"{prefix}.missing_count": float((~valid).sum()),
                        f"{prefix}.mean_s": float(error.mean()),
                        f"{prefix}.std_s": float(error.std(ddof=0)),
                        f"{prefix}.mae_s": float(error.abs().mean()),
                        f"{prefix}.p10_s": float(error.quantile(.1)),
                        f"{prefix}.p50_s": float(error.quantile(.5)),
                        f"{prefix}.p90_s": float(error.quantile(.9)),
                        f"{prefix}.late_fraction": float((error > 1e-6).mean())})
    return summary
