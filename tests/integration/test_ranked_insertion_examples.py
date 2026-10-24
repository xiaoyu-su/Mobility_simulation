import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest
import yaml

from tools.paired_eval.metrics import per_driver_metrics

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT/'tests/regression/run_example.py'


def run(example, settings, output, noise=.3):
    config = output.with_suffix('.yaml')
    config.write_text(yaml.safe_dump(settings))
    result = subprocess.run([sys.executable, str(RUNNER), example, '--source-root', str(ROOT),
                             '--output', str(output), '--driver-acceptance-config', str(config),
                             '--network-tt-noise-sigma', str(noise)], cwd=ROOT,
                            capture_output=True, text=True, timeout=180,
                            env=dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', PYTHONHASHSEED='0'))
    assert result.returncode == 0, result.stdout+'\n'+result.stderr
    assert (output/'final_state.csv').is_file()
    users = pd.read_csv(output/'1_user-stats.csv')
    decisions = pd.read_csv(output/'driver_acceptance_op_0.csv')
    assert len(users) == 100 and users.request_id.is_unique
    assert set(decisions[decisions.accepted].request_id) == set(users[users.dropoff_time.notna()].request_id)
    assert not decisions[decisions.accepted].request_id.duplicated().any()
    assert set(decisions[decisions.terminal_decline].request_id).isdisjoint(set(decisions[decisions.accepted].request_id))
    assert (users.promised_pickup_time.notna() == users.dropoff_time.notna()).all()
    per_driver_metrics(output)
    return users


@pytest.mark.integration
@pytest.mark.parametrize('example', ['insertion', 'immediate_batch'])
@pytest.mark.parametrize('mode', ['always', 'never', 'logistic', 'future'])
def test_complete_ranked_insertions_try_distinct_drivers_and_finish_bookings(example, mode, tmp_path):
    settings = dict(op_driver_acceptance='logistic', op_driver_acceptance_max_declines=0,
                    op_driver_acceptance_weight_objective=True, op_driver_choice_model='singleton',
                    op_driver_acceptance_ranked_fallback=True)
    if mode in ('always','never'):
        settings['op_driver_acceptance_probability'] = 1 if mode == 'always' else 0
    else:
        settings.update(op_driver_acceptance_intercept=0, op_driver_acceptance_beta_eta=-.15,
                        op_driver_acceptance_beta_value=.1)
    if mode == 'future':
        settings.update(op_driver_acceptance_future_value=True, op_driver_acceptance_future_value_top_k=3)
    output = tmp_path/'ranked'
    users = run(example, settings, output)
    rows = pd.read_csv(output/'ranked_insertion_op_0.csv')
    audit = json.loads((output/'ranked_insertion_op_0.json').read_text())
    assert not rows.duplicated(['request_id','vehicle_id']).any()
    assert audit['counters']['accepted_requests'] == users.dropoff_time.notna().sum()
    assert audit['counters']['offers'] == len(rows)
    assert audit['counters']['requests'] == 100
    for _, group in rows.groupby('request_id', sort=False):
        assert list(group.candidate_rank) == list(range(1,len(group)+1))
        assert group.delta_objective.is_monotonic_increasing
        assert group.accepted.sum() <= 1
        if group.accepted.any():
            assert group.iloc[-1].accepted and not group.terminal_request_decline.any()
        else:
            assert group.iloc[-1].terminal_request_decline
            assert group.iloc[-1].candidate_rank == group.iloc[-1].candidate_count
    if mode == 'always':
        assert rows.candidate_rank.eq(1).all()
        control = tmp_path/'control'
        run(example, {**settings, 'op_driver_acceptance_ranked_fallback':False}, control)
        for name in ['1_user-stats.csv','standard_eval.csv','driver_acceptance_op_0.csv','driver_choice_op_0.csv']:
            pd.testing.assert_frame_equal(pd.read_csv(output/name),pd.read_csv(control/name),check_exact=True)
    elif mode == 'never':
        assert users.dropoff_time.isna().all() and not rows.accepted.any()
    else:
        assert audit['counters']['fallback_acceptances'] > 0
        assert rows.candidate_rank.gt(1).any()
        if mode == 'future':
            assert (output/'future_value_op_0.csv').is_file()


@pytest.mark.integration
@pytest.mark.parametrize('example',['insertion','immediate_batch','batch'])
def test_explicit_false_is_exactly_the_existing_path(example,tmp_path):
    settings = dict(op_driver_acceptance='logistic',op_driver_acceptance_intercept=0,
                    op_driver_acceptance_beta_eta=-.15,op_driver_acceptance_beta_value=.1,
                    op_driver_acceptance_max_declines=0,op_driver_choice_model='singleton')
    run(example,settings,tmp_path/'plain')
    run(example,{**settings,'op_driver_acceptance_ranked_fallback':False},tmp_path/'disabled')
    for name in ['1_user-stats.csv','standard_eval.csv','driver_acceptance_op_0.csv','driver_choice_op_0.csv']:
        pd.testing.assert_frame_equal(pd.read_csv(tmp_path/'plain'/name),pd.read_csv(tmp_path/'disabled'/name),check_exact=True)
    assert not (tmp_path/'disabled/ranked_insertion_op_0.csv').exists()


@pytest.mark.integration
@pytest.mark.parametrize('choice',['off','logit'])
def test_ranked_driver_classes_with_and_without_singleton_choice_adapter(choice,tmp_path):
    scenario=yaml.safe_load((ROOT/'studies/example_study/scenarios/example_ir_ranked_classes.yaml').read_text())[0]
    settings={k:v for k,v in scenario.items() if k.startswith('op_driver_')}
    settings['op_driver_choice_model']=choice
    output=tmp_path/'classes'
    run('insertion',settings,output)
    decisions=pd.read_csv(output/'driver_acceptance_op_0.csv')
    audit=json.loads((output/'ranked_insertion_op_0.json').read_text())
    assert set(decisions.driver_class)=={'full_time','part_time'}
    assert audit['counters']['fallback_acceptances']>0
    assert (output/'driver_choice_op_0.csv').exists()==(choice!='off')
