"""Run matched-seed AV preference/repositioning policies with full physical tails."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pandas as pd

from src.misc.seeding import file_digest
from tools.paired_eval.__main__ import ROOT,source_record,validate_pair
from tools.paired_eval.metrics import per_driver_metrics
from tools.paired_eval.statistics import paired_statistics
from tools.synthetic_market.build import json_write
from tools.synthetic_market.worker import verify_bundle


def experiment(args):
    bundle,output=args.bundle.resolve(),args.output.resolve()
    if output.exists():raise ValueError('Refusing to overwrite AV experiment')
    if not args.seeds or len(set(args.seeds))!=len(args.seeds) or any(not 0<=s<2**32 for s in args.seeds):
        raise ValueError('AV seeds must be unique within 0..2**32-1')
    if args.timeout<=0:raise ValueError('AV worker timeout must be positive')
    if not args.preferences or len(set(args.preferences))!=len(args.preferences) or any(not -3600<=p<=3600 for p in args.preferences):
        raise ValueError('Unique finite AV preferences within +/-3600 seconds are required')
    if not args.repositioning or len(set(args.repositioning))!=len(args.repositioning):raise ValueError('Duplicate AV repositioning arms')
    metadata=verify_bundle(bundle)
    if 'av_product' not in metadata:raise ValueError('AV experiment requires a mixed-fleet bundle')
    output.mkdir(parents=True)
    record=dict(status='running',source=source_record(),bundle=str(bundle),bundle_manifest_sha256=file_digest(bundle/'manifest.json'),
                seeds=args.seeds,preferences=args.preferences,repositioning=args.repositioning,human_policy=args.human_policy,
                runs=[],validated_pairs=[],scope='Conditional model policy effects; adoption and fence are assumptions, not identified field effects')
    save=lambda:json_write(output/'manifest.json',record)
    save();rows=[];drivers=[]
    try:
        for seed in args.seeds:
            first=None
            for repo in args.repositioning:
                for preference in args.preferences:
                    arm=f'preference_{preference:g}_{repo}'
                    run=output/'runs'/f'seed_{seed}'/arm;run.parent.mkdir(parents=True,exist_ok=True)
                    log=run.with_suffix('.txt')
                    command=[sys.executable,'-m','tools.synthetic_market.worker','--bundle',str(bundle),'--output',str(run),
                             '--seed',str(seed),'--policy',args.human_policy,'--av-preference-seconds',str(preference),'--av-repositioning',repo]
                    item=dict(seed=seed,arm=arm,preference_seconds=preference,av_repositioning=repo,command=command,
                              output=str(run),log=str(log),status='running');record['runs'].append(item);save()
                    env=dict(os.environ,PYTHONHASHSEED='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
                             MPLBACKEND='Agg',MPLCONFIGDIR=str(run.parent/'matplotlib'))
                    begin=time.monotonic()
                    with log.open('w') as stream:
                        result=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=args.timeout)
                    item.update(returncode=result.returncode,wall_seconds=time.monotonic()-begin,status='complete' if result.returncode==0 else 'failed');save()
                    if result.returncode:raise RuntimeError(f'AV simulation failed: {log}')
                    audit=json.loads((run/'random_streams.json').read_text())
                    if first is None:first=audit
                    else:
                        validate_pair(first,audit)
                        record['validated_pairs'].append(dict(seed=seed,arm=arm,matching_demand_network_and_initial_fleet=True))
                    report=json.loads((run/'av_report.json').read_text())
                    rows.append(dict(seed=seed,arm=arm,**report))
                    config=json.loads((bundle/'parameters.json').read_text())
                    frame=per_driver_metrics(run,clip_initial_inactivity=config.get('op_dyn_fs_method')=='TimeBasedFS')
                    drivers.append(frame.assign(seed=seed,arm=arm))
                    pd.DataFrame(rows).to_csv(output/'seed_summary.csv',index=False)
                    print(f'seed {seed} {arm}: {report["completed"]} completed, {report["av_completed"]} AV, zero rule violations',flush=True)
        summary=pd.DataFrame(rows);pd.concat(drivers,ignore_index=True).to_csv(output/'per_driver.csv',index=False)
        comparisons=[];baseline=summary[summary.preference_seconds.eq(0)&~summary.av_repositioning]
        if len(baseline)==len(args.seeds):
            for arm in summary.arm.unique():
                candidate=summary[summary.arm.eq(arm)].set_index('seed')
                for metric in ['completed','av_completed','human_completed','eligible_arrival_wait_mean_s','other_arrival_wait_mean_s',
                               'av_utilization','av_idle_share','human_trips_per_online_hour','av_reposition_distance_km',
                               'human_won_while_idle_av_closer']:
                    a=baseline.set_index('seed').loc[args.seeds,metric].tolist();b=candidate.loc[args.seeds,metric].tolist()
                    if any(pd.isna(v) for v in a+b):continue
                    comparisons.append(dict(arm=arm,metric=metric,**paired_statistics(a,b)))
        pd.DataFrame(comparisons).to_csv(output/'paired_comparison.csv',index=False)
        verify_bundle(bundle)
        if source_record()['code_digest']!=record['source']['code_digest']:raise RuntimeError('Source changed during AV experiment')
        record.update(status='complete',report_sha256={p.name:file_digest(p) for p in output.iterdir() if p.is_file() and p.name!='manifest.json'})
        save()
    except BaseException as error:
        for item in record['runs']:
            if item['status']=='running':item['status']='failed'
        record.update(status='failed',error=f'{type(error).__name__}: {error}');save();raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seeds',type=int,nargs='+',required=True)
    parser.add_argument('--preferences',type=float,nargs='+',default=[-300,0,300])
    parser.add_argument('--repositioning',choices=['off','demand'],nargs='+',default=['off','demand'])
    parser.add_argument('--human-policy',choices=['no_repo','repo'],default='repo')
    parser.add_argument('--timeout',type=int,default=3600)
    experiment(parser.parse_args())


if __name__=='__main__':main()
