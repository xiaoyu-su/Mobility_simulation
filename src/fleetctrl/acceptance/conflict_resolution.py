"""Deterministic greedy winners for sampled driver choices."""

from dataclasses import dataclass

from src.fleetctrl.acceptance.choice_model import request_key


@dataclass(frozen=True)
class Resolution:
    accepted: tuple
    rejected: tuple  # (selected offer, rejection reason)


def resolve_choices(choices, protected_requests=(), unavailable_vehicles=()):
    choices = tuple(choices)
    if len({choice.vehicle_id for choice in choices}) != len(choices):
        raise ValueError("Only one menu choice per driver is allowed in an episode")
    proposals = []
    for choice in choices:
        if choice.selected is not None:
            if choice.selected not in choice.offers or choice.selected.vehicle_id != choice.vehicle_id:
                raise ValueError("Selected offer does not belong to the driver's menu")
            index = choice.offers.index(choice.selected)
            probability = choice.probabilities[index]
            proposals.append((choice.selected, probability))
    proposals.sort(key=lambda item: (item[0].priority, -item[1], item[0].vehicle_id,
                                    request_key(item[0].request_id)))
    claimed = set(protected_requests)
    occupied = set(unavailable_vehicles)
    accepted, rejected = [], []
    for offer, _ in proposals:
        if offer.request_id in claimed:
            rejected.append((offer, "request_conflict"))
        elif offer.vehicle_id in occupied:
            rejected.append((offer, "vehicle_unavailable"))
        else:
            accepted.append(offer)
            claimed.add(offer.request_id)
            occupied.add(offer.vehicle_id)
    return Resolution(tuple(accepted), tuple(rejected))
