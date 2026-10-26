"""Deterministic vehicle-type travel-time scaling, separate from execution noise."""

import math


def travel_time_factor(value):
    if isinstance(value, bool):
        raise ValueError('travel_time_factor must be finite within [1,10]')
    try:
        factor=float(value)
    except (TypeError,ValueError):
        raise ValueError('travel_time_factor must be finite within [1,10]') from None
    if not math.isfinite(factor) or not 1<=factor<=10:
        raise ValueError('travel_time_factor must be finite within [1,10]')
    return factor


def planned_time(vehicle, seconds):
    factor=getattr(vehicle,'travel_time_factor',1.0)
    return seconds if factor==1 else seconds*factor
