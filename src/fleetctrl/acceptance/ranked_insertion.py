"""Sequential, one-offer-per-driver fallback over feasible insertion plans."""

import csv
import json
import math
from pathlib import Path

from src.misc.globals import G_SKIP_OUTPUT
from src.misc.seeding import STREAM_SCHEME


PARAMETER = "op_driver_acceptance_ranked_fallback"


def enabled(attributes):
    flag = attributes.get(PARAMETER, False)
    if flag is None:
        return False
    if flag not in (True, False, 0, 1):
        raise ValueError(f"{PARAMETER} must be boolean or 0/1")
    return bool(flag)


def select_insertion_candidate(acceptance, candidates, request, simulation_time, av_product=None):
    """Preserve the original stable minimum exactly when fallback is disabled."""
    if av_product is not None:
        candidates=av_product.threshold_candidates(candidates,request,simulation_time)
    if acceptance is not None and acceptance.ranked_fallback is not None:
        return acceptance.ranked_fallback.select(candidates, request, simulation_time)
    return min(candidates, key=lambda item: item[2]) if candidates else None


class RankedInsertionFallback:
    def __init__(self, acceptance, attributes, scenario, output_directory):
        if attributes.get("op_module") not in ("PoolingIRSOnly", "PoolingIRSAssignmentBatchOptimization"):
            raise ValueError("Ranked fallback supports the two immediate insertion controllers; batch rematching is Phase 5c")
        if scenario.get("sim_env") != "ImmediateDecisionsSimulation" or scenario.get("rq_type") not in (None, "BasicRequest"):
            raise ValueError("Ranked fallback requires ImmediateDecisionsSimulation and BasicRequest")
        if acceptance.max_declines != 0:
            raise ValueError("Ranked fallback requires op_driver_acceptance_max_declines=0: one offer per distinct driver")
        self.acceptance = acceptance
        self.results = {}  # request -> winning vehicle ID, or None when exhausted
        self.counters = dict(requests=0, retained_candidates=0, offers=0, declines=0,
                             accepted_requests=0, fallback_acceptances=0,
                             exhausted_requests=0, no_candidate_requests=0)
        self.columns = ["simulation_time", "operator_id", "request_id", "vehicle_id",
                        "candidate_rank", "candidate_count", "delta_objective", "probability",
                        "accepted", "terminal_request_decline", "candidate_vehicle_ids", "candidate_costs"]
        self.path = self.audit_path = None
        if not scenario.get(G_SKIP_OUTPUT, 0):
            directory = Path(output_directory)
            directory.mkdir(parents=True, exist_ok=True)
            self.path = directory / f"ranked_insertion_op_{acceptance.operator_id}.csv"
            self.audit_path = self.path.with_suffix(".json")
            with self.path.open("w", newline="") as stream:
                csv.DictWriter(stream, fieldnames=self.columns).writeheader()
            self.write_audit()

    def select(self, candidates, request, simulation_time):
        # Validate and freeze the complete retained list before consuming draws.
        for vid, plan, cost in candidates:
            if not math.isfinite(float(cost)):
                raise ValueError("Ranked insertion candidate costs must be finite")
            if plan.vid != vid or request.get_rid_struct() not in plan.pax_info:
                raise ValueError("Ranked insertion candidate does not match its vehicle/request")
        ranked, seen = [], set()
        for item in sorted(candidates, key=lambda candidate: candidate[2]):
            if item[0] not in seen:
                ranked.append(item)
                seen.add(item[0])
        rid = request.get_rid_struct()
        if rid in self.results:
            winner = self.results[rid]
            if winner is None:
                return None
            for candidate in ranked:
                if candidate[0] == winner:
                    return candidate
            raise ValueError("Previously accepted driver is absent from replayed insertion candidates")
        self.counters["requests"] += 1
        self.counters["retained_candidates"] += len(ranked)
        if not ranked:
            self.counters["no_candidate_requests"] += 1
            self.results[rid] = None
            return None
        for index, (vid, plan, cost) in enumerate(ranked):
            probability = self.acceptance.probability(vid, request, plan, simulation_time)
            final = index == len(ranked) - 1
            accepted = self.acceptance.accept(vid, request, plan, simulation_time, final_candidate=final)
            self.counters["offers"] += 1
            self.counters["declines"] += not accepted
            if self.path is not None:
                values = [simulation_time, self.acceptance.operator_id, rid, vid, index + 1,
                          len(ranked), cost, probability, accepted, final and not accepted,
                          ";".join(str(item[0]) for item in ranked),
                          json.dumps([float(item[2]) for item in ranked])]
                with self.path.open("a", newline="") as stream:
                    csv.DictWriter(stream, fieldnames=self.columns).writerow(dict(zip(self.columns, values)))
            if accepted:
                self.counters["accepted_requests"] += 1
                self.counters["fallback_acceptances"] += index > 0
                self.results[rid] = vid
                return vid, plan, cost
        self.counters["exhausted_requests"] += 1
        self.results[rid] = None
        return None

    def write_audit(self):
        if self.audit_path is not None:
            self.audit_path.write_text(json.dumps({
                "enabled": True, "scheme": STREAM_SCHEME,
                "ranking": "ascending existing delta objective; stable original insertion order for ties",
                "candidate_scope": "existing feasible insertion list after configured heuristics; cheapest plan per distinct driver",
                "decision": "one singleton offer per driver, stop at first acceptance; zero response latency",
                "terminal_decline": "only the last refusal after all retained drivers decline",
                "stream": "driver_acceptance/{operator_id}/{vehicle_id}/{request_id}",
                "max_declines_scope": "must be zero; no same-driver retries, total offers bounded by candidate count",
                "counters": self.counters}, indent=2) + "\n")
