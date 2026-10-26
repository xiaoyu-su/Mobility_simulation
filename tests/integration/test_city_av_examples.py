"""Complete city-bundle/worker/report runs, with matched human controls."""

import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from tools.city_av.build import build
from tools.paired_eval.__main__ import ROOT


def city_fixture(directory,router='NetworkBasicWithStore'):
    directory.mkdir(parents=True)
    network=directory/'network';(network/'base').mkdir(parents=True)
    pd.DataFrame(dict(node_index=[0,1,2],is_stop_only=[0,0,0],pos_x=[0,100,200],pos_y=[0,0,0])).to_csv(network/'base/nodes.csv',index=False)
    pd.DataFrame([dict(from_node=a,to_node=b,distance=100,travel_time=20) for a,b in [(0,1),(1,0),(1,2),(2,1)]]).to_csv(network/'base/edges.csv',index=False)
    (network/'base/crs.info').write_text('EPSG:32632')
    pd.DataFrame(dict(node_index=[0,1,2],zone_id=[10,10,20])).to_csv(directory/'zones.csv',index=False)
    rows=[dict(request_id=1000+i,rq_time=i*60,start=n,end=(n+1)%3) for i,n in enumerate([0,0,1,1,2,2])]
    rows += [dict(request_id=2000+i,rq_time=901+i*61,start=i%3,end=(i+1)%3) for i in range(6)]
    rows += [dict(request_id=i,rq_time=1801+i*61,start=i%3,end=1 if i%3==0 else 0) for i in range(48)]
    pd.DataFrame(rows).to_csv(directory/'requests.csv',index=False)
    c=dict(schema_version=1,city='fixture_city',input_kind='native',network_path='network',router=router,network_dynamics=None,
           zone_map='zones.csv',requests='requests.csv',reference_start=0,reference_end=900,warmup_start=900,
           evaluation_start=1800,evaluation_end=5400,time_step=60,fleet_size=6,av_share=.5,opt_in_share=1,
           fence_share=.5,travel_time_factor=1.25,max_wait_seconds=480,pickup_service_seconds=20,dropoff_service_seconds=30,
           provenance=dict(kind='synthetic_unit_fixture',not_real_city_data=True))
    path=directory/'config.json';path.write_text(json.dumps(c));return path,c


def run_city(arguments,log):
    with log.open('w') as stream:
        result=subprocess.run([sys.executable,'-m','tools.city_av',*map(str,arguments)],cwd=ROOT,stdout=stream,
            stderr=subprocess.STDOUT,timeout=300,env=dict(os.environ,PYTHONHASHSEED='0',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
    assert result.returncode==0,log.read_text()


@pytest.mark.integration
@pytest.mark.parametrize('router,controller',[('NetworkBasicWithStore','PoolingIRSOnly'),
    ('NetworkBasicWithStoreCpp','PoolingIRSOnly'),('NetworkBasicWithStore','PoolingIRSAssignmentBatchOptimization')])
def test_native_city_controls_threshold_speed_and_exact_replay_complete(tmp_path,router,controller):
    if router.endswith('Cpp'):pytest.importorskip('src.routing.road.cpp_router.PyNetwork')
    cfg,c=city_fixture(tmp_path/'source',router);c['controller']=controller;c['max_route_candidates']=1
    cfg.write_text(json.dumps(c));bundle=tmp_path/'bundle'
    run_city(['build','--config',cfg,'--data-root',cfg.parent,'--output',bundle],tmp_path/'build.txt')
    meta=json.loads((bundle/'manifest.json').read_text());assert meta['reference']['rows']==6 and meta['av_product']['fence_zones']==[10]
    assert meta['evaluation_count']==48 and meta['warmup_count']==6
    assert bool(meta['runtime_files_sha256'])==router.endswith('Cpp')
    policies=[dict(name='cost_control',eta_threshold_seconds=None,travel_time_factor=1.25,av_repositioning='off'),
              dict(name='threshold_0',eta_threshold_seconds=0,travel_time_factor=1.25,av_repositioning='off'),
              dict(name='threshold_240',eta_threshold_seconds=240,travel_time_factor=1.25,av_repositioning='off'),
              dict(name='equal_speed',eta_threshold_seconds=240,travel_time_factor=1,av_repositioning='off')]
    grid=tmp_path/'grid.json';grid.write_text(json.dumps(policies))
    first=tmp_path/'experiment';run_city(['run','--bundles',bundle,'--policies',grid,'--seeds',3,'--workers',2,'--output',first],tmp_path/'run.txt')
    manifest=json.loads((first/'manifest.json').read_text());assert manifest['status']=='complete' and len(manifest['runs'])==5 and len(manifest['validated_pairs'])==4
    rows=pd.read_csv(first/'seed_results.csv').set_index('arm')
    assert rows.loc['all_human','av_count']==0 and rows.loc['all_human','human_count']==6
    assert rows.loc['threshold_240','av_completed']>0 and rows.loc['threshold_240','threshold_av_choices']>0
    assert rows.loc['threshold_240','av_travel_time_factor']==1.25 and rows.loc['equal_speed','av_travel_time_factor']==1
    assert rows.rule_violations.eq(0).all() and rows.shared_placement_sha256.nunique()==1
    for arm in rows.index:
        folder=first/'runs/fixture_city/seed_3'/arm
        u=pd.read_csv(folder/'1_user-stats.csv');assert len(u)==54 and u.request_id.is_unique
        assert u.pickup_time.notna().equals(u.dropoff_time.notna())
        assert not (folder/'repositioning_op_0.json').exists()
        if arm=='all_human':assert not (folder/'av_product_op_0.json').exists()
        search=json.loads((folder/'city_search_contract.json').read_text())
        assert search['all_human_shadow_groups']==(arm=='all_human') and search['per_group_position_budget']==1
    replay_grid=tmp_path/'replay_grid.json';replay_grid.write_text(json.dumps([policies[2]]))
    replay=tmp_path/'replay';run_city(['run','--bundles',bundle,'--policies',replay_grid,'--seeds',3,'--workers',2,'--output',replay],tmp_path/'replay.txt')
    for arm in ['all_human','threshold_240']:
        for name in ['1_user-stats.csv','2-0_op-stats.csv','initial_placement.csv','city_report.json','random_streams.json']:
            relative=Path('runs/fixture_city/seed_3')/arm/name
            assert (first/relative).read_bytes()==(replay/relative).read_bytes()
    # A recording column is not a physics proof: check actual native routes
    # against this independent 20-seconds-per-edge fixture, with noise disabled.
    checked=0
    for arm,factor in [('threshold_240',1.25),('equal_speed',1)]:
        legs=pd.read_csv(first/'runs/fixture_city/seed_3'/arm/'2-0_op-stats.csv')
        for leg in legs[legs.vehicle_type.eq('av_vehtype')&legs.status.eq('route')&legs.driven_distance.gt(0)].itertuples():
            a=leg.start_pos.split(';');b=leg.end_pos.split(';')
            if a[1]!='-1' or b[1]!='-1':continue
            assert leg.end_time-leg.start_time==pytest.approx(abs(int(a[0])-int(b[0]))*20*factor)
            checked+=1
    assert checked>0
    summary=tmp_path/'summary'
    run_city(['report','--experiments',first,replay,'--output',summary],tmp_path/'summary.txt')
    integrity=json.loads((summary/'integrity.json').read_text())
    assert integrity['physical_runs']==7 and integrity['unique_seed_conditions']==5 and len(integrity['fresh_process_replay_records'])==2
    assert (summary/'city_policy_curves.png').is_file() and (summary/'common_rider_effects.csv').is_file()
    # Modified evidence cannot silently enter a published pooled result.
    from tools.city_av.summary import summarize
    target=first/'runs/fixture_city/seed_3/threshold_240/city_report.json';original=target.read_bytes()
    try:
        target.write_bytes(original+b'\n')
        with pytest.raises(ValueError,match='Raw city output changed'):summarize([first],tmp_path/'bad_summary')
    finally:target.write_bytes(original)


@pytest.mark.integration
def test_verified_market_dataset_adapts_without_retagging_or_mutating_parent(tmp_path):
    from tests.integration.test_market_pipeline import fixture,command
    from src.misc.seeding import file_digest
    trips,zones,network=fixture(tmp_path/'source',matrix=True)
    data=pd.read_parquet(trips);data['shared_request_flag']=['N' if i%3==0 else 'Y' for i in range(len(data))];data.to_parquet(trips,index=False)
    parent=tmp_path/'parent'
    command(['build','--trips',str(trips),'--zone-map',str(zones),'--network',str(network),'--network-type','NetworkTTMatrix',
             '--data-kind','fixture','--sample-fraction','1','--fleet-size','9','--end-seconds','32400','--warmup-seconds','7200',
             '--av-share','.34','--av-fence-share','1','--av-opt-in-share','1','--output',str(parent)],tmp_path/'parent.txt')
    before={str(p.relative_to(parent)):file_digest(p) for p in parent.rglob('*') if p.is_file()}
    m=json.loads((parent/'manifest.json').read_text())
    c=dict(schema_version=1,city='market_fixture',input_kind='market_bundle',parent_code_digest=m['source']['code_digest'],
           reference_start=0,reference_end=18000,warmup_start=18000,evaluation_start=25200,evaluation_end=32400,
           time_step=60,fleet_size=9,av_share=.34,opt_in_share=1,fence_share=1,provenance=dict(kind='fixture'))
    cfg=tmp_path/'config.json';cfg.write_text(json.dumps(c));bundle=tmp_path/'city'
    build(cfg,parent,bundle)
    assert before=={str(p.relative_to(parent)):file_digest(p) for p in parent.rglob('*') if p.is_file()}
    requests=pd.read_csv(bundle/'demand/requests.csv');assert requests.pooling_allowed.eq(0).any()
    grid=tmp_path/'grid.json';grid.write_text(json.dumps([dict(name='threshold_240',eta_threshold_seconds=240,av_repositioning='off')]))
    run_city(['run','--bundles',bundle,'--policies',grid,'--seeds',0,'--output',tmp_path/'experiment'],tmp_path/'run.txt')
    rows=pd.read_csv(tmp_path/'experiment/seed_results.csv');assert len(rows)==2 and rows.all_accepted_complete.all() and rows.rule_violations.eq(0).all()
