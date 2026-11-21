"""One boot and dual-clock stage budget under the original90min root window."""
from pathlib import Path
import time

class PhaseBudget:
 def __init__(self,window,limits):
  self.window=dict(window);self.limits=limits;self.caps=dict(limits['phase_wall_caps_s'])
  assert sum(self.caps.values())+limits['root_guard_slack_s']==5400 and limits['maximum_task_wall_s']==5400
  assert window['absolute_deadline_unix']<=1795395600 and 0<window['absolute_deadline_unix']-window['started_unix']<=5400
  self.active=None;self.started=None;self.used={key:0. for key in self.caps};self.records=[]
 def remaining(self):
  assert self.window['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  return min(self.window['absolute_deadline_unix']-time.time(),self.window['hard_stop_monotonic']-time.monotonic())
 def enter(self,name):
  assert name in self.caps and self.active is None,'PHASE_OVERLAP_OR_UNKNOWN'
  self.remaining();self.active=name;self.started=(time.time(),time.monotonic());self.check();return self.deadlines()
 def check(self):
  assert self.active is not None and self.started is not None
  elapsed=max(time.time()-self.started[0],time.monotonic()-self.started[1])
  assert elapsed>=0 and self.used[self.active]+elapsed<self.caps[self.active],'CURRENT_PHASE_WALL_CAP_EXHAUSTED'
  assert self.remaining()>5,'ROOT_PHASE_DUAL_CLOCK_EXHAUSTED'
  return elapsed
 def deadlines(self):
  left=self.caps[self.active]-self.used[self.active]
  return dict(absolute_deadline_unix=min(self.started[0]+left,self.window['absolute_deadline_unix']-5),hard_stop_monotonic=min(self.started[1]+left,self.window['hard_stop_monotonic']-5),boot_id=self.window['boot_id'])
 def leave(self):
  assert self.active is not None
  elapsed=max(time.time()-self.started[0],time.monotonic()-self.started[1]);self.used[self.active]+=max(0.,elapsed)
  record=dict(phase=self.active,elapsed_wall_s=elapsed,phase_used_s=self.used[self.active],phase_cap_s=self.caps[self.active],root_remaining_s=self.remaining());self.records.append(record);self.active=None;self.started=None;return record
