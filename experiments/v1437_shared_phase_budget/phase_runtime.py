"""Production stage transition receipts; clocks never change an event source."""
import copy
import importlib.util
from pathlib import Path
import signal
import time

C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1437_shared_phase_clock',C/'phase_budget.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class PhaseRuntime:
 def __init__(self,window,limits,save):
  self.budget=m.PhaseBudget(window,limits);self.save=save
 def transition(self,name):
  signal.setitimer(signal.ITIMER_REAL,0)
  if self.budget.active is not None:self.budget.leave()
  try:
   end=self.budget.enter(name)
  finally:self.save(self.budget.snapshot())
  signal.setitimer(signal.ITIMER_REAL,max(.001,min(end['absolute_deadline_unix']-time.time(),end['hard_stop_monotonic']-time.monotonic())))
  return end
 def check(self,name):
  assert self.budget.active==name,'WRONG_EXECUTION_PHASE'
  return self.budget.check()
 def finish(self):
  signal.setitimer(signal.ITIMER_REAL,0)
  if self.budget.active is not None:self.budget.leave()
  value=self.budget.snapshot();self.save(value);return value

class NativePhaseGate:
 def __init__(self,runtime,limits,vehicle,capture):
  self.runtime=runtime;self.limits=limits;self.vehicle=vehicle;self.capture=capture
 def __call__(self,stage,requested):
  assert type(requested)is int and requested>=0,'INVALID_NATIVE_COUNT_REQUEST'
  stopping=stage=='ACTUAL_STOP_TAIL'
  self.runtime.check('complete_zero_tail'if stopping else'normal')
  vehicle=self.vehicle()
  if vehicle is not None:
   cap=self.limits['maximum_actual_native']-(0 if stopping else 200)
   assert vehicle.count+requested<=cap,'ACTUAL_ROUTE_NATIVE_BUDGET'
   capture=self.capture()
   if capture is not None and requested:capture.update(vehicle,requested_native=requested)

def bind_stop_authority(owner,runtime):
 """Use only the preregistered stop stage; retain all source/budget fields."""
 runtime.check('complete_zero_tail');end=runtime.budget.deadlines()
 before=owner.native.vehicle.count
 owner.transaction.stop_phase_entered=True
 # No new generation/audit is authorized in the stop stage. The existing
 # current reserve alone may finish within its original global count caps.
 old=copy.deepcopy(owner.authority);owner.authority.update(end)
 changed={k for k in old if old[k]!=owner.authority[k]}
 assert changed<={'absolute_deadline_unix','hard_stop_monotonic','boot_id'}
 reserve=owner.native.reserve
 if hasattr(reserve,'authority'):
  previous=copy.deepcopy(reserve.authority);reserve.authority.update(end)
  assert {k for k in previous if previous[k]!=reserve.authority[k]}<=set(end)
  assert reserve.current['input_sha256']==reserve.authority['current_input_sha256']
  assert reserve.snapshot_sha256==reserve.authority['causal_snapshot_sha256']
 assert owner.native.vehicle.count==before
 return dict(phase='complete_zero_tail',native_tick=before,only_clock_fields_changed=True,new_generation_authorized=False,deadlines=end)
