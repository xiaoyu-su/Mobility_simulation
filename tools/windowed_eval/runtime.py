"""Simulation state capture, continuation, and explicitly scoped policy replacement."""

import gzip
import importlib.metadata
import json
import logging
import math
from pathlib import Path
import random
import shutil
import sys

import numpy as np
import pandas as pd

from src.FleetSimulationBase import FleetSimulationBase,build_operator_attribute_dicts
from src.fleetctrl.acceptance.driver_acceptance import create_driver_acceptance
from src.fleetctrl.pooling.objectives import return_pooling_objective_function
from src.misc.globals import G_DIR_OUTPUT,G_OP_VR_CTRL_F
from src.misc.init_modules import load_simulation_environment
from src.misc.seeding import file_digest,canonical_digest
from tools.paired_eval.__main__ import source_record
from tools.windowed_eval.snapshot import dumps,loads
from tools.windowed_eval.metrics import cohort_observations,cohort_metrics,cohort_driver_credit


def dependencies():
    versions={}
    for name in ['numpy','pandas','scipy','pyyaml','gurobipy']:
        try:versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:versions[name]=None
    return versions


def attach_events(simulation):
    events={'accepted':{},'rejected':{}}
    broker=simulation.broker
    booking=type(broker).inform_user_booking
    leaving=type(broker).inform_user_leaving_system
    def accept(rid,request,time,operator):
        result=booking(broker,rid,request,time,operator)
        events['accepted'][rid]=time
        return result
    def reject(rid,time):
        events['rejected'][rid]=time
        return leaving(broker,rid,time)
    broker.inform_user_booking=accept
    broker.inform_user_leaving_system=reject
    return events


def build(parameters,output):
    output=Path(output)
    if output.exists():raise ValueError(f'Refusing to empty existing simulation output: {output}')
    original=FleetSimulationBase.get_directory_dict
    def directories(parameters,operators):
        return {**original(parameters,operators),G_DIR_OUTPUT:str(output)}
    FleetSimulationBase.get_directory_dict=staticmethod(directories)
    # Some subclasses log before base initialization installs their file handler.
    # Route those messages to the current baseline console, never the last seed.
    logging.basicConfig(stream=sys.stderr,level=logging.WARNING,force=True)
    try:return load_simulation_environment(parameters)
    finally:FleetSimulationBase.get_directory_dict=staticmethod(original)


def capture(simulation,requests,events,next_time,directory):
    directory=Path(directory);directory.mkdir(parents=True)
    simulation.record_stats(force=True)
    prefix=directory/'prefix';prefix.mkdir()
    for path in Path(simulation.dir_names[G_DIR_OUTPUT]).iterdir():
        if path.is_file() and path.suffix in ('.csv','.json'):
            shutil.copy2(path,prefix/path.name)
    envelope=dict(simulation=simulation,requests=requests,events=events,next_time=next_time,
                  numpy_state=np.random.get_state(),python_state=random.getstate())
    payload=gzip.compress(dumps(envelope),mtime=0)
    snapshot=directory/'state.pickle.gz';snapshot.write_bytes(payload)
    metadata=dict(format=1,next_time=next_time,python=list(sys.version_info[:3]),dependencies=dependencies(),source=source_record(),
                  snapshot_sha256=file_digest(snapshot),prefix_sha256={p.name:file_digest(p) for p in prefix.iterdir()},
                  request_ids_sha256=canonical_digest(sorted(str(rid) for rid in requests)))
    (directory/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return directory


def restore(directory):
    directory=Path(directory);metadata=json.loads((directory/'metadata.json').read_text())
    if metadata.get('format')!=1 or metadata['python']!=list(sys.version_info[:3]) or metadata['source']['code_digest']!=source_record()['code_digest'] or metadata['dependencies']!=dependencies():
        raise ValueError('Snapshot interpreter/source does not match the running code')
    if file_digest(directory/'state.pickle.gz')!=metadata['snapshot_sha256']:
        raise ValueError('Snapshot hash mismatch')
    for name,digest in metadata['prefix_sha256'].items():
        if file_digest(directory/'prefix'/name)!=digest:raise ValueError('Snapshot prefix hash mismatch')
    envelope=loads(gzip.decompress((directory/'state.pickle.gz').read_bytes()))
    np.random.set_state(envelope['numpy_state']);random.setstate(envelope['python_state'])
    return envelope,metadata


def retarget(simulation,output):
    output=Path(output)
    simulation.dir_names[G_DIR_OUTPUT]=str(output)
    simulation.user_stat_f=str(output/'1_user-stats.csv')
    simulation.network_stat_f=str(output/'3_network-stats.csv')
    simulation.pt_stat_f=str(output/'4_pt_stats.csv')
    simulation.demand.output_f=str(output/'1_user-stats.csv')
    simulation.log_file=str(output/'00_simulation.log')
    for op in simulation.operators:
        op.dir_names[G_DIR_OUTPUT]=str(output)
        op.dyn_fltctrl_output_f=str(output/f'3-{op.op_id}_op-dyn_atts.csv')
        op._additional_assignment_records_f=str(output/f'5-{op.op_id}_op-assignment_records.csv')
        acceptance=op.driver_acceptance
        if acceptance is None:continue
        acceptance.path=output/f'driver_acceptance_op_{op.op_id}.csv'
        for attribute,stem in [('choice','driver_choice'),('ranked_fallback','ranked_insertion'),('forbid_rematch','forbid_rematch')]:
            helper=getattr(acceptance,attribute,None)
            if helper is not None:
                helper.path=output/f'{stem}_op_{op.op_id}.csv';helper.audit_path=helper.path.with_suffix('.json')
        if acceptance.future_value is not None:
            acceptance.future_value.decisions_path=output/f'future_value_op_{op.op_id}.csv'
            acceptance.future_value.audit_path=acceptance.future_value.decisions_path.with_suffix('.json')


def swap_policy(simulation,parameters,output):
    old=simulation.operators[0].driver_acceptance
    attributes=build_operator_attribute_dicts(parameters,1)[0]
    simulation.scenario_parameters.update(parameters)
    simulation.scenario_name=parameters['scenario_name']
    simulation.list_op_dicts=[attributes]
    op=simulation.operators[0]
    current=create_driver_acceptance(attributes,simulation.scenario_parameters,0,op.sim_vehicles,output)
    if current is not None and old is not None:
        current.outcomes=old.outcomes;current.draws=old.draws;current.declines=old.declines
        if current.choice is not None and old.choice is not None:
            current.choice.owners=dict(old.choice.owners);current.choice.round=old.choice.round
        if current.ranked_fallback is not None and old.ranked_fallback is not None:
            current.ranked_fallback.results=dict(old.ranked_fallback.results)
    op.driver_acceptance=current
    objective=return_pooling_objective_function(attributes[G_OP_VR_CTRL_F])
    op.vr_ctrl_f=current.wrap_objective(objective) if current is not None else objective
    for plan in op.veh_plans.values():plan.set_utility(None)
    if hasattr(op,'RPBO_Module'):
        optimizer=op.RPBO_Module;optimizer.objective_function=op.vr_ctrl_f
        # Existing trip plans are re-evaluated by the native next-round update;
        # invalidate cached utilities without replaying legs or replacing tours.
        for trip in optimizer.rtv_obj.values():
            for plan in trip.veh_plans:plan.set_utility(None)
    simulation.save_scenario_inputs()


def advance(simulation,time):
    if time<simulation.end_time:
        simulation.step(time)
    else:
        simulation.update_sim_state_fleets(time-simulation.time_step,time)
        simulation.routing_engine.update_network(time+simulation.time_step,update_state=False)


def run_task(job):
    output=Path(job['output'])
    if output.exists():raise ValueError(f'Refusing to overwrite task output: {output}')
    output.mkdir(parents=True)
    envelope,metadata=restore(job['snapshot'])
    sim=envelope['simulation']
    if envelope['next_time']!=job['start'] or sim.scenario_parameters['random_seed']!=job['parameters']['random_seed']:
        raise ValueError('Job window/seed does not match its saved state')
    if not job['start']<job['end']<=job['horizon'] or (job['horizon']-job['start'])%sim.time_step:
        raise ValueError('Invalid window observation horizon')
    history=output/'inherited_history';shutil.copytree(Path(job['snapshot'])/'prefix',history)
    for path in history.iterdir():shutil.copy2(path,output/path.name)
    retarget(sim,output)
    logging.basicConfig(filename=str(output/'00_simulation.log'),level=logging.WARNING,force=True)
    changed=bool(job['policy_changed'])
    if changed:
        for stem in ['driver_acceptance','driver_choice','future_value','ranked_insertion','forbid_rematch']:
            for path in output.glob(stem+'_op_*'):
                if path.is_file():path.unlink()
        swap_policy(sim,job['parameters'],output)
    for time in range(envelope['next_time'],job['horizon'],sim.time_step):advance(sim,time)
    # Observe physical events before the cutoff without admitting requests or
    # making dispatch decisions at the excluded right endpoint.
    sim.update_sim_state_fleets(job['horizon']-sim.time_step,job['horizon'])
    sim.record_stats(force=True)
    state=pd.DataFrame([request.record_data() for request in envelope['requests'].values()])
    state.to_csv(output/'request_state.csv',index=False)
    rows=cohort_observations(envelope['requests'],envelope['events'],job['start'],job['end'],job['horizon'])
    rows.to_csv(output/'cohort_observations.csv',index=False)
    cohort_driver_credit(rows,pd.read_csv(output/'2_vehicle_types.csv')).to_csv(output/'cohort_drivers.csv',index=False)
    summary=cohort_metrics(rows)
    (output/'cohort_summary.json').write_text(json.dumps({k:v if math.isfinite(v) else None for k,v in summary.items()},indent=2,allow_nan=False)+'\n')
    pd.DataFrame([vehicle.return_final_state(job['horizon']) for vehicle in sim.sim_vehicles.values()]).to_csv(output/'window_final_state.csv',index=False)
    model=sim.operators[0].driver_acceptance
    actual=dict(acceptance=model is not None,
                choice=model.choice.mode if model is not None and model.choice is not None else 'off',
                ranked=model is not None and model.ranked_fallback is not None,
                rematch=model is not None and model.forbid_rematch is not None,
                future_value=model is not None and model.future_value is not None,
                weighted=model is not None and bool(model.weight_objective))
    (output/'window_state.json').write_text(json.dumps(dict(start=job['start'],end=job['end'],horizon=job['horizon'],
        snapshot_sha256=metadata['snapshot_sha256'],policy_changed=changed,source=source_record(),
        request_count=len(state),cohort_count=len(rows),active_policy=actual,
        operator_attributes=sim.list_op_dicts,cohort_request_ids_sha256=canonical_digest(rows.request_id.tolist())),indent=2)+'\n')
    return summary
