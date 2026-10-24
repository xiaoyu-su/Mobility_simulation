"""Logistic driver acceptance with explicit units and isolated random streams.

The intercept and slopes are user-supplied model assumptions. In particular a
published fare-per-USD coefficient cannot be used as a trip-distance slope.
"""

import csv
from dataclasses import asdict, dataclass
import json
import math
from numbers import Integral
from pathlib import Path

from src.misc.globals import G_PRQS_ACC_OFFER, G_SKIP_OUTPUT
from src.misc.seeding import derive_rng, STREAM_SCHEME
from src.fleetctrl.acceptance.future_value import FutureValue, enabled as future_enabled, ENABLED, TOP_K
from src.fleetctrl.acceptance.driver_choice import DriverChoice, choice_mode, PARAMETER as CHOICE_PARAMETER
from src.fleetctrl.acceptance.ranked_insertion import RankedInsertionFallback, enabled as ranked_enabled, PARAMETER as RANKED_PARAMETER
from src.fleetctrl.acceptance.forbid_rematch import ForbidRematch, enabled as rematch_enabled, PARAMETER as REMATCH_PARAMETER


PREFIX = "op_driver_acceptance"
PARAMETERS = [PREFIX, *[f"{PREFIX}_{suffix}" for suffix in
              ("intercept", "beta_eta", "beta_value", "probability", "max_declines", "classes", "weight_objective",
               "future_value", "future_value_top_k")]]
PARAMETERS.append(CHOICE_PARAMETER)
PARAMETERS.append(RANKED_PARAMETER)
PARAMETERS.append(REMATCH_PARAMETER)
SUPPORTED_CONTROLLERS = {"PoolingIRSOnly", "PoolingIRSAssignmentBatchOptimization", "RidePoolingBatchAssignmentFleetcontrol"}


def finite_number(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        value = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{name} must be a finite number") from None
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return value


@dataclass(frozen=True)
class DriverClass:
    share: float
    intercept: float
    beta_eta: float  # per minute of planned pickup delay from decision time
    beta_value: float  # per kilometer of direct passenger trip

    def probability(self, pickup_eta_s, trip_distance_m):
        eta = finite_number(pickup_eta_s, "pickup_eta_s")
        distance = finite_number(trip_distance_m, "trip_distance_m")
        if eta < 0 or distance < 0:
            raise ValueError("Pickup ETA and trip distance must be nonnegative")
        utility = self.intercept + self.beta_eta * (eta / 60) + self.beta_value * (distance / 1000)
        if math.isnan(utility):
            raise ValueError("Driver acceptance utility is undefined; check coefficient magnitudes")
        # Stable sigmoid at large positive/negative utilities.
        if utility >= 0:
            return 1 / (1 + math.exp(-utility))
        exponential = math.exp(utility)
        return exponential / (1 + exponential)


class DriverAcceptance:
    def __init__(self, attributes, scenario, operator_id, vehicles, output_directory):
        self.operator_id = operator_id
        self.seed = scenario["random_seed"]
        override = attributes.get(f"{PREFIX}_probability")
        self.override = None if override is None else finite_number(override, f"{PREFIX}_probability")
        if self.override is not None and not 0 <= self.override <= 1:
            raise ValueError(f"{PREFIX}_probability must be between 0 and 1")
        self.max_declines = attributes.get(f"{PREFIX}_max_declines", 2)
        if isinstance(self.max_declines, bool) or not isinstance(self.max_declines, Integral) or self.max_declines < 0:
            raise ValueError(f"{PREFIX}_max_declines must be a nonnegative integer")
        self.weight_objective = attributes.get(f"{PREFIX}_weight_objective", False)
        if self.weight_objective not in (True, False, 0, 1):
            raise ValueError(f"{PREFIX}_weight_objective must be boolean or 0/1")
        use_future_value = future_enabled(attributes)
        if use_future_value and not self.weight_objective:
            raise ValueError(f"{ENABLED} requires {PREFIX}_weight_objective=True")
        raw_classes = attributes.get(f"{PREFIX}_classes")
        if raw_classes is None:
            raw_classes = {"default": {"share": 1, **{key: attributes.get(f"{PREFIX}_{key}")
                           for key in ("intercept", "beta_eta", "beta_value")}}}
            if self.override is not None:
                raw_classes["default"].update(intercept=0, beta_eta=0, beta_value=0)
        if not isinstance(raw_classes, dict) or not raw_classes:
            raise ValueError(f"{PREFIX}_classes must be a nonempty mapping")
        self.classes = {}
        for name, values in sorted(raw_classes.items(), key=lambda item: str(item[0])):
            if not isinstance(name, str) or not name or not isinstance(values, dict):
                raise ValueError("Driver classes need nonempty names and coefficient mappings")
            if set(values) != {"share", "intercept", "beta_eta", "beta_value"}:
                raise ValueError("Each driver class needs exactly share/intercept/beta_eta/beta_value")
            coefficients = {key: finite_number(values[key], f"{name}.{key}") for key in values}
            if coefficients["share"] <= 0:
                raise ValueError("Driver class shares must be positive")
            self.classes[name] = DriverClass(**coefficients)
        if not math.isclose(sum(group.share for group in self.classes.values()), 1, abs_tol=1e-9, rel_tol=0):
            raise ValueError("Driver class shares must sum to one")
        self.vehicle_classes = {}
        for vehicle in vehicles:
            draw = (derive_rng(self.seed, f"driver_class/{operator_id}/{vehicle.vid}").random()
                    if len(self.classes) > 1 else 0)
            cumulative = 0
            for name, group in self.classes.items():
                cumulative += group.share
                if draw < cumulative:
                    self.vehicle_classes[vehicle.vid] = name
                    break
            else:
                self.vehicle_classes[vehicle.vid] = next(reversed(self.classes))
        self.outcomes = {}  # (rid, vid) -> final accepted/declined; never redraw a booked assignment
        self.draws = {}  # isolated per-request/vehicle decision streams
        self.declines = {}
        self.future_value = (FutureValue(self, vehicles, attributes.get(TOP_K, 5),
                                        None if scenario.get(G_SKIP_OUTPUT, 0) else output_directory)
                             if use_future_value else None)
        self.path = None
        if not scenario.get(G_SKIP_OUTPUT, 0):
            directory = Path(output_directory)
            directory.mkdir(parents=True, exist_ok=True)
            self.path = directory / f"driver_acceptance_op_{operator_id}.csv"
            self.columns = ["simulation_time", "operator_id", "vehicle_id", "request_id", "driver_class",
                            "attempt", "pickup_eta_s", "trip_distance_m", "probability", "uniform_draw",
                            "accepted", "decline_count", "terminal_decline"]
            with self.path.open("w", newline="") as stream:
                csv.DictWriter(stream, fieldnames=self.columns).writeheader()
            audit = {"scheme": STREAM_SCHEME, "master_seed": self.seed, "operator_id": operator_id,
                     "decision_stream": "driver_acceptance/{operator_id}/{vehicle_id}/{request_id}",
                     "class_stream": "driver_class/{operator_id}/{vehicle_id}",
                     "units": {"beta_eta": "per minute", "beta_value": "per direct-trip kilometer"},
                     "classes": {name: asdict(group) for name, group in self.classes.items()},
                     "vehicle_classes": self.vehicle_classes, "probability_override": self.override,
                     "max_declines": int(self.max_declines), "max_attempts": int(self.max_declines + 1),
                     "weight_objective": bool(self.weight_objective), "coefficient_status": "user-supplied, not calibrated"}
            declared_choice = choice_mode(attributes)
            if declared_choice != "off":
                audit["driver_choice"] = {
                    "mode": declared_choice,
                    "audit_file": f"driver_choice_op_{operator_id}.json",
                    "probability_column": "base one-offer probability for delegated singletons; conditional item probability for actual menus",
                    "draw_column": "legacy Bernoulli draws for singletons; missing for categorical outcomes, whose draw is in the choice log"}
            (directory / f"driver_acceptance_op_{operator_id}.json").write_text(json.dumps(audit, indent=2) + "\n")
        mode = choice_mode(attributes)
        self.choice = DriverChoice(self, mode, scenario, output_directory) if mode != "off" else None
        self.ranked_fallback = (RankedInsertionFallback(self, attributes, scenario, output_directory)
                                if ranked_enabled(attributes) else None)
        self.forbid_rematch = (ForbidRematch(self, attributes, scenario, output_directory)
                              if rematch_enabled(attributes) else None)
        if self.forbid_rematch is not None and self.path is not None:
            audit_path = self.path.with_suffix(".json")
            audit = json.loads(audit_path.read_text())
            audit["forbid_rematch"] = {"enabled": True, "max_attempts_scope": "one per request/driver pair",
                                       "terminal_decline": "last genuine refusal if final optimizer solution leaves request unassigned"}
            audit_path.write_text(json.dumps(audit, indent=2) + "\n")
        if self.ranked_fallback is not None and self.path is not None:
            audit_path = self.path.with_suffix(".json")
            audit = json.loads(audit_path.read_text())
            audit["ranked_fallback"] = {"enabled": True, "max_attempts_scope": "one per retained distinct driver",
                                       "terminal_decline": "request exhausted, not an intermediate driver refusal"}
            audit_path.write_text(json.dumps(audit, indent=2) + "\n")

    def probability(self, vehicle_id, request, plan, simulation_time):
        if self.override is not None:
            return self.override
        pickup = plan.pax_info[request.get_rid_struct()][0]
        eta = max(0, pickup - simulation_time)
        return self.probability_at_eta(vehicle_id, request, eta)

    def probability_at_eta(self, vehicle_id, request, eta):
        if self.override is not None:
            return self.override
        return self.classes[self.vehicle_classes[vehicle_id]].probability(eta, request.init_direct_td)

    def begin_matching_round(self, simulation_time, routing_engine):
        if self.future_value is not None:
            self.future_value.begin_round(simulation_time, routing_engine)
        if self.choice is not None:
            self.choice.begin_round()

    def accept(self, vehicle_id, request, plan, simulation_time, *, final_candidate=None):
        if self.choice is not None:
            if final_candidate is not None:
                return self.choice.accept_single(vehicle_id, request, plan, simulation_time, final_candidate=final_candidate)
            return self.choice.accept_single(vehicle_id, request, plan, simulation_time)
        if final_candidate is not None:
            return self._accept_ranked_candidate(vehicle_id, request, plan, simulation_time, final_candidate)
        return self._accept_legacy(vehicle_id, request, plan, simulation_time)

    def _accept_ranked_candidate(self, vehicle_id, request, plan, simulation_time, final_candidate):
        if self.ranked_fallback is None and self.forbid_rematch is None:
            raise ValueError("Ranked driver decisions require ranked fallback enabled")
        if request.status >= G_PRQS_ACC_OFFER:
            return True
        rid = request.get_rid_struct()
        key = rid, vehicle_id
        if key in self.outcomes:
            return self.outcomes[key]
        if self.future_value is not None:
            self.future_value.record_selected(vehicle_id, request, plan, simulation_time)
        probability = self.probability(vehicle_id, request, plan, simulation_time)
        draw = None
        if probability in (0, 1):
            accepted = probability == 1
        else:
            if key not in self.draws:
                self.draws[key] = derive_rng(self.seed, f"driver_acceptance/{self.operator_id}/{vehicle_id}/{rid}")
            draw = float(self.draws[key].random())
            accepted = draw < probability
        previous_declines = self.declines.get(rid, 0)
        count = previous_declines + (not accepted)
        if not accepted:
            self.declines[rid] = count
        if self.path is not None:
            values = [simulation_time, self.operator_id, vehicle_id, rid, self.vehicle_classes[vehicle_id],
                      previous_declines + 1, max(0, plan.pax_info[rid][0] - simulation_time),
                      request.init_direct_td, probability, draw, accepted, count, not accepted and final_candidate]
            record = dict(zip(self.columns, values))
            if self.forbid_rematch is not None:
                self.forbid_rematch.record_attempt(record)
            else:
                with self.path.open("a", newline="") as stream:
                    csv.DictWriter(stream, fieldnames=self.columns).writerow(record)
        self.outcomes[key] = accepted
        return accepted

    def _accept_legacy(self, vehicle_id, request, plan, simulation_time):
        if self.forbid_rematch is not None:
            return self._accept_ranked_candidate(vehicle_id, request, plan, simulation_time, False)
        # Never allow a fresh stochastic decision to abandon an accepted or
        # onboard rider. This also covers later vehicle/plan reassignment.
        if request.status >= G_PRQS_ACC_OFFER:
            return True
        rid = request.get_rid_struct()
        key = (rid, vehicle_id)
        if key in self.outcomes:
            return self.outcomes[key]
        if self.future_value is not None:
            self.future_value.record_selected(vehicle_id, request, plan, simulation_time)
        probability = self.probability(vehicle_id, request, plan, simulation_time)
        eta = max(0, plan.pax_info[rid][0] - simulation_time)
        remaining = max(0, self.max_declines + 1 - self.declines.get(rid, 0))
        for _ in range(remaining):
            draw = None
            if probability in (0, 1):
                accepted = probability == 1
            else:
                if key not in self.draws:
                    self.draws[key] = derive_rng(self.seed, f"driver_acceptance/{self.operator_id}/{vehicle_id}/{rid}")
                draw = float(self.draws[key].random())
                accepted = draw < probability
            count = self.declines.get(rid, 0)
            if not accepted:
                count += 1
                self.declines[rid] = count
            terminal = not accepted and count > self.max_declines
            if self.path is not None:
                record = dict(zip(self.columns, [simulation_time, self.operator_id, vehicle_id, rid,
                              self.vehicle_classes[vehicle_id], count if not accepted else count + 1,
                              eta, request.init_direct_td, probability, draw, accepted, count, terminal]))
                with self.path.open("a", newline="") as stream:
                    csv.DictWriter(stream, fieldnames=self.columns).writerow(record)
            if accepted:
                self.outcomes[key] = True
                return True
        self.outcomes[key] = False
        return False

    def record_menu_outcome(self, vehicle_id, request, plan, simulation_time, accepted, probability):
        """Record a resolved menu decision, without another Bernoulli draw.

        The choice log owns its categorical draw/interval. The legacy-format
        decision log records the conditional item probability and no fake draw.
        """
        rid = request.get_rid_struct()
        key = rid, vehicle_id
        if request.status >= G_PRQS_ACC_OFFER or key in self.outcomes:
            raise ValueError("Cannot replace a committed or previously recorded driver decision")
        if self.max_declines != 0:
            raise ValueError("Menu outcomes require a single choice episode without retries")
        if self.future_value is not None:
            self.future_value.record_selected(vehicle_id, request, plan, simulation_time)
        self.outcomes[key] = bool(accepted)
        count = self.declines.get(rid, 0)
        if not accepted:
            count += 1
            self.declines[rid] = count
        if self.path is not None:
            eta = max(0, plan.pax_info[rid][0] - simulation_time)
            attempt = (count if not accepted else count + 1) if self.forbid_rematch is not None else 1
            values = [simulation_time, self.operator_id, vehicle_id, rid, self.vehicle_classes[vehicle_id],
                      attempt, eta, request.init_direct_td, probability, None, bool(accepted), count,
                      not accepted and self.forbid_rematch is None]
            record = dict(zip(self.columns, values))
            if self.forbid_rematch is not None:
                self.forbid_rematch.record_attempt(record)
            else:
                with self.path.open("a", newline="") as stream:
                    csv.DictWriter(stream, fieldnames=self.columns).writerow(record)

    def wrap_objective(self, base_function):
        if not self.weight_objective:
            return base_function
        reward = getattr(base_function, "assignment_reward_per_request", None)
        if reward is None:
            raise ValueError("Acceptance reward weighting requires distance_and_user_times_with_walk")

        def weighted(simulation_time, vehicle, plan, requests, routing_engine):
            base_value = base_function(simulation_time, vehicle, plan, requests, routing_engine)
            penalty = 0
            for rid in plan.pax_info:
                request = requests[rid]
                if request.status < G_PRQS_ACC_OFFER:
                    probability = self.probability(vehicle.vid, request, plan, simulation_time)
                    if self.future_value is not None:
                        probability = self.future_value.estimate(probability, vehicle.vid, request,
                                                                 simulation_time, routing_engine).served_value
                    penalty += 1 - probability
            # Preserve the original arithmetic in the p=1 sanity check.
            return base_value if penalty == 0 else base_value + reward * penalty
        return weighted


def create_driver_acceptance(attributes, scenario, operator_id, vehicles, output_directory):
    mode = attributes.get(PREFIX)
    if mode in (None, "off", False):
        if rematch_enabled(attributes):
            raise ValueError(f"{REMATCH_PARAMETER} requires {PREFIX}=logistic")
        if ranked_enabled(attributes):
            raise ValueError(f"{RANKED_PARAMETER} requires {PREFIX}=logistic")
        if choice_mode(attributes) != "off":
            raise ValueError(f"{CHOICE_PARAMETER} requires {PREFIX}=logistic")
        if future_enabled(attributes):
            raise ValueError(f"{ENABLED} requires {PREFIX}=logistic")
        return None
    if mode != "logistic":
        raise ValueError(f"{PREFIX} must be off or logistic")
    if attributes.get("op_module") not in SUPPORTED_CONTROLLERS or scenario.get("n_cpu_per_sim", 1) != 1:
        raise ValueError("Driver acceptance currently supports the three baseline controllers with one worker")
    if scenario.get("broker_type") is not None or scenario.get("sim_env") not in ("ImmediateDecisionsSimulation", "BatchOfferSimulation"):
        raise ValueError("Driver acceptance currently requires baseline road-trip simulation and BrokerBasic")
    if attributes.get("op_rp_batch_optimizer") not in (None, "AlonsoMora"):
        raise ValueError("Driver acceptance currently supports AlonsoMora batch optimization")
    return DriverAcceptance(attributes, scenario, operator_id, vehicles, output_directory)
