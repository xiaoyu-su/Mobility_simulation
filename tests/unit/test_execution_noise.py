from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from src.FleetSimulationBase import FleetSimulationBase
from src.demand.TravelerModels import BasicRequest
from src.misc.execution import travel_time_noise_sigma, promised_times_enabled, validate_execution_settings
from src.misc.globals import *
from src.simulation.Legs import VehicleRouteLeg
from src.simulation.Offers import TravellerOffer
from src.simulation.Vehicles import SimulationVehicle
from tools.paired_eval.metrics import promise_error_summary


class LineNetwork:
    """Each edge takes 10 planning seconds and is 100 meters long."""
    def return_best_route_1to1(self, origin, destination):
        return [origin[0], destination[0]]

    def return_position_from_str(self, value):
        return (int(value), None, None)

    def return_position_str(self, pos):
        return str(pos)

    def get_zones_external_route_costs(self, *args, **kwargs):
        return 0, 0, 0

    def return_travel_costs_1to1(self, origin, destination):
        return 10, 10, 100

    def move_along_route(self, route, position, time_step, *, target_position,
                         sim_vid_id, new_sim_time, record_node_times):
        fraction = position[2] or 0
        remaining = (1 - fraction) * 10
        if time_step < remaining:
            return ((position[0], route[0], fraction + time_step / 10),
                    time_step * 10, -1, [], [])
        arrival = new_sim_time + remaining
        return (target_position, remaining * 10, arrival, [route[0]],
                [arrival] if record_node_times else [])


def vehicle(sigma=0, vid=0):
    attributes = {G_VTYPE_NAME: "test", G_VTYPE_MAX_PAX: 4, G_VTYPE_FIX_COST: 0,
                  G_VTYPE_DIST_COST: 1, G_VTYPE_BATTERY_SIZE: 1, G_VTYPE_RANGE: 100}
    obj = SimulationVehicle(0, vid, attributes, LineNetwork(), {}, [], True, True,
                            {"random_seed": 17, "network_tt_noise_sigma": sigma})
    obj.pos, obj.soc = (1, None, None), 1
    return obj


@pytest.mark.parametrize("sigma", [-1, np.nan, np.inf, "bad", None, True])
def test_invalid_noise_settings_fail(sigma):
    with pytest.raises(ValueError, match="network_tt_noise_sigma"):
        travel_time_noise_sigma({"network_tt_noise_sigma": sigma})


def test_defaults_do_not_construct_or_draw_an_execution_rng():
    assert travel_time_noise_sigma({}) == 0
    assert not promised_times_enabled({})
    assert promised_times_enabled({"record_promised_times": 1})
    assert promised_times_enabled({"network_tt_noise_sigma": .3})
    with pytest.raises(ValueError, match="record_promised_times"):
        promised_times_enabled({"record_promised_times": "false"})
    obj = vehicle(0)
    assert obj._execution_rng is None
    obj.assign_vehicle_plan([VehicleRouteLeg(VRL_STATES.ROUTE, (2, None, None), {})], 100)
    obj.update_veh_state(100, 120)
    assert obj.op_output[0][G_VR_LEG_END_TIME] == 110
    assert "travel_time_multiplier" not in obj.op_output[0]


@pytest.mark.parametrize("parameters", [{"network_tt_noise_sigma": .3, "sim_env": "SUMOcontrolledSim"},
                                       {"network_tt_noise_sigma": .3, "network_type": "NetworkBasicSumoCoupling"},
                                       {"record_promised_times": True, "broker_type": "PTBroker"}])
def test_unsupported_external_or_multimodal_timing_is_rejected(parameters):
    with pytest.raises(ValueError):
        validate_execution_settings(parameters)


@pytest.mark.parametrize("multiplier", [.5, 2.0])
def test_one_draw_per_driving_leg_preserves_wall_clock_distance_and_energy(multiplier):
    obj = vehicle(.4)
    obj._execution_rng = Mock()
    obj._execution_rng.lognormal.return_value = multiplier
    drive = VehicleRouteLeg(VRL_STATES.ROUTE, (2, None, None), {})
    stop = VehicleRouteLeg(VRL_STATES.BOARDING, (2, None, None), {}, duration=5)
    obj.assign_vehicle_plan([drive, stop], 100)
    half_time = 100 + 5 * multiplier
    obj.update_veh_state(100, half_time)
    assert obj.pos == (1, 2, .5)
    assert obj.cl_tt_multiplier == multiplier
    # An unchanged leg supplied by a new plan must retain its draw.
    obj.assign_vehicle_plan([VehicleRouteLeg(VRL_STATES.ROUTE, (2, None, None), {}), stop], half_time)
    obj.update_route()
    obj.update_veh_state(half_time, 130)
    obj._execution_rng.lognormal.assert_called_once_with(-.4 * .4 / 2, .4)
    driving, stationary = obj.op_output
    assert driving[G_VR_LEG_END_TIME] == 100 + 10 * multiplier
    assert stationary[G_VR_LEG_END_TIME] == 105 + 10 * multiplier
    assert driving[G_VR_LEG_DISTANCE] == pytest.approx(100)
    assert obj.soc == pytest.approx(1 - 100 / 100000)
    assert driving["travel_time_multiplier"] == multiplier
    assert stationary["travel_time_multiplier"] == 1
    assert obj.status == VRL_STATES.IDLE
    # Replay node timestamps are also absolute wall-clock times.
    times = [float(entry.split(":")[1]) for entry in driving[G_VR_REPLAY_ROUTE].split(";")]
    assert times == [100, 100 + 10 * multiplier]


def test_execution_stream_is_repeatable_per_vehicle_and_does_not_touch_global_state():
    np.random.seed(8)
    before = np.random.get_state()
    first, repeat, other = vehicle(.3), vehicle(.3), vehicle(.3, vid=1)
    draws = first._execution_rng.lognormal(-.045, .3, size=100000)
    np.testing.assert_array_equal(draws, repeat._execution_rng.lognormal(-.045, .3, size=100000))
    assert not np.array_equal(draws, other._execution_rng.lognormal(-.045, .3, size=100000))
    # Deterministic sample check of the mean-one parameterization, not a fixture target.
    assert draws.mean() == pytest.approx(1, abs=.005)
    after = np.random.get_state()
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def request(enabled=True):
    row = pd.Series({"request_id": 7, "rq_time": 100, "start": 1, "end": 2,
                     "latest_decision_time": 200})
    return BasicRequest(row, LineNetwork(), 1, {"record_promised_times": enabled})


def test_only_the_booked_operator_promise_is_frozen_before_booking_callbacks():
    rq = request()
    rq.receive_offer(0, TravellerOffer(7, 0, 5, 20, 100), 110)
    rq.receive_offer(1, TravellerOffer(7, 1, 30, 60, 100), 120)
    rq.choose_offer = lambda parameters, time: 1
    def book(rid, obj, time, operator):
        obj.receive_offer(1, TravellerOffer(7, 1, 999, 999, 100), time)
        return [(rid, obj)]
    sim = SimpleNamespace(scenario_parameters={}, broker=SimpleNamespace(inform_user_booking=book),
                          demand=SimpleNamespace(waiting_rq={}, undecided_rq={7: rq}))
    FleetSimulationBase._rid_chooses_offer(sim, 7, rq, 125)
    rq.capture_service_promise(0)
    rq.user_boards_vehicle(140, 1, 2, rq.o_pos, None)
    rq.user_leaves_vehicle(185, rq.d_pos, None)
    record = rq.record_data()
    assert record["promise_operator_id"] == 1
    assert record["promised_pickup_time"] == 130  # request time + wait, not booking time + wait
    assert record["promised_dropoff_time"] == 190
    assert record["pickup_error_s"] == 10 and record["dropoff_error_s"] == -5
    assert sim.demand.waiting_rq[7] is rq
    with pytest.raises(ValueError, match="Serving operator"):
        rq.user_boards_vehicle(150, 0, 2, rq.o_pos, None)


def test_unserved_and_unrecorded_requests_do_not_invent_promises_or_zero_errors():
    rq = request()
    rq.receive_offer(0, TravellerOffer(7, 0, None, None, None), 100)
    rq.capture_service_promise(0)
    assert rq.record_data()["promised_pickup_time"] is None
    assert rq.record_data()["pickup_error_s"] is None
    assert "promised_pickup_time" not in request(False).record_data()


def test_error_summary_uses_signed_errors_and_counts_missing_service():
    users = pd.DataFrame({"promise_operator_id": [0, 0, np.nan],
                          "promised_pickup_time": [100, 200, np.nan],
                          "promised_dropoff_time": [150, 250, np.nan],
                          "pickup_time": [110, 190, np.nan], "dropoff_time": [170, 240, np.nan]})
    metrics = promise_error_summary(users)
    assert metrics["promised_requests"] == 2
    assert metrics["pickup_promise_error.mean_s"] == 0
    assert metrics["pickup_promise_error.std_s"] == 10
    assert metrics["pickup_promise_error.mae_s"] == 10
    assert metrics["pickup_promise_error.late_fraction"] == .5
    assert metrics["pickup_promise_error.missing_count"] == 1
    assert metrics["dropoff_promise_error.mean_s"] == 5


def test_delayed_committed_stops_remain_in_the_plan_and_execute_after_deadline():
    from src.fleetctrl.planning.VehiclePlan import BoardingPlanStop, VehiclePlan

    obj, rq = vehicle(.3), request()
    obj.rq_db[7] = rq
    pickup = BoardingPlanStop((2, None, None), boarding_dict={1: [7]}, change_nr_pax=1,
                              latest_pickup_time_dict={7: 115}, duration=5)
    dropoff = BoardingPlanStop((3, None, None), boarding_dict={-1: [7]}, change_nr_pax=-1,
                               latest_arrival_time_dict={7: 130}, duration=5)
    plan = VehiclePlan(obj, 100, obj.routing_engine, [pickup, dropoff])
    assert plan.feasible  # predicted pickup 110, dropoff 125
    assert not plan.update_tt_and_check_plan(obj, 140, obj.routing_engine, keep_feasible=True)
    assert plan.list_plan_stops == [pickup, dropoff]
    assert all(stop.is_infeasible_locked() for stop in plan.list_plan_stops)
    assert plan.get_dedicated_rid_list() == [7]
    obj._execution_rng = Mock()
    obj._execution_rng.lognormal.return_value = 2
    legs = [VehicleRouteLeg(VRL_STATES.ROUTE, (2, None, None), {}),
            VehicleRouteLeg(VRL_STATES.BOARDING, (2, None, None), {1: [rq]}, duration=5),
            VehicleRouteLeg(VRL_STATES.ROUTE, (3, None, None), {}),
            VehicleRouteLeg(VRL_STATES.BOARDING, (3, None, None), {-1: [rq]}, duration=5)]
    obj.assign_vehicle_plan(legs, 140)
    boarding, alighting, _, start_alighting = obj.update_veh_state(140, 200)
    assert boarding[7][0] == 160 and start_alighting[7][0] == 185
    assert alighting[7] == 190
    assert obj._execution_rng.lognormal.call_count == 2
    assert not obj.pax and not obj.assigned_route
