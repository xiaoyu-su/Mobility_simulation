"""One ordinary complete FleetPy simulation using a private market input bundle."""

import argparse
import json
from pathlib import Path

import pandas as pd

from src.FleetSimulationBase import FleetSimulationBase
from src.misc.init_modules import load_simulation_environment
from src.misc.globals import G_DIR_NETWORK,G_DIR_DEMAND,G_DIR_FCTRL,G_DIR_ZONES,G_DIR_FC,G_DIR_INFRA,G_DIR_OUTPUT,G_DIR_VEH
from src.misc.seeding import file_digest
from tools.paired_eval.__main__ import source_record, ROOT
from tools.windowed_eval.runtime import attach_events
from tools.synthetic_market.build import market_dependencies
from tools.synthetic_market.report import request_ids,activity_frame


def verify_bundle(bundle):
    bundle=Path(bundle);manifest=json.loads((bundle/'manifest.json').read_text())
    if manifest['status']!='complete':raise ValueError('Market bundle is incomplete')
    if source_record()['code_digest']!=manifest['source']['code_digest']:
        raise ValueError('Market bundle source changed; rebuild from the recorded inputs')
    if market_dependencies()!=manifest['dependencies']:
        raise ValueError('Market bundle dependency versions changed; rebuild inputs')
    for name,digest in manifest.get('runtime_files_sha256',{}).items():
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or file_digest(path)!=digest:
            raise ValueError(f'City routing runtime changed: {name}; rebuild inputs')
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
    parser.add_argument('--av-preference-seconds',type=float)
    parser.add_argument('--av-repositioning',choices=['off','demand'])
    parser.add_argument('--av-eta-threshold-seconds')
    parser.add_argument('--av-travel-time-factor',type=float)
    parser.add_argument('--av-opt-in-share',type=float)
    parser.add_argument('--av-retarget',choices=['off','on'])
    parser.add_argument('--av-forecast-noise-sigma',type=float)
    parser.add_argument('--av-joint-repositioning',choices=['off','on'])
    parser.add_argument('--av-repositioning-timestep',type=int)
    parser.add_argument('--av-separate-search',choices=['off','on'])
    parser.add_argument('--av-service-priority',choices=['off','on'])
    parser.add_argument('--city-shared-placement',action='store_true')
    parser.add_argument('--all-human',action='store_true')
    args=parser.parse_args();bundle=args.bundle.resolve();output=args.output.resolve()
    if output.exists():raise ValueError('Refusing to overwrite market simulation output')
    manifest=verify_bundle(bundle)
    if (args.city_shared_placement or args.all_human) and manifest.get('shared_initialization')!='city-av-placement-v1':
        raise ValueError('City controls require a declared shared-placement bundle')
    if args.all_human and not args.city_shared_placement:
        raise ValueError('Human control requires matching city initial placement')
    parameters=json.loads((bundle/'parameters.json').read_text())
    parameters.update(random_seed=args.seed,scenario_name=f'market_{args.policy}_{args.seed}',
        evaluate=1,keep_old=False,show_progress_bar=False,log_level='warning',bugfix=False)
    if args.policy=='repo':parameters['op_repo_method']='PavoneFCHiGHS'
    av_overrides={k:v for k,v in vars(args).items() if k.startswith('av_') and v is not None}
    if av_overrides:
        if not parameters.get('op_av_vehicle_types'):raise ValueError('AV policy overrides require an AV input bundle')
        if args.av_preference_seconds is not None:parameters['op_av_preference_s']=args.av_preference_seconds
        if args.av_repositioning is not None:parameters['op_av_repositioning']=args.av_repositioning=='demand'
        if args.av_eta_threshold_seconds is not None:
            parameters['op_av_eta_threshold_s']=None if args.av_eta_threshold_seconds=='off' else float(args.av_eta_threshold_seconds)
        if args.av_travel_time_factor is not None:parameters['vehicle_travel_time_factors']={'av_vehtype':args.av_travel_time_factor}
        if args.av_opt_in_share is not None:parameters['op_av_opt_in_share']=args.av_opt_in_share
        if args.av_retarget is not None:parameters['op_av_retarget']=args.av_retarget=='on'
        if args.av_forecast_noise_sigma is not None:parameters['op_av_forecast_sigma']=args.av_forecast_noise_sigma
        if args.av_joint_repositioning is not None:parameters['op_av_joint_repositioning']=args.av_joint_repositioning=='on'
        if args.av_repositioning_timestep is not None:parameters['op_av_repositioning_timestep']=args.av_repositioning_timestep
        if args.av_separate_search is not None:parameters['op_av_separate_search']=args.av_separate_search=='on'
        if args.av_service_priority is not None:parameters['op_av_service_priority']=args.av_service_priority=='on'
    if args.all_human:
        if av_overrides:raise ValueError('Human-only control cannot have AV policy overrides')
        for key in list(parameters):
            if key.startswith('op_av_') or key=='vehicle_travel_time_factors':parameters.pop(key)
        parameters['op_fleet_composition']={'default_vehtype':manifest['fleet_size']}
    original=FleetSimulationBase.get_directory_dict
    original_initialization=FleetSimulationBase.load_initial_state
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
    if args.city_shared_placement:
        from tools.city_av.initialization import initialize_shared
        FleetSimulationBase.load_initial_state=lambda simulation:initialize_shared(simulation,bundle,manifest)
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
    finally:
        FleetSimulationBase.get_directory_dict=staticmethod(original)
        FleetSimulationBase.load_initial_state=original_initialization
    for name in ['final_state.csv','standard_eval.csv','1_user-stats.csv','random_streams.json']:
        if not (output/name).is_file():raise RuntimeError(f'Missing complete simulation output: {name}')
    users=pd.read_csv(output/'1_user-stats.csv')
    if len(users)!=manifest['target_count'] or not users.request_id.is_unique:
        raise RuntimeError('Market simulation does not account for the full unique request cohort')
    if not users.pickup_time.notna().equals(users.dropoff_time.notna()):
        raise RuntimeError('Market simulation did not complete picked-up bookings')
    if set(events['accepted'])!=set(users.loc[users.dropoff_time.notna(),'request_id']):
        raise RuntimeError('Market simulation did not complete every accepted booking')
    observed=pd.read_csv(bundle/'observed_cohort.csv').set_index('request_id')
    indexed=users.set_index('request_id')
    if (indexed.pickup_time-observed.request_s).lt(-1e-7).any():raise RuntimeError('Pickup before source request')
    legs=activity_frame(output)
    pooled=set()
    for row in legs[legs.status.eq('route')&legs.occupancy.ge(2)].itertuples():pooled.update(request_ids(row.rq_on_board))
    private=set(demand.index[demand.pooling_allowed.eq(0)])
    if private&pooled:raise RuntimeError('Private requests were pooled')
    for _,group in legs.groupby('vehicle_id'):
        group=group.sort_values(['start_time','end_time'])
        if (group.end_time<group.start_time-1e-7).any() or (group.start_time.to_numpy()[1:]<group.end_time.to_numpy()[:-1]-1e-7).any():
            raise RuntimeError('Nonchronological market vehicle activity')
    tail=json.loads((output/'completion_tail.json').read_text())
    if tail['status']!='complete':raise RuntimeError('Incomplete physical tail')
    (output/'market_input_contract.json').write_text(json.dumps(dict(requests=len(requests),patience_loaded_for_all=True,
        booked_requests=len(events['accepted']),completed_requests=int(users.dropoff_time.notna().sum()),
        all_booked_requests_completed=True,early_pickups=0,private_requests=len(private),
        private_pooling_violations=0,chronological_activity=True,physical_tail_complete=True),indent=2)+'\n')
    if parameters.get('op_av_vehicle_types'):
        from tools.synthetic_market.av_report import av_report
        av_report(bundle,output)
    verify_bundle(bundle)


if __name__=='__main__':main()
