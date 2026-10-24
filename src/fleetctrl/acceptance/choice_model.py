"""Logit choice over request offers and an outside option, without dispatch."""

from dataclasses import dataclass
import math


def request_key(request_id):
    return type(request_id).__name__, repr(request_id)


@dataclass(frozen=True)
class ChoiceOffer:
    request_id: object
    vehicle_id: int
    probability: float
    priority: float = 0.0  # lower supplied assignment cost/priority wins ties

    def __post_init__(self):
        if self.request_id is None:
            raise ValueError("None is reserved for the outside option")
        hash(self.request_id)
        if not math.isfinite(self.probability) or not 0 <= self.probability <= 1:
            raise ValueError("Offer probability must be finite and in [0,1]")
        if not math.isfinite(self.priority):
            raise ValueError("Offer priority must be finite")


@dataclass(frozen=True)
class MenuChoice:
    vehicle_id: int
    offers: tuple
    probabilities: tuple
    outside_probability: float
    selected: ChoiceOffer | None
    uniform_draw: float | None


def menu_distribution(vehicle_id, offers):
    offers = tuple(sorted(offers, key=lambda offer: request_key(offer.request_id)))
    if any(offer.vehicle_id != vehicle_id for offer in offers):
        raise ValueError("A driver menu may contain only that driver's offers")
    if len({offer.request_id for offer in offers}) != len(offers):
        raise ValueError("Duplicate request in driver menu")
    if not offers:
        return offers, (), 1.0
    if len(offers) == 1:
        p = offers[0].probability
        return offers, (p,), 1 - p  # exact Phase 3 single-offer arithmetic
    certain = [offer.probability == 1 for offer in offers]
    if any(certain):
        count = sum(certain)
        return offers, tuple(1 / count if flag else 0.0 for flag in certain), 0.0
    logits = [math.log(offer.probability) - math.log1p(-offer.probability)
              if offer.probability > 0 else -math.inf for offer in offers]
    maximum = max(0, *logits)  # outside utility is zero
    weights = [math.exp(utility - maximum) for utility in logits]
    outside = math.exp(-maximum)
    total = math.fsum([*weights, outside])
    return offers, tuple(weight / total for weight in weights), outside / total


def choose_menu(vehicle_id, offers, rng):
    offers, probabilities, outside = menu_distribution(vehicle_id, offers)
    positive = [i for i, probability in enumerate((*probabilities, outside)) if probability > 0]
    draw = None
    if len(positive) == 1:
        selected_index = positive[0]
    else:
        draw = float(rng.random())
        if not 0 <= draw < 1:
            raise ValueError("Choice draw must be in [0,1)")
        cumulative = 0.0
        selected_index = len(offers)  # rounding remainder belongs to outside
        for i, probability in enumerate(probabilities):
            cumulative += probability
            if draw < cumulative:
                selected_index = i
                break
        if outside == 0 and selected_index == len(offers):
            selected_index = positive[-1]  # floating-point tail at zero outside
    selected = offers[selected_index] if selected_index < len(offers) else None
    return MenuChoice(vehicle_id, offers, probabilities, outside, selected, draw)
