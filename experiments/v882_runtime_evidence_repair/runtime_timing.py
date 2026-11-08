"""Bounded inclusive wall/thread timers; large buffers preallocated, profile IO after loop.

Python calls still create small temporary objects. This is not a hard-real-time allocator.
"""
import gc,json,time
from pathlib import Path
import numpy as np

class Timing:
    FIELDS=('tick_before','stage_id','wall_start_s','wall_elapsed_s','thread_cpu_elapsed_s')
    def __init__(self,maximum_steps,wall=None,cpu=None):
        self.wall=wall or time.monotonic;self.cpu=cpu or time.thread_time
        self.rows=np.empty((int(maximum_steps)*16+4096,5),dtype=np.float64);self.rows.fill(0.)
        self.used=0;self.stages={};self.maximum_lag_s=0.;self.overrun=None
    def begin(self):return self.wall(),self.cpu()
    def end(self,stage,tick,stamp):
        wall=self.wall();cpu=self.cpu()
        if self.used>=len(self.rows):raise RuntimeError('BOUNDED_TIMING_BUFFER_FULL')
        sid=self.stages.setdefault(stage,len(self.stages));self.rows[self.used]=tick,sid,stamp[0],max(0.,wall-stamp[0]),max(0.,cpu-stamp[1]);self.used+=1
    def call(self,stage,tick,function,*args,**kwargs):
        start=self.begin()
        try:return function(*args,**kwargs)
        finally:self.end(stage,tick,start)
    def lag(self,tick,target,observed):
        self.maximum_lag_s=max(self.maximum_lag_s,observed-target)
        if observed-target>.1:
            self.overrun=dict(native_tick_completed=tick,target_monotonic_s=target,observed_monotonic_s=observed,lag_s=observed-target,limit_s=.1)
    def save(self,out):
        out=Path(out);array=self.rows[:self.used]
        np.savez_compressed(out/'RUNTIME_TIMING.npz',rows=array,fields=np.asarray(self.FIELDS))
        summaries={}
        for name,sid in self.stages.items():
            selected=array[array[:,1]==sid];values=selected[:,3];j=int(np.argmax(values))
            summaries[name]=dict(calls=len(values),inclusive_wall_s=float(values.sum()),p50_s=float(np.quantile(values,.5)),p95_s=float(np.quantile(values,.95)),p99_s=float(np.quantile(values,.99)),maximum_s=float(values[j]),maximum_tick_before=int(selected[j,0]),cpu_at_maximum_s=float(selected[j,4]))
        result=dict(maximum_wall_lag_s=self.maximum_lag_s,overrun=self.overrun,stages=self.stages,inclusive_stages_do_not_add=True,wall_minus_thread_cpu_is_not_unique_scheduler_attribution=True,recorded_rows=self.used,capacity=len(self.rows),summaries=summaries)
        (out/'RUNTIME_TIMING.json').write_text(json.dumps(result,indent=2)+'\n');return result

class CyclicGCWindow:
    """Collect beforeARM; defer only cyclic GC during bounded live loop; restore exact prior flag."""
    def __init__(self):self.was_enabled=gc.isenabled();self.entered=False
    def enter(self):
        if self.entered:raise RuntimeError('GC_WINDOW_REENTERED')
        if self.was_enabled:gc.collect();gc.disable()
        self.entered=True
    def close(self):
        if not self.entered:return
        if self.was_enabled:gc.enable()
        else:gc.disable()
        self.entered=False
