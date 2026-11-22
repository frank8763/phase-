"""One combined new-driver SOURCE check: no repeated old suites/numerics."""
import ast,copy,fcntl,hashlib,importlib.abc,os,signal,sys,time,traceback,types
from pathlib import Path
from context import C,O,R,OLD,put,read,sha,digest

def main():
 start=time.monotonic();os.environ['MUJOCO_GL']='osmesa'
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
 import resource_policy
 resource_policy.apply()
 from context import load
 load('v1624_immutable_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','OpenGL','jax','rclpy','vehicle','factory','runtime','kernel'}:raise AssertionError('DRIVER_SOURCE_NO_NUMERICS:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 result=dict(passed=False,closed=False,models=0,physical_native=0,FFI=0,source_only=True,complete_runtime_qualified=False)
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  from runtime_binding import SerialExecutor,serial_function
  from work import ModelWork
  from context import admission
  files={str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()}
  legacy=read(OLD/'WORKER_FREEZE.json')['files']
  paths=['owner.py','worker_context.py','route_dispatch.py','live_entry.py','reconnect.py','native_audit.py','base_safety.py']
  for name in paths:
   p=OLD/name;assert legacy[str(p.relative_to(R))]==sha(p);files[str(p.relative_to(R))]=sha(p)
  files.update(read(R/'experiments/v1218_fixed24_current/PACKAGE_FREEZE.json')['files'])
  # Preserve the full original source closure by its prior immutable manifest;
  # mismatches are explicit, never silently accepted as historical equivalence.
  missing=[p for p,h in legacy.items()if not(R/p).is_file()or sha(R/p)!=h]
  assert not missing,('ORIGINAL_RUNTIME_SOURCE_CHAIN_CHANGED',missing[:8])
  files.update(legacy)
  for name in ['AUTHORIZATION.json','TASKS_LOCKED.json','PILOT_TASK.json','LIMITS_DRAFT.json','PILOT_SPEC_AMENDMENT.json']:
   files[str((O/name).relative_to(R))]=sha(O/name)
  assert all(sha(R/p)==h for p,h in files.items())
  # Execute only new serialization/ordering/resource wrappers with SOFTWAREjobs.
  calls=[]
  def job(row):calls.append(row['index']);assert row['cpu']==2;return row['index']
  with SerialExecutor(max_workers=4)as pool:
   assert list(pool.map(job,[dict(index=i,cpu=5)for i in range(6)]))==list(range(6))
  assert calls==list(range(6))
  ledger=ModelWork(dict(cpp_native_cap=3,python_native_cap=2),time.time()+30)
  ledger.before('cpp',3);ledger.done('cpp',3);assert ledger.snapshot()['cpp_native']==3
  negatives=[]
  def refuse(label,fn):
   try:fn()
   except (AssertionError,PermissionError,KeyError,RuntimeError):negatives.append(label)
   else:raise AssertionError('SOURCE_NEGATIVE_ACCEPTED:'+label)
  refuse('modelcap',lambda:ledger.before('cpp',1))
  inflight=ModelWork(dict(cpp_native_cap=3,python_native_cap=2),time.time()+30);inflight.before('cpp',3)
  assert inflight.snapshot()['cpp_native']is None and inflight.snapshot()['cpp_completed_native']==0
  refuse('inflight_reentry',lambda:inflight.before('python',1))
  refuse('actual_admission_missing',lambda:admission(read(O/'PILOT_TASK.json')))
  tasks=read(O/'TASKS_LOCKED.json');old=read(OLD/'TASKS.json')
  for row in tasks['tasks']:
   route=row['task']['case_id'];seed=next(t['seed']for t in old if t['case_id']==route and t['task_id']in ['main_slot01','main_slot09','main_slot17'])
   assert row['task']['seed']==seed
  # Real production CLI refused and persisted BEFORE binding any models.
  import runpy
  originalargv=sys.argv;sys.argv=[str(C/'driver.py')]
  try:
   try:runpy.run_path(str(C/'driver.py'),run_name='__main__')
   except AssertionError as error:assert str(error)=='NEW_ORIGINAL_CONTRACT_PILOT_NOT_ADMITTED'
   else:raise AssertionError('UNADMITTED_DRIVER_EXECUTED')
  finally:sys.argv=originalargv
  assert read(O/'CLI_REFUSAL.json')['models']==0
  for p in C.glob('*.py'):compile(ast.parse(p.read_text()),str(p),'exec')
  put(O/'SOURCE_FREEZE.json',dict(files=files,source_API_only=True,models_authorized=False,physical_admission=False))
  result.update(passed=True,negative_cases=negatives,source_members=len(files),
   all_original_runtime_closure_SHA_verified=True,software_serial_jobs=6,
   no_legacy_worker_or_audit_or_qualifier_main_executed=True,
   original_contract_selected_by_user=True,new_phase_only_sensor_seed_fixed=True,
   no_numeric_current_execution_qualified=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
