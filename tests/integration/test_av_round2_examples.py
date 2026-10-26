import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from src.misc.seeding import file_digest
from tests.integration.test_market_pipeline import fixture,command,ROOT


def build_case(tmp_path,controller,features):
    trips,zones,network=fixture(tmp_path/'source',matrix=True)
    data=pd.read_parquet(trips);data['shared_request_flag']='N';data['shared_match_flag']='N'
    data['on_scene_datetime']=data.pickup_datetime-pd.Timedelta(seconds=20);data.to_parquet(trips,index=False)
    bundle=tmp_path/'bundle'
    command(['build','--trips',str(trips),'--zone-map',str(zones),'--network',str(network),
             '--network-type','NetworkTTMatrix','--data-kind','fixture','--sample-fraction','1','--fleet-size','9',
             '--end-seconds','32400','--controller',controller,'--av-share','.34','--av-zones','101','102',
             '--av-opt-in-share','1','--av-travel-time-factor','1.25','--pickup-service','training_curb',
             '--output',str(bundle),*features],tmp_path/'build.txt')
    return bundle


@pytest.mark.integration
@pytest.mark.parametrize('controller',['PoolingIRSOnly','PoolingIRSAssignmentBatchOptimization','RidePoolingBatchAssignmentFleetcontrol'])
def test_slow_av_factor_survives_real_loader_and_scales_physical_routes(controller,tmp_path):
    bundle=build_case(tmp_path,controller,['--driver-model','classes','--av-preference-seconds','300'])
    # A declared physics fixture removes execution noise and traffic changes;
    # route durations can then be checked against independent matrix entries.
    manifest=json.loads((bundle/'manifest.json').read_text())
    factors=pd.read_csv(bundle/'network/calibrated_factors.csv');factors.travel_time_factor=1
    factors.to_csv(bundle/'network/calibrated_factors.csv',index=False)
    parameters=json.loads((bundle/'parameters.json').read_text());parameters['network_tt_noise_sigma']=0
    (bundle/'parameters.json').write_text(json.dumps(parameters,indent=2)+'\n')
    manifest['fixture_override']='Constant traffic and zero noise for independent physical type-factor checks'
    manifest['output_sha256']={str(p.relative_to(bundle)):file_digest(p) for p in bundle.rglob('*') if p.is_file() and p.name!='manifest.json'}
    (bundle/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    command(['run','--bundle',str(bundle),'--output',str(tmp_path/'experiment'),'--seeds','3'],tmp_path/'run.txt')
    matrix=np.load(bundle/'network/ff/tables/nn_fastest_tt.npy')
    checked=0
    for arm in ['no_repo','repo']:
        run=tmp_path/'experiment/runs/seed_3'/arm
        audit=json.loads((run/'vehicle_time_factors.json').read_text())
        assert audit['av_vehtype']=={'loaded':1.25,'effective':1.25}
        legs=pd.read_csv(run/'2-0_op-stats.csv')
        for leg in legs[legs.vehicle_type.eq('av_vehtype')&legs.status.isin(['route','reposition'])&legs.driven_distance.gt(0)].itertuples():
            a=leg.start_pos.split(';');b=leg.end_pos.split(';')
            if a[1]!='-1' or b[1]!='-1':continue
            expected=matrix[int(a[0]),int(b[0])]*1.25
            # NetworkTTMatrix rounds router event times to centiseconds at each
            # movement update. Bound that documented quantization separately
            # from the type factor; omitting 1.25 changes these trips by seconds.
            updates=np.ceil((leg.end_time-leg.start_time)/parameters['time_step'])+2
            assert leg.end_time-leg.start_time==pytest.approx(expected,abs=.01*1.25*updates)
            checked+=1
        report=json.loads((run/'av_report.json').read_text())
        assert report['av_completed']>0 and report['av_travel_time_factor']==1.25 and report['rule_violations']==0
    assert checked>0


@pytest.mark.integration
@pytest.mark.parametrize('controller',['PoolingIRSOnly','PoolingIRSAssignmentBatchOptimization'])
def test_threshold_joint_noise_retarget_and_replay_complete(controller,tmp_path):
    bundle=build_case(tmp_path,controller,['--av-repositioning','--av-eta-threshold-seconds','240',
                      '--av-joint-repositioning','--av-retarget','--av-forecast-noise-sigma','.5',
                      '--av-repositioning-timestep','60','--dynamic-fleet','--driver-model','classes','--future-value'])
    command(['run','--bundle',str(bundle),'--output',str(tmp_path/'first'),'--seeds','5'],tmp_path/'first.txt')
    command(['run','--bundle',str(bundle),'--output',str(tmp_path/'replay'),'--seeds','5'],tmp_path/'replay.txt')
    for arm in ['no_repo','repo']:
        first=tmp_path/'first/runs/seed_5'/arm;replay=tmp_path/'replay/runs/seed_5'/arm
        report=json.loads((first/'av_report.json').read_text())
        assert report['threshold_decisions']>0 and report['threshold_av_choices']>0 and report['threshold_violations']==0
        assert report['av_completed']==report['threshold_av_choices']
        assert report['joint_repositioning'] and report['retarget_repositioning'] and report['forecast_sigma']==.5
        product=json.loads((first/'av_product_op_0.json').read_text())
        assert any(r['forecast_error_factors'] for r in product['repositioning_rounds'])
        if arm=='repo':assert report['human_forecast_av_coverage_sum']>0
        for name in ['1_user-stats.csv','2-0_op-stats.csv','av_report.json','av_product_op_0.json']:
            assert (first/name).read_bytes()==(replay/name).read_bytes()


@pytest.mark.integration
def test_threshold_policy_grid_runs_distinct_controls_and_preserves_loaded_inputs(tmp_path):
    bundle=build_case(tmp_path,'PoolingIRSOnly',['--av-repositioning'])
    grid=tmp_path/'grid.json'
    grid.write_text(json.dumps([{'name':'cost_control','eta_threshold_seconds':None,'travel_time_factor':1.25},
                               {'name':'threshold_240','eta_threshold_seconds':240,'travel_time_factor':1.25},
                               {'name':'equal_speed','eta_threshold_seconds':240,'travel_time_factor':1}]))
    args=[sys.executable,'-m','tools.av_eval','--bundle',str(bundle),'--policy-grid',str(grid),
          '--seeds','7','--output',str(tmp_path/'experiment')]
    with (tmp_path/'run.txt').open('w') as stream:
        result=subprocess.run(args,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=300,
                              env=dict(os.environ,PYTHONHASHSEED='0',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'))
    assert result.returncode==0,(tmp_path/'run.txt').read_text()
    m=json.loads((tmp_path/'experiment/manifest.json').read_text())
    assert m['status']=='complete' and len(m['validated_pairs'])==2
    rows=pd.read_csv(tmp_path/'experiment/seed_summary.csv').set_index('arm')
    assert rows.loc['cost_control','av_travel_time_factor']==1.25
    assert rows.loc['equal_speed','av_travel_time_factor']==1
    assert pd.isna(rows.loc['cost_control','eta_threshold_seconds'])
    assert rows.loc['threshold_240','eta_threshold_seconds']==240
    for arm in rows.index:
        config=json.loads((tmp_path/'experiment/runs/seed_7'/arm/'00_config.json').read_text())
        assert config['scenario_parameters']['op_av_separate_search'] is True
