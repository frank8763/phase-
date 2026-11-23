"""Once EW pure software admission; no numerical functions or model imports."""
import ast,copy,fcntl,importlib.abc,os,runpy,sys,time,traceback,types
from context import C,O,R,ROOT,SOURCE,put,read,sha,load

def make_module(path,names):
 m=types.ModuleType('software_identity');m.__file__=str(path);tree=ast.parse(path.read_text());fns=[copy.deepcopy(n)for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names]
 assert len(fns)==len(names);exec(compile(ast.fix_missing_locations(ast.Module(body=fns,type_ignores=[])),str(path),'exec',dont_inherit=True),vars(m));return m

def main():
 start=time.monotonic();assert O==SOURCE;os.environ['MUJOCO_GL']='osmesa';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
 import resource_policy
 resource_policy.apply();load('v1773_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(SOURCE)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','OpenGL','jax','rclpy','kernel','factory','vehicle','route_tools','ctypes','planner','fast_predict','scipy'}:raise AssertionError('SOURCE_NO_NUMERICAL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 with(SOURCE/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 prior=R/'runs/v1765_ns_formal_binding';source=read(prior/'SOURCE_FREEZE.json')['files'].copy();result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  assert read(prior/'SOURCE_QUALIFICATION.json')['passed']and read(prior/'SOURCE_OUTER_CLOSED.json')['passed']and read(R/'runs/v1769_overnight_phase_campaign/NS_RELAY_RESULT.json')['passed']
  restore=read(R/'runs/v1772_exact_ew_proposal_restore/RESULT.json');assert restore['passed']and restore['restored_original_paths_exact']
  index=read(R/'runs/v1382_weekend_campaign/storage/v1237/v1237.INDEX.json');expected={x['path']:x for x in index['files']}
  for row in restore['retained']:
   assert expected[row['original']]['sha256']==row['sha256']==sha(R/row['original']);source[row['original']]=row['sha256']
  for folder in [C,R/'experiments/v1774_ew_source_recovery',R/'experiments/v1775_ew_overnight_rounds']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     source[str(p.relative_to(R))]=sha(p)
  for p in [prior/'SOURCE_QUALIFICATION.json',prior/'SOURCE_OUTER_CLOSED.json',SOURCE/'ROUND_AUTHORIZATION.json',R/'runs/v1772_exact_ew_proposal_restore/RESULT.json',R/'runs/v1769_overnight_phase_campaign/NS_RELAY_RESULT.json']:source[str(p.relative_to(R))]=sha(p)
  for aid in [r['assignment_id']for r in read(ROOT/'FORMAL_LEDGER.json')['rows'][:12]]:
   b=read(ROOT/'rounds'/aid/'POST_ROUND_STORAGE_BARRIER.json');assert b['passed']
   for a,h in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:assert sha(R/b[a])==b[h]
  reused=[]
  for n in ['phase_contract.py','resources.py','capture.py','history_binding.py','work.py','quota.py','transforms.py','clock_window.py','error_stop.py']:
   assert(C/n).read_bytes()==(R/'experiments/v1765_ns_formal_binding'/n).read_bytes();reused.append(n)
  registry=load('v1773_registry',C/'phase_contract.py');scope=load('v1773_pure_route',C/'route_scope.py');locked=read(ROOT/'TASKS_LOCKED.json');order=[a['assignment_id']for row in locked['tasks']for a in row['assignments']];assert len(order)==20 and order[12]=='phase_09__full'
  negatives=[];positive=[]
  for aid in order:
   chosen=registry.select(locked,aid,ROOT)
   if chosen['task']['case_id']=='EAST_WEST':assert scope.qualified(chosen['task'],chosen['variant'])
   else:
    try:scope.qualified(chosen['task'],chosen['variant'])
    except AssertionError:negatives.append('non_EW_'+aid)
    else:raise AssertionError('WRONG_ROUTE_ALLOWED')
  task=registry.select(locked,'phase_09__full',ROOT)['task']
  for patch,variant in [({},'no_onward'),({'slot':17},'full'),({'historical_prefix_native':1},'full')]:
   try:scope.qualified(dict(task,**patch),variant)
   except AssertionError:negatives.append('invalid_EW_scope')
   else:raise AssertionError('WRONG_EW_SCOPE')
  seams=load('v1773_audit_seams',C/'audit_seams.py')
  for variant in ['full','no_time']:
   m=make_module(seams.PARENT,['audit']);p=seams.fresh_phase_auditor(m,source);assert p['all_other_original_audit_AST_unchanged']
   tm=make_module(seams.TIMING,['verify']);p2=seams.time_eligibility_audit(tm,source,variant);assert p2['original_all40_independent_numerical_proofs_unchanged']
   positive.append(dict(variant=variant,parent=p,timing=p2))
  m=make_module(seams.PARENT,['audit']);m.audit=lambda *_:None
  try:seams.fresh_phase_auditor(m,source)
  except AssertionError:negatives.append('original_audit_code_forged')
  else:raise AssertionError('FORGED_AUDIT_ALLOWED')
  # Pure AST proof that no_time changes exactly one eligibility condition.
  transforms=load('v1773_time_source_transform',C/'transforms.py');timing=R/transforms.TIMING;tree=ast.parse(timing.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='generate');new,proof=transforms.transformed(timing.read_text(),'time','no_time');newfn=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name=='generate')
  changes=[n for n in ast.walk(newfn)if isinstance(n,ast.If)and isinstance(n.test,ast.BoolOp)and ast.unparse(n.test.values[0])=='wait == 0'];assert len(changes)==1
  changes[0].test=copy.deepcopy(changes[0].test.values[1]);assert ast.dump(newfn,include_attributes=False)==ast.dump(fn,include_attributes=False)
  # Exercise production pool routing using software futures, without any worker/model.
  pool=load('v1773_pool_software',C/'worker_pool.py');path=R/'experiments/v1271_ew_joint_phase_validation/ew_retained_parallel.py';module=make_module(path,['generate','solve_job']);before=module.generate.__code__;pool.bind(module,SOURCE,{'software':'noactualwindow'},source);assert module.generate.__code__ is before
  calls=[]
  class Future:
   def __init__(self,job):self.job=job
   def result(self,*a,**k):return dict(id=self.job['id'],cpu=self.job['cpu'],calls=0,analytical_cpp_native=0,partial_unknown=False,error=None,models=0,physical_native=0)
  class SoftwareExecutor:
   def __init__(self,**kwargs):calls.append(kwargs);assert kwargs['max_workers']==1 and kwargs['initializer']is pool.initialize
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def submit(self,fn,job):assert fn is module.solve_job;return Future(job)
  pool.concurrent=types.SimpleNamespace(futures=types.SimpleNamespace(ProcessPoolExecutor=SoftwareExecutor))
  with pool.Pool(max_workers=4,mp_context=pool.multiprocessing.get_context('spawn'))as executor:
   futures=[executor.submit(module.solve_job,dict(id=i,cpu=[2,3,4,5][i%4]))for i in range(6)]
   answers=[f.result()for f in futures]
  assert [x['id']for x in answers]==list(range(6))and all(x['cpu']==2 for x in answers)and len(calls)==1
  try:pool.bind(module,SOURCE,{},source)
  except AssertionError:negatives.append('pool_rebind_poison')
  else:raise AssertionError('POOL_REBIND_ALLOWED')
  # All production CLI rejects before binding a model or planner.
  for name in ['entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as e:assert str(e)=='REGISTERED_PHASE_ASSIGNMENT_NOT_ADMITTED';negatives.append('unadmitted_'+name)
   else:raise AssertionError('UNADMITTED_CLI_ALLOWED')
  assert all(sha(R/n)==h for n,h in source.items());target=SOURCE/'source_target';target.mkdir();put(target/'QUALIFICATION.json',dict(passed=True,positive_cases=positive,negative_cases=negatives,unchanged_modules_reused_by_SHA=reused,original_generate_solve_job_code_unchanged=True,software_pool_order6_and_CPU2_and_one_worker=True,new_worker_numeric_execution_unqualified=True,no_old_numerical_suite_repeated=True))
  put(SOURCE/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False));result.update(passed=True,source_members=len(source),qualified_case_id='EAST_WEST',qualified_variants=['full','no_time'],negative_cases=len(negatives),source_proof_sha256=sha(target/'QUALIFICATION.json'))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(SOURCE/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(SOURCE/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
