"""Single bounded job, polled without blocking ROS observations/brake timers."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


class PlanningJob:
    def __init__(self,folder,worker=None,timeout_s=20.,hard_stop_monotonic=None):
        self.folder=Path(folder);self.worker=Path(worker or Path(__file__).with_name('route_worker.py'))
        self.timeout_s=timeout_s;self.hard_stop=hard_stop_monotonic;self.job=None;self.log=None
        self.started=None;self.sequence=0;self.request=None;self.result_path=None

    def start(self,request):
        assert self.job is None,'PLANNER_ALREADY_ACTIVE'
        if self.hard_stop is not None:assert self.hard_stop-time.monotonic()>self.timeout_s+5,'PLANNER_ROOT_RESERVE'
        self.folder.mkdir(exist_ok=True);self.sequence+=1
        self.request=dict(request,request_id=self.sequence)
        path=self.folder/('request%02d.json'%self.sequence);self.result_path=self.folder/('result%02d.json'%self.sequence)
        assert not path.exists() and not self.result_path.exists(),'PLANNER_RESULT_OVERWRITE'
        path.write_text(json.dumps(self.request,allow_nan=False)+'\n')
        self.log=(self.folder/('worker%02d.console'%self.sequence)).open('x')
        env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='');env.pop('LD_PRELOAD',None);env['PHASE_BOUNDED_WRITER_ROLE']='PLANNER'
        self.job=subprocess.Popen(['taskset','-c','4',sys.executable,'-B',str(self.worker),str(path),str(self.result_path)],env=env,stdout=self.log,stderr=subprocess.STDOUT,start_new_session=True)
        self.started=time.monotonic()

    def poll(self):
        assert self.job is not None
        if time.monotonic()-self.started>=self.timeout_s or (self.hard_stop is not None and time.monotonic()>=self.hard_stop-5):
            self.cancel();return dict(passed=False,functional_timeout=True,error_class='BOUNDED_PLANNING_TIMEOUT',request_id=self.sequence)
        code=self.job.poll()
        if code is None:return None
        self.job.wait();self.job=None;self.log.close();self.log=None
        assert code==0 and self.result_path.is_file(),'PLANNER_EXIT_OR_RESULT_MISSING'
        value=json.loads(self.result_path.read_text());assert value['request_id']==self.sequence,'FOREIGN_PLANNER_RESULT'
        assert value['models']==0 and value['physical_native']==0,'PLANNER_PHYSICAL_SCOPE'
        return value

    def cancel(self):
        if self.job is not None:
            if self.job.poll() is None:
                os.killpg(self.job.pid,signal.SIGTERM)
                try:self.job.wait(timeout=2)
                except subprocess.TimeoutExpired:os.killpg(self.job.pid,signal.SIGKILL);self.job.wait(timeout=2)
            self.job=None
        if self.log is not None:self.log.close();self.log=None
