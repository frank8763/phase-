"""Grant ordering/calendar authority/owner finalcheck; old hook cases reused."""
import ast,fcntl,importlib.abc,os,runpy,sys,time,traceback
from pathlib import Path
from context import C,O,R,put,read,sha,load,admission

def main():
 start=time.monotonic();os.environ['MUJOCO_GL']='osmesa';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1632_immutable_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','OpenGL','jax','rclpy','kernel','runtime','factory','vehicle'}:raise AssertionError('PILOT_RESOURCE_SOURCE_ONLY:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,source_only=True,actual_runtime_qualified=False)
 try:
  prior=read(R/'runs/v1631_history_safe_source_checks/SOURCE_QUALIFICATION.json');assert prior['passed']and prior['original_history_and_writeguard_both_installed']
  outer=read(R/'runs/v1631_history_safe_source_checks/SOURCE_OUTER_CLOSED.json');assert outer['all_source_SHA_verified_after_child_exit']
  source=read(R/'runs/v1631_history_safe_source_checks/SOURCE_FREEZE.json')['files'].copy()
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for n in ['AUTHORIZATION.json','TASKS_LOCKED.json','PILOT_TASK.json','LIMITS_DRAFT.json','PILOT_SPEC_AMENDMENT.json']:source[str((O/n).relative_to(R))]=sha(O/n)
  for n in ['runs/v1631_history_safe_source_checks/SOURCE_QUALIFICATION.json','runs/v1631_history_safe_source_checks/SOURCE_OUTER_CLOSED.json','runs/v1620_mechanism_boundary/UNATTENDED_CONTINUATION_AUTHORIZATION_20261123.json']:source[n]=sha(R/n)
  assert all(sha(R/n)==h for n,h in source.items())
  for name in ['history_binding.py','work.py','quota.py','runtime_binding.py','audit_binding.py','transforms.py']:
   assert(C/name).read_bytes()==(R/'experiments/v1631_history_safe_source_checks'/name).read_bytes()
  driver=ast.parse((C/'driver.py').read_text());fn=next(n for n in driver.body if isinstance(n,ast.FunctionDef)and n.name=='execute')
  calls=[n for n in ast.walk(fn)if isinstance(n,ast.Call)]
  source_grant=next(n.lineno for n in calls if isinstance(n.func,ast.Name)and n.func.id=='refresh'and len(n.args)>1 and ast.unparse(n.args[0])=="'STOPPED_EVENT_PREPARATION'"and ast.unparse(n.args[1])=='32 * 1024 ** 2')
  proposal=next(n.lineno for n in calls if ast.unparse(n.func)=="(out / 'WEST_EAST_STATIC_SOURCE.json').write_bytes")
  initializer_grants=[n.lineno for n in calls if isinstance(n.func,ast.Name)and n.func.id=='refresh'and ast.unparse(n.args[0])=="'CANONICAL_INITIALIZER_PREPARATION'"]
  factory=next(n.lineno for n in calls if ast.unparse(n.func)=='factory.create_vehicle')
  assert source_grant<proposal<max(initializer_grants)<factory
  original=R/'runs/v1281_partial_reconnection_fixed24/WEST_EAST_STATIC_SOURCE.json'
  assert original.stat().st_size<32*1024**2
  observed=R/'runs/v1626_explicit_intervention_binding/pilot_WE_full/WEST_EAST_STATIC_SOURCE.json'
  assert sha(original)==sha(observed)
  assert 'and allsource' in (C/'owner.py').read_text()and 'all_source_SHA_verified_after_child_exit' in (C/'owner.py').read_text()
  assert 'root=now+5400' in (C/'owner.py').read_text()
  assert 'overall_calendar_deadline_unix' in (C/'context.py').read_text()
  try:runpy.run_path(str(C/'driver.py'),run_name='__main__')
  except AssertionError as error:assert str(error)=='NEW_ORIGINAL_CONTRACT_PILOT_NOT_ADMITTED'
  else:raise AssertionError('UNADMITTED_DRIVER_EXECUTED')
  assert read(O/'CLI_REFUSAL.json')['models']==0
  put(O/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False))
  result.update(passed=True,source_members=len(source),original_public_proposal_bytes=original.stat().st_size,grant_order_verified=True,old_hook_source_proof_reused_SHA=True,whole_source_owner_check_required=True,overall_calendar_deadline_removed_only_for_new_scope=True,real_CLI_missing_admission_refused=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
