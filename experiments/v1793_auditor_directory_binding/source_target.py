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
 prior=R/'runs/v1789_lossless_job_packet';source=read(prior/'SOURCE_FREEZE.json')['files'].copy();result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  assert read(prior/'SOURCE_QUALIFICATION.json')['passed']and read(prior/'SOURCE_OUTER_CLOSED.json')['passed']and read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  for folder in [C,R/'experiments/v1794_auditor_source_recovery',R/'experiments/v1795_closed_transport_completion',R/'experiments/v1796_phase10_full_single']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     source[str(p.relative_to(R))]=sha(p)
  for p in [prior/'SOURCE_QUALIFICATION.json',prior/'SOURCE_OUTER_CLOSED.json',SOURCE/'ROUND_AUTHORIZATION.json',SOURCE/'RED_REPRODUCTION.json']:source[str(p.relative_to(R))]=sha(p)
  reused=[]
  for p in C.glob('*.py'):
   if p.name not in {'source_target.py','audit_binding.py'}:
    assert p.read_bytes()==(R/'experiments/v1789_lossless_job_packet'/p.name).read_bytes();reused.append(p.name)
  seams=load('v1793_unchanged_audit_seams',C/'audit_seams.py');binding=load('v1793_new_directory_binding',C/'audit_binding.py');positive=[];negative=[]
  class ReachedBase(Exception):pass
  for variant in ['full','no_time']:
   touched=[];proofs=[];calls=[];target=SOURCE/'software_functional/RESULT.json';functional={'passed':True};native=module(OLD/'native_audit.py','audit')
   def loader(name,path):
    path=Path(path);assert path.parent==OLD and path.is_file()and source[str(path.relative_to(R))]==sha(path),'NESTED_AUDIT_PATH_NOT_EXACT';calls.append(str(path.relative_to(R)))
    if path.name=='ew_audit.py':
     m=module(path,'audit');m.Path=Path;m.C=R/'experiments/v1271_ew_joint_phase_validation';m.read=lambda p:functional;m.load=loader;return m
    assert path.name=='base_safety.py'
    m=types.ModuleType('base_safety_software_stop');m.__file__=str(path)
    def stop(*args,**kwargs):raise ReachedBase('original native -> EW -> base safety dispatch reached before numerical body')
    m.audit=stop;return m
   native.Path=Path;native.C=R/'experiments/v1271_ew_joint_phase_validation';native.branch=lambda _: 'ew_observe';native.read=lambda _:[];native.dump=lambda *_:None;native.load=loader
   original=native.audit.__code__;binding.bind_reader(native,target,functional,source,seams,touched,proofs,variant);assert native.audit.__code__is original
   try:native.audit(dict(output=str(target.parent),case_id='EAST_WEST'))
   except ReachedBase:pass
   else:raise AssertionError('NESTED_DIRECTORY_REGRESSION_NOT_EXERCISED')
   assert calls==[str((OLD/'ew_audit.py').relative_to(R)),str((OLD/'base_safety.py').relative_to(R))]and len(proofs)==1
   timing=module(OLD/'audit_time.py','verify');timing.C=R/'experiments/v1271_ew_joint_phase_validation';binding.bind_reader(timing,target,functional,source,seams,touched,proofs,variant);assert timing.C==OLD and len(proofs)==2
   positive.append(dict(variant=variant,exact_original_dispatcher_code_unchanged=True,nested_dispatch_to_base_before_numerics=calls,directory_bindings=[x for x in touched if isinstance(x,dict)],seam_proofs=proofs,numerical_body_not_called=True))
  for kind in ['source','code','directory']:
   m=module(OLD/'native_audit.py','audit');m.C=R/'experiments/v1271_ew_joint_phase_validation';s=source.copy()
   if kind=='source':s[str((OLD/'native_audit.py').relative_to(R))]='0'*64
   if kind=='code':m.audit=lambda *_:None
   if kind=='directory':m.C=R/'experiments/v1204_goal_audit_worker'
   try:binding.bind_local_directory(m,s,seams)
   except AssertionError:negative.append(kind+'_forgery_refused')
   else:raise AssertionError('FORGED_DIRECTORY_SOURCE_CODE_ALLOWED')
  # Every relevant C-relative original dependency remains exact and available.
  dependencies=[]
  for n in ['native_audit.py','ew_audit.py','audit_time.py','audit_chain.py']:
   tree=ast.parse((OLD/n).read_text())
   for x in ast.walk(tree):
    if isinstance(x,ast.BinOp)and isinstance(x.op,ast.Div)and isinstance(x.left,ast.Name)and x.left.id=='C'and isinstance(x.right,ast.Constant)and isinstance(x.right.value,str):
     p=OLD/x.right.value;assert p.is_file()and source[str(p.relative_to(R))]==sha(p);dependencies.append(str(p.relative_to(R)))
  for name in ['entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as e:assert str(e)=='REGISTERED_PHASE_ASSIGNMENT_NOT_ADMITTED';negative.append('unadmitted_'+name)
   else:raise AssertionError('UNADMITTED_CLI_ALLOWED')
  assert all(sha(R/n)==h for n,h in source.items());target=SOURCE/'source_target';target.mkdir();put(target/'QUALIFICATION.json',dict(passed=True,positive_cases=positive,negative_cases=negative,unchanged_production_modules_reused_by_SHA=reused,original_numeric_tests_not_repeated=True,exact_C_relative_dependencies=sorted(set(dependencies)),prior_software_proof_sha256=sha(prior/'source_target/QUALIFICATION.json'),no_old_task_reaudit_or_replay=True))
  put(SOURCE/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False));result.update(passed=True,source_members=len(source),qualified_case_id='EAST_WEST',qualified_variants=['full','no_time'],negative_cases=len(negative),source_proof_sha256=sha(target/'QUALIFICATION.json'))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(SOURCE/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(SOURCE/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
