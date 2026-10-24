import json
from pathlib import Path
import subprocess
import sys

import pytest

from tools.windowed_eval.pool import run_pool
from tools.windowed_eval.__main__ import ROOT,validate


def task(tmp_path,index):
    job=tmp_path/f'job{index}.json'
    job.write_text(json.dumps({'snapshot':str(tmp_path/'missing'),'output':str(tmp_path/f'out{index}')}))
    return dict(id=str(index),job=str(job),log=str(tmp_path/f'worker{index}.txt'),status='pending')


def test_real_worker_failure_preserves_log_and_does_not_launch_pending_jobs(tmp_path):
    tasks=[task(tmp_path,0),task(tmp_path,1)];saved=[]
    with pytest.raises(RuntimeError,match='failed'):
        run_pool(tasks,1,30,lambda:saved.append([t['status'] for t in tasks]),ROOT)
    assert tasks[0]['returncode']!=0 and tasks[0]['status']=='failed'
    assert tasks[1]['status']=='pending' and not Path(tasks[1]['log']).exists()
    assert 'FileNotFoundError' in Path(tasks[0]['log']).read_text()
    assert saved


def test_timeout_kills_real_process_and_records_failure(tmp_path,monkeypatch):
    real=subprocess.Popen
    monkeypatch.setattr('tools.windowed_eval.pool.subprocess.Popen',lambda command,**kwargs:real(
        [sys.executable,'-c','import time; time.sleep(5)'],**kwargs))
    tasks=[task(tmp_path,0)]
    with pytest.raises(RuntimeError,match='timed_out'):
        run_pool(tasks,1,.15,lambda:None,ROOT)
    assert tasks[0]['status']=='timed_out' and tasks[0]['returncode']!=0


def test_failed_task_cancels_other_live_processes(tmp_path,monkeypatch):
    real=subprocess.Popen
    def launch(command,**kwargs):
        code='raise SystemExit(3)' if command[-1].endswith('job0.json') else 'import time; time.sleep(5)'
        return real([sys.executable,'-c',code],**kwargs)
    monkeypatch.setattr('tools.windowed_eval.pool.subprocess.Popen',launch)
    tasks=[task(tmp_path,0),task(tmp_path,1)]
    with pytest.raises(RuntimeError,match='failed'):run_pool(tasks,2,30,lambda:None,ROOT)
    assert tasks[0]['returncode']==3 and tasks[1]['status']=='cancelled'


def parameters():
    base=dict(op_module='PoolingIRSOnly',nr_mod_operators=1,network_type='NetworkBasicWithStore',
              rq_type='BasicRequest',sim_env='ImmediateDecisionsSimulation',random_seed=0,
              start_time=0,end_time=120,time_step=60,
              op_vr_control_func_dict={'func_key':'distance_and_user_times_with_walk','vot':.45})
    return {'baseline':dict(base),'candidate':dict(base)}


@pytest.mark.parametrize('window,cooldown,seeds,workers,timeout',[
    (0,0,[0],1,10),(61,0,[0],1,10),(60,1,[0],1,10),(60,0,[0,0],1,10),
    (60,0,[-1],1,10),(60,0,[0],0,10),(60,0,[0],1,0),
])
def test_invalid_window_controls_fail_before_any_work(window,cooldown,seeds,workers,timeout):
    with pytest.raises(ValueError):validate(parameters(),window,cooldown,seeds,workers,timeout)


@pytest.mark.parametrize('changes',[{'op_module':'PoolingIRSAssignmentBatchOptimization'},
    {'op_fleet_composition':{'default_vehtype':7}},{'network_type':'NetworkBasicCpp'},
    {'op_driver_acceptance_forbid_rematch':True}])
def test_unsupported_or_invalid_policy_swaps_are_rejected(changes):
    p=parameters();p['candidate'].update(changes)
    with pytest.raises(ValueError):validate(p,60,0,[0],1,10)


def test_window_partition_includes_a_shorter_final_window():
    p=parameters();p['baseline']['end_time']=180;p['candidate']['end_time']=180
    assert validate(p,120,60,[0,1],2,10)==[(0,0,120),(1,120,180)]
