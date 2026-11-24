"""Common RPCCR task binding only; original numerical and audit proofs reused."""
import ast,copy,fcntl,importlib.abc,os,runpy,sys,time,traceback
from pathlib import Path
from context import C,O,R,OLD,read,put,sha,load

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply();load('v1810_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory','ctypes','planner','fast_predict','scipy'}:raise AssertionError('SOURCE_NO_MODELS:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 bases=[R/'runs/v1806_dwa_common_phase',R/'runs/v1744_formal_interface_qualification'];files={};result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,reference_query_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  inherited=[]
  for base in bases:
   assert read(base/'SOURCE_QUALIFICATION.json')['passed']and read(base/'SOURCE_OUTER_CLOSED.json')['passed'];recovery=read(base/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and not recovery['uncovered_members']
   for k,v in read(base/'SOURCE_FREEZE.json')['files'].items():assert k not in files or files[k]==v;files[k]=v
   inherited.append(dict(root=str(base.relative_to(R)),freeze_sha256=sha(base/'SOURCE_FREEZE.json'),recovery_path=str((base/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(base/'CURRENT_SOURCE_REMOTE_RECOVERY.json')))
  for folder in [C,R/'experiments/v1811_rpccr_common_source_recovery',R/'experiments/v1812_rpccr_common_runtime_recovery']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [O/'PILOT_TASK.json',O/'LIMITS_DRAFT.json',O/'ROUND_AUTHORIZATION.json',R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json']:files[str(p.relative_to(R))]=sha(p)
  reused=[]
  for n in ['runtime_binding.py','audit_binding.py','audit_seams.py','transforms.py','history_binding.py','work.py','clock_window.py','error_stop.py']:
   assert(C/n).read_bytes()==(R/'experiments/v1744_formal_interface_qualification'/n).read_bytes();reused.append(n)
  for n in ['resources.py','capture.py','quota.py']:assert(C/n).read_bytes()==(R/'experiments/v1806_dwa_common_phase'/n).read_bytes();reused.append(n)
  old=ast.parse((R/'experiments/v1744_formal_interface_qualification/driver.py').read_text());new=ast.parse((C/'driver.py').read_text());calls=[n for n in ast.walk(new)if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='attempt'and n.value.args and isinstance(n.value.args[0],ast.Constant)and n.value.args[0].value=='NPLUS1_FRESH_CLOSE_GRANT'];assert len(calls)==1
  class Restore(ast.NodeTransformer):
   def visit_Expr(self,n):return None if n is calls[0]else self.generic_visit(n)
   def visit_Call(self,n):
    n=self.generic_visit(n)
    if isinstance(n.func,ast.Name)and n.func.id=='dict'and any(k.arg=='formal_prospective_task'for k in n.keywords):
     n.keywords=[k for k in n.keywords if k.arg!='common_prospective_task']
     for k in n.keywords:
      if k.arg=='formal_prospective_task':k.value=ast.Constant(True)
    return n
  assert ast.dump(Restore().visit(new),include_attributes=False)==ast.dump(old,include_attributes=False),'UNRELATED_CONTROLLER_DRIVER_MODIFIED'
  registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');shared=registry['tasks'][0]['task'];task=read(O/'PILOT_TASK.json');dwa=read(R/'runs/v1806_dwa_common_phase/PILOT_TASK.json')
  keys=['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction','native_limit','stop_native','speed']
  for k in keys:assert task[k]==dwa[k]==shared[k]
  assert task['mechanism_variant']=='full'and task['common_method']=='RP-CCR'and task['formal_assignment_id']=='common_01__RPCCR'
  assert task['output']!=dwa['output']and task['common_task_id']==dwa['common_task_id']=='common_01'
  # Exact production context must reject before any model binding/import.
  negative=[]
  for n in ['pilot_entry.py','driver.py']:
   try:runpy.run_path(str(C/n),run_name='__main__')
   except AssertionError as e:assert str(e)=='RPCCR_COMMON_NOT_ADMITTED';negative.append('unadmitted_'+n)
   else:raise AssertionError('MODEL_CLI_ADMITTED_WITHOUT_AUTHORITY')
  assert all(sha(R/n)==h for n,h in files.items());put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=inherited));put(O/'SOURCE_QUALIFICATION_PROOF.json',dict(passed=True,common_physical_task_exactly_matches_DWA_on_all_keys=keys,unchanged_original_WE_runtime_audit_modules=reused,driver_AST_unchanged_except_existing_quiescent_grant_and_result_metadata=True,negative_cases=negative,no_old_numeric_suite_repeated=True))
  put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False));result.update(passed=True,source_members=len(files),negative_cases=len(negative),common_method='RP-CCR',common_task='common_01',source_proof_sha256=sha(O/'SOURCE_QUALIFICATION_PROOF.json'))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
