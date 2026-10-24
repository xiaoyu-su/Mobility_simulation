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
    'example_batch_forbid_rematch.yaml',
    'example_batch_forbid_rematch_menus.yaml',
    'example_batch_forbid_rematch_future.yaml',
])
def test_native_rematching_replays_exactly_in_fresh_processes_with_matched_inputs(scenario,tmp_path):
    output=tmp_path/'experiment'
    result=subprocess.run([sys.executable,'-m','tools.paired_eval',
                           '--constant-config',str(SCENARIOS/'constant_config_pool.csv'),
                           '--baseline-scenarios',str(SCENARIOS/scenario),
                           '--candidate-scenarios',str(SCENARIOS/scenario),
                           '--network-tt-noise-sigma','.3','--seeds','5','11','--output',str(output)],
                          cwd=ROOT,capture_output=True,text=True,timeout=240,
                          env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'))
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    manifest=json.loads((output/'manifest.json').read_text())
    assert manifest['status']=='complete' and len(manifest['validated_pairs'])==2
    assert all(run['returncode']==0 for run in manifest['runs'])
    comparison=pd.read_csv(output/'paired_comparison.csv')
    assert comparison.loc[comparison.n_pairs==2,'mean_difference'].eq(0).all()
    for seed in [5,11]:
        pair=output/'runs'/f'seed_{seed}'
        for name in ['1_user-stats.csv','standard_eval.csv','driver_acceptance_op_0.csv','forbid_rematch_op_0.csv']:
            pd.testing.assert_frame_equal(pd.read_csv(pair/'baseline'/name),pd.read_csv(pair/'candidate'/name),check_exact=True)
        audit=json.loads((pair/'candidate/forbid_rematch_op_0.json').read_text())
        assert audit==json.loads((pair/'baseline/forbid_rematch_op_0.json').read_text())
        assert audit['counters']['solver_resolves']>0
        d=pd.read_csv(pair/'candidate/driver_acceptance_op_0.csv')
        users=pd.read_csv(pair/'candidate/1_user-stats.csv')
        assert len(users)==100 and users.request_id.is_unique
        assert set(d[d.accepted].request_id)==set(users[users.dropoff_time.notna()].request_id)
        assert not d.duplicated(['request_id','vehicle_id']).any()
        assert set(d[d.terminal_decline].request_id).isdisjoint(set(d[d.accepted].request_id))
        if 'menus' in scenario:
            pd.testing.assert_frame_equal(pd.read_csv(pair/'baseline/driver_choice_op_0.csv'),pd.read_csv(pair/'candidate/driver_choice_op_0.csv'),check_exact=True)
            rows=pd.read_csv(pair/'candidate/forbid_rematch_op_0.csv')
            assert rows.groupby(['round','vehicle_id']).accepted.sum().le(1).all()
        if 'future' in scenario:
            pd.testing.assert_frame_equal(pd.read_csv(pair/'baseline/future_value_op_0.csv'),pd.read_csv(pair/'candidate/future_value_op_0.csv'),check_exact=True)
