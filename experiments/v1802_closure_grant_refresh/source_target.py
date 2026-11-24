"""Once software regression of original nested auditor directory resolution."""
import ast,copy,fcntl,importlib.abc,os,runpy,sys,time,traceback,types
from pathlib import Path
from context import C,O,R,ROOT,SOURCE,OLD,put,read,sha,load

def module(path,name):
 m=types.ModuleType('exact_original_auditor_software');m.__file__=str(path)
 fn=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name==name)
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(path),'exec',dont_inherit=True),vars(m));return m

def main():
 start=time.monotonic();assert O==SOURCE
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1793_original_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(SOURCE)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','OpenGL','jax','rclpy','kernel','factory','vehicle','route_tools','ctypes','planner','fast_predict','scipy'}:raise AssertionError('SOURCE_NO_NUMERICAL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 with(SOURCE/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 prior=R/'runs/v1797_auditor_regression_syntax';source=read(prior/'SOURCE_FREEZE.json')['files'].copy();result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  assert read(prior/'SOURCE_QUALIFICATION.json')['passed']and read(prior/'SOURCE_OUTER_CLOSED.json')['passed']and read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  for folder in [C,R/'experiments/v1803_closure_source_recovery',R/'experiments/v1795_closed_transport_completion',R/'experiments/v1804_remaining_ablation_rounds']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     source[str(p.relative_to(R))]=sha(p)
  for p in [prior/'SOURCE_QUALIFICATION.json',prior/'SOURCE_OUTER_CLOSED.json',SOURCE/'ROUND_AUTHORIZATION.json',SOURCE/'CAPACITY_DIAGNOSIS.json']:source[str(p.relative_to(R))]=sha(p)
  reused=[]
  for p in C.glob('*.py'):
   if p.name not in {'source_target.py','driver.py','resources.py'}:
    assert p.read_bytes()==(R/'experiments/v1797_auditor_regression_syntax'/p.name).read_bytes();reused.append(p.name)
  priorproof=read(prior/'source_target/QUALIFICATION.json');assert priorproof['passed']
  resources=load('v1802_actual_resource_refresh',C/'resources.py')
  quota_module=load('quota',C/'quota.py');limits=read(ROOT/'LIMITS.json');folder=SOURCE/'software_quota';folder.mkdir()
  original_measure=quota_module.grant.base.measure;original_used=quota_module.base.used
  allocated=88*1024**2;total=12*1024**3;capture_hold=70*1024**2
  # Exact production quota, original expiry/hold/root rules. Only saved fixture
  # census replaces du, not any quota assertion. No file or array compression credit.
  quota_module.grant.base.measure=lambda output,limits:(allocated,total)
  quota_module.base.used=lambda output:allocated
  q=quota_module.EvidenceQuota(folder,limits);q.bind_external_names([]);q.write_enforcement_active=True;resources.reserve_terminal(q);q.hold('canonical-physical-prefix',capture_hold)
  q.prepare_grant(1*1024**2,phase='COMPLETE_ZERO_TAIL_OR_CLOSURE',valid_for_s=300,external_writers=[])
  pending=2*23552000+65536+8192*6
  try:q.admit(pending,'COMPLETE_NPZ:FULL_STATE_NPLUS1.npz')
  except AssertionError as e:assert str(e)=='BYTE_GRANT_EXHAUSTED'
  else:raise AssertionError('STALE_CLOSE_GRANT_REPRODUCTION_NOT_RED')
  grant=resources.prepare_closed_capture(q,'normal',False);q.admit(pending,'COMPLETE_NPZ:FULL_STATE_NPLUS1.npz');assert grant['capacity_bytes']<=224*1024**2 and grant['expires_monotonic']-grant['prepared_monotonic']==300
  positive=[dict(stale_small_grant_rejected=True,fresh_exact_census_grant_passed=True,pending_logical_NPZ_bytes=pending,allocated_bytes=allocated,capture_hold=capture_hold,terminal_hold=resources.TERMINAL_BYTES,new_capacity_bytes=grant['capacity_bytes'],task_cap_unchanged=limits['maximum_task_evidence_bytes'],ttl_unchanged=True)]
  negative=[]
  for phase,inflight in [('replay',False),('normal',True),('independent_audit',False)]:
   try:resources.prepare_closed_capture(q,phase,inflight)
   except AssertionError:negative.append('nonquiescent_close_refresh')
   else:raise AssertionError('INVALID_CLOSE_REFRESH_ALLOWED')
  allocated=150*1024**2
  try:
   resources.prepare_closed_capture(q,'normal',False);q.admit(pending,'COMPLETE_NPZ:FULL_STATE_NPLUS1.npz')
  except AssertionError:negative.append('actual_task_capacity_insufficient')
  else:raise AssertionError('REAL_TASK_CAP_RELAXED')
  allocated=88*1024**2;total=15*1024**3
  try:resources.prepare_closed_capture(q,'normal',False)
  except AssertionError:negative.append('actual_root_capacity_insufficient')
  else:raise AssertionError('REAL_ROOT_CAP_RELAXED')
  quota_module.grant.base.measure=original_measure;quota_module.base.used=original_used
  # All original control/numerical/capture logic is SHA-reused. Exact driver delta.
  original=ast.parse((R/'experiments/v1797_auditor_regression_syntax/driver.py').read_text());updated=ast.parse((C/'driver.py').read_text())
  removals=[n for n in ast.walk(updated)if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='attempt'and n.value.args and isinstance(n.value.args[0],ast.Constant)and n.value.args[0].value=='NPLUS1_FRESH_CLOSE_GRANT'];assert len(removals)==1
  class Remove(ast.NodeTransformer):
   def visit_Expr(self,n):return None if n is removals[0]else self.generic_visit(n)
  assert ast.dump(Remove().visit(updated),include_attributes=False)==ast.dump(original,include_attributes=False),'NUMERICAL_OR_CONTROL_DRIVER_CHANGED'
  dependencies=['driver.py','resources.py'];proofs=[]
  for name in ['entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as e:assert str(e)=='REGISTERED_PHASE_ASSIGNMENT_NOT_ADMITTED';negative.append('unadmitted_'+name)
   else:raise AssertionError('UNADMITTED_CLI_ALLOWED')
  assert all(sha(R/n)==h for n,h in source.items());target=SOURCE/'source_target';target.mkdir();put(target/'QUALIFICATION.json',dict(passed=True,positive_cases=positive,negative_cases=negative,unchanged_production_modules_reused_by_SHA=reused,original_numeric_tests_not_repeated=True,only_changed_modules=dependencies,prior_software_proof_sha256=sha(prior/'source_target/QUALIFICATION.json'),no_old_task_reaudit_or_replay=True))
  put(SOURCE/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False));result.update(passed=True,source_members=len(source),qualified_case_id='EAST_WEST',qualified_variants=['full','no_time'],negative_cases=len(negative),source_proof_sha256=sha(target/'QUALIFICATION.json'))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(SOURCE/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(SOURCE/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
