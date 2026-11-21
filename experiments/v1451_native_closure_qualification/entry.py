"""Premodel qualification and a separately admitted one-shot numerical entry."""
import argparse
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def guard(output):
 source=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(source.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=output);exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),scope);sys.addaudithook(scope['write_guard'])

class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','vehicle','factory','rclpy'}:raise AssertionError('ZERO200_ENTRY_NO_MODELS:'+name)

def qualify():
 assert not(O/'ENTRY_ONCE_CLAIM.json').exists();(O/'ENTRY_ONCE_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),models=0))+'\n')
 guard(O);finder=NoModel();sys.meta_path.insert(0,finder);original_profile=sys.getprofile()
 def no_models(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/'):
   leaf=frame.f_code.co_filename.rsplit('/',1)[-1];name=frame.f_code.co_name
   if(name in {'__init__','step'}and leaf in {'coupled_model.py','vehicle.py','prediction.py'})or(name=='compute'and leaf in {'coupled_control.py','vehicle_control.py'}):raise AssertionError('ZERO200_ENTRY_CONSTRUCTOR_COMPUTE_FORBIDDEN')
 sys.setprofile(no_models);first=None;result=dict(passed=False,models=0,physical_native=0,allocator_recomputations=0,actual_replay_native=0,software_only=True)
 contract=exact('v1451_entry_contract',C/'contract.py');io=exact('v1451_entry_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');negatives=[]
 def refused(name,fn):
  try:fn()
  except (AssertionError,RuntimeError,TimeoutError):negatives.append(name);return
  raise AssertionError('ZERO200_ENTRY_NEGATIVE_ACCEPTED:'+name)
 try:
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   driver=exact('v1451_exact_driver',C/'driver.py');budgetmod=driver.budgets
   refused('missing_narrow_admission',lambda:driver.run({}, {}, {}))
   assert not any(n in sys.modules for n in ['mujoco','vehicle','factory','rclpy'])
   now=time.time();mono=time.monotonic();w=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+600,hard_stop_monotonic=mono+600,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
   b=budgetmod.NativeBudget(w);actual=SimpleNamespace(time=0.);other=SimpleNamespace(time=0.);b.bind_actual(actual)
   refused('bootstrap_no_native',lambda:b.call(lambda *_:None,None,actual))
   refused('stage_skip',lambda:b.enter('allocator'))
   b.enter('actual_zero_tail')
   refused('actual_wrong_data',lambda:b.call(lambda *_:None,None,other))
   # Pure counter callbacks: not MuJoCo, not physical or replay integrations.
   for _ in range(200):b.call(lambda *_:None,None,actual)
   refused('actual201',lambda:b.call(lambda *_:None,None,actual))
   b.enter('allocator');refused('allocator_no_native',lambda:b.call(lambda *_:None,None,actual))
   refused('incomplete_independent_compute',lambda:b.enter('own_replay'))
   b.allocator_compute=200 # explicitly software accounting input, no compute
   b.enter('own_replay');refused('replay_actual_state',lambda:b.call(lambda *_:None,None,actual))
   for _ in range(200):b.call(lambda *_:None,None,other)
   refused('replay201',lambda:b.call(lambda *_:None,None,other));b.enter('closed')
   timed=budgetmod.NativeBudget(w);timed.phase_end_monotonic=time.monotonic()-1
   refused('phase_timeout',timed.check)
   badclock=dict(w,boot_id='wrong');refused('wrong_boot',budgetmod.NativeBudget(badclock).check)
   unknown=budgetmod.NativeBudget(w);unknown.bind_actual(actual);unknown.enter('actual_zero_tail')
   def failing(*_):raise RuntimeError('SOFTWARE_NATIVE_CALL_FAILURE')
   refused('native_inflight_failure',lambda:unknown.call(failing,None,actual));snap=unknown.snapshot();assert snap['actual_native']is None and snap['completed_actual_lower_bound']==0
   outcome=dict(first_error=None,secondary_errors=[])
   software=O/'software_entry';software.mkdir()
   def save(name,value):io.atomic(software/name,dict(software_only=True,payload=value))
   driver.first_error(outcome,RuntimeError('SOFTWARE_PRIMARY'),save,'software');assert 'SOFTWARE_PRIMARY'in outcome['first_error']['error']
   def broken(*_):raise RuntimeError('SOFTWARE_SECONDARY_SAVE')
   driver.first_error(outcome,RuntimeError('SOFTWARE_LATER'),broken,'later');assert 'SOFTWARE_PRIMARY'in outcome['first_error']['error']and len(outcome['secondary_errors'])==2
   callresult=dict(canonical_factory_call_attempts=0)
   # Storage-free sentinel, not an actual canonical vehicle factory.
   assert driver.factory_once(lambda:'sentinel',save,callresult)=='sentinel'
   refused('duplicate_factory_claim',lambda:driver.factory_once(lambda:'sentinel',save,callresult))
   scheduler=exact('v1451_entry_once_scheduler',C/'owner.py')
   scheduler.claim_once(software/'OWNER_ONCE.json')
   try:scheduler.claim_once(software/'OWNER_ONCE.json')
   except FileExistsError:negatives.append('once_owner_second_claim')
   else:raise AssertionError('OWNER_ONCE_SECOND_CLAIM_ACCEPTED')
   import io as stdio
   console=stdio.BytesIO();bounded=scheduler.BoundedConsole(console,4);bounded.feed(b'abcd')
   refused('parent_console_cap',lambda:bounded.feed(b'e'));assert bounded.charged==4 and console.getvalue()==b'abcd'
   scheduler.put(software/'SOFTWARE_OWNER_CLOSE.json',dict(closed=True,not_actual_closure=True))
   actualmodule=exact('v1451_original_owner_source',C/'closure_owner.py')
   refused('owner_event_not_available',actualmodule.forbidden)
   # Guard dispatch is exercised with fake frame objects; no source-defined
   # Predictor or Allocator function is entered, and no old suite is replayed.
   fake=lambda filename,name:SimpleNamespace(f_code=SimpleNamespace(co_filename=str(R/filename),co_name=name))
   profile=b.profile
   refused('private_model_constructor',lambda:profile(fake('experiments/v1114_coupled_steering_mode/coupled_model.py','__init__'),'call',None))
   refused('closed_compute',lambda:profile(fake('experiments/v1114_coupled_steering_mode/coupled_control.py','compute'),'call',None))
   wrapper=SimpleNamespace(mj_step=lambda *_:None,mj_step1=lambda *_:None,mj_step2=lambda *_:None)
   probe=budgetmod.NativeBudget(w)
   with budgetmod.guard_native_API(wrapper,probe):
    refused('guard_bootstrap_step',lambda:wrapper.mj_step(None,actual));refused('splitstep',lambda:wrapper.mj_step1(None,actual))
    sys.setprofile(None);assert getattr(sys.getprofile(),'_zero200_guard',False)
   assert sys.getprofile()is no_models
   contract.prerequisite_hashes();storage=contract.storage_preflight()
   life=exact('v1451_lazy_original_binding',R/'experiments/v1449_route_initializer_binding/lifecycle.py')
   assert life.owner_module.native_module.NativeStep.__init__.__code__.co_filename==str(R/'experiments/v1423_integrated_route_audit/native_step.py')
   assert life.pump_module.Pump.prefix_step.__code__.co_filename==str(R/'experiments/v1449_route_initializer_binding/pump.py')
   source={str(p.relative_to(R)):contract.sha(p)for p in sorted(C.glob('*'))if p.is_file()}
   # Reuse every frozen production dependency from the already passed binding
   # without reexecuting Torch, OSMesa, socket, ROS or previous entry suites.
   frozen=contract.read(R/'runs/v1449_route_initializer_binding/SOURCE_FREEZE.json')['files'];assert all(contract.sha(R/p)==h for p,h in frozen.items());source.update(frozen)
   for p in ['experiments/v1447_full_module_guard_identity/guard_binding.py','experiments/v1447_full_module_guard_identity/task_cache.py','experiments/v1430_actual_allocator_provenance/allocation.py','experiments/v1439_actual_ros_startup_close/capture_budget.py','experiments/v1439_actual_ros_startup_close/bounded_io.py','experiments/v882_runtime_evidence_repair/physical.py','experiments/v1067_causal_replan_brake_reserve/scene_binding.py']:source[p]=contract.sha(R/p)
   result.update(passed=True,entry_gates={k:True for k in contract.GATES},negatives_rejected=negatives,software_counter_callbacks_actual200=200,software_counter_callbacks_replay200=200,actual_numeric_counter_calls=0,source_hashes=source,prerequisite_hashes=contract.prerequisite_hashes(),storage=storage,actual_cpu=sorted(os.sched_getaffinity(0)),original_writeguard=True,actual_zero_tail_allocator_replay_not_executed=True,physical_route_admission=False)
 except BaseException as exc:
  import traceback
  first=dict(error=repr(exc),traceback=traceback.format_exc());result['first_error']=first
 finally:
  sys.setprofile(original_profile);sys.meta_path.remove(finder)
  io.atomic(O/'ENTRY_QUALIFICATION.json',result);io.atomic(O/'ENTRY_CLOSED.json',dict(closed=True,passed=result['passed'],first_error=first,models=0))
  if result['passed']:io.atomic(O/'SOURCE_FREEZE.json',dict(files=result['source_hashes'],models=0,physical_route_admission=False))
 return 0 if result['passed']else 1

def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--qualify-entry',action='store_true');g.add_argument('--run',action='store_true');g.add_argument('--prepare-admission',action='store_true');g.add_argument('--launch',action='store_true');a=p.parse_args()
 if a.prepare_admission or a.launch:
  os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));owner=exact('v1451_once_owner',C/'owner.py')
  if a.prepare_admission:owner.prepare_admission();return 0
  value=owner.launch();return 0 if value['passed']else 1
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 os.chdir(R);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply()
 if a.qualify_entry:return qualify()
 guard(O/'zero200');driver=exact('v1451_once_actual_driver',C/'driver.py');v=driver.run(driver.contract.read(O/'TASK.json'),driver.contract.read(O/'APPROVAL.json'),driver.contract.read(O/'ROUND_WINDOW.json'));return 0 if v['passed']else 1
if __name__=='__main__':raise SystemExit(main())
