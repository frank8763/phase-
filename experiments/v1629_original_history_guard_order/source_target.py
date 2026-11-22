"""Necessary real audit-hook ordering check, no old suite/model imports."""
import ast,fcntl,hashlib,importlib.abc,os,sys,time,traceback,types
from pathlib import Path
from context import C,O,R,put,read,sha,load

def main():
 start=time.monotonic();os.environ['MUJOCO_GL']='osmesa'
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','runtime','factory','vehicle'}:raise AssertionError('HISTORY_ORDER_NO_NUMERICS:'+name)
 sys.meta_path.insert(0,Ban())
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,original_contract=True,complete_runtime_qualified=False)
 try:
  prior=read(R/'runs/v1626_explicit_intervention_binding/SOURCE_QUALIFICATION.json');assert prior['passed']and prior['constructors_or_model_or_policy_calls']==0
  source=read(R/'runs/v1626_explicit_intervention_binding/SOURCE_FREEZE.json')['files'].copy()
  for p in C.iterdir():
   if p.is_file():source[str(p.relative_to(R))]=sha(p)
  for n in ['AUTHORIZATION.json','TASKS_LOCKED.json','PILOT_TASK.json','LIMITS_DRAFT.json','PILOT_SPEC_AMENDMENT.json']:source[str((O/n).relative_to(R))]=sha(O/n)
  assert all(sha(R/n)==h for n,h in source.items())
  from history_binding import install
  original_source=read(R/'runs/v1626_explicit_intervention_binding/SOURCE_FREEZE.json')['files']
  old=ast.parse((R/'experiments/v1626_explicit_intervention_binding/driver.py').read_text());new=ast.parse((C/'driver.py').read_text())
  get=lambda tree,name:next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name)
  oldbody=get(old,'execute');expected=ast.parse('old.history_guard(out)').body[0]
  class Remove(ast.NodeTransformer):
   def visit_Expr(self,node):return None if ast.dump(node)==ast.dump(expected)else node
  assert ast.dump(Remove().visit(oldbody))==ast.dump(get(new,'execute'))
  history=install(O,source)
  common=load('v1629_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py')
  guards=load('v1629_original_initializer_guard_scope',R/'experiments/v1447_full_module_guard_identity/guard_binding.py')
  with guards.bind_original_guard(O)as receipt:
   common.guard(O)
   assert receipt['installed_original_guard_count']==1
   negatives=[]
   try:sys.addaudithook(lambda *args:None)
   except AssertionError as error:
    assert str(error)=='MULTIPLE_INITIALIZER_WRITE_GUARDS';negatives.append('unknown_or_multiple_initializer_hook')
   else:raise AssertionError('UNDECLARED_HOOK_ACCEPTED')
  current=O/'NATIVE_TRACE.npz';current.write_bytes(b'EXPLICIT_SOFTWARE_NON_NUMERICAL_PAYLOAD')
  assert current.read_bytes()==b'EXPLICIT_SOFTWARE_NON_NUMERICAL_PAYLOAD'
  try:(R/'runs/v1626_explicit_intervention_binding/pilot_WE_full/SENSORS.json.gz').open('rb')
  except AssertionError as error:
   assert str(error).startswith('FRESH_HISTORY_READ_FORBIDDEN');negatives.append('historical_raw_read')
  else:raise AssertionError('HISTORICAL_RAW_READ_ACCEPTED')
  assert source=={n:sha(R/n)for n in source}
  put(O/'SOURCE_FREEZE.json',dict(files=source,models_authorized=False,source_only=True))
  result.update(passed=True,negative_cases=negatives,original_history_and_writeguard_both_installed=True,exact_execute_AST_except_history_registration=True,old_numeric_definitions_sourceproof_reused_not_rerun=True,source_members=len(source),proof=history,software_payload_not_physics=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
