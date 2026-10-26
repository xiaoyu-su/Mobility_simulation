"""Thread-capped isolated city workers with matched-input and physical checks."""

from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

import pandas as pd

from src.misc.seeding import file_digest, STREAM_SCHEME
from tools.av_eval.__main__ import policy_profiles
from tools.city_av.report import city_report
from tools.paired_eval.__main__ import ROOT, source_record, validate_pair
from tools.synthetic_market.build import json_write
from tools.synthetic_market.worker import verify_bundle


def validate_city_pair(first, second):
    """Hold demand/network/geometry/SOC fixed; vehicle-type replacement is explicit."""
    for field in ['city','fleet_size','shared_placement_sha256']:
        if first[field]!=second[field]:raise ValueError(f'City pair differs in {field}')
    a,b=first['random_audit'],second['random_audit']
    for field in ['scheme','mode','master_seed','demand','network_input_sha256','initial_vehicle_count']:
        if a[field]!=b[field]:raise ValueError(f'City pair differs in {field}')
    if a['mode']!='independent' or a['scheme']!=STREAM_SCHEME:raise ValueError('City pairs need independent named streams')
    if first['av_count']==second['av_count']:validate_pair(a,b)


def experiment(args):
    output=args.output.resolve()
    if output.exists():raise ValueError('Refusing to overwrite city experiment')
    if not args.seeds or len(set(args.seeds))!=len(args.seeds) or any(type(s) is not int or not 0<=s<2**32 for s in args.seeds):raise ValueError('Invalid/duplicate city seeds')
    if not 1<=args.workers<=4 or args.timeout<=0:raise ValueError('City workers must be1..4 and timeout positive')
    policy_hash=file_digest(args.policies)
    policies=policy_profiles(SimpleNamespace(policy_grid=args.policies))
    for p in policies:
        if p['av_repositioning']!='off' or any(k in p for k in ['opt_in_share','retarget','forecast_noise_sigma','joint_repositioning','repositioning_timestep']):
            raise ValueError('City core grid varies only threshold, preference and type factor; repositioning stays off')
        if p['name']=='all_human':raise ValueError('all_human is reserved for the matched fleet control')
    policies=[dict(name='all_human',all_human=True),*policies]
    bundles={}
    for path in args.bundles:
        path=path.resolve();meta=verify_bundle(path)
        if meta.get('shared_initialization')!='city-av-placement-v1':raise ValueError('Not a city shared-placement bundle')
        if meta['city'] in bundles:raise ValueError('Duplicate city in experiment')
        bundles[meta['city']]=(path,meta)
    output.mkdir(parents=True)
    shutil.copyfile(args.policies,output/'policy_grid.json')
    if file_digest(output/'policy_grid.json')!=policy_hash:raise ValueError('Policy input changed during snapshot')
    cpus=sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') and shutil.which('taskset') else []
    source=source_record();record=dict(status='running',started_utc=datetime.now(timezone.utc).isoformat(),source=source,
        policies=policies,policy_grid_sha256=policy_hash,seeds=args.seeds,workers=args.workers,
        bundles={city:dict(path=str(path),manifest_sha256=file_digest(path/'manifest.json')) for city,(path,_) in bundles.items()},
        thread_environment=dict(PYTHONHASHSEED='0',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'),
        cpu_pinning='one permitted logical CPU per worker command' if cpus else 'unavailable; BLAS/OMP threads still capped',
        runs=[],validated_pairs=[],scope='Within-city policy transfer at fixed source demand and fleet; cities/source years/load regimes differ')
    save=lambda:json_write(output/'manifest.json',record)
    jobs=[]
    for city,(bundle,meta) in bundles.items():
        for seed in args.seeds:
            for policy in policies:
                name=policy['name'];folder=output/'runs'/city/f'seed_{seed}'/name;folder.parent.mkdir(parents=True,exist_ok=True)
                command=[sys.executable,'-m','tools.synthetic_market.worker','--bundle',str(bundle),'--output',str(folder),
                         '--seed',str(seed),'--policy','no_repo','--city-shared-placement']
                if policy.get('all_human'):command.append('--all-human')
                else:
                    command.extend(['--av-separate-search','on','--av-repositioning','off','--av-preference-seconds',str(policy['preference_seconds'])])
                    for key,flag in [('eta_threshold_seconds','--av-eta-threshold-seconds'),('travel_time_factor','--av-travel-time-factor')]:
                        if key in policy:command.extend([flag,'off' if policy[key] is None else str(policy[key])])
                entry=dict(city=city,seed=seed,arm=name,output=str(folder),log=str(folder.with_suffix('.txt')),command=command,
                           cpu=None,status='pending');record['runs'].append(entry);jobs.append(entry)
    save()
    def run(entry):
        env=dict(os.environ,**record['thread_environment'],MPLBACKEND='Agg',MPLCONFIGDIR=str(Path(entry['output']).parent/'matplotlib'))
        start=time.monotonic()
        with open(entry['log'],'w') as stream:
            result=subprocess.run(entry['command'],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=args.timeout)
        if result.returncode:raise RuntimeError(f"City worker exit{result.returncode}: {entry['log']}")
        report=city_report(bundles[entry['city']][0],entry['output'])
        return report,time.monotonic()-start
    rows=[];pair_records={};type_records={}
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            pending=iter(jobs);futures={}
            def submit(cpu):
                entry=next(pending,None)
                if entry is None:return
                entry.update(cpu=cpu,status='running')
                if cpu is not None:entry['command']=['taskset','-c',str(cpu),*entry['command']]
                futures[pool.submit(run,entry)]=entry
            for index in range(args.workers):submit(cpus[index%len(cpus)] if cpus else None)
            save()
            while futures:
                done,_=wait(futures,return_when=FIRST_COMPLETED)
                for future in done:
                    entry=futures.pop(future)
                    try:report,elapsed=future.result()
                    except BaseException as error:
                        entry.update(status='failed',error=f'{type(error).__name__}: {error}');save();raise
                    entry.update(status='complete',returncode=0,wall_seconds=elapsed)
                    folder=Path(entry['output']);audit=json.loads((folder/'random_streams.json').read_text())
                    entry['output_sha256']={p.name:file_digest(p) for p in folder.iterdir() if p.is_file()}
                    key=(entry['city'],entry['seed'])
                    pair=dict(city=entry['city'],fleet_size=report['fleet_size'],av_count=report['av_count'],
                              shared_placement_sha256=report['shared_placement_sha256'],random_audit=audit)
                    if key in pair_records:
                        validate_city_pair(pair_records[key],pair)
                        record['validated_pairs'].append(dict(city=entry['city'],seed=entry['seed'],arm=entry['arm'],matching_geometry_soc_demand_network=True))
                    else:pair_records[key]=pair
                    type_key=(*key,report['av_count'])
                    if type_key in type_records:validate_pair(type_records[type_key],audit)
                    else:type_records[type_key]=audit
                    rows.append(dict(seed=entry['seed'],arm=entry['arm'],**report))
                    pd.DataFrame(rows).sort_values(['city','seed','arm']).to_csv(output/'seed_results.csv',index=False)
                    submit(entry['cpu'])
                    save();print(f"{entry['city']} seed{entry['seed']} {entry['arm']}: {report['completed']} completed, {report['av_completed']} AV; checks pass",flush=True)
        for bundle,_ in bundles.values():verify_bundle(bundle)
        if file_digest(args.policies)!=policy_hash:raise RuntimeError('City policy grid changed during execution')
        if source_record()['code_digest']!=source['code_digest']:raise RuntimeError('Source changed during city experiment')
        record.update(status='complete',output_sha256={p.name:file_digest(p) for p in output.iterdir() if p.is_file() and p.name!='manifest.json'})
        save();return record
    except BaseException as error:
        record.update(status='failed',error=f'{type(error).__name__}: {error}')
        for entry in jobs:
            if entry['status']=='running':entry['status']='uncollected_after_failure'
            if entry['status']=='pending':entry['status']='not_run_after_failure'
        save();raise
