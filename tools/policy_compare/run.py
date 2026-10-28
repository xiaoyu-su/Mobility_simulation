"""Multi-policy orchestration over the already validated paired runner."""
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace
from src.misc.seeding import canonical_digest,file_digest
from tools.paired_eval.__main__ import ROOT,source_record,check_policy_pair,run_experiment
from tools.paired_eval.worker import load_parameters
from tools.synthetic_market.build import json_write


def parse_spec(path):
    path=Path(path).resolve();spec=json.loads(path.read_text())
    allowed={'schema_version','name','constant_config','reference','policies','seeds','timeout','network_tt_noise_sigma'}
    required={'schema_version','name','constant_config','reference','policies','seeds'}
    if not isinstance(spec,dict) or set(spec)-allowed or not required<=set(spec) or spec.get('schema_version')!=1:raise ValueError('Unknown comparison fields/version')
    if not isinstance(spec['policies'],list) or not isinstance(spec['reference'],dict) or not isinstance(spec['seeds'],list) or not isinstance(spec['name'],str) or not spec['name'].strip():raise ValueError('Invalid comparison specification types')
    policies=[spec['reference'],*spec['policies']]
    if not spec['policies']:raise ValueError('At least one candidate policy is required')
    names=[]
    for p in policies:
        if not isinstance(p,dict) or set(p)!={'name','scenario'} or not isinstance(p.get('name'),str) or not isinstance(p.get('scenario'),str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',p['name']):raise ValueError('Invalid policy name or scenario fields')
        names.append(p['name']);p['scenario']=str((path.parent/p['scenario']).resolve())
    if len(set(names))!=len(names):raise ValueError('Policy names must be unique')
    seeds=spec['seeds']
    if not seeds or len(set(seeds))!=len(seeds) or any(type(s) is not int or not 0<=s<2**32 for s in seeds):raise ValueError('Seeds must be unique supported integers')
    spec['constant_config']=str((path.parent/spec['constant_config']).resolve());spec.setdefault('timeout',3600)
    if type(spec['timeout']) is not int or spec['timeout']<=0:raise ValueError('Positive timeout required')
    sigma=spec.get('network_tt_noise_sigma')
    if sigma is not None and (isinstance(sigma,bool) or not isinstance(sigma,(int,float)) or not math.isfinite(sigma) or sigma<0):raise ValueError('Noise sigma must be finite and nonnegative')
    base=load_parameters(spec['constant_config'],spec['reference']['scenario'])
    for p in spec['policies']:check_policy_pair(base,load_parameters(spec['constant_config'],p['scenario']))
    return spec


def run(spec_path,output):
    spec_path=Path(spec_path).resolve();output=Path(output).resolve()
    if output.exists():raise ValueError('Refusing to overwrite comparison output')
    spec=parse_spec(spec_path);source=source_record();inputs={str(spec_path):file_digest(spec_path)}
    paths=[Path(spec['constant_config'])]+[Path(p['scenario']) for p in [spec['reference'],*spec['policies']]]
    for p in paths:inputs[str(p)]=file_digest(p)
    costs={str(p.resolve()):file_digest(p) for p in (ROOT/'data/vehicles').glob('*.csv')}
    if not costs:raise ValueError('No bound vehicle specifications')
    output.mkdir(parents=True);(output/'configs').mkdir();json_write(output/'configs/spec.json',spec)
    shutil.copyfile(spec['constant_config'],output/'configs'/('constants'+Path(spec['constant_config']).suffix))
    for policy in [spec['reference'],*spec['policies']]:shutil.copyfile(policy['scenario'],output/'configs'/(policy['name']+Path(policy['scenario']).suffix))
    (output/'vehicle_specs').mkdir()
    for path in costs:shutil.copyfile(path,output/'vehicle_specs'/Path(path).name)
    m=dict(schema_version=1,kind='policy_comparison_v1',status='running',source=source,name=spec['name'],reference=spec['reference']['name'],seeds=spec['seeds'],input_sha256=inputs,cost_files_sha256={Path(p).name:h for p,h in costs.items()},configuration_sha256={p.name:file_digest(p) for p in (output/'configs').iterdir()},runs=[],children=[],policy_differences={},runtime=dict(n_cpu_per_sim=1,random_stream_mode='independent',record_promised_times=True),scope='Matched conditional full-run policy effects; no empirical calibration or automatic policy ranking')
    save=lambda:json_write(output/'manifest.json',m);save()
    base=load_parameters(spec['constant_config'],spec['reference']['scenario']);context=dict(reference_name=spec['reference']['name'],reference_parameters={k:v for k,v in base.items() if k not in ['scenario_name','random_seed']},execution_noise_sigma=spec.get('network_tt_noise_sigma',base.get('network_tt_noise_sigma',0)),cost_files=m['cost_files_sha256'],source=source['code_digest']);background=None
    try:
        for candidate in spec['policies']:
            params=load_parameters(spec['constant_config'],candidate['scenario']);m['policy_differences'][candidate['name']]={k:dict(reference=base.get(k),candidate=params.get(k)) for k in sorted(set(base)|set(params)) if base.get(k)!=params.get(k) and k!='scenario_name'}
            child=output/'paired'/candidate['name'];start=time.monotonic()
            args=SimpleNamespace(constant_config=Path(spec['constant_config']),baseline_scenarios=Path(spec['reference']['scenario']),candidate_scenarios=Path(candidate['scenario']),seeds=spec['seeds'],output=child,timeout=spec['timeout'],network_tt_noise_sigma=spec.get('network_tt_noise_sigma'),record_promised_times=True)
            run_experiment(args);cm=json.loads((child/'manifest.json').read_text())
            for entry in cm['runs']:
                folder=child/entry['directory'];arm=spec['reference']['name'] if entry['arm']=='baseline' else candidate['name']
                audit=json.loads((folder/'random_streams.json').read_text());loaded=dict(demand_sources={k:v['source_sha256'] for k,v in audit['demand'].items()},network_input_sha256=audit['network_input_sha256'],initial_vehicle_count=audit['initial_vehicle_count'])
                if background is not None and loaded!=background:raise ValueError('Comparison changes physical background inputs across seeds/policies')
                background=loaded;m['comparison_contract']=dict(**context,physical_background=background);m['comparison_context']=canonical_digest(m['comparison_contract'])
                m['runs'].append(dict(seed=entry['seed'],arm=arm,directory=str(folder.relative_to(output)),status='complete',returncode=entry['returncode'],output_sha256={p.name:file_digest(p) for p in folder.iterdir() if p.is_file()}))
            m['children'].append(dict(directory=str(child.relative_to(output)),manifest_sha256=file_digest(child/'manifest.json'),wall_seconds=time.monotonic()-start));save()
            if any(file_digest(Path(p))!=h for p,h in {**inputs,**costs}.items()):raise ValueError('Scenario, cost or physical input changed during comparison')
        if source_record()['code_digest']!=source['code_digest']:raise ValueError('Comparison source changed during execution')
        m['status']='complete';save()
        from tools.policy_compare.report import report
        report([output],output/'report',reference=spec['reference']['name'])
        json_write(output/'report_receipt.json',dict(experiment_manifest_sha256=file_digest(output/'manifest.json'),analysis_manifest_sha256=file_digest(output/'report/manifest.json')))
    except BaseException as e:
        m.update(status='failed',error=f'{type(e).__name__}: {e}');save();raise
    return m
