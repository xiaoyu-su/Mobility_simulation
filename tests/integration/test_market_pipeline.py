"""Clearly labeled fixture checks of the complete market build/simulate/report path."""

from datetime import datetime,timedelta
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from src.misc.init_modules import load_routing_engine
from tools.paired_eval.metrics import per_driver_metrics

ROOT=Path(__file__).resolve().parents[2]


def fixture(directory,observed=True,matrix=False):
    directory.mkdir(parents=True)
    nodes=[2966,2980,2993];zones=[101,102,103]
    mapping=pd.DataFrame(dict(node_index=nodes,zone_id=zones,is_centroid=[1,1,1]))
    mapping.to_csv(directory/'zones.csv',index=False)
    router=load_routing_engine('NetworkBasicWithStore',str(ROOT/'data/networks/example_network'))
    travel={(a,b):router.return_travel_costs_1to1((nodes[a],None,None),(nodes[b],None,None))[1]
            for a in range(3) for b in range(3) if a!=b}
    rows=[]
    for day in ['2019-11-05','2019-11-12','2019-11-19','2019-11-26']:
        midnight=datetime.fromisoformat(day)
        for i in range(100):
            seconds=25200+(i*300 if i<3 else 900+(i-3)*60)
            a=0 if i<3 else i%3;b=(a+1+i%2)%3
            if b==a:b=(a+1)%3
            wait=60+(i%3)*30;request=midnight+timedelta(seconds=seconds)
            pickup=request+timedelta(seconds=wait)
            ride=max(30,travel[a,b]*[.9,1.1,1.2,1.4][i%4])
            row=dict(hvfhs_license_num='HV0003',pickup_datetime=pickup,dropoff_datetime=pickup+timedelta(seconds=ride),
                     PULocationID=zones[a],DOLocationID=zones[b])
            if observed:row['request_datetime']=request
            rows.append(row)
    path=directory/'fixture.parquet';pd.DataFrame(rows).to_parquet(path,index=False)
    network=ROOT/'data/networks/example_network'
    if matrix:
        network=directory/'matrix_network';(network/'base').mkdir(parents=True);(network/'ff/tables').mkdir(parents=True)
        pd.DataFrame(dict(node_index=[0,1,2],is_stop_only=[False]*3,pos_x=[0,100,200],pos_y=[0]*3)).to_csv(network/'base/nodes.csv',index=False)
        edges=[];tt=np.zeros((3,3));distance=np.zeros((3,3))
        for a,b in travel:
            route=router.return_travel_costs_1to1((nodes[a],None,None),(nodes[b],None,None))
            tt[a,b]=route[1];distance[a,b]=route[2]
            edges.append(dict(from_node=a,to_node=b,distance=route[2],travel_time=route[1]))
        pd.DataFrame(edges).to_csv(network/'base/edges.csv',index=False)
        (network/'base/crs.info').write_text('EPSG:32632')
        np.save(network/'ff/tables/nn_fastest_tt.npy',tt);np.save(network/'ff/tables/nn_fastest_distance.npy',distance)
        mapping.node_index=[0,1,2];mapping.to_csv(directory/'zones.csv',index=False)
    return path,directory/'zones.csv',network


def command(arguments,log):
    with log.open('w') as stream:
        result=subprocess.run([sys.executable,'-m','tools.synthetic_market',*arguments],cwd=ROOT,
            stdout=stream,stderr=subprocess.STDOUT,timeout=300,
            env=dict(os.environ,PYTHONHASHSEED='0',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
    assert result.returncode==0,log.read_text()


@pytest.mark.integration
@pytest.mark.parametrize('controller,observed,router_type,features',[
    ('PoolingIRSOnly',True,'NetworkBasicWithStore',[]),
    ('PoolingIRSAssignmentBatchOptimization',False,'NetworkBasic',['--driver-model','classes','--future-value']),
    ('RidePoolingBatchAssignmentFleetcontrol',True,'NetworkTTMatrix',['--driver-model','classes']),
    ('PoolingIRSOnly',True,'NetworkBasicWithStore',['--dynamic-fleet']),
])
def test_market_bundle_runs_complete_matched_sims_and_reports(controller,observed,router_type,features,tmp_path):
    trips,zones,network=fixture(tmp_path/'source',observed,matrix=router_type=='NetworkTTMatrix')
    bundle=tmp_path/'bundle'
    build=['build','--trips',str(trips),'--zone-map',str(zones),'--network',str(network),'--network-type',router_type,
           '--data-kind','fixture','--sample-fraction','1','--fleet-size','9','--end-seconds','32400',
           '--controller',controller,'--output',str(bundle),*features]
    if not observed:build.extend(['--request-time-proxy-seconds','60'])
    command(build,tmp_path/'build.txt')
    metadata=json.loads((bundle/'manifest.json').read_text())
    assert metadata['status']=='complete' and metadata['data_kind']=='fixture'
    assert metadata['target_count']==100 and metadata['training_count']==300
    assert metadata['observed_wait_available']==observed and metadata['travel_noise_sigma']>0
    assert set(pd.read_csv(bundle/'training_cohort.csv').service_date)==set(metadata['training_dates'])
    assert not pd.read_csv(bundle/'training_cohort.csv').service_date.eq(metadata['target_date']).any()
    output=tmp_path/'experiment'
    command(['run','--bundle',str(bundle),'--output',str(output),'--seeds','5','11'],tmp_path/'run.txt')
    manifest=json.loads((output/'manifest.json').read_text())
    assert manifest['status']=='complete' and len(manifest['validated_pairs'])==2
    for seed in [5,11]:
        for arm in ['no_repo','repo']:
            run=output/'runs'/f'seed_{seed}'/arm
            users=pd.read_csv(run/'1_user-stats.csv')
            assert len(users)==100 and users.request_id.is_unique
            assert users.pickup_time.notna().equals(users.dropoff_time.notna())
            contract=json.loads((run/'market_input_contract.json').read_text())
            assert contract['patience_loaded_for_all'] and contract['all_booked_requests_completed']
            config=json.loads((run/'00_config.json').read_text())
            assert config['directories']['vehicles']==str(bundle/'vehicles')
            legs=pd.read_csv(run/'2-0_op-stats.csv')
            assert legs.travel_time_multiplier.ne(1).any()
            per_driver_metrics(run,clip_initial_inactivity='--dynamic-fleet' in features)
            if '--driver-model' in features:
                decisions=pd.read_csv(run/'driver_acceptance_op_0.csv')
                assert set(decisions.loc[decisions.accepted,'request_id'])==set(users.loc[users.dropoff_time.notna(),'request_id'])
                assert set(decisions.loc[decisions.terminal_decline,'request_id']).isdisjoint(set(users.loc[users.pickup_time.notna(),'request_id']))
            if '--future-value' in features:assert len(pd.read_csv(run/'future_value_op_0.csv'))>0
            if arm=='repo':
                audit=json.loads((run/'repositioning_op_0.json').read_text())
                assert len(audit['rounds'])==8 and audit['solver']=='scipy.optimize.milp/HiGHS'
                if '--dynamic-fleet' not in features:
                    assert sum(len(row['flows']) for row in audit['rounds'])>0
                    legs=pd.read_csv(run/'2-0_op-stats.csv');assert legs.status.eq('reposition').any()
            else:assert not (run/'repositioning_op_0.json').exists()
        if '--dynamic-fleet' in features:
            assert pd.read_csv(output/'runs'/f'seed_{seed}'/'repo/2-0_op-stats.csv').status.eq('out_of_service').any()
    report=json.loads((output/'calibration_report.json').read_text())
    assert report['data_kind']=='fixture' and report['calibration_status']=='fixture_validation_only'
    assert all(row['observed_completion_rate'] is None and row['observed_utilization'] is None for row in report['runs'])
    assert all((row['observed_pickup_wait_median_s'] is not None)==observed for row in report['runs'])
    # Fresh-process exact replay checks data, physical execution and decisions.
    replay=tmp_path/'replay'
    command(['run','--bundle',str(bundle),'--output',str(replay),'--seeds','5','11'],tmp_path/'replay.txt')
    for table in ['seed_summary.csv','paired_comparison.csv','per_driver.csv']:
        pd.testing.assert_frame_equal(pd.read_csv(output/table),pd.read_csv(replay/table),check_exact=True)
    for seed in [5,11]:
        for arm in ['no_repo','repo']:
            for table in ['1_user-stats.csv','2-0_op-stats.csv','standard_eval.csv']:
                suffix=Path('runs')/f'seed_{seed}'/arm/table
                pd.testing.assert_frame_equal(pd.read_csv(output/suffix),pd.read_csv(replay/suffix),check_exact=True)
