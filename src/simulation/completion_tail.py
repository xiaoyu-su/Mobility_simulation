"""Opt-in, audited completion of assignments after the demand horizon."""
import json
from pathlib import Path
from src.misc.globals import VRL_STATES


def completion_tail(sim):
    maximum = sim.scenario_parameters['completion_tail_max_seconds']
    if isinstance(maximum, bool) or int(maximum) != maximum or not 0 <= maximum <= 7 * 86400:
        raise ValueError('completion_tail_max_seconds must be an integer in 0..604800')
    current = sim.end_time
    steps = 0
    while True:
        sim.update_sim_state_fleets(current - sim.time_step, current, only_active=True)
        for operators in sim.charging_operator_dict.values():
            for operator in operators.values():
                operator.time_trigger(current)
        remaining = 0
        passengers = []
        for vehicle in sim.sim_vehicles.values():
            if vehicle.assigned_route and vehicle.assigned_route[0].status == VRL_STATES.OUT_OF_SERVICE:
                vehicle.end_current_leg(current)
            remaining += len(vehicle.assigned_route)
            passengers.extend(rq.get_rid_struct() for rq in vehicle.pax)
        steps += 1
        status = 'complete' if remaining == 0 and not passengers else 'running'
        if status == 'running' and (remaining == 0 or current + sim.time_step > sim.end_time + maximum):
            status = 'incomplete'
        if status != 'running':
            audit = dict(status=status,maximum_tail_seconds=int(maximum),last_processed_time=current,
                         elapsed_after_horizon_s=current - sim.end_time,steps=steps,
                         remaining_tasks=remaining,onboard_request_ids=passengers,
                         idle_vehicle_updates_skipped=True,driving_time_step=sim.time_step)
            if not sim.skip_output:
                (Path(sim.dir_names['output']) / 'completion_tail.json').write_text(json.dumps(audit,indent=2)+'\n')
            sim.record_stats(force=True)
            if status != 'complete':
                raise RuntimeError(f'Completion tail exhausted with {remaining} tasks and {len(passengers)} onboard requests')
            return
        current += sim.time_step
        sim.routing_engine.update_network(current,update_state=False)
