"""Same-tick Alonso-Mora re-solves after driver request/vehicle refusals."""

import csv
import json
from pathlib import Path

from src.misc.globals import G_PRQS_ACC_OFFER, G_SKIP_OUTPUT, G_RA_SOLVER
from src.misc.seeding import STREAM_SCHEME

PARAMETER = "op_driver_acceptance_forbid_rematch"


def enabled(attributes):
    value = attributes.get(PARAMETER, False)
    if value is None:
        return False
    if value not in (True, False, 0, 1):
        raise ValueError(f"{PARAMETER} must be boolean or 0/1")
    return bool(value)


class ForbidRematch:
    def __init__(self, acceptance, attributes, scenario, output_directory):
        if attributes.get("op_module") != "RidePoolingBatchAssignmentFleetcontrol":
            raise ValueError("Forbid/rematch requires the pure Alonso-Mora batch controller; insertion fallback is Phase 5b")
        if attributes.get("op_rp_batch_optimizer", "AlonsoMora") != "AlonsoMora" or attributes.get(G_RA_SOLVER, "Gurobi") != "Gurobi":
            raise ValueError("Forbid/rematch currently requires single-worker AlonsoMora with Gurobi")
        if scenario.get("sim_env") != "BatchOfferSimulation" or scenario.get("rq_type") not in (None, "BasicRequest"):
            raise ValueError("Forbid/rematch requires BatchOfferSimulation and BasicRequest")
        if acceptance.max_declines != 0:
            raise ValueError("Forbid/rematch requires op_driver_acceptance_max_declines=0: one decision per request/driver")
        self.acceptance = acceptance
        self.pending_rows = []
        self.round = 0
        self.columns = ["simulation_time", "round", "pass", "operator_id", "vehicle_id", "request_id",
                        "base_probability", "accepted", "edge_forbidden", "decision_kind"]
        self.counters = dict(rounds=0, solver_resolves=0, offered_pairs=0, forbidden_pairs=0,
                             accepted_requests=0, recovered_requests=0, terminal_requests=0,
                             pruned_trip_variables=0)
        self.path = self.audit_path = None
        if not scenario.get(G_SKIP_OUTPUT, 0):
            directory = Path(output_directory)
            self.path = directory / f"forbid_rematch_op_{acceptance.operator_id}.csv"
            self.audit_path = self.path.with_suffix(".json")
            with self.path.open("w", newline="") as stream:
                csv.DictWriter(stream, fieldnames=self.columns).writeheader()
            self.write_audit()

    def record_attempt(self, row):
        self.pending_rows.append(row)

    def _flush_attempts(self, terminal):
        # A driver's refusal is not a terminal request rejection until re-solving
        # finishes. Buffer genuine attempt rows rather than inventing extra offers.
        marked = set()
        for row in reversed(self.pending_rows):
            rid = row["request_id"]
            if rid in terminal and rid not in marked and not row["accepted"]:
                row["terminal_decline"] = True
                marked.add(rid)
        if self.pending_rows and self.acceptance.path is not None:
            with self.acceptance.path.open("a", newline="") as stream:
                csv.DictWriter(stream, fieldnames=self.acceptance.columns).writerows(self.pending_rows)
        self.pending_rows.clear()

    def resolve(self, controller, solutions):
        optimizer = controller.RPBO_Module
        self.round += 1
        self.counters["rounds"] += 1
        required, refused = {}, set()
        rows = []
        bound = len(controller.rq_dict) * len(controller.sim_vehicles) + 1
        choice = self.acceptance.choice
        single_request = choice is not None and choice.mode == "logit"
        try:
            for iteration in range(bound):
                previous = set(self.acceptance.outcomes)
                if choice is not None:
                    choice.prepare_batch(solutions, controller.rq_dict, controller.sim_time)
                new_refusals = 0
                for vid, plan in sorted(solutions.items()):
                    if plan is None:
                        continue
                    for rid in sorted(plan.pax_info, key=str):
                        request = controller.rq_dict[rid]
                        if request.status >= G_PRQS_ACC_OFFER:
                            continue
                        accepted = self.acceptance.accept(vid, request, plan, controller.sim_time)
                        if accepted:
                            if rid in required and required[rid] != vid:
                                raise RuntimeError("Optimizer moved a driver-accepted request during rematching")
                            required[rid] = vid
                        else:
                            removed = optimizer.forbid_request_vehicle(rid, vid)
                            if removed is None:
                                raise RuntimeError("Optimizer selected an already forbidden request/driver pair")
                            self.counters["pruned_trip_variables"] += removed
                            self.counters["forbidden_pairs"] += 1
                            new_refusals += 1
                            refused.add(rid)
                        if (rid, vid) not in previous:
                            self.counters["offered_pairs"] += 1
                            rows.append(dict(zip(self.columns, [controller.sim_time, self.round, iteration,
                                self.acceptance.operator_id, vid, rid,
                                self.acceptance.probability(vid, request, plan, controller.sim_time),
                                accepted, not accepted,
                                "menu_item" if single_request else "singleton"])))
                if not new_refusals:
                    final_owners = {rid: vid for vid, plan in solutions.items() if plan is not None for rid in plan.pax_info}
                    if any(final_owners.get(rid) != vid for rid, vid in required.items()):
                        raise RuntimeError("Rematching lost a previously accepted request")
                    terminal = refused - required.keys()
                    controller._driver_declined_requests.update(terminal)
                    self.counters["accepted_requests"] += len(required)
                    self.counters["recovered_requests"] += len(refused & required.keys())
                    self.counters["terminal_requests"] += len(terminal)
                    self._flush_attempts(terminal)
                    if self.path is not None and rows:
                        with self.path.open("a", newline="") as stream:
                            csv.DictWriter(stream, fieldnames=self.columns).writerows(rows)
                    return solutions
                self.counters["solver_resolves"] += 1
                optimizer.reoptimise_after_driver_declines(required, single_request)
                solutions = {vid: optimizer.get_optimisation_solution(vid) for vid in range(len(controller.sim_vehicles))}
            raise RuntimeError("Forbid/rematch exceeded the finite request/driver edge bound")
        finally:
            optimizer.clear_driver_acceptance_constraints()

    def write_audit(self):
        if self.audit_path is not None:
            self.audit_path.write_text(json.dumps({
                "enabled": True, "scheme": STREAM_SCHEME,
                "algorithm": "prune declined request/driver edges and cached trips; re-solve retained native ILP at the same simulation time",
                "accepted_protection": "temporary mandatory request/driver constraints during re-solves; existing commitments unchanged",
                "logit_capacity": "at most one new accepted request per driver across all passes of a matching round",
                "negative_menu_items": "outside/unselected items forbid their offered request/driver edges",
                "terminal_decline": "last genuine refusal only for requests still unassigned after re-solving",
                "scope": "retained feasible trip graph, instantaneous decisions, no replay of finished legs or injected plans",
                "counters": self.counters}, indent=2) + "\n")
