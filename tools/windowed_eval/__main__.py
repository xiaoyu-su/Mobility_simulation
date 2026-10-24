"""Compare same-controller policy interventions from baseline boundary snapshots."""

import argparse
import contextlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

import pandas as pd

from src.misc.execution import validate_execution_settings
from src.FleetSimulationBase import build_operator_attribute_dicts
from src.fleetctrl.acceptance.driver_acceptance import create_driver_acceptance
from src.fleetctrl.pooling.objectives import return_pooling_objective_function
from src.misc.globals import G_OP_VR_CTRL_F
from src.misc.seeding import file_digest,STREAM_SCHEME
from tools.paired_eval.__main__ import ROOT,check_policy_pair,source_record
from tools.paired_eval.worker import load_parameters
from tools.paired_eval.statistics import paired_statistics
from tools.windowed_eval.metrics import cohort_observations
from tools.windowed_eval.pool import run_pool
from tools.windowed_eval.runtime import build,attach_events,capture,dependencies


def validate(parameters,window,cooldown,seeds,workers,timeout):
    if not seeds or len(set(seeds))!=len(seeds) or any(s<0 or s>=2**32 for s in seeds):
        raise ValueError('Seeds must be unique within 0..2**32-1')
    if workers<1 or timeout<=0:raise ValueError('Workers and timeout must be positive')
    a,b=parameters['baseline'],parameters['candidate'];check_policy_pair(a,b)
    if a['op_module']!=b['op_module']:raise ValueError('Window interventions currently require the same controller type')
    for key in set(a)|set(b):
        if a.get(key)!=b.get(key) and key not in ('scenario_name','op_vr_control_func_dict','op_driver_choice_model') and not key.startswith('op_driver_acceptance'):
            raise ValueError(f'Unsupported in-place policy change: {key}')
    for values in parameters.values():
        if values.get('network_type') not in ('NetworkBasic','NetworkBasicWithStore'):
            raise ValueError('Window snapshots currently support the two Python road routers')
        if values.get('rq_type')!='BasicRequest' or values.get('sim_env') not in ('ImmediateDecisionsSimulation','BatchOfferSimulation'):
            raise ValueError('Window evaluation requires BasicRequest baseline road simulations')
        if values.get('op_solver','Gurobi')!='Gurobi':raise ValueError('Window optimizer state currently supports Gurobi')
        if values.get('skip_file_writing',False):raise ValueError('Window evaluation requires output records')
        validate_execution_settings(values)
        # Validate the replacement policy before spending a full baseline run.
        attributes=build_operator_attribute_dicts(values,1)[0]
        model=create_driver_acceptance(attributes,dict(values,n_cpu_per_sim=1,skip_file_writing=True),0,[],None)
        objective=return_pooling_objective_function(attributes[G_OP_VR_CTRL_F])
        if model is not None:model.wrap_objective(objective)
    dt=a['time_step'];start,end=a['start_time'],a['end_time']
    if not all(isinstance(x,int) and not isinstance(x,bool) for x in [dt,start,end,window,cooldown]):
        raise ValueError('Window times and simulation grid must be integer seconds')
    if dt<=0 or end<=start or window<=0 or cooldown<0 or window%dt or cooldown%dt or (end-start)%dt:
        raise ValueError('Windows/cooldown must align with the positive simulation time grid')
    return [(index,t,min(t+window,end)) for index,t in enumerate(range(start,end,window))]


def normalized(parameters,seed,study,sigma):
    values=dict(parameters,random_seed=seed,random_stream_mode='independent',study_name=study,
                n_cpu_per_sim=1,evaluate=1,log_level='warning',show_progress_bar=False,keep_old=False,
                record_promised_times=True,bugfix=False)
    if sigma is not None:values['network_tt_noise_sigma']=sigma
    return values


def experiment(args):
    output=args.output.resolve()
    if output.exists():raise ValueError(f'Refusing to overwrite experiment: {output}')
    params={arm:load_parameters(args.constant_config,path) for arm,path in
            [('baseline',args.baseline_scenarios),('candidate',args.candidate_scenarios)]}
    for values in params.values():
        if args.network_tt_noise_sigma is not None:values['network_tt_noise_sigma']=args.network_tt_noise_sigma
    windows=validate(params,args.window_seconds,args.cooldown_seconds,args.seeds,args.workers,args.timeout)
    output.mkdir(parents=True);configs=output/'configs';configs.mkdir()
    for name,path in [('constants',args.constant_config),('baseline',args.baseline_scenarios),('candidate',args.candidate_scenarios)]:
        shutil.copy2(path,configs/(name+path.suffix))
    manifest=dict(status='running',scheme=STREAM_SCHEME,source=source_record(),dependencies=dependencies(),seeds=args.seeds,
                  windows=[dict(index=i,start=s,end=e) for i,s,e in windows],cooldown_seconds=args.cooldown_seconds,
                  workers=args.workers,n_cpu_per_sim=1,command=[sys.executable,'-m','tools.windowed_eval',*sys.argv[1:]],
                  runtime=dict(python=sys.version,executable=sys.executable,random_stream_mode='independent',
                      parent_environment={k:os.environ.get(k) for k in ['PYTHONHASHSEED','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']},
                      worker_environment=dict(PYTHONHASHSEED='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')),
                  config_sha256={p.name:file_digest(p) for p in configs.iterdir()},baselines=[],runs=[],validated_pairs=[])
    def save():
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    save();start_clock=time.monotonic()
    try:
        policy_changed=any(params['baseline'].get(k)!=params['candidate'].get(k) for k in
                           set(params['baseline'])|set(params['candidate']) if k!='scenario_name')
        for seed in args.seeds:
            folder=output/'baselines'/f'seed_{seed}';folder.mkdir(parents=True)
            baseline=normalized(params['baseline'],seed,args.constant_config.resolve().parent.parent.name,args.network_tt_noise_sigma)
            with (folder/'console.txt').open('w') as stream,contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
                sim=build(baseline,folder/'full_run');requests=dict(sim.demand);events=attach_events(sim)
                sim._started=True;snapshots={}
                for t in range(sim.start_time,sim.end_time,sim.time_step):
                    if any(t==s for _,s,_ in windows):
                        snapshots[t]=capture(sim,requests,events,t,folder/f'snapshot_{t}')
                    sim.step(t)
                sim.record_stats();sim.save_final_state();sim.record_remaining_assignments()
                sim.demand.record_remaining_users();sim.evaluate()
                pd.DataFrame([r.record_data() for r in requests.values()]).to_csv(folder/'full_request_state.csv',index=False)
                (folder/'events.json').write_text(json.dumps(events,indent=2)+'\n')
                for index,s,e in windows:
                    reference=cohort_observations(requests,events,s,e,e+args.cooldown_seconds)
                    reference.to_csv(folder/f'reference_{index}.csv',index=False)
                    for arm in ['baseline','candidate']:
                        taskdir=output/'tasks'/f'seed_{seed}'/f'window_{index}'/arm;taskdir.mkdir(parents=True)
                        job=dict(snapshot=str(snapshots[s]),output=str(taskdir/'run'),start=s,end=e,
                                 horizon=e+args.cooldown_seconds,policy_changed=arm=='candidate' and policy_changed,
                                 parameters=normalized(params[arm],seed,baseline['study_name'],args.network_tt_noise_sigma))
                        jobfile=taskdir/'job.json';jobfile.write_text(json.dumps(job,indent=2)+'\n')
                        manifest['runs'].append(dict(id=f'{seed}/{index}/{arm}',seed=seed,window=index,arm=arm,
                            job=str(jobfile),log=str(taskdir/'console.txt'),output=str(taskdir/'run'),status='pending'))
            manifest['baselines'].append(dict(seed=seed,directory=str(folder),snapshots=len(snapshots),
                                              full_run_sha256={p.name:file_digest(p) for p in (folder/'full_run').iterdir() if p.is_file()}))
            save();print(f'Seed {seed}: full baseline complete, {len(windows)} snapshots captured',flush=True)
        manifest['baseline_wall_seconds']=time.monotonic()-start_clock
        tasks_started=time.monotonic()
        manifest['maximum_active_workers']=run_pool(manifest['runs'],args.workers,args.timeout,save,ROOT)
        manifest['task_wall_seconds']=time.monotonic()-tasks_started
        # A restored world must never append into the full baseline's files.
        for baseline in manifest['baselines']:
            folder=Path(baseline['directory'])
            for name,digest in baseline['full_run_sha256'].items():
                if file_digest(folder/'full_run'/name)!=digest:
                    raise RuntimeError(f'Window task modified baseline output: {name}')
            for snapshot in folder.glob('snapshot_*'):
                metadata=json.loads((snapshot/'metadata.json').read_text())
                if file_digest(snapshot/'state.pickle.gz')!=metadata['snapshot_sha256']:
                    raise RuntimeError('Window task modified baseline snapshot')
                for name,digest in metadata['prefix_sha256'].items():
                    if file_digest(snapshot/'prefix'/name)!=digest:
                        raise RuntimeError('Window task modified snapshot history')
        summaries=[];cohorts={}
        for seed in args.seeds:
            cohorts[seed]={'baseline':set(),'candidate':set()}
            for index,s,e in windows:
                ids=[]
                for arm in ['baseline','candidate']:
                    root=output/'tasks'/f'seed_{seed}'/f'window_{index}'/arm/'run'
                    rows=pd.read_csv(root/'cohort_observations.csv',dtype={'request_id':str})
                    observed=set(rows.request_id)
                    state=json.loads((root/'window_state.json').read_text())
                    snapshot=json.loads((output/'baselines'/f'seed_{seed}'/f'snapshot_{s}'/'metadata.json').read_text())
                    if state['snapshot_sha256']!=snapshot['snapshot_sha256']:
                        raise ValueError('Window arms did not restore the declared baseline snapshot')
                    if observed & cohorts[seed][arm]:raise ValueError('A request belongs to multiple evaluated windows')
                    cohorts[seed][arm].update(observed);ids.append(observed)
                    if arm=='baseline':
                        reference=pd.read_csv(output/'baselines'/f'seed_{seed}'/f'reference_{index}.csv',dtype={'request_id':str})
                        pd.testing.assert_frame_equal(rows,reference,check_exact=True)
                    values=json.loads((root/'cohort_summary.json').read_text())
                    summaries.extend(dict(seed=seed,window=index,arm=arm,metric=k,value=v) for k,v in values.items())
                if ids[0]!=ids[1]:raise ValueError('Policy cohorts differ within a snapshot pair')
                manifest['validated_pairs'].append(dict(seed=seed,window=index,cohort_count=len(ids[0]),
                    snapshot_sha256=snapshot['snapshot_sha256'],baseline_matches_full_reference=True))
            expected=pd.read_csv(output/'baselines'/f'seed_{seed}'/'full_request_state.csv',dtype={'request_id':str})
            expected=set(expected.loc[expected.rq_time.ge(params['baseline']['start_time']) &
                expected.rq_time.lt(params['baseline']['end_time']),'request_id'])
            if cohorts[seed]['baseline']!=expected or cohorts[seed]['candidate']!=expected:
                raise ValueError('Windows do not account for every request in the configured interval')
        summary=pd.DataFrame(summaries);summary.to_csv(output/'seed_window_summary.csv',index=False)
        comparison=[]
        for index,s,e in windows:
            for metric in sorted(summary.metric.unique()):
                values=summary[(summary.window==index)&(summary.metric==metric)]
                a=[values[(values.seed==seed)&(values.arm=='baseline')].value.iloc[0] for seed in args.seeds]
                b=[values[(values.seed==seed)&(values.arm=='candidate')].value.iloc[0] for seed in args.seeds]
                comparison.append(dict(window=index,start=s,end=e,metric=metric,**paired_statistics(a,b)))
        pd.DataFrame(comparison).to_csv(output/'paired_window_comparison.csv',index=False)
        if source_record()['code_digest']!=manifest['source']['code_digest']:raise RuntimeError('Source changed during window evaluation')
        manifest.update(status='complete',wall_seconds=time.monotonic()-start_clock,
                        report_sha256={p.name:file_digest(p) for p in [output/'seed_window_summary.csv',output/'paired_window_comparison.csv']})
        save();print(f'Completed {len(manifest["runs"])} window runs; full-baseline reference checks passed. Reports: {output}',flush=True)
    except BaseException as error:
        manifest.update(status='failed',error=f'{type(error).__name__}: {error}');save();raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['constant-config','baseline-scenarios','candidate-scenarios','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--seeds',type=int,nargs='+',required=True)
    parser.add_argument('--window-seconds',type=int,default=1800)
    parser.add_argument('--cooldown-seconds',type=int,default=300)
    parser.add_argument('--workers',type=int,default=1)
    parser.add_argument('--timeout',type=int,default=180)
    parser.add_argument('--network-tt-noise-sigma',type=float)
    args=parser.parse_args()
    experiment(args)


if __name__=='__main__':main()
