"""Real full baselines and restored policy windows, with exact serial/parallel replay."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[2]
SCENARIOS=ROOT/'studies/example_study/scenarios'


def command(arguments,log):
    with log.open('w') as stream:
        result=subprocess.run([sys.executable,*arguments],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,
            timeout=360,env=dict(os.environ,PYTHONHASHSEED='0',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
    assert result.returncode==0,log.read_text()


@pytest.mark.integration
@pytest.mark.parametrize('constant,baseline,candidate,flag',[
    ('ir','example_ir_driver_choice','example_ir_ranked_future_value','ranked_future'),
    ('ir','example_ir_batch_driver_choice','example_ir_batch_ranked_fallback','ranked'),
    ('pool','example_batch_driver_choice','example_batch_forbid_rematch_menus','rematch_menus'),
    ('pool','example_batch_forbid_rematch','example_batch_forbid_rematch_future','rematch_future'),
])
def test_saved_worlds_match_full_baseline_and_parallel_replay(constant,baseline,candidate,flag,tmp_path):
    constant=SCENARIOS/f'constant_config_{constant}.csv'
    baseline=SCENARIOS/f'{baseline}.yaml';candidate=SCENARIOS/f'{candidate}.yaml'
    for workers in [1,2]:
        output=tmp_path/f'workers_{workers}'
        command(['-m','tools.windowed_eval','--constant-config',str(constant),
                 '--baseline-scenarios',str(baseline),'--candidate-scenarios',str(candidate),
                 '--seeds','5','--window-seconds','3600','--cooldown-seconds','300',
                 '--network-tt-noise-sigma','.3','--workers',str(workers),'--output',str(output)],
                tmp_path/f'workers_{workers}.txt')
        manifest=json.loads((output/'manifest.json').read_text())
        assert manifest['status']=='complete' and len(manifest['validated_pairs'])==2
        assert manifest['maximum_active_workers']==workers
        assert len({task['pid'] for task in manifest['runs']})==4
        assert all(task['status']=='complete' for task in manifest['runs'])
        users=pd.read_csv(output/'baselines/seed_5/full_run/1_user-stats.csv')
        assert len(users)==100 and users.request_id.is_unique
        assert users.pickup_time.notna().equals(users.dropoff_time.notna())
        decisions=pd.read_csv(output/'baselines/seed_5/full_run/driver_acceptance_op_0.csv')
        assert set(decisions[decisions.accepted].request_id)==set(users[users.dropoff_time.notna()].request_id)
        for arm in ['baseline','candidate']:
            cohorts=[]
            for index in [0,1]:
                run=output/'tasks/seed_5'/f'window_{index}'/arm/'run'
                rows=pd.read_csv(run/'cohort_observations.csv')
                cohorts.extend(rows.request_id)
                assert rows.rq_time.ge(index*3600).all() and rows.rq_time.lt((index+1)*3600).all()
                assert rows.dropoff_time.dropna().lt((index+1)*3600+300).all()
                assert set(rows.status)<={'completed','rejected','accepted_censored','picked_up_censored','unresolved_censored'}
                assert (run/'window_final_state.csv').is_file()
                credit=pd.read_csv(run/'cohort_drivers.csv')
                assert credit.completed_cohort_trips.sum()==rows.status.eq('completed').sum()
                assert credit.completed_cohort_gross_fare_cent.sum()==rows.fare.sum()
                state=json.loads((run/'window_state.json').read_text())
                assert state['cohort_count']==len(rows) and state['request_count']==100
                if arm=='candidate':
                    active=state['active_policy']
                    assert active['ranked']==flag.startswith('ranked')
                    assert active['rematch']==flag.startswith('rematch')
                    assert active['future_value']==('future' in flag)
                    if 'menus' in flag:assert active['choice']=='logit'
                    for feature in ['ranked_insertion' if active['ranked'] else 'forbid_rematch']:
                        assert len(pd.read_csv(run/f'{feature}_op_0.csv'))>0
                    if active['future_value']:assert len(pd.read_csv(run/'future_value_op_0.csv'))>0
            assert len(cohorts)==len(set(cohorts))==100
    # Capturing/force-flushing state must also preserve the ordinary full simulation.
    command(['-m','tools.paired_eval.worker','--constant-config',str(constant),'--scenarios',str(baseline),
             '--seed','5','--study-name','example_study','--output',str(tmp_path/'ordinary'),
             '--network-tt-noise-sigma','.3','--record-promised-times'],tmp_path/'ordinary.txt')
    for name in ['1_user-stats.csv','standard_eval.csv','2-0_op-stats.csv','driver_acceptance_op_0.csv','final_state.csv']:
        pd.testing.assert_frame_equal(pd.read_csv(tmp_path/'ordinary'/name),
            pd.read_csv(tmp_path/'workers_1/baselines/seed_5/full_run'/name),check_exact=True)
    for name in ['seed_window_summary.csv','paired_window_comparison.csv']:
        pd.testing.assert_frame_equal(pd.read_csv(tmp_path/'workers_1'/name),pd.read_csv(tmp_path/'workers_2'/name),check_exact=True)
    for index in [0,1]:
        for arm in ['baseline','candidate']:
            for name in ['cohort_observations.csv','cohort_drivers.csv','window_final_state.csv','2-0_op-stats.csv']:
                suffix=Path('tasks/seed_5')/f'window_{index}'/arm/'run'/name
                pd.testing.assert_frame_equal(pd.read_csv(tmp_path/'workers_1'/suffix),
                    pd.read_csv(tmp_path/'workers_2'/suffix),check_exact=True)
