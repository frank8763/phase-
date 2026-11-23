"""Once NS software interfaces only; old numerical suites are not executed."""
import ast,copy,fcntl,importlib.abc,os,runpy,sys,time,traceback,types
from context import C,O,R,ROOT,SOURCE,put,read,sha,load

def main():
 start=time.monotonic();assert O==SOURCE
 os.environ['MUJOCO_GL']='osmesa';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
 import resource_policy
 resource_policy.apply();load('v1765_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(SOURCE)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','OpenGL','jax','rclpy','kernel','factory','vehicle','route_tools','ctypes','planner','fast_predict'}:raise AssertionError('SOURCE_NO_NUMERICAL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 with(SOURCE/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 prior=R/'runs/v1744_formal_interface_qualification';source=read(prior/'SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  assert read(prior/'SOURCE_QUALIFICATION.json')['passed']and read(prior/'SOURCE_OUTER_CLOSED.json')['passed']
  negatives=[];positive=[];reused=[]
  for p in [p for folder in [C,R/'experiments/v1766_ns_source_recovery',R/'experiments/v1767_ns_phase05_single']for p in folder.iterdir()]:
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for p in [prior/'SOURCE_QUALIFICATION.json',prior/'SOURCE_OUTER_CLOSED.json',SOURCE/'ROUND_AUTHORIZATION.json',R/'runs/v1762_sccr_phase_g2/POST_ROUND_STORAGE_BARRIER.json']:
   source[str(p.relative_to(R))]=sha(p)
  # All originally frozen NS package, scene, proposal and safety dependencies are inherited.
  package=read(R/'experiments/v1246_entry_recovery_handoff/PACKAGE_FREEZE.json')['files']
  assert all(source.get(n)==h and sha(R/n)==h for n,h in package.items())
  static=R/'runs/v1281_partial_reconnection_fixed24/NORTH_SOUTH_STATIC_SOURCE.json';assert source[str(static.relative_to(R))]==sha(static)and static.stat().st_size<16*1024**2
  for n in ['phase_contract.py','resources.py','capture.py','history_binding.py','work.py','quota.py','transforms.py','clock_window.py','error_stop.py']:
   assert(C/n).read_bytes()==(R/'experiments/v1744_formal_interface_qualification'/n).read_bytes();reused.append(n)
  scope=load('v1765_pure_scope',C/'route_scope.py');registry=load('v1765_pure_registry',C/'phase_contract.py');locked=read(ROOT/'TASKS_LOCKED.json')
  order=[a['assignment_id']for row in locked['tasks']for a in row['assignments']]
  assert order[8]=='phase_05__full'and len(order)==20
  selected=registry.select(locked,'phase_05__full',ROOT);task=selected['task'];assert not selected['models_authorized']and not selected['physical_authorized']
  assert task['seed']==10060009 and task['phase']==2.407648011504974 and scope.qualified(task,'full')
  scientific=copy.deepcopy(selected['original_registered_task'])
  for k in ['output','run_root','run_id','task_id']:scientific.pop(k)
  assert registry.digest(scientific)==selected['scientific_task_sha256']
  for aid in order:
   d=registry.select(locked,aid,ROOT)
   if d['task']['case_id']=='NORTH_SOUTH':assert scope.qualified(d['task'],d['variant'])
   else:
    try:scope.qualified(d['task'],d['variant'])
    except AssertionError:negatives.append('unqualified_route_'+aid)
    else:raise AssertionError('WRONG_ROUTE_AUTHORIZED')
  for patch,variant in [({},'no_onward'),({'slot':13},'full'),({'historical_prefix_native':1},'full'),({'sensor_seed_unchanged':False},'full')]:
   try:scope.qualified(dict(task,**patch),variant)
   except AssertionError:negatives.append('bad_NS_scope')
   else:raise AssertionError('BAD_NS_SCOPE_ACCEPTED')
  for aid in order[:8]:
   b=read(ROOT/'rounds'/aid/'POST_ROUND_STORAGE_BARRIER.json');assert b['passed']
   for a,h in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:assert sha(R/b[a])==b[h]
  b=read(R/'runs/v1762_sccr_phase_g2/POST_ROUND_STORAGE_BARRIER.json');assert b['passed']and all(sha(R/n)==h for n,h in b['proof_paths_SHA256'].items())
  seams=load('v1765_NS_audit_seam',C/'audit_seams.py');tree=ast.parse(seams.PARENT.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='audit')
  m=types.ModuleType('software_NS_definition');m.__file__=str(seams.PARENT)
  exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(fn)],type_ignores=[])),str(seams.PARENT),'exec',dont_inherit=True),vars(m))
  proof=seams.fresh_phase_auditor(m,source);assert proof['all_other_original_audit_AST_unchanged']
  transformed=copy.deepcopy(fn);matches=[n for n in transformed.body if isinstance(n,ast.If)and ast.unparse(n.test)=="task['slot'] == 13"];assert len(matches)==1;transformed.body.remove(matches[0])
  assert proof['transformed_audit_AST_sha256']==__import__('hashlib').sha256(ast.dump(transformed,include_attributes=False).encode()).hexdigest()
  for fake_source,fake_code in [(dict(source,**{str(seams.PARENT.relative_to(R)):'0'*64}),False),(source,True)]:
   z=types.ModuleType('bad_NS');z.__file__=str(seams.PARENT);exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(fn)],type_ignores=[])),str(seams.PARENT),'exec',dont_inherit=True),vars(z))
   if fake_code:z.audit=lambda *_:None
   try:seams.fresh_phase_auditor(z,fake_source)
   except AssertionError:negatives.append('audit_source_or_code_identity')
   else:raise AssertionError('FORGED_NS_AUDIT_ACCEPTED')
  # Exercise the production recursive result-reader seam using software metadata.
  binding=load('v1765_production_reader',C/'audit_binding.py');canonical=dict(passed=False,first_error='retained');functional=dict(passed=True,scientific_passed=False)
  from pathlib import Path
  target=SOURCE/'software_RESULT.json';other=SOURCE/'other.json';calls=[]
  child=types.ModuleType('software_child');child.__file__=str(C/'software_child.py');child.read=lambda p:canonical
  root=types.ModuleType('software_root');root.__file__=str(C/'software_root.py');root.read=lambda p:canonical;root.load=lambda n,p:child
  touched=[];seen=[];root=binding.bind_reader(root,target,functional,source,seams,touched,seen)
  assert root.read(target)is functional and root.read(other)is canonical
  nested=root.load('child',C/'software_child.py');assert nested.read(target)is functional and nested.read(other)is canonical
  assert canonical==dict(passed=False,first_error='retained')and len(touched)==2 and not seen
  complete=dict(new_actual_native=3,fully_recorded_native=3,evidence_saved=True,replay=dict(passed=True),model_native_inflight_unknown=False,actual_original_goal_reached=True,first_error=None)
  assert binding.audit_kind(complete)=='full_goal'
  assert binding.audit_kind(dict(complete,actual_original_goal_reached=False,first_error={'error':'refusal'}))=='prefix_safety_only'
  for patch in [dict(new_actual_native=None),dict(new_actual_native=0),dict(model_native_inflight_unknown=True),dict(evidence_saved=False),dict(replay={'passed':False}),dict(fully_recorded_native=2)]:assert binding.audit_kind(dict(complete,**patch))=='unreviewable'
  # Static production binding: no numerical package load is performed in SOURCE.
  runtime=(C/'runtime_binding.py').read_text();assert 'dispatch.ns_executor()'in runtime and 'dispatch.current_executor()'not in runtime and 'transforms.bind('not in runtime
  assert runtime.index('cached.bind(')<runtime.index('dispatch.ns_executor()')
  driver=(C/'driver.py').read_text();assert 'NORTH_SOUTH_STATIC_SOURCE.json'in driver and 'WEST_EAST_STATIC_SOURCE.json'not in driver
  assert "binding['owner'].navigate(v,read(out/'physics/SETUP.json'),task,window['normal_end_unix'],out,result)"in driver
  # Native production CLI rejects missing admission before numerical imports.
  for name in ['entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as e:assert str(e)=='REGISTERED_PHASE_ASSIGNMENT_NOT_ADMITTED';negatives.append('unadmitted_'+name)
   else:raise AssertionError('UNADMITTED_CLI_ACCEPTED')
  assert all(sha(R/n)==h for n,h in source.items())
  positive=[dict(locked_NS_phase_05_identity=True,all20_order_retained=True,NS_full_only=True,old_NS_package_files=len(package),original_NS_public_proposal_bytes=static.stat().st_size),proof,dict(recursive_functional_reader_exercised=True,canonical_result_unchanged=True,full_prefix_incomplete_dispatch_exercised=True,original_numerical_auditor_not_executed=True)]
  target=SOURCE/'source_target';target.mkdir();put(target/'QUALIFICATION.json',dict(passed=True,positive_cases=positive,negative_cases=negatives,unchanged_modules_reused_by_SHA=reused,inherited_source_qualification_sha256=sha(prior/'SOURCE_QUALIFICATION.json'),inherited_freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),actual_original_numerical_suite_not_repeated=True,new_independent_sample=False))
  put(SOURCE/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False))
  result.update(passed=True,source_members=len(source),qualified_case_id='NORTH_SOUTH',qualified_variants=['full'],negative_cases=len(negatives),source_proof_sha256=sha(target/'QUALIFICATION.json'))
 except BaseException as error:
  result.update(first_error=repr(error),traceback=traceback.format_exc());put(SOURCE/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
 finally:
  result.update(closed=True,wall_s=time.monotonic()-start);put(SOURCE/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
