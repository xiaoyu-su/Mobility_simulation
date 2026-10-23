"""Exercise retry/rejection branches without requiring an optimization solve."""

from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from src.fleetctrl.RidePoolingBatchAssignmentFleetcontrol import RidePoolingBatchAssignmentFleetcontrol
from src.fleetctrl.RidePoolingBatchOptimizationFleetControlBase import RidePoolingBatchOptimizationFleetControlBase
from src.misc.globals import REJECTION_REASON


@pytest.fixture
def controller(monkeypatch):
    # These tests exercise post-optimization bookkeeping; the optimizer itself
    # is exercised by the full-simulation regression cases.
    monkeypatch.setattr(
        RidePoolingBatchOptimizationFleetControlBase,
        "_call_time_trigger_request_batch",
        lambda self, now: setattr(self, "sim_time", now),
    )
    controller = object.__new__(RidePoolingBatchAssignmentFleetcontrol)
    controller.optimisation_time_step = 60
    controller.max_wait_time_2 = None
    controller.rid_to_assigned_vid = {}
    controller.unassigned_requests_1 = {}
    controller.unassigned_requests_2 = {}
    controller.rq_dict = {}
    controller.RPBO_Module = SimpleNamespace(delete_request=Mock(), add_new_request=Mock())
    controller.change_prq_time_constraints = Mock()
    controller._create_rejection = Mock()
    return controller


def test_unassigned_request_is_registered_again_with_extended_pickup_window(controller):
    request = SimpleNamespace(get_o_stop_info=lambda: ((7, None, None), 100, 400))
    controller.max_wait_time_2 = 600
    controller.unassigned_requests_1 = {42: 1}
    controller.rq_dict = {42: request}

    controller._call_time_trigger_request_batch(60)

    controller.RPBO_Module.delete_request.assert_called_once_with(42)
    controller.change_prq_time_constraints.assert_called_once_with(60, 42, 700)
    controller.RPBO_Module.add_new_request.assert_called_once_with(42, request)
    assert controller.unassigned_requests_1 == {}
    assert controller.unassigned_requests_2 == {42: 1}
    controller._create_rejection.assert_not_called()


@pytest.mark.parametrize("has_new_request", [False, True])
def test_second_attempt_rejects_its_own_request(controller, has_new_request):
    first_request = object()
    retried_request = object()
    controller.rq_dict = {7: first_request, 42: retried_request}
    controller.unassigned_requests_1 = {7: 1} if has_new_request else {}
    controller.unassigned_requests_2 = {42: 1}

    controller._call_time_trigger_request_batch(60)

    expected = []
    if has_new_request:
        expected.append(call(first_request, 60, reason=REJECTION_REASON.NO_VEHICLE_AVAILABLE))
    expected.append(call(retried_request, 60, reason=REJECTION_REASON.NO_VEHICLE_AVAILABLE))
    assert controller._create_rejection.call_args_list == expected
    assert controller.unassigned_requests_2 == {}
