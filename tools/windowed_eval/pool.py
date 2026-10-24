"""Bounded fresh-process pool with per-task timeouts and complete failure records."""

import os
from pathlib import Path
import subprocess
import sys
import time


def run_pool(tasks,workers,timeout,save,root):
    active={};next_index=0;peak=0
    environment=dict(os.environ,PYTHONHASHSEED='0',MPLBACKEND='Agg',OMP_NUM_THREADS='1',
                     OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    try:
        while next_index<len(tasks) or active:
            while next_index<len(tasks) and len(active)<workers:
                task=tasks[next_index];next_index+=1
                log=Path(task['log']);log.parent.mkdir(parents=True,exist_ok=True)
                stream=log.open('w')
                command=[sys.executable,'-m','tools.windowed_eval.worker','--job',task['job']]
                try:
                    process=subprocess.Popen(command,cwd=root,env={**environment,'MPLCONFIGDIR':str(log.parent/'matplotlib')},
                                             stdout=stream,stderr=subprocess.STDOUT)
                except BaseException:
                    stream.close();raise
                started=time.monotonic()
                task.update(status='running',command=command,pid=process.pid,started_monotonic=started)
                active[process.pid]=(process,stream,task,started)
                peak=max(peak,len(active));save()
            for pid,(process,stream,task,started) in list(active.items()):
                code=process.poll();expired=time.monotonic()-started>timeout
                if code is None and not expired:continue
                if code is None:
                    process.kill();code=process.wait()
                stream.close();del active[pid]
                task.update(returncode=code,status='timed_out' if expired else 'complete' if code==0 else 'failed',
                            finished_monotonic=time.monotonic())
                save()
                if code or expired:raise RuntimeError(f"Window task {task['id']} {task['status']}; see {task['log']}")
            if active:time.sleep(.05)
    finally:
        for process,stream,task,started in active.values():
            if process.poll() is None:process.kill()
            task.update(returncode=process.wait(),status='cancelled',finished_monotonic=time.monotonic())
            stream.close()
        if active:save()
    return peak
