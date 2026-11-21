"""Exact pre-call count guard; bootstrap and replay cannot be hidden as actual."""
from contextlib import contextmanager
from pathlib import Path
import time

class NativeBudget:
 def __init__(self,window):
  self.window=dict(window);self.stage='bootstrap';self.actual=0;self.replay=0;self.inflight=None;self.actual_data=None;self.history=[]
 def check(self):
  assert self.window['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  assert min(self.window['absolute_deadline_unix']-time.time(),self.window['hard_stop_monotonic']-time.monotonic())>5,'ZERO200_ROOT_DUAL_CLOCK_EXHAUSTED'
 def bind_actual(self,data):
  assert self.stage=='bootstrap'and self.actual_data is None and self.inflight is None
  assert float(data.time)==0.;self.actual_data=data
 def enter(self,stage):
  assert self.inflight is None and self.actual_data is not None
  order=['bootstrap','actual_zero_tail','allocator','own_replay','closed']
  assert stage in order and order.index(stage)==order.index(self.stage)+1,'ZERO200_STAGE_REWIND_OR_SKIP'
  if stage=='allocator':assert self.actual==200,'INCOMPLETE_ACTUAL200_TAIL'
  if stage=='closed':assert self.replay==200,'INCOMPLETE_OWN_REPLAY200'
  self.check();self.history.append(dict(from_stage=self.stage,to_stage=stage,actual=self.actual,replay=self.replay));self.stage=stage
 def call(self,original,model,data):
  self.check();assert self.inflight is None
  assert self.stage in {'actual_zero_tail','own_replay'},'NATIVE_STEP_FORBIDDEN_IN_CURRENT_STAGE'
  field='actual'if self.stage=='actual_zero_tail'else'replay'
  assert (data is self.actual_data)==(field=='actual'),'ACTUAL_REPLAY_STATE_OWNER_MISMATCH'
  assert getattr(self,field)<200,'ZERO200_NATIVE_CAP_EXHAUSTED'
  self.inflight=field;value=original(model,data);setattr(self,field,getattr(self,field)+1);self.inflight=None;return value
 def snapshot(self):
  return dict(stage=self.stage,actual_native=None if self.inflight=='actual'else self.actual,own_replay_native=None if self.inflight=='replay'else self.replay,inflight_unknown=self.inflight,completed_actual_lower_bound=self.actual,completed_replay_lower_bound=self.replay,history=self.history)

@contextmanager
def guard_native_API(mj,budget):
 original={name:getattr(mj,name)for name in ['mj_step','mj_step1','mj_step2']}
 def step(model,data):return budget.call(original['mj_step'],model,data)
 def forbidden(*_,**__):raise RuntimeError('SPLIT_NATIVE_INTEGRATION_UNREGISTERED')
 mj.mj_step=step;mj.mj_step1=forbidden;mj.mj_step2=forbidden
 try:yield step
 finally:
  for name,value in original.items():setattr(mj,name,value)
