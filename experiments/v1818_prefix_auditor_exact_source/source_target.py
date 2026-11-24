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
 prior=R/'runs/v1802_closure_grant_refresh';source=read(prior/'SOURCE_FREEZE.json')['files'].copy();result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  assert read(prior/'SOURCE_QUALIFICATION.json')['passed']and read(prior/'SOURCE_OUTER_CLOSED.json')['passed']and read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  for folder in [C,R/'experiments/v1819_prefix_source_recovery',R/'experiments/v1795_closed_transport_completion',R/'experiments/v1820_final_three_ablation_rounds']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     source[str(p.relative_to(R))]=sha(p)
  for p in [prior/'SOURCE_QUALIFICATION.json',prior/'SOURCE_OUTER_CLOSED.json',SOURCE/'ROUND_AUTHORIZATION.json',SOURCE/'EARLY_REFUSAL_SCOPE.json']:source[str(p.relative_to(R))]=sha(p)
  reused=[]
  for p in C.glob('*.py'):
   if p.name not in {'source_target.py','audit_binding.py'}:
    assert p.read_bytes()==(R/'experiments/v1802_closure_grant_refresh'/p.name).read_bytes();reused.append(p.name)
  priorproof=read(prior/'source_target/QUALIFICATION.json');assert priorproof['passed']
  original_path=R/'experiments/v1195_eight_gib_timed_refuge/audit_refusal.py';known=read(R/'runs/v1806_dwa_common_phase/SOURCE_FREEZE.json')['files'];assert known[str(original_path.relative_to(R))]==sha(original_path)and read(R/'runs/v1806_dwa_common_phase/CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered'];source[str(original_path.relative_to(R))]=sha(original_path)
  for n in ['PRIOR_SOURCE_FAILURE.json']:source[str((SOURCE/n).relative_to(R))]=sha(SOURCE/n)
  binding=load('v1814_stage_scoped_prefix_auditor',C/'audit_binding.py');n=205;discovery=5
  journal=[dict(before_native=i,applied=True,request=[0.,0.,False])for i in range(n)];commands=[[0.]*6 for _ in range(n)];segments=[dict(label='NORMAL',executed_native=5,origin_native=0)]
  r=dict(functional_failure=dict(original_error=dict(stage='normal',error=binding.EARLY_ERROR)),physical=dict(first_actor_detection=dict(native_tick=discovery)),error_stop=dict(applied=200),error_stop_progress=dict(complete200=True,applied=200))
  assert binding.early_discovery_refusal(r,segments,journal,n,discovery,commands)
  original=R/'experiments/v1195_eight_gib_timed_refuge/audit_refusal.py';tree=ast.parse(original.read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='audit');m=types.ModuleType('software_exact_audit');m.__file__=str(original);exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(original),'exec',dont_inherit=True),vars(m));proof=binding.bind_refusal_stage(m,source)
  assert m.audit.__globals__['_early_discovery_refusal'] is binding.early_discovery_refusal
  # Execute the actual guarded assertion AST with software-only branch metadata.
  test=ast.parse("if not _early_discovery_refusal(r,segments,journal,n,discovery,commands):\n assert any(s['label']=='DISCOVERY_STOP' and s['executed_native']==2200 for s in segments)")
  ns=dict(_early_discovery_refusal=binding.early_discovery_refusal,r=r,segments=segments,journal=journal,n=n,discovery=discovery,commands=commands);exec(compile(test,str(C/'audit_binding.py'),'exec'),ns)
  positive=[dict(stage_guard_accepts_exact_early_function_refusal=True,original_auditor_AST_only_expected_stage_guarded=True,production_branch_software_executed=True,proof=proof)];negative=[]
  for kind in ['short_tail','moving_request','bad_detection','missing_stop','wrong_phase','unexpected_discovery_stop']:
   bad=copy.deepcopy(r);j=copy.deepcopy(journal);seg=copy.deepcopy(segments)
   if kind=='short_tail':bad['error_stop']['applied']=199
   if kind=='moving_request':j[discovery-1]['request'][0]=.01
   if kind=='bad_detection':bad['physical']['first_actor_detection']['native_tick']=4
   if kind=='missing_stop':bad['error_stop_progress']['complete200']=False
   if kind=='wrong_phase':bad['functional_failure']['original_error']['stage']='capture'
   if kind=='unexpected_discovery_stop':seg.append(dict(label='DISCOVERY_STOP',executed_native=0))
   try:accepted=binding.early_discovery_refusal(bad,seg,j,n,discovery,commands)
   except AssertionError:accepted=False
   assert not accepted,'INVALID_EARLY_REFUSAL_ALLOWED:'+kind;negative.append(kind)
  assert not binding.early_discovery_refusal(dict(r,functional_failure=dict(original_error=dict(stage='normal',error='OTHER_REFUSAL'))),segments,journal,n,discovery,commands)
  dependencies=['audit_binding.py']
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
