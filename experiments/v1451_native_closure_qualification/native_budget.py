"""Shared clocks, exact pre-call accounting and permanent no-private-model guard."""
from contextlib import contextmanager
from pathlib import Path
import sys
import time
R=Path(__file__).resolve().parents[2]
CAPS={'bootstrap':180,'actual_zero_tail':120,'allocator':120,'own_replay':120,'closed':60}
class NativeBudget:
 def __init__(self,window):
  self.window=dict(window);self.stage='bootstrap';self.actual=0;self.replay=0;self.inflight=None;self.actual_data=None;self.replay_data=None;self.history=[]
  self.actual_compute=0;self.allocator_compute=0;self.compute_inflight=None;self.violations=[];self._set_phase_clock()
 def _set_phase_clock(self):
  self.phase_end_unix=min(self.window['absolute_deadline_unix']-5,time.time()+CAPS[self.stage])
  self.phase_end_monotonic=min(self.window['hard_stop_monotonic']-5,time.monotonic()+CAPS[self.stage])
 def remaining(self):
  assert self.window['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'ZERO200_BOOT_CHANGED'
  return min(self.window['absolute_deadline_unix']-time.time()-5,self.window['hard_stop_monotonic']-time.monotonic()-5,self.phase_end_unix-time.time(),self.phase_end_monotonic-time.monotonic())
 def check(self):assert self.remaining()>0,'ZERO200_SHARED_DUAL_CLOCK_EXHAUSTED'
 def bind_actual(self,data):
  assert self.stage=='bootstrap'and self.actual_data is None and self.inflight is None
  assert float(data.time)==0.;self.actual_data=data
 def enter(self,stage):
  self.check();assert self.inflight is None and self.compute_inflight is None and self.actual_data is not None
  order=list(CAPS);assert stage in order and order.index(stage)==order.index(self.stage)+1,'ZERO200_STAGE_REWIND_OR_SKIP'
  if stage=='allocator':assert self.actual==200,'INCOMPLETE_ACTUAL200_TAIL'
  if stage=='own_replay':assert self.allocator_compute==200,'INCOMPLETE_ALLOCATOR200'
  if stage=='closed':assert self.replay==200,'INCOMPLETE_OWN_REPLAY200'
  self.history.append(dict(from_stage=self.stage,to_stage=stage,actual=self.actual,replay=self.replay,unix=time.time(),monotonic=time.monotonic()));self.stage=stage;self._set_phase_clock()
 def call(self,original,model,data):
  self.check();assert self.inflight is None
  assert self.stage in {'actual_zero_tail','own_replay'},'NATIVE_STEP_FORBIDDEN_IN_CURRENT_STAGE'
  field='actual'if self.stage=='actual_zero_tail'else'replay'
  assert (data is self.actual_data)==(field=='actual'),'ACTUAL_REPLAY_STATE_OWNER_MISMATCH'
  if field=='replay':
   if self.replay_data is None:self.replay_data=data
   assert self.replay_data is data,'REPLAY_STATE_RESET_OR_OWNER_CHANGED'
  assert getattr(self,field)<200,'ZERO200_NATIVE_CAP_EXHAUSTED'
  self.inflight=field;value=original(model,data);setattr(self,field,getattr(self,field)+1);self.inflight=None;return value
 def profile(self,frame,event,arg):
  name=frame.f_code.co_name;file=frame.f_code.co_filename
  if event=='c_call'and getattr(arg,'__name__','')in {'mj_step','mj_step1','mj_step2'}:
   assert getattr(arg,'__name__','')=='mj_step'and self.inflight is not None,'UNCOUNTED_OR_SPLIT_NATIVE_C_CALL'
  if event=='call'and file.startswith(str(R)+'/'):
   leaf=file.rsplit('/',1)[-1]
   if name in {'step','__init__'}and leaf in {'coupled_model.py','prediction.py','kernel.py'}:
    self.violations.append(leaf+':'+name);raise RuntimeError('ZERO200_PRIVATE_MODEL_FORBIDDEN')
   if name=='compute'and leaf in {'coupled_control.py','vehicle_control.py'}:
    assert self.stage in {'actual_zero_tail','allocator'},'ALLOCATOR_COMPUTE_FORBIDDEN_IN_CURRENT_STAGE'
    if leaf=='coupled_control.py':
     self.check();assert self.compute_inflight is None
     field='actual_compute'if self.stage=='actual_zero_tail'else'allocator_compute'
     assert getattr(self,field)<200,'ZERO200_ALLOCATOR_COMPUTE_CAP'
     self.compute_inflight=(id(frame),field)
  if event=='return'and self.compute_inflight is not None and id(frame)==self.compute_inflight[0]:
   if arg is not None:
    field=self.compute_inflight[1];setattr(self,field,getattr(self,field)+1);self.compute_inflight=None
 def snapshot(self):
  return dict(stage=self.stage,actual_native=None if self.inflight=='actual'else self.actual,own_replay_native=None if self.inflight=='replay'else self.replay,inflight_unknown=self.inflight,completed_actual_lower_bound=self.actual,completed_replay_lower_bound=self.replay,actual_allocator_computations=None if self.compute_inflight and self.compute_inflight[1]=='actual_compute'else self.actual_compute,independent_allocator_recomputations=None if self.compute_inflight and self.compute_inflight[1]=='allocator_compute'else self.allocator_compute,compute_inflight_unknown=None if self.compute_inflight is None else self.compute_inflight[1],completed_actual_compute_lower_bound=self.actual_compute,completed_independent_compute_lower_bound=self.allocator_compute,private_prediction_native=0,violations=list(self.violations),history=self.history)

@contextmanager
def guard_native_API(mj,budget):
 original={name:getattr(mj,name)for name in ['mj_step','mj_step1','mj_step2']};setprofile=sys.setprofile;previous=sys.getprofile()
 def step(model,data):return budget.call(original['mj_step'],model,data)
 def forbidden(*_,**__):raise RuntimeError('SPLIT_NATIVE_INTEGRATION_UNREGISTERED')
 def install(replacement):
  if getattr(replacement,'_zero200_guard',False):return setprofile(replacement)
  def composed(frame,event,arg):
   budget.profile(frame,event,arg)
   if replacement is not None:replacement(frame,event,arg)
  composed._zero200_guard=True;setprofile(composed)
 mj.mj_step=step;mj.mj_step1=forbidden;mj.mj_step2=forbidden;sys.setprofile=install;install(previous)
 try:yield step
 finally:
  sys.setprofile=setprofile;setprofile(previous)
  for name,value in original.items():setattr(mj,name,value)
