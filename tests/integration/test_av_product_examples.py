import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from tests.integration.test_market_pipeline import fixture,command,ROOT


@pytest.mark.integration
@pytest.mark.parametrize('controller,extras',[
    ('PoolingIRSOnly',['--driver-model','classes','--future-value']),
    ('PoolingIRSAssignmentBatchOptimization',['--driver-model','classes']),
    ('RidePoolingBatchAssignmentFleetcontrol',['--driver-model','classes']),
    ('PoolingIRSOnly',['--dynamic-fleet','--driver-model','classes']),
])
def test_av_rules_loader_acceptance_physics_and_repositioning(controller,extras,tmp_path):
    trips,zones,network=fixture(tmp_path/'source',matrix=True)
    data=pd.read_parquet(trips)
    data['shared_request_flag']=['N' if i%3==0 else 'Y' for i in range(len(data))]
    data['shared_match_flag']='N'
    data['on_scene_datetime']=data.pickup_datetime-pd.Timedelta(seconds=20)
    data.to_parquet(trips,index=False)
    bundle=tmp_path/'bundle'
    command(['build','--trips',str(trips),'--zone-map',str(zones),'--network',str(network),
             '--network-type','NetworkTTMatrix','--data-kind','fixture','--sample-fraction','1',
             '--fleet-size','9','--end-seconds','32400','--controller',controller,'--av-share','.34',
             '--av-zones','101','102','--av-opt-in-share','.5','--av-preference-seconds','300',
             '--av-repositioning','--pickup-service','training_curb','--output',str(bundle),*extras],tmp_path/'build.txt')
    command(['run','--bundle',str(bundle),'--output',str(tmp_path/'experiment'),'--seeds','3'],tmp_path/'run.txt')
    for arm in ['no_repo','repo']:
        path=tmp_path/'experiment/runs/seed_3'/arm
        report=json.loads((path/'av_report.json').read_text());audit=json.loads((path/'av_product_op_0.json').read_text())
        assert report['av_count']==3 and report['human_count']==6
        assert report['rule_violations']==0 and report['all_accepted_complete']
        assert report['av_completed']>0 and report['eligible_requests']<100
        assert report['av_reposition_orders']>0
        roster=pd.read_csv(path/'2_vehicle_types.csv')
        assert set(roster[roster.vehicle_id.isin(audit['av_ids'])].vehicle_type)=={'av_vehtype'}
        decisions=pd.read_csv(path/'driver_acceptance_op_0.csv')
        av_decisions=decisions[decisions.vehicle_id.isin(audit['av_ids'])]
        assert len(av_decisions)>0 and av_decisions.probability.eq(1).all() and av_decisions.accepted.all()
        config=json.loads((path/'00_config.json').read_text())
        assert config['list_operator_attributes'][0]['op_av_vehicle_types']==['av_vehtype']


@pytest.mark.integration
def test_av_zero_opt_in_prevents_all_av_service_and_policy_replay_is_exact(tmp_path):
    trips,zones,network=fixture(tmp_path/'source',matrix=True)
    bundle=tmp_path/'bundle'
    command(['build','--trips',str(trips),'--zone-map',str(zones),'--network',str(network),
             '--network-type','NetworkTTMatrix','--data-kind','fixture','--sample-fraction','1',
             '--fleet-size','9','--end-seconds','32400','--av-share','.34','--av-zones','101','102',
             '--av-opt-in-share','0','--output',str(bundle)],tmp_path/'build.txt')
    for suffix in ['first','replay']:
        args=[sys.executable,'-m','tools.av_eval','--bundle',str(bundle),'--output',str(tmp_path/suffix),
              '--seeds','5','--preferences','0','300','--repositioning','off','demand']
        with (tmp_path/f'{suffix}.txt').open('w') as stream:
            result=subprocess.run(args,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=300,
                                  env=dict(os.environ,PYTHONHASHSEED='0',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'))
        assert result.returncode==0,(tmp_path/f'{suffix}.txt').read_text()
    summary=pd.read_csv(tmp_path/'first/seed_summary.csv')
    assert summary.av_completed.eq(0).all() and summary.rule_violations.eq(0).all()
    m=json.loads((tmp_path/'first/manifest.json').read_text());assert m['status']=='complete' and len(m['validated_pairs'])==3
    pd.testing.assert_frame_equal(summary,pd.read_csv(tmp_path/'replay/seed_summary.csv'),check_exact=True)
    for arm in ['preference_0_off','preference_300_off','preference_0_demand','preference_300_demand']:
        for file in ['1_user-stats.csv','2-0_op-stats.csv','av_product_op_0.json','av_dispatch_op_0.csv']:
            relative=Path('runs/seed_5')/arm/file
            assert (tmp_path/'first'/relative).read_bytes()==(tmp_path/'replay'/relative).read_bytes()
