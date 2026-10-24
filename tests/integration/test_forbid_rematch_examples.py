import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest
import yaml

from tools.paired_eval.metrics import per_driver_metrics,driver_acceptance_summary

ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/'tests/regression/run_example.py'


def run(settings,output,example='batch',noise=.3):
    config=output.with_suffix('.yaml');config.write_text(yaml.safe_dump(settings))
    result=subprocess.run([sys.executable,str(RUNNER),example,'--source-root',str(ROOT),'--output',str(output),
                           '--driver-acceptance-config',str(config),'--network-tt-noise-sigma',str(noise)],cwd=ROOT,
                          capture_output=True,text=True,timeout=180,
                          env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONHASHSEED='0'))
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    assert (output/'final_state.csv').is_file()
    users=pd.read_csv(output/'1_user-stats.csv');decisions=pd.read_csv(output/'driver_acceptance_op_0.csv')
    assert len(users)==100 and users.request_id.is_unique
    accepted=decisions.loc[decisions.accepted.astype(bool)]
    terminal=decisions.loc[decisions.terminal_decline.astype(bool)]
    assert set(accepted.request_id)==set(users[users.dropoff_time.notna()].request_id)
    assert set(terminal.request_id).isdisjoint(set(accepted.request_id))
    assert not accepted.request_id.duplicated().any()
    assert (users.promised_pickup_time.notna()==users.dropoff_time.notna()).all()
    per_driver_metrics(output);driver_acceptance_summary(output)
    return users


@pytest.mark.integration
@pytest.mark.parametrize('mode',['always','never','zero_reward','singleton','menus','future'])
def test_native_batch_rematching_never_reoffers_declined_edges_or_loses_bookings(mode,tmp_path):
    settings=dict(op_driver_acceptance='logistic',op_driver_acceptance_max_declines=0,
                  op_driver_acceptance_weight_objective=True,op_driver_acceptance_forbid_rematch=True)
    if mode in ['always','never','zero_reward']:settings['op_driver_acceptance_probability']=1 if mode=='always' else 0
    else:settings.update(op_driver_acceptance_intercept=0,op_driver_acceptance_beta_eta=-.15,op_driver_acceptance_beta_value=.1)
    if mode=='singleton':settings['op_driver_choice_model']='singleton'
    if mode=='menus':settings['op_driver_choice_model']='logit'
    if mode=='future':settings.update(op_driver_acceptance_future_value=True,op_driver_acceptance_future_value_top_k=3)
    if mode=='never':settings['op_driver_acceptance_weight_objective']=False
    output=tmp_path/'rematch';users=run(settings,output)
    d=pd.read_csv(output/'driver_acceptance_op_0.csv');rows=pd.read_csv(output/'forbid_rematch_op_0.csv')
    audit=json.loads((output/'forbid_rematch_op_0.json').read_text());c=audit['counters']
    assert not d.duplicated(['request_id','vehicle_id']).any()
    assert not rows.duplicated(['request_id','vehicle_id']).any()
    assert c['offered_pairs']==len(rows)==len(d)
    assert c['accepted_requests']==users.dropoff_time.notna().sum()
    assert c['terminal_requests']==d.terminal_decline.sum()
    assert c['forbidden_pairs']==rows.edge_forbidden.sum()==(~d.accepted).sum()
    if mode=='always':
        assert c['solver_resolves']==0 and d.uniform_draw.isna().all()
        control=tmp_path/'control';run({**settings,'op_driver_acceptance_forbid_rematch':False},control)
        for name in ['1_user-stats.csv','standard_eval.csv','driver_acceptance_op_0.csv']:
            pd.testing.assert_frame_equal(pd.read_csv(output/name),pd.read_csv(control/name),check_exact=True)
    elif mode=='never':
        assert users.dropoff_time.isna().all() and not d.accepted.any() and c['solver_resolves']>0
    elif mode=='zero_reward':
        assert users.dropoff_time.isna().all() and d.empty and rows.empty and c['solver_resolves']==0
    else:
        assert c['solver_resolves']>0
        if mode!='menus':assert c['recovered_requests']>0
        if mode=='menus':
            assert rows.groupby(['round','vehicle_id']).accepted.sum().le(1).all()
            choice=json.loads((output/'driver_choice_op_0.json').read_text())
            assert choice['counters']['multi_item_episodes']>0
        if mode=='future':assert (output/'future_value_op_0.csv').is_file()


@pytest.mark.integration
@pytest.mark.parametrize('example',['insertion','immediate_batch','batch'])
def test_explicit_disabled_rematching_retains_existing_outputs(example,tmp_path):
    settings=dict(op_driver_acceptance='logistic',op_driver_acceptance_max_declines=0,
                  op_driver_acceptance_intercept=0,op_driver_acceptance_beta_eta=-.15,
                  op_driver_acceptance_beta_value=.1,op_driver_choice_model='singleton')
    run(settings,tmp_path/'plain',example)
    run({**settings,'op_driver_acceptance_forbid_rematch':False},tmp_path/'off',example)
    for name in ['1_user-stats.csv','standard_eval.csv','driver_acceptance_op_0.csv','driver_choice_op_0.csv']:
        pd.testing.assert_frame_equal(pd.read_csv(tmp_path/'plain'/name),pd.read_csv(tmp_path/'off'/name),check_exact=True)
    assert not (tmp_path/'off/forbid_rematch_op_0.csv').exists()
