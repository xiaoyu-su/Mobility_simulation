"""Neutral worker: import FleetPy exclusively from the selected source tree.

Executed by absolute filename for both the unmodified Git archive and the fork.
Only paths, explicitly recorded profile overrides, and observation hooks differ
from the selected native scenario. No fork tools are imported into the reference.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.source.resolve(), args.output.resolve()
    if output.exists():
        raise ValueError('Refusing to overwrite fidelity worker output')
    profile = json.loads(args.profile.read_text())
    sys.path.insert(0, str(root))
    from src.FleetSimulationBase import FleetSimulationBase
    from src.misc.config import ConstantConfig, ScenarioConfig
    from src.misc.init_modules import load_simulation_environment
    from src.misc.globals import (G_DIR_NETWORK, G_DIR_DEMAND, G_DIR_VEH,
                                  G_DIR_FCTRL, G_DIR_ZONES, G_DIR_OUTPUT)

    parameters = ConstantConfig(str(root / profile['constants']))
    scenarios = ScenarioConfig(str(root / profile['scenarios']))
    matches = [p for p in scenarios if p['scenario_name'] == profile['scenario']]
    if len(matches) != 1:
        raise ValueError('Native scenario must select exactly one original row')
    parameters += matches[0]
    parameters.update(profile.get('overrides', {}))
    parameters.update(study_name='native_fidelity', n_cpu_per_sim=1, evaluate=1,
                      log_level='warning', keep_old=False, show_progress_bar=False)
    original = FleetSimulationBase.get_directory_dict
    data = Path(profile['data_root']).resolve()

    def private_paths(p, operators):
        paths = original(p, operators)
        paths.update({G_DIR_NETWORK: str(data / 'networks' / p['network_name']),
                      G_DIR_DEMAND: str(data / 'demand' / p['demand_name'] / 'matched' / p['network_name']),
                      G_DIR_VEH: str(root / 'data/vehicles'),
                      G_DIR_FCTRL: str(root / 'data/fleetctrl'), G_DIR_OUTPUT: str(output)})
        for i, operator in enumerate(operators):
            if operator.get('op_zone_system'):
                paths[f'op_{i}'][G_DIR_ZONES] = str(data / 'zones' / operator['op_zone_system'] / p['network_name'])
        return paths

    FleetSimulationBase.get_directory_dict = staticmethod(private_paths)
    try:
        sim = load_simulation_environment(parameters)
        requests = [rq for group in sim.demand.future_requests.values() for rq in group.values()]
        initial_ids = [str(rq.rid) for rq in requests]
        if len(initial_ids) != len(set(initial_ids)) or not initial_ids:
            raise RuntimeError('Native fidelity demand is empty or duplicated')
        initial = [[op, vid, str(v.pos), float(v.soc)] for (op, vid), v in sorted(sim.sim_vehicles.items())]
        initial_hash = hashlib.sha256(json.dumps(initial, separators=(',', ':')).encode()).hexdigest()
        for operator in sim.operators:
            if getattr(operator, 'av_product', None) is not None or getattr(operator, 'driver_acceptance', None) is not None:
                raise RuntimeError('Fidelity profile unexpectedly enables a new product/acceptance model')
        accepted, rejected = {}, {}
        broker = sim.broker
        booking, leaving = broker.inform_user_booking, broker.inform_user_leaving_system

        def observe_booking(rid, request, time, operator):
            result = booking(rid, request, time, operator)
            accepted[str(rid)] = time
            return result

        def observe_leaving(rid, time):
            rejected[str(rid)] = time
            return leaving(rid, time)

        broker.inform_user_booking = observe_booking
        broker.inform_user_leaving_system = observe_leaving
        sim.run()
        for name in ['standard_eval.csv', '1_user-stats.csv', '2-0_op-stats.csv', 'final_state.csv']:
            if not (output / name).is_file():
                raise RuntimeError(f'Missing native fidelity output: {name}')
        users = pd.read_csv(output / '1_user-stats.csv', dtype={'request_id': str})
        completed = set(users.loc[users.dropoff_time.notna(), 'request_id'])
        if not users.request_id.is_unique or set(users.request_id) != set(initial_ids):
            raise RuntimeError('Native fidelity run lost or duplicated requests')
        if not users.pickup_time.notna().equals(users.dropoff_time.notna()) or completed != set(accepted):
            raise RuntimeError('Native fidelity run did not complete every accepted booking')
        if completed & set(rejected):
            raise RuntimeError('Native fidelity run served a terminally rejected request')
        remaining = sum(len(v.assigned_route) for v in sim.sim_vehicles.values())
        onboard = sum(len(v.pax) for v in sim.sim_vehicles.values())
        if remaining or onboard:
            raise RuntimeError('Native completion drain left tasks or passengers')
        imported = {name: str(Path(module.__file__).resolve()) for name, module in list(sys.modules.items())
                    if (name == 'src' or name.startswith('src.')) and getattr(module, '__file__', None)}
        if not imported or any(not Path(p).is_relative_to(root) for p in imported.values()):
            raise RuntimeError('Reference imported simulator code outside its source tree')
        runtime = {str(Path(p).relative_to(root)): digest(p) for p in imported.values()
                   if Path(p).suffix in ['.so', '.pyd']}
        write_json(output / 'fidelity_contract.json', dict(
            requests=len(users), completed=len(completed), accepted=accepted, rejected=rejected,
            initial_request_ids=sorted(initial_ids), initial_vehicle_positions_soc_sha256=initial_hash,
            initial_vehicle_count=len(initial), all_accepted_complete=True, terminal_rejected_service=0,
            remaining_tasks=remaining, onboard_passengers=onboard, imported_simulator_files=imported,
            imported_native_runtime_sha256=runtime, simulator_imports_confined_to_selected_source=True,
            effective_parameters=dict(parameters), profile_sha256=digest(args.profile)))
    finally:
        FleetSimulationBase.get_directory_dict = staticmethod(original)


if __name__ == '__main__':
    main()
