"""One ordinary complete FleetPy simulation using a private market input bundle."""

import argparse
import json
from pathlib import Path

import pandas as pd

from src.FleetSimulationBase import FleetSimulationBase
from src.misc.init_modules import load_simulation_environment
from src.misc.globals import G_DIR_NETWORK,G_DIR_DEMAND,G_DIR_FCTRL,G_DIR_ZONES,G_DIR_FC,G_DIR_INFRA,G_DIR_OUTPUT,G_DIR_VEH
from src.misc.seeding import file_digest
from tools.paired_eval.__main__ import source_record
from tools.windowed_eval.runtime import attach_events
from tools.synthetic_market.build import market_dependencies


def verify_bundle(bundle):
    bundle=Path(bundle);manifest=json.loads((bundle/'manifest.json').read_text())
    if manifest['status']!='complete':raise ValueError('Market bundle is incomplete')
    if source_record()['code_digest']!=manifest['source']['code_digest']:
        raise ValueError('Market bundle source changed; rebuild from the recorded inputs')
    if market_dependencies()!=manifest['dependencies']:
        raise ValueError('Market bundle dependency versions changed; rebuild inputs')
    for name,digest in manifest['output_sha256'].items():
        path=(bundle/name).resolve()
        if not path.is_relative_to(bundle.resolve()):raise ValueError('Market input path escapes its bundle')
        if file_digest(path)!=digest:raise ValueError(f'Market input hash mismatch: {name}')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--policy',choices=['no_repo','repo'],required=True)
    args=parser.parse_args();bundle=args.bundle.resolve();output=args.output.resolve()
    if output.exists():raise ValueError('Refusing to overwrite market simulation output')
    manifest=verify_bundle(bundle)
    parameters=json.loads((bundle/'parameters.json').read_text())
    parameters.update(random_seed=args.seed,scenario_name=f'market_{args.policy}_{args.seed}',
        evaluate=1,keep_old=False,show_progress_bar=False,log_level='warning',bugfix=False)
    if args.policy=='repo':parameters['op_repo_method']='PavoneFCHiGHS'
    original=FleetSimulationBase.get_directory_dict
    def private_inputs(parameters,operators):
        result=original(parameters,operators)
        result.update({G_DIR_NETWORK:str(bundle/'network'),G_DIR_DEMAND:str(bundle/'demand'),
            G_DIR_VEH:str(bundle/'vehicles'),
            G_DIR_FCTRL:str(bundle/'fleetctrl'),G_DIR_ZONES:str(bundle/'zones/network'),
            G_DIR_INFRA:str(bundle/'infra'),G_DIR_OUTPUT:str(output)})
        result['op_0']={**result.get('op_0',{}),G_DIR_ZONES:str(bundle/'zones/network'),
                        G_DIR_FC:str(bundle/'forecasts'/str(parameters['op_temporal_resolution']))}
        return result
    FleetSimulationBase.get_directory_dict=staticmethod(private_inputs)
    try:
        sim=load_simulation_environment(parameters)
        demand=pd.read_csv(bundle/'demand/requests.csv').set_index('request_id')
        requests=dict(sim.demand)
        if set(requests)!=set(demand.index):raise RuntimeError('Market loader changed request identities')
        for rid,request in requests.items():
            if request.latest_start_time!=demand.loc[rid,'latest_start_time']:
                raise RuntimeError('Market patience was dropped by the traveler loader')
        events=attach_events(sim)
        sim.run()
    finally:FleetSimulationBase.get_directory_dict=staticmethod(original)
    for name in ['final_state.csv','standard_eval.csv','1_user-stats.csv','random_streams.json']:
        if not (output/name).is_file():raise RuntimeError(f'Missing complete simulation output: {name}')
    users=pd.read_csv(output/'1_user-stats.csv')
    if len(users)!=manifest['target_count'] or not users.request_id.is_unique:
        raise RuntimeError('Market simulation does not account for the full unique request cohort')
    if not users.pickup_time.notna().equals(users.dropoff_time.notna()):
        raise RuntimeError('Market simulation did not complete picked-up bookings')
    if set(events['accepted'])!=set(users.loc[users.dropoff_time.notna(),'request_id']):
        raise RuntimeError('Market simulation did not complete every accepted booking')
    (output/'market_input_contract.json').write_text(json.dumps(dict(requests=len(requests),patience_loaded_for_all=True,
        booked_requests=len(events['accepted']),completed_requests=int(users.dropoff_time.notna().sum()),
        all_booked_requests_completed=True),indent=2)+'\n')
    verify_bundle(bundle)


if __name__=='__main__':main()
