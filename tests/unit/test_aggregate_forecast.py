"""Check zone aggregation against hand-computed departure/arrival counts."""

import pandas as pd
import pytest

from src.fleetctrl.forecast.AggForecastZoning import AggForecastZoneSystem


@pytest.mark.parametrize("trip_type, expected", [
    ("out", {0: 5.0, 1: 7.0}),
    ("in", {0: 10.0, 1: 11.0}),
])
def test_forecast_aggregates_zone_counts(trip_type, expected):
    forecast = object.__new__(AggForecastZoneSystem)
    forecast.forecast_df = pd.DataFrame({
        "time": [900, 900, 900, 1800],
        "zone_id": [0, 0, 1, 0],
        "out perfect_trips": [2, 3, 7, 99],
        "in perfect_trips": [4, 6, 11, 99],
    }).set_index(["time", "zone_id"])
    forecast.fc_times = [900, 1800]
    forecast.fc_temp_resolution = 900
    forecast.in_fc_type = "in perfect_trips"
    forecast.out_fc_type = "out perfect_trips"

    if trip_type == "out":
        actual = forecast.get_trip_departure_forecasts(900, 1800, aggregation_level="zone_id")
    else:
        actual = forecast.get_trip_arrival_forecasts(900, 1800, aggregation_level="zone_id")

    assert actual == expected
