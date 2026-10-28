"""Full multi-policy matching and AV reporting through one public CLI."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pandas as pd
import pytest
from src.misc.seeding import file_digest
from tools.policy_compare.report import report
from tools.policy_compare.run import parse_spec
from tests.integration.test_city_av_examples import city_fixture,run_city
from tools.paired_eval.__main__ import ROOT
from tools.city_av.reposition import MODE


def cli(arguments,log):
    with log.open('w') as f:r=subprocess.run([sys.executable,'-m','tools.policy_compare',*map(str,arguments)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=600,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONHASHSEED='0'))
    assert r.returncode==0,log.read_text()


@pytest.mark.integration
@pytest.mark.parametrize('profile',['insertion','immediate_batch','alonso_mora'])
def test_multi_policy_full_comparison_seals_replays_and_portable_snapshots(tmp_path,profile):
    s=parse_spec(ROOT/'studies/policy_comparison'/f'{profile}.json');s['seeds']=[3,9];spec=tmp_path/'spec.json';spec.write_text(json.dumps(s));out=tmp_path/'comparison'
    cli(['run','--spec',spec,'--output',out],tmp_path/'run.txt')
    m=json.loads((out/'manifest.json').read_text());a=json.loads((out/'report/manifest.json').read_text());n=len(s['policies'])
    assert m['status']=='complete' and len(m['runs'])==4*n
    assert a['physical_records']==4*n and a['unique_conditions']==2*(n+1) and len(a['replays'])==2*(n-1)
    assert all(r['all_physical_checks_pass'] and r['accepted_promises_checked'] for r in a['physical_checks'])
    data=pd.read_csv(out/'report/seed_kpis.csv');assert data.requests.eq(100).all() and data.rule_violations.eq(0).all()
    effects=pd.read_csv(out/'report/kpi_movements.csv');assert effects[effects.metric.eq('completion_rate')].n_pairs.eq(2).all()
    assert m['comparison_contract']['execution_noise_sigma']==s['network_tt_noise_sigma'] and m['comparison_contract']['physical_background']['initial_vehicle_count']==5
    if profile!='immediate_batch':assert data.reoffered_requests.gt(0).any()
    assert set(m['policy_differences'])=={p['name'] for p in s['policies']}
    for e in m['runs']:
        folder=out/e['directory'];u=pd.read_csv(folder/'1_user-stats.csv');assert u.pickup_time.notna().equals(u.dropoff_time.notna())
        assert u.promised_pickup_time.notna().equals(u.dropoff_time.notna())
        decisions=pd.read_csv(folder/'driver_acceptance_op_0.csv');row=data[data.seed.eq(e['seed'])&data.arm.eq(e['arm'])].iloc[0]
        assert row.reoffered_requests==decisions.groupby(['operator_id','request_id']).vehicle_id.nunique().gt(1).sum()
        assert row.repeat_driver_offer_attempts==len(decisions)-len(decisions.drop_duplicates(['operator_id','request_id','vehicle_id']))
        for name,h in e['output_sha256'].items():assert file_digest(folder/name)==h
    receipt=json.loads((out/'report_receipt.json').read_text());assert receipt['experiment_manifest_sha256']==file_digest(out/'manifest.json')
    # Moving the sealed result works despite original raw directory strings.
    moved=tmp_path/'portable';shutil.move(out,moved);before={str(p):file_digest(p) for p in (moved/'paired').rglob('*') if p.is_file()}
    r=report([moved],tmp_path/'portable_report');assert r['unique_conditions']==a['unique_conditions'] and all(file_digest(Path(p))==h for p,h in before.items())
    with pytest.raises(ValueError,match='overwrite'):report([moved],tmp_path/'portable_report')
    e=m['runs'][0];target=moved/e['directory']/'1_user-stats.csv';raw=target.read_bytes()
    try:
        target.write_bytes(raw+b'\n')
        with pytest.raises(ValueError,match='Changed or invalid sealed'):report([moved],tmp_path/'tampered')
    finally:target.write_bytes(raw)


@pytest.mark.integration
@pytest.mark.parametrize('router,controller',[('NetworkBasicWithStore','PoolingIRSOnly'),('NetworkBasicWithStoreCpp','PoolingIRSOnly'),('NetworkBasicWithStore','PoolingIRSAssignmentBatchOptimization')])
def test_unified_av_kpis_match_actual_city_source_clocks_and_readonly_outputs(tmp_path,router,controller):
    if router.endswith('Cpp'):pytest.importorskip('src.routing.road.cpp_router.PyNetwork')
    cfg,c=city_fixture(tmp_path/'source',router);c.update(controller=controller,av_repositioning_forecast=MODE);cfg.write_text(json.dumps(c));bundle=tmp_path/'bundle'
    edges=cfg.parent/'network/base/edges.csv';network=pd.read_csv(edges);network['travel_time']=180;network.to_csv(edges,index=False)
    run_city(['build','--config',cfg,'--data-root',cfg.parent,'--output',bundle],tmp_path/'build.txt')
    policies=tmp_path/'policies.json';policies.write_text(json.dumps([dict(name=f'threshold_{t}'+('_repo' if mode=='demand' else ''),eta_threshold_seconds=t,travel_time_factor=1.25,av_repositioning=mode) for t,mode in [(0,'off'),(240,'off'),(240,'demand')]]))
    studies=[]
    for name in ['first','replay']:
        root=tmp_path/name;run_city(['run','--bundles',bundle,'--policies',policies,'--seeds',3,'--output',root],tmp_path/(name+'.txt'));studies.append(root)
    before={str(p):file_digest(p) for root in studies for p in root.rglob('*') if p.is_file()}
    cli(['report','--experiments',*studies,'--reference','threshold_0','--output',tmp_path/'report'],tmp_path/'report.txt')
    m=json.loads((tmp_path/'report/manifest.json').read_text());assert m['physical_records']==8 and m['unique_conditions']==4 and len(m['replays'])==4
    data=pd.read_csv(tmp_path/'report/seed_kpis.csv').set_index('arm');study=json.loads((studies[0]/'manifest.json').read_text())
    for entry in study['runs']:
        old=json.loads((Path(entry['output'])/'city_report.json').read_text());row=data.loc[entry['arm']]
        assert row.completed==old['completed'] and row.av_completed==old['av_completed']
        assert row.empty_distance_km==pytest.approx(old['fleet_empty_distance_km']) and row.wait_mean_s==pytest.approx(old['all_wait_mean_s'])
        if row.av_count:assert row.av_utilization==pytest.approx(old['av_utilization'])
        if entry['arm'].endswith('_repo'):assert row.av_reposition_distance_km>0 and row.av_reposition_distance_km==pytest.approx(old['av_repositioning_distance_km'])
    assert data.loc['threshold_240','av_completed']>0 and all(file_digest(Path(p))==h for p,h in before.items())
    # Fresh source/input regime is a separate stratum, not an extra seed or replay.
    c['max_wait_seconds']=720;other_cfg=cfg.parent/'other.json';other_cfg.write_text(json.dumps(c));other=tmp_path/'other_bundle'
    run_city(['build','--config',other_cfg,'--data-root',cfg.parent,'--output',other],tmp_path/'other-build.txt')
    run_city(['run','--bundles',other,'--policies',policies,'--seeds',3,'--output',tmp_path/'other'],tmp_path/'other-run.txt')
    r=report([studies[0],tmp_path/'other'],tmp_path/'strata',reference='threshold_0');assert r['strata']==2 and r['unique_conditions']==8
