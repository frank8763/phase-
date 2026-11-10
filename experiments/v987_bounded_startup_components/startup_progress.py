"""Durable phase/progress metadata only; no sensor, state or control mutation."""
import time
from pathlib import Path
from closure import dump
from budget import check_restore
class Progress:
    def __init__(self,out,task,record,clock=time):
        self.out=Path(out);self.task=task;self.record=record;self.clock=clock;self.rows=[]
    def guard(self):check_restore(self.record,self.out,self.task['run_id'],self.clock)
    def write(self,phase,vehicle=None,**extra):
        dump(self.out/'STARTUP_PROGRESS.json',dict(phase=phase,native_tick=None if vehicle is None else vehicle.count,
            sim_time=None if vehicle is None else float(vehicle.d.time),run_id=self.task['run_id'],
            at=self.clock.time(),restore_deadline_unix=self.record['restore_deadline_unix'],new_branch_started=False,**extra))
    def stage(self,name,operation):
        self.guard();self.write(name);start=self.clock.monotonic();cpu=time.thread_time();error=None
        try:return operation()
        except BaseException as e:error=repr(e);raise
        finally:
            self.rows.append(dict(stage=name,wall_s=self.clock.monotonic()-start,thread_cpu_s=time.thread_time()-cpu,error=error))
            dump(self.out/'STARTUP_PHASES.json',dict(stages=self.rows,no_new_control_integrations=True))
