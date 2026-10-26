"""Actual repositioning, private service, both insertion controllers and native routing."""

import json
import math
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from tests.integration.test_city_av_examples import city_fixture,run_city
from tools.city_av.reposition import MODE,inspect_repositioning


@pytest.mark.integration
@pytest.mark.parametrize('router,controller',[('NetworkBasicWithStore','PoolingIRSOnly'),
    ('NetworkBasicWithStoreCpp','PoolingIRSOnly'),('NetworkBasicWithStore','PoolingIRSAssignmentBatchOptimization')])
def test_city_demand_repositioning_physically_moves_only_empty_avs_and_replays(tmp_path,router,controller):
    if router.endswith('Cpp'):pytest.importorskip('src.routing.road.cpp_router.PyNetwork')
    cfg,c=city_fixture(tmp_path/'source',router);c.update(controller=controller,av_repositioning_forecast=MODE)
    cfg.write_text(json.dumps(c));edges=pd.read_csv(cfg.parent/'network/base/edges.csv');edges.travel_time=180;edges.to_csv(cfg.parent/'network/base/edges.csv',index=False)
    bundle=tmp_path/'bundle';run_city(['build','--config',cfg,'--data-root',cfg.parent,'--output',bundle],tmp_path/'build.txt')
    policies=[dict(name=f'threshold_{threshold}'+('_repo' if mode=='demand' else ''),eta_threshold_seconds=threshold,
        travel_time_factor=1.25,av_repositioning=mode) for threshold in [0,240] for mode in ['off','demand']]
    grid=tmp_path/'grid.json';grid.write_text(json.dumps(policies));output=tmp_path/'experiment'
    run_city(['run','--bundles',bundle,'--policies',grid,'--seeds',3,'--workers',2,'--output',output],tmp_path/'run.txt')
    report=pd.read_csv(output/'seed_results.csv').set_index('arm')
    assert len(report)==5 and report.rule_violations.eq(0).all() and report.all_accepted_complete.all()
    assert report.shared_placement_sha256.nunique()==1
    for name,row in report.iterrows():
        enabled=name.endswith('_repo');assert bool(row.av_repositioning_enabled)==enabled
        assert bool(row.av_repositioning_physically_exercised)==enabled
        assert (row.av_repositioning_distance_km>0)==enabled
        folder=output/'runs/fixture_city/seed_3'/name
        contract=json.loads((folder/'city_repositioning_contract.json').read_text())
        assert contract['empty_repositioning_only'] and contract['no_human_repositioning']
        if not enabled:assert not contract['commands'] and not contract['physical_legs']
    folder=output/'runs/fixture_city/seed_3/threshold_240_repo'
    meta=json.loads((bundle/'manifest.json').read_text());config=json.loads((folder/'00_config.json').read_text())['scenario_parameters']
    product=json.loads((folder/'av_product_op_0.json').read_text());legs=pd.read_csv(folder/'2-0_op-stats.csv')
    moving=legs[legs.status.eq('reposition')];assert moving.vehicle_id.isin(product['av_ids']).all() and moving.occupancy.eq(0).all()
    checked=0
    for leg in moving.itertuples():
        if leg.start_pos.split(';')[1]!='-1' or leg.end_pos.split(';')[1]!='-1':continue
        assert leg.end_time-leg.start_time==pytest.approx(leg.driven_distance/100*180*1.25)
        checked+=1
    assert checked>0
    forged=legs.copy();forged.loc[forged.status.eq('reposition'),'vehicle_id']=0
    with pytest.raises(RuntimeError,match='human vehicle'):inspect_repositioning(bundle,meta,config,product,forged,folder,set(product['av_ids']))
    replay_grid=tmp_path/'replay_grid.json';replay_grid.write_text(json.dumps([policies[2],policies[3]]));replay=tmp_path/'replay'
    run_city(['run','--bundles',bundle,'--policies',replay_grid,'--seeds',3,'--workers',2,'--output',replay],tmp_path/'replay.txt')
    for arm in ['all_human','threshold_240','threshold_240_repo']:
        for name in ['1_user-stats.csv','2-0_op-stats.csv','city_report.json','city_repositioning_contract.json','initial_placement.csv']:
            relative=Path('runs/fixture_city/seed_3')/arm/name;assert (output/relative).read_bytes()==(replay/relative).read_bytes()
    summary=tmp_path/'summary';run_city(['report','--experiments',output,replay,'--output',summary],tmp_path/'report.txt')
    effects=pd.read_csv(summary/'paired_effects.csv')
    assert ((effects.arm=='threshold_240_repo')&(effects.control=='threshold_240')).any()
    assert (summary/'av_repositioning_comparison.png').is_file() and 'Matched repositioning changes' in (summary/'RESULTS.md').read_text()


@pytest.mark.integration
def test_city_repositioning_rejects_missing_reference_before_simulating(tmp_path):
    from tools.city_av.build import build
    from tools.city_av.run import experiment
    from types import SimpleNamespace
    cfg,_=city_fixture(tmp_path/'source');bundle=tmp_path/'bundle';build(cfg,cfg.parent,bundle)
    grid=tmp_path/'grid.json';grid.write_text(json.dumps([dict(name='invalid',av_repositioning='demand')]))
    with pytest.raises(ValueError,match='reference-forecast'):
        experiment(SimpleNamespace(output=tmp_path/'bad',bundles=[bundle],policies=grid,seeds=[0],workers=1,timeout=60))
    assert not (tmp_path/'bad').exists()


@pytest.mark.integration
def test_historical_market_reference_repositioning_preserves_private_riders_and_parent(tmp_path):
    from tests.integration.test_market_pipeline import fixture,command
    from src.misc.seeding import file_digest
    trips,zones,network=fixture(tmp_path/'source',matrix=True)
    data=pd.read_parquet(trips);data['shared_request_flag']=['N' if i%3==0 else 'Y' for i in range(len(data))];data.to_parquet(trips,index=False)
    parent=tmp_path/'parent'
    command(['build','--trips',str(trips),'--zone-map',str(zones),'--network',str(network),'--network-type','NetworkTTMatrix',
        '--data-kind','fixture','--sample-fraction','1','--fleet-size','9','--end-seconds','32400','--warmup-seconds','7200',
        '--av-share','.34','--av-fence-share','1','--av-opt-in-share','1','--output',str(parent)],tmp_path/'parent.txt')
    hashes={str(p.relative_to(parent)):file_digest(p) for p in parent.rglob('*') if p.is_file()}
    m=json.loads((parent/'manifest.json').read_text())
    c=dict(schema_version=1,city='market_fixture',input_kind='market_bundle',parent_code_digest=m['source']['code_digest'],
        reference_start=0,reference_end=18000,warmup_start=18000,evaluation_start=25200,evaluation_end=32400,time_step=60,
        fleet_size=9,av_share=.34,opt_in_share=1,fence_share=1,av_repositioning_forecast=MODE,provenance=dict(kind='fixture'))
    cfg=tmp_path/'config.json';cfg.write_text(json.dumps(c));bundle=tmp_path/'bundle'
    run_city(['build','--config',cfg,'--data-root',parent,'--output',bundle],tmp_path/'build.txt')
    assert hashes=={str(p.relative_to(parent)):file_digest(p) for p in parent.rglob('*') if p.is_file()}
    demand=pd.read_csv(bundle/'demand/requests.csv');assert demand.pooling_allowed.eq(0).any()
    policies=[dict(name='threshold_240'+('_repo' if r=='demand' else ''),eta_threshold_seconds=240,av_repositioning=r) for r in ['off','demand']]
    grid=tmp_path/'grid.json';grid.write_text(json.dumps(policies));output=tmp_path/'experiment'
    run_city(['run','--bundles',bundle,'--policies',grid,'--seeds',0,'--output',output],tmp_path/'run.txt')
    report=pd.read_csv(output/'seed_results.csv').set_index('arm')
    assert report.all_accepted_complete.all() and report.rule_violations.eq(0).all()
    assert report.loc['threshold_240_repo','av_repositioning_physically_exercised']
    reference=pd.read_csv(bundle/'repositioning_reference.csv')
    assert pd.to_datetime(reference.reference_date).lt(pd.Timestamp(m['target_date'])).all()


@pytest.mark.integration
@pytest.mark.parametrize('controller',['PoolingIRSOnly','PoolingIRSAssignmentBatchOptimization'])
def test_service_priority_preempts_soft_target_before_booking_and_preserves_physics(controller,tmp_path):
    from tools.city_av.report import city_report
    from tools.paired_eval.__main__ import ROOT
    cfg,c=city_fixture(tmp_path/'source');c.update(controller=controller,av_repositioning_forecast=MODE,fleet_size=2)
    points=[(0,0),(100,0),(150,1),(200,0),(400,0)]
    pd.DataFrame([dict(node_index=i,is_stop_only=0,pos_x=x,pos_y=y) for i,(x,y) in enumerate(points)]).to_csv(cfg.parent/'network/base/nodes.csv',index=False)
    edges=[]
    for a,b in [(0,1),(1,2),(2,3),(1,3),(3,4)]:
        distance=math.dist(points[a],points[b])
        for x,y in [(a,b),(b,a)]:edges.append(dict(from_node=x,to_node=y,distance=distance,travel_time=2*distance))
    pd.DataFrame(edges).to_csv(cfg.parent/'network/base/edges.csv',index=False)
    pd.DataFrame(dict(node_index=list(range(5)),zone_id=[10,10,10,10,20],is_centroid=[0,0,1,0,1])).to_csv(cfg.parent/'zones.csv',index=False)
    requests=[dict(request_id=1000+i,rq_time=i*120,start=0,end=3) for i in range(6)]
    requests += [dict(request_id=2000,rq_time=901,start=1,end=3),dict(request_id=2001,rq_time=1801,start=1,end=3)]
    pd.DataFrame(requests).to_csv(cfg.parent/'requests.csv',index=False);cfg.write_text(json.dumps(c));bundle=tmp_path/'bundle'
    run_city(['build','--config',cfg,'--data-root',cfg.parent,'--output',bundle],tmp_path/'build.txt')
    for label,extra in [('legacy',[]),('priority',['--av-service-priority','on'])]:
        command=[sys.executable,'-m','tools.synthetic_market.worker','--bundle',str(bundle),'--output',str(tmp_path/label),
            '--seed','0','--policy','no_repo','--city-shared-placement','--av-repositioning','demand',
            '--av-eta-threshold-seconds','240','--av-travel-time-factor','1.25','--av-separate-search','on',*extra]
        with (tmp_path/(label+'.txt')).open('w') as log:
            result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=180,
                env=dict(os.environ,PYTHONHASHSEED='0',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        assert result.returncode==0,(tmp_path/(label+'.txt')).read_text()
    legacy=pd.read_csv(tmp_path/'legacy/2-0_op-stats.csv');fixed=pd.read_csv(tmp_path/'priority/2-0_op-stats.csv')
    if controller=='PoolingIRSOnly':
        assert (legacy.status.eq('reposition')&legacy.occupancy.gt(0)&legacy.driven_distance.gt(0)).any()
    assert not (fixed.status.eq('reposition')&fixed.occupancy.gt(0)).any()
    product=json.loads((tmp_path/'priority/av_product_op_0.json').read_text());assert product['service_preemptions']
    users=pd.read_csv(tmp_path/'priority/1_user-stats.csv');assert users.pickup_time.notna().all() and users.dropoff_time.notna().all()
    report=city_report(bundle,tmp_path/'priority');assert report['all_accepted_complete'] and report['av_repositioning_physically_exercised']


@pytest.mark.integration
@pytest.mark.parametrize('controller',['PoolingIRSOnly','PoolingIRSAssignmentBatchOptimization'])
def test_service_priority_combines_with_human_acceptance_future_value_shifts_and_joint_noise(controller,tmp_path):
    from tests.integration.test_av_round2_examples import build_case
    from tools.paired_eval.__main__ import ROOT
    bundle=build_case(tmp_path,controller,['--av-repositioning','--av-eta-threshold-seconds','240',
        '--av-joint-repositioning','--av-retarget','--av-forecast-noise-sigma','.5',
        '--av-repositioning-timestep','60','--dynamic-fleet','--driver-model','classes','--future-value'])
    for label,policy in [('no_repo','no_repo'),('repo','repo'),('replay','repo')]:
        command=[sys.executable,'-m','tools.synthetic_market.worker','--bundle',str(bundle),'--output',str(tmp_path/label),
            '--seed','5','--policy',policy,'--av-service-priority','on']
        with (tmp_path/(label+'.txt')).open('w') as log:
            result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=300,
                env=dict(os.environ,PYTHONHASHSEED='0',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        assert result.returncode==0,(tmp_path/(label+'.txt')).read_text()
        product=json.loads((tmp_path/label/'av_product_op_0.json').read_text());assert product['service_priority'] and product['joint_repositioning']
        d=pd.read_csv(tmp_path/label/'2-0_op-stats.csv');assert not (d.vehicle_type.eq('av_vehtype')&d.status.eq('reposition')&d.occupancy.gt(0)).any()
        assert (tmp_path/label/'future_value_op_0.csv').is_file() and (tmp_path/label/'driver_acceptance_op_0.csv').is_file()
    for name in ['1_user-stats.csv','2-0_op-stats.csv','av_product_op_0.json','driver_acceptance_op_0.csv']:
        assert (tmp_path/'repo'/name).read_bytes()==(tmp_path/'replay'/name).read_bytes()
