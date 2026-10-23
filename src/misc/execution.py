"""Opt-in execution settings, separate from routing/planning travel times."""

import math


def travel_time_noise_sigma(parameters):
    value = parameters.get("network_tt_noise_sigma", 0)
    try:
        sigma = float(value)
    except (ValueError, TypeError):
        raise ValueError("network_tt_noise_sigma must be finite and nonnegative") from None
    if isinstance(value, bool) or not math.isfinite(sigma) or sigma < 0:
        raise ValueError("network_tt_noise_sigma must be finite and nonnegative")
    return sigma


def promised_times_enabled(parameters):
    value = parameters.get("record_promised_times", False)
    if value not in (False, True, 0, 1):
        raise ValueError("record_promised_times must be a boolean or 0/1")
    return bool(value) or travel_time_noise_sigma(parameters) > 0


def validate_execution_settings(parameters):
    sigma = travel_time_noise_sigma(parameters)
    recording = promised_times_enabled(parameters)
    if recording and parameters.get("broker_type") is not None:
        raise ValueError("Promised-time recording currently supports BrokerBasic road trips only")
    if sigma > 0 and (parameters.get("sim_env") in ("MATSim", "SUMOcontrolledSim")
                      or "SumoCoupling" in str(parameters.get("network_type", ""))):
        raise ValueError("Execution travel-time noise cannot control externally simulated vehicle movement")
