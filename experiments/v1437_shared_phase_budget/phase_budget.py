"""One boot and dual-clock stage budget under the original90min root window."""
from pathlib import Path
import math
import time

class PhaseBudget:
 def __init__(self,window,limits):
  self.window=dict(window);self.limits=limits;self.caps=dict(limits['phase_wall_caps_s'])
  assert sum(self.caps.values())+limits['root_guard_slack_s']==5400 and limits['maximum_task_wall_s']==5400
  assert window['absolute_deadline_unix']<=1795395600 and 0<window['absolute_deadline_unix']-window['started_unix']<=5400
  assert list(self.caps)==['normal','complete_zero_tail','peer_close','allocator_recompute','own_fullstate_replay','recorded_audit','main_repeat_pair','final_metadata']
  assert all(type(v)in (int,float)and math.isfinite(v)and v>0 for v in self.caps.values())
  assert abs((window['hard_stop_monotonic']-window['started_monotonic'])-(window['absolute_deadline_unix']-window['started_unix']))<=1e-5
  self.active=None;self.started=None;self.used={key:0. for key in self.caps};self.records=[];self.last_index=-1
 def remaining(self):
  assert self.window['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  return min(self.window['absolute_deadline_unix']-time.time(),self.window['hard_stop_monotonic']-time.monotonic())
 def boundary(self,name):
  assert name in self.caps
  later=list(self.caps)[list(self.caps).index(name)+1:]
  reserve=sum(self.caps[k]for k in later)+self.limits['root_guard_slack_s']
  return dict(absolute_deadline_unix=self.window['absolute_deadline_unix']-reserve,hard_stop_monotonic=self.window['hard_stop_monotonic']-reserve,boot_id=self.window['boot_id'])
 def enter(self,name):
  assert name in self.caps and self.active is None,'PHASE_OVERLAP_OR_UNKNOWN'
  index=list(self.caps).index(name);assert index>self.last_index,'PHASE_REENTRY_OR_REWIND'
  self.remaining();self.active=name;self.last_index=index;self.started=(time.time(),time.monotonic());self.check();return self.deadlines()
 def check(self):
  assert self.active is not None and self.started is not None
  elapsed=max(time.time()-self.started[0],time.monotonic()-self.started[1])
  assert elapsed>=0 and self.used[self.active]+elapsed<self.caps[self.active],'CURRENT_PHASE_WALL_CAP_EXHAUSTED'
  assert self.remaining()>5,'ROOT_PHASE_DUAL_CLOCK_EXHAUSTED'
  end=self.deadlines();assert min(end['absolute_deadline_unix']-time.time(),end['hard_stop_monotonic']-time.monotonic())>0,'PHASE_RESERVED_FUTURE_EXHAUSTED'
  return elapsed
 def deadlines(self):
  left=self.caps[self.active]-self.used[self.active]
  end=self.boundary(self.active)
  return dict(absolute_deadline_unix=min(self.started[0]+left,end['absolute_deadline_unix']),hard_stop_monotonic=min(self.started[1]+left,end['hard_stop_monotonic']),boot_id=self.window['boot_id'])
 def leave(self):
  assert self.active is not None
  end=self.deadlines()
  elapsed=max(time.time()-self.started[0],time.monotonic()-self.started[1]);self.used[self.active]+=max(0.,elapsed)
  within=self.used[self.active]<self.caps[self.active]and min(end['absolute_deadline_unix']-time.time(),end['hard_stop_monotonic']-time.monotonic())>0
  record=dict(phase=self.active,elapsed_wall_s=elapsed,phase_used_s=self.used[self.active],phase_cap_s=self.caps[self.active],root_remaining_s=self.remaining(),completed_within_phase_bound=within);self.records.append(record);self.active=None;self.started=None;return record
 def snapshot(self):
  return dict(window=self.window,phase_caps=self.caps,used=self.used,records=self.records,active=self.active,started=self.started,last_index=self.last_index,models_counted_by_stage=False)
 def restore(self,value):
  assert self.active is None and self.last_index==-1
  assert value['window']==self.window and value['phase_caps']==self.caps and value['active']is None
  assert not value.get('secondary_phase_save_errors',[]),'NATIVE_PHASE_TRANSITION_EVIDENCE_GAP'
  records=value['records'];indices=[list(self.caps).index(r['phase'])for r in records]
  assert indices==sorted(set(indices))and set(value['used'])==set(self.caps)
  assert all(r['completed_within_phase_bound']is True for r in records),'EXPIRED_NATIVE_PHASE_CANNOT_ENTER_SUCCESS_AUDIT'
  assert value['last_index']==(indices[-1]if indices else -1)
  for key in self.caps:
   total=sum(r['elapsed_wall_s']for r in records if r['phase']==key)
   assert math.isfinite(total)and total>=0 and value['used'][key]==total
  self.used=dict(value['used']);self.records=list(records);self.last_index=value['last_index'];self.remaining()
