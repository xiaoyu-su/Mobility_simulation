"""Phase 5 integration: compatibility episodes and solver-selected menus.

The menu mode selects at most one new request per driver per batch round.
It does not expand request-vehicle graphs or reroute declined requests.
"""

import csv
import json
from pathlib import Path

from src.fleetctrl.acceptance.choice_model import ChoiceOffer, MenuChoice, choose_menu, request_key
from src.fleetctrl.acceptance.conflict_resolution import resolve_choices
from src.misc.globals import G_PRQS_ACC_OFFER, G_SKIP_OUTPUT
from src.misc.seeding import canonical_digest, derive_rng, STREAM_SCHEME


PARAMETER = "op_driver_choice_model"


def choice_mode(attributes):
    mode = attributes.get(PARAMETER)
    # The existing YAML 1.1/CSV decoder maps bare "off" to False.
    mode = "off" if mode in (None, False) else mode
    if mode not in ("off", "singleton", "logit"):
        raise ValueError(f"{PARAMETER} must be off, singleton, or logit")
    return mode


class DriverChoice:
    def __init__(self, acceptance, mode, scenario, output_directory):
        self.acceptance = acceptance
        self.mode = mode
        if mode == "logit" and acceptance.max_declines != 0:
            raise ValueError("Logit driver menus require op_driver_acceptance_max_declines=0; singleton preserves legacy retries")
        if scenario.get("rq_type") not in (None, "BasicRequest"):
            raise ValueError("Driver choice currently supports BasicRequest immediate-on-offer decisions")
        self.round = 0
        self.owners = {}  # accepted uncommitted request -> driver; protects separate episodes
        self.counters = dict(rounds=0, episodes=0, singleton_episodes=0, multi_item_episodes=0,
                             outside_choices=0, conflict_rejections=0, offered_items=0, accepted_items=0)
        self.path = None
        self.audit_path = None
        self.columns = ["simulation_time", "round", "episode", "operator_id", "vehicle_id", "request_id",
                        "menu_size", "base_probability", "choice_probability", "outside_probability",
                        "interval_start", "interval_end", "uniform_draw", "selected", "accepted", "reason", "legacy_delegated"]
        if not scenario.get(G_SKIP_OUTPUT, 0):
            directory = Path(output_directory)
            self.path = directory / f"driver_choice_op_{acceptance.operator_id}.csv"
            self.audit_path = directory / f"driver_choice_op_{acceptance.operator_id}.json"
            with self.path.open("w", newline="") as stream:
                csv.DictWriter(stream, fieldnames=self.columns).writeheader()
            self.write_audit()

    def begin_round(self):
        self.round += 1
        self.counters["rounds"] += 1

    def _write(self, choice, accepted, reasons, simulation_time, legacy=False):
        self.counters["episodes"] += 1
        self.counters["offered_items"] += len(choice.offers)
        self.counters["singleton_episodes" if len(choice.offers) == 1 else "multi_item_episodes"] += 1
        self.counters["outside_choices"] += choice.selected is None
        rows = []
        cumulative = 0.0
        last_positive = max((i for i, p in enumerate(choice.probabilities) if p > 0), default=-1)
        for index, (offer, probability) in enumerate(zip(choice.offers, choice.probabilities)):
            key = (offer.request_id, offer.vehicle_id)
            won = key in accepted
            self.counters["accepted_items"] += won
            self.counters["conflict_rejections"] += reasons.get(key) == "request_conflict"
            interval_end = (1.0 if choice.outside_probability == 0 and index == last_positive
                            else cumulative + probability)
            values = [simulation_time, self.round, self.counters["episodes"], self.acceptance.operator_id,
                      offer.vehicle_id, offer.request_id, len(choice.offers), offer.probability, probability,
                      choice.outside_probability, cumulative, interval_end, choice.uniform_draw, choice.selected == offer,
                      won, reasons.get(key, "accepted" if won else "other_item_chosen"), legacy]
            cumulative = interval_end
            rows.append(dict(zip(self.columns, values)))
        if self.path is not None:
            with self.path.open("a", newline="") as stream:
                csv.DictWriter(stream, fieldnames=self.columns).writerows(rows)

    def accept_single(self, vehicle_id, request, plan, simulation_time, *, final_candidate=None):
        if request.status >= G_PRQS_ACC_OFFER:
            return True
        rid = request.get_rid_struct()
        key = rid, vehicle_id
        if key in self.acceptance.outcomes:
            return self.acceptance.outcomes[key]
        if rid in self.owners and self.owners[rid] != vehicle_id:
            raise ValueError("Request already accepted by another driver")
        probability = self.acceptance.probability(vehicle_id, request, plan, simulation_time)
        if final_candidate is None:
            accepted = self.acceptance._accept_legacy(vehicle_id, request, plan, simulation_time)
        else:
            accepted = self.acceptance._accept_ranked_candidate(vehicle_id, request, plan, simulation_time, final_candidate)
        offer = ChoiceOffer(rid, vehicle_id, probability)
        choice = MenuChoice(vehicle_id, (offer,), (probability,), 1 - probability,
                            offer if accepted else None, None)
        resolution = resolve_choices((choice,))
        winners = {(item.request_id, item.vehicle_id) for item in resolution.accepted}
        if accepted:
            self.owners[rid] = vehicle_id
        self._write(choice, winners, {} if accepted else {key: "outside"}, simulation_time, legacy=True)
        return key in winners

    def prepare_batch(self, solutions, requests, simulation_time):
        if self.mode != "logit":
            return
        menus, plans, seen = {}, {}, set()
        for vid, plan in sorted(solutions.items()):
            if plan is None:
                continue
            for rid in sorted(plan.pax_info, key=request_key):
                request = requests[rid]
                if request.status >= G_PRQS_ACC_OFFER:
                    continue
                if rid in self.owners and self.owners[rid] != vid:
                    raise ValueError("Request already accepted by another driver")
                if rid in seen:
                    raise ValueError("Solver selected the same uncommitted request for multiple vehicles")
                seen.add(rid)
                if (rid, vid) in self.acceptance.outcomes:
                    continue
                probability = self.acceptance.probability(vid, request, plan, simulation_time)
                menus.setdefault(vid, []).append(ChoiceOffer(rid, vid, probability))
                plans[(rid, vid)] = plan
        choices = []
        for vid, offers in sorted(menus.items()):
            if len(offers) == 1:
                offer = offers[0]
                self.accept_single(vid, requests[offer.request_id], plans[(offer.request_id, vid)], simulation_time)
                continue
            token = canonical_digest([request_key(offer.request_id) for offer in sorted(offers, key=lambda item: request_key(item.request_id))])
            rng = derive_rng(self.acceptance.seed,
                             f"driver_choice/{self.acceptance.operator_id}/{vid}/{self.round}/{token}")
            choices.append(choose_menu(vid, offers, rng))
        protected = {rid for rid, request in requests.items() if request.status >= G_PRQS_ACC_OFFER}
        resolution = resolve_choices(choices, protected_requests=protected)
        winners = {(offer.request_id, offer.vehicle_id) for offer in resolution.accepted}
        rejected = {(offer.request_id, offer.vehicle_id): reason for offer, reason in resolution.rejected}
        for choice in choices:
            reasons = dict(rejected)
            for offer, probability in zip(choice.offers, choice.probabilities):
                key = offer.request_id, offer.vehicle_id
                accepted = key in winners
                if accepted:
                    self.owners[offer.request_id] = offer.vehicle_id
                if not accepted and key not in reasons:
                    reasons[key] = "outside" if choice.selected is None else "other_item_chosen"
                self.acceptance.record_menu_outcome(offer.vehicle_id, requests[offer.request_id], plans[key],
                                                    simulation_time, accepted, probability)
            self._write(choice, winners, reasons, simulation_time)

    def write_audit(self):
        if self.audit_path is None:
            return
        audit = {"mode": self.mode, "master_seed": self.acceptance.seed, "scheme": STREAM_SCHEME,
                 "stream": "driver_choice/{operator_id}/{vehicle_id}/{round}/{canonical_menu_digest}",
                 "utility": "log(p)-log(1-p); outside utility 0",
                 "certainty_rule": "uniform over probability-one items; zero outside",
                 "conflict_priority": "lower supplied priority, higher choice probability, vehicle ID, request ID",
                 "singleton": "delegates Phase 3 draws/retries; no additional draw",
                 "scope": "solver-selected new-request menus; no candidate expansion or alternative-driver rerouting",
                 "counters": self.counters}
        if getattr(self.acceptance, "ranked_fallback", None) is not None:
            audit["singleton"] = "one decision per ranked candidate driver; delegates existing request/driver draws"
            audit["scope"] = "ranked insertion singleton episodes; stop at first accepted driver"
        if getattr(self.acceptance, "forbid_rematch", None) is not None:
            audit["scope"] = "native optimizer edge forbidding and same-tick re-solves"
            audit["singleton"] = "one cached decision per request/driver pair; no repeated same-driver offer"
            audit["logit_round_capacity"] = "at most one new accepted request per driver over all solver passes"
        self.audit_path.write_text(json.dumps(audit, indent=2, allow_nan=False) + "\n")
