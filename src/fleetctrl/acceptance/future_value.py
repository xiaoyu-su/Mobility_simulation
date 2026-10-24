"""Deterministic fallback-value estimates; no dispatch or acceptance draws.

Candidates are ranked exactly by their direct road-network pickup ETA within a
frozen matching-round snapshot. This is a reachability proxy, not a feasible
pooled-tour guarantee or a reservation of alternative drivers.
"""

import csv
from dataclasses import dataclass
import heapq
import json
import math
from numbers import Integral
from pathlib import Path

from src.misc.globals import VRL_STATES


ENABLED = "op_driver_acceptance_future_value"
TOP_K = "op_driver_acceptance_future_value_top_k"


def enabled(attributes):
    flag = attributes.get(ENABLED, False)
    if flag is None:
        return False
    if flag not in (True, False, 0, 1):
        raise ValueError(f"{ENABLED} must be boolean or 0/1")
    return bool(flag)


def at_least_one(probabilities):
    """Stable 1 - product(1 - p), including empty, zero, and one cases."""
    probabilities = tuple(probabilities)
    for probability in probabilities:
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("Fallback probabilities must be finite and within [0,1]")
    if 1 in probabilities:
        return 1.0
    logs = [math.log1p(-probability) for probability in probabilities]
    return -math.expm1(math.fsum(logs)) if logs else 0.0


@dataclass(frozen=True)
class Estimate:
    probability: float
    fallback: float | None
    served_value: float
    alternatives: tuple


class FutureValue:
    def __init__(self, acceptance, vehicles, top_k=5, output_directory=None):
        if isinstance(top_k, bool) or not isinstance(top_k, Integral) or top_k < 0:
            raise ValueError(f"{TOP_K} must be a nonnegative integer")
        self.acceptance = acceptance
        self.vehicles = tuple(vehicles)
        self.top_k = int(top_k)
        self.context = None
        self.routing_engine = None
        self.snapshot = ()
        self.rankings = {}
        self.fallbacks = {}
        self.counters = dict(rounds=0, weight_evaluations=0, candidate_queries=0,
                             candidate_cache_hits=0, fallback_cache_hits=0, routing_queries=0)
        self.audit_path = None
        self.decisions_path = None
        if output_directory is not None:
            directory = Path(output_directory)
            directory.mkdir(parents=True, exist_ok=True)
            self.audit_path = directory / f"future_value_op_{acceptance.operator_id}.json"
            self.decisions_path = directory / f"future_value_op_{acceptance.operator_id}.csv"
            self.columns = ["simulation_time", "round", "operator_id", "vehicle_id", "request_id",
                            "pickup_eta_s", "probability", "fallback_probability", "fallback_evaluated",
                            "served_value", "alternative_vehicle_ids", "alternative_pickup_etas_s"]
            with self.decisions_path.open("w", newline="") as stream:
                csv.DictWriter(stream, fieldnames=self.columns).writeheader()
            self.write_audit()

    def begin_round(self, simulation_time, routing_engine):
        self.context = (simulation_time, id(routing_engine))
        self.routing_engine = routing_engine
        self.snapshot = tuple((vehicle.vid, vehicle.pos, vehicle.max_pax, vehicle.status)
                              for vehicle in sorted(self.vehicles, key=lambda vehicle: vehicle.vid))
        self.rankings.clear()
        self.fallbacks.clear()
        self.counters["rounds"] += 1

    def _key(self, request):
        origin, earliest, latest = request.get_o_stop_info()
        return origin, earliest, latest, request.nr_pax

    def _nearest(self, request, simulation_time):
        key = self._key(request)
        if key in self.rankings:
            self.counters["candidate_cache_hits"] += 1
            return self.rankings[key]
        self.counters["candidate_queries"] += 1
        origin, earliest, latest, passengers = key
        by_position = {}

        def reachable():
            for vid, position, capacity, status in self.snapshot:
                if position is None or status == VRL_STATES.OUT_OF_SERVICE or capacity < passengers:
                    continue
                if position not in by_position:
                    self.counters["routing_queries"] += 1
                    _, travel_time, _ = self.routing_engine.return_travel_costs_1to1(position, origin)
                    by_position[position] = travel_time
                travel_time = by_position[position]
                if not math.isfinite(travel_time) or travel_time < 0:
                    continue
                eta = max(0, travel_time, earliest - simulation_time)
                if eta <= latest - simulation_time:
                    yield (eta, vid)

        # k+1 is sufficient for every possible exclusion of the selected driver.
        # Rank vehicles, not unique positions: colocated drivers are distinct.
        nearest = tuple(heapq.nsmallest(self.top_k + 1, reachable()))
        self.rankings[key] = nearest
        return nearest

    def estimate(self, probability, vehicle_id, request, simulation_time, routing_engine):
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("Current acceptance probability must be finite and within [0,1]")
        self.counters["weight_evaluations"] += 1
        if probability == 1:
            return Estimate(probability, None, 1.0, ())
        if self.top_k == 0 or self.acceptance.override == 0:
            return Estimate(probability, 0.0, probability, ())
        if routing_engine is None:
            raise ValueError("Future-value estimates need a prepared matching-round routing engine")
        if self.context != (simulation_time, id(routing_engine)):
            self.begin_round(simulation_time, routing_engine)
        key = (self._key(request), request.init_direct_td, vehicle_id)
        if key in self.fallbacks:
            self.counters["fallback_cache_hits"] += 1
            fallback, alternatives = self.fallbacks[key]
        else:
            nearest = self._nearest(request, simulation_time)
            alternatives = tuple((eta, vid) for eta, vid in nearest if vid != vehicle_id)[:self.top_k]
            fallback = at_least_one(self.acceptance.probability_at_eta(vid, request, eta)
                                    for eta, vid in alternatives)
            self.fallbacks[key] = fallback, alternatives
        value = probability + (1 - probability) * fallback
        return Estimate(probability, fallback, value, alternatives)

    def record_selected(self, vehicle_id, request, plan, simulation_time):
        if self.decisions_path is None:
            return
        probability = self.acceptance.probability(vehicle_id, request, plan, simulation_time)
        estimate = self.estimate(probability, vehicle_id, request, simulation_time, self.routing_engine)
        eta = max(0, plan.pax_info[request.get_rid_struct()][0] - simulation_time)
        row = [simulation_time, self.counters["rounds"], self.acceptance.operator_id, vehicle_id,
               request.get_rid_struct(), eta, probability, estimate.fallback, estimate.fallback is not None,
               estimate.served_value, ";".join(str(vid) for _, vid in estimate.alternatives),
               ";".join(str(eta) for eta, _ in estimate.alternatives)]
        with self.decisions_path.open("a", newline="") as stream:
            csv.DictWriter(stream, fieldnames=self.columns).writerow(dict(zip(self.columns, row)))

    def write_audit(self):
        if self.audit_path is None:
            return
        audit = {"enabled": True, "top_k": self.top_k,
                 "formula": "p + (1 - p) * (1 - product(1 - alternative_p))",
                 "ranking": "direct road-network pickup ETA, then vehicle ID",
                 "eligibility": "positioned, not out_of_service, sufficient total passenger capacity, reachable by latest pickup",
                 "scope": "frozen matching-round reachability proxy; no pooled-tour feasibility guarantee or actual fallback dispatch",
                 "probabilities": "one offer per driver, conditionally independent; current retry policy unchanged",
                 "selected_records": "one row per first selected-driver decision, before acceptance sampling",
                 "counters": self.counters}
        self.audit_path.write_text(json.dumps(audit, indent=2, allow_nan=False) + "\n")
