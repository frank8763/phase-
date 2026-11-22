"""Only new prefix import and source/study namespace seam; zero numerical calls."""
import ast,copy,fcntl,importlib.abc,os,runpy,sys,time,traceback,types,json
from pathlib import Path
from context import C,O,R,ROOT,SOURCE,put,read,sha,load

def main():
 start=time.monotonic();assert O==SOURCE and SOURCE==R/'runs'/C.name and ROOT==R/'runs/v1643_formal_parent_metadata'
 os.environ['MUJOCO_GL']='osmesa';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1646_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(SOURCE)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','OpenGL','jax','rclpy','kernel','runtime','factory','vehicle','route_tools'}:raise AssertionError('PREFIX_SOURCE_NO_NUMERICAL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 with(SOURCE/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 inherited=read(ROOT/'SOURCE_FREEZE.json')['files'];source=inherited.copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  prior=ROOT/'rounds/phase_01__full';assert read(prior/'POST_ROUND_STORAGE_BARRIER.json')['passed']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for p in [ROOT/'SOURCE_QUALIFICATION.json',ROOT/'source_target/QUALIFICATION.json',prior/'POST_ROUND_STORAGE_BARRIER.json',prior/'RUNTIME_CLOSED_REVIEW.json']:source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items())
  reused=[]
  for n in ['driver.py','resources.py','capture.py','history_binding.py','work.py','quota.py','transforms.py','phase_contract.py','audit_seams.py']:
   assert(C/n).read_bytes()==(R/'experiments/v1643_formal_parent_metadata'/n).read_bytes();reused.append(n)
  assert read(ROOT/'SOURCE_QUALIFICATION.json')['passed']and read(ROOT/'source_target/QUALIFICATION.json')['source_code_only_old_audit_not_executed']
  module=load('v1646_prefix_dependency',C/'audit_binding.py');negatives=[]
  def refuse(label,fn):
   try:fn()
   except(AssertionError,KeyError):negatives.append(label)
   else:raise AssertionError('NEW_DEPENDENCY_NEGATIVE_ACCEPTED:'+label)
  previous,dependency=module.prefix_import_scope(source)
  try:
   assert Path(sys.path[0]).resolve()==R/'experiments/v1195_eight_gib_timed_refuge'
   assert 'route_tools'not in sys.modules
  finally:sys.path[:]=previous
  assert 'route_tools'not in sys.modules
  bad=source.copy();bad['experiments/v1195_eight_gib_timed_refuge/route_tools.py']='0'*64;before=sys.path[:]
  refuse('changed_dependency_source',lambda:module.prefix_import_scope(bad));assert sys.path==before
  fake=types.ModuleType('route_tools');fake.__file__=str(SOURCE/'SOFTWARE_FOREIGN_MODULE.py');sys.modules['route_tools']=fake
  try:refuse('foreign_resident_module',lambda:module.prefix_import_scope(source))
  finally:sys.modules.pop('route_tools')
  assert sys.path==before
  # The exact audit math function and call are unchanged; only surrounding
  # dependency scope/restore bookkeeping differs from the frozen source.
  old_tree=ast.parse((R/'experiments/v1643_formal_parent_metadata/audit_binding.py').read_text());new_tree=ast.parse((C/'audit_binding.py').read_text())
  for name in ['audit','audit_kind']:
   a=next(n for n in old_tree.body if isinstance(n,ast.FunctionDef)and n.name==name);b=next(n for n in new_tree.body if isinstance(n,ast.FunctionDef)and n.name==name);assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
  prefix=next(n for n in new_tree.body if isinstance(n,ast.FunctionDef)and n.name=='audit_prefix')
  assert any(isinstance(n,ast.Try)and any('sys.path[:]'in ast.unparse(k)for k in n.finalbody)for n in ast.walk(prefix))
  assert [ast.unparse(n)for n in ast.walk(prefix)if isinstance(n,ast.Call)and ast.unparse(n.func)=='module.audit']==['module.audit(task, result_override=scratch, output_path=path)']
  registry=load('v1646_unchanged_registry',C/'phase_contract.py');selected=registry.select(read(ROOT/'TASKS_LOCKED.json'),'phase_01__no_onward',ROOT)
  assert selected['task']['phase']==2.2609711555894934 and selected['task']['seed']==10060001 and selected['task']['output']==str(ROOT/'rounds/phase_01__no_onward/actual')
  oldenv=os.environ.get('PHASE_FORMAL_ASSIGNMENT')
  try:
   os.environ['PHASE_FORMAL_ASSIGNMENT']='phase_01__no_onward';ctx=load('v1646_actual_round_context_source',C/'context.py');assert ctx.ROOT==ROOT and ctx.SOURCE==SOURCE and ctx.O==ROOT/'rounds/phase_01__no_onward'
   refuse('unadmitted_paired_context',ctx.admission)
   os.environ['PHASE_FORMAL_ASSIGNMENT']='phase_99__full';refuse('unregistered_namespace',lambda:load('v1646_foreign_context_source',C/'context.py'))
  finally:
   if oldenv is None:os.environ.pop('PHASE_FORMAL_ASSIGNMENT',None)
   else:os.environ['PHASE_FORMAL_ASSIGNMENT']=oldenv
  for name in ['entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as error:assert str(error)=='REGISTERED_PHASE_ASSIGNMENT_NOT_ADMITTED'
   else:raise AssertionError('UNADMITTED_NEW_SOURCE_EXECUTED')
  target=SOURCE/'source_target';target.mkdir()
  put(target/'QUALIFICATION.json',dict(passed=True,source_only=True,models=0,physical_native=0,replay_native=0,FFI_loads=0,dependency=dependency,dependency_module_not_imported=True,old_numeric_auditor_not_executed=True,sys_path_restored=True,qualified_case_id='WEST_EAST',qualified_variants=['full','no_onward'],negative_cases=negatives,shared_study_root=str(ROOT.relative_to(R)),new_source_root=str(SOURCE.relative_to(R)),first_case_not_rerun=True,prior_source_proof_sha256=sha(ROOT/'source_target/QUALIFICATION.json'),unchanged_modules_reused=reused))
  put(SOURCE/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False))
  result.update(passed=True,source_members=len(source),qualified_case_id='WEST_EAST',qualified_variants=['full','no_onward'],negative_cases=len(negatives),shared_study_root=str(ROOT.relative_to(R)),first_formal_case_retained=True,unchanged_modules_reused=reused,real_CLI_missing_admission_refused=True,source_proof_sha256=sha(target/'QUALIFICATION.json'))
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc());put(SOURCE/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(SOURCE/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
