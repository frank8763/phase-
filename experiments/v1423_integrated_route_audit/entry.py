"""Actual unified native/audit binding entry; zero construction and integration."""
import ast
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
class NoPhysical(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('INTEGRATED_ENTRY_NO_PHYSICAL:'+name)
def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 assert sys.argv[1:]==['--entry-check']and os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 assert not(O/'ENTRY_QUALIFICATION.json').exists();os.chdir(R);sys.meta_path.insert(0,NoPhysical());calls=[]
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:
   calls.append(frame.f_code.co_name);raise AssertionError('INTEGRATED_ZERO_MODEL_CONSTRUCTOR_OR_STEP')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==5
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  lifecycle=exact('v1423_unified_lifecycle',C/'lifecycle.py');audit=exact('v1423_integrated_recorded_audit',C/'audit.py');allocation=exact('v1423_independent_allocator_binding',C/'allocation.py')
  old,Adapter,factory,replay=lifecycle.physical_binding(O)
  assert Path(Adapter.compute.__code__.co_filename).resolve()==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
  assert Path(lifecycle.owner_module.native_module.NativeStep.apply.__code__.co_filename).resolve()==C/'native_step.py'
  assert Path(lifecycle.owner_module.transaction_module.owner.OwnerRequest.__init__.__code__.co_filename).resolve()==R/'experiments/v1422_ordered_route_event/event_owner.py'
  # Budget call executes before any reserve/private or physical operation. This
  # synthetic owner only exercises the real no-model guard, never a plant step.
  from types import SimpleNamespace
  native=lifecycle.owner_module.native_module.NativeStep.__new__(lifecycle.owner_module.native_module.NativeStep);native.vehicle=SimpleNamespace(count=0);native.applied=0;native.in_step=False;events=[]
  def exhausted(stage,n):events.append((stage,n));raise RuntimeError('QUALIFIED_PER_NATIVE_BUDGET_EXHAUSTED')
  native.before_native_budget=exhausted
  try:native.apply(0.,0.,phase='ENTRY_ONLY',control_owner='DISCLOSED_SHARED_EXECUTION_BRIDGE',delivery=None)
  except RuntimeError as exc:assert str(exc)=='QUALIFIED_PER_NATIVE_BUDGET_EXHAUSTED'
  else:raise AssertionError('NATIVE_BUDGET_DID_NOT_STOP_BEFORE_CERTIFICATE')
  assert events==[('ACTUAL_NATIVE',1)]
  # Real receipt parser rejects omissions/mutation/duplicates before any audit
  # can publish PASS. These are tiny software rows, not model or plant evidence.
  row=dict(before_native=0,applied=False,request=[0.,0.,False]);after=dict(row,applied=True);identity=audit.recorded.digest(row)
  valid=[dict(kind='BEFORE_NATIVE',row=row,source_row_sha256=identity),dict(kind='AFTER_NATIVE',row=after,source_row_sha256=identity)]
  assert audit.recorded.receipts(valid,before_kind='BEFORE_NATIVE',after_kind='AFTER_NATIVE',bound_hash=True)==[after]
  negatives=[]
  for name,data in [('missing_after',valid[:1]),('changed_request',[valid[0],dict(valid[1],row=dict(after,request=[.1,0.,False]))]),('duplicate_after',valid+[valid[1]])]:
   try:audit.recorded.receipts(data,before_kind='BEFORE_NATIVE',after_kind='AFTER_NATIVE',bound_hash=True)
   except AssertionError:negatives.append(name)
   else:raise AssertionError('INCOMPLETE_RECEIPT_ACCEPTED:'+name)
  try:lifecycle.admit({}, {}, {})
  except lifecycle.NotAdmitted as exc:assert str(exc)=='ACTUAL_ROUTE_FULL_QUALIFICATION_AND_BUDGET_MISSING'
  else:raise AssertionError('PREPARATION_ADMITTED_ACTUAL_MODELS')
  assert not calls
  value=dict(passed=True,models=0,analytical_native=0,physical_native=0,actual_cpu=[2],original_writeguard=True,constructor_step_profile_guard=True,unified_current_event_owner_native_lifecycle_binding=True,real_factory_replay_original_adapter_imported_without_models=True,budget_guard_before_private_or_actual_work=True,recorded_receipt_negatives=negatives,complete_recorded_actual_audit_unexecuted=True,independent_allocator_recomputation_unexecuted=True,full_route_admission=False,source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.glob('*')if p.is_file()})
  lifecycle.io.atomic(O/'ENTRY_QUALIFICATION.json',value);print(json.dumps(value))
if __name__=='__main__':main()
