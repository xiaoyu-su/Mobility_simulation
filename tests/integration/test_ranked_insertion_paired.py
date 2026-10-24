import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[2]
SCENARIOS=ROOT/'studies/example_study/scenarios'


@pytest.mark.integration
@pytest.mark.parametrize('scenario',[
    'example_ir_ranked_fallback.yaml',
    'example_ir_batch_ranked_fallback.yaml',
    'example_ir_ranked_future_value.yaml',
])
def test_ranked_runs_replay_exactly_with_matched_background_and_no_double_service(scenario,tmp_path):
    output=tmp_path/'experiment'
    command=[sys.executable,'-m','tools.paired_eval','--constant-config',str(SCENARIOS/'constant_config_ir.csv'),
             '--baseline-scenarios',str(SCENARIOS/scenario),'--candidate-scenarios',str(SCENARIOS/scenario),
             '--network-tt-noise-sigma','.3','--seeds','5','11','--output',str(output)]
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=240,
                          env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'))
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    manifest=json.loads((output/'manifest.json').read_text())
    assert manifest['status']=='complete' and len(manifest['validated_pairs'])==2
    assert all(r['returncode']==0 for r in manifest['runs'])
    comparison=pd.read_csv(output/'paired_comparison.csv')
    assert comparison.loc[comparison.n_pairs==2,'mean_difference'].eq(0).all()
    for seed in [5,11]:
        pair=output/'runs'/f'seed_{seed}'
        left,right=pair/'baseline',pair/'candidate'
        for name in ['1_user-stats.csv','standard_eval.csv','driver_acceptance_op_0.csv',
                     'driver_choice_op_0.csv','ranked_insertion_op_0.csv']:
            pd.testing.assert_frame_equal(pd.read_csv(left/name),pd.read_csv(right/name),check_exact=True)
        audit=json.loads((right/'ranked_insertion_op_0.json').read_text())
        assert audit==json.loads((left/'ranked_insertion_op_0.json').read_text())
        assert audit['counters']['fallback_acceptances']>0
        users=pd.read_csv(right/'1_user-stats.csv')
        decisions=pd.read_csv(right/'driver_acceptance_op_0.csv')
        assert len(users)==100 and users.request_id.is_unique
        assert set(decisions[decisions.accepted].request_id)==set(users[users.dropoff_time.notna()].request_id)
        assert not decisions[decisions.accepted].request_id.duplicated().any()
        if 'future_value' in scenario:
            pd.testing.assert_frame_equal(pd.read_csv(left/'future_value_op_0.csv'),pd.read_csv(right/'future_value_op_0.csv'),check_exact=True)
