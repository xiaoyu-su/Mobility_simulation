"""Paired no-repositioning/HiGHS comparisons and honest calibration availability."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd

from src.misc.seeding import file_digest
from tools.paired_eval.__main__ import ROOT,source_record,validate_pair
from tools.paired_eval.metrics import per_driver_metrics,distribution_metrics,seed_summary
from tools.paired_eval.statistics import paired_statistics
from tools.synthetic_market.build import json_write
from tools.synthetic_market.worker import verify_bundle
from tools.synthetic_market.report import calibration_report


def experiment(args):
    output=args.output.resolve();bundle=args.bundle.resolve()
    if output.exists():raise ValueError('Refusing to overwrite market experiment')
    if not args.seeds or len(set(args.seeds))!=len(args.seeds) or any(not 0<=s<2**32 for s in args.seeds):
        raise ValueError('Seeds must be unique in 0..2**32-1')
    if args.timeout<=0:raise ValueError('Timeout must be positive')
    metadata=verify_bundle(bundle);output.mkdir(parents=True)
    manifest=dict(status='running',source=source_record(),bundle=str(bundle),bundle_sha256=file_digest(bundle/'manifest.json'),
        data_kind=metadata['data_kind'],seeds=args.seeds,runs=[],validated_pairs=[],reports=[],
        command=[sys.executable,'-m','tools.synthetic_market',*sys.argv[1:]])
    save=lambda:json_write(output/'manifest.json',manifest)
    save();summaries=[];drivers_all=[]
    try:
        for seed in args.seeds:
            audits={}
            for arm in ['no_repo','repo']:
                folder=output/'runs'/f'seed_{seed}';folder.mkdir(parents=True,exist_ok=True)
                run=folder/arm;log=folder/f'{arm}.txt'
                command=[sys.executable,'-m','tools.synthetic_market.worker','--bundle',str(bundle),
                    '--output',str(run),'--seed',str(seed),'--policy',arm]
                item=dict(seed=seed,arm=arm,output=str(run),log=str(log),command=command,status='running')
                manifest['runs'].append(item);save()
                environment=dict(os.environ,PYTHONHASHSEED='0',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
                                 MPLBACKEND='Agg',MPLCONFIGDIR=str(folder/'matplotlib'))
                with log.open('w') as stream:
                    result=subprocess.run(command,cwd=ROOT,env=environment,stdout=stream,stderr=subprocess.STDOUT,timeout=args.timeout)
                item.update(returncode=result.returncode,status='complete' if result.returncode==0 else 'failed');save()
                if result.returncode:raise RuntimeError(f'Market simulation failed: {log}')
                audits[arm]=json.loads((run/'random_streams.json').read_text())
                parameters=json.loads((bundle/'parameters.json').read_text())
                drivers=per_driver_metrics(run,clip_initial_inactivity=parameters.get('op_dyn_fs_method')=='TimeBasedFS')
                drivers_all.append(drivers.assign(seed=seed,arm=arm))
                summary=seed_summary(run,drivers,distribution_metrics(drivers))
                legs=pd.read_csv(run/'2-0_op-stats.csv') if (run/'2-0_op-stats.csv').exists() else pd.DataFrame(columns=['status','driven_distance'])
                summary['reposition_distance_m']=float(legs.loc[legs.status.eq('reposition'),'driven_distance'].sum())
                summary['out_of_service_legs']=float(legs.status.eq('out_of_service').sum())
                users=pd.read_csv(run/'1_user-stats.csv');report=calibration_report(bundle,users,drivers,run)
                # Completion/wait summaries refer to the evaluation cohort, costs to the full physical run.
                summary.update(completed_requests=report['completed'],completion_rate=report['completion_rate'],
                               pickup_wait_median_s=report['simulated_arrival_wait_median_s'])
                summaries.extend(dict(seed=seed,arm=arm,metric=k,value=v) for k,v in summary.items())
                manifest['reports'].append(dict(seed=seed,arm=arm,**report))
                if arm=='repo':
                    audit=json.loads((run/'repositioning_op_0.json').read_text())
                    item['repositioning_rounds']=len(audit['rounds']);item['repositioning_orders']=sum(len(r['flows']) for r in audit['rounds'])
            validate_pair(audits['no_repo'],audits['repo'])
            manifest['validated_pairs'].append(dict(seed=seed,input_audit=audits['no_repo']));save()
            print(f'seed {seed}: both complete; demand/network/fleet inputs match',flush=True)
        values=pd.DataFrame(summaries);values.to_csv(output/'seed_summary.csv',index=False)
        pd.concat(drivers_all,ignore_index=True).to_csv(output/'per_driver.csv',index=False)
        comparison=[]
        for metric in sorted(values.metric.unique()):
            selected=values[values.metric.eq(metric)]
            a=[selected.loc[selected.seed.eq(s)&selected.arm.eq('no_repo'),'value'].iloc[0] for s in args.seeds]
            b=[selected.loc[selected.seed.eq(s)&selected.arm.eq('repo'),'value'].iloc[0] for s in args.seeds]
            comparison.append(dict(metric=metric,**paired_statistics(a,b)))
        pd.DataFrame(comparison).to_csv(output/'paired_comparison.csv',index=False)
        json_write(output/'calibration_report.json',dict(data_kind=metadata['data_kind'],
            calibration_status='fixture_validation_only' if metadata['data_kind']=='fixture' else 'held_out_trip_comparison',
            accounting='Initial stationary inactive legs may be left-truncated at simulation start; raw activity is unchanged',
            assumptions=metadata['assumptions'],runs=manifest['reports']))
        if source_record()['code_digest']!=manifest['source']['code_digest']:raise RuntimeError('Source changed during market experiment')
        verify_bundle(bundle)
        manifest.update(status='complete',report_sha256={p.name:file_digest(p) for p in output.iterdir() if p.is_file() and p.name!='manifest.json'})
        save();print(f'Market experiment complete: {output}',flush=True)
    except BaseException as error:
        for run in manifest['runs']:
            if run['status']=='running':run['status']='failed'
        manifest.update(status='failed',error=f'{type(error).__name__}: {error}');save();raise
