"""New cached-library seam only: two DLL loads, zero numerical calls."""
import ast,ctypes,fcntl,os,runpy,sys,time,traceback,types
from pathlib import Path
from context import C,O,R,put,read,sha,load

def main():
 start=time.monotonic();os.environ['MUJOCO_GL']='osmesa';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1636_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,source_only=True,actual_runtime_qualified=False,FFI_loads=0,FFI_calls=0)
 source=read(R/'runs/v1632_original_pilot_resources/SOURCE_FREEZE.json')['files'].copy()
 try:
  assert read(R/'runs/v1632_original_pilot_resources/COMPLETION.json')['closed']
  assert read(R/'runs/v1632_original_pilot_resources/POST_ROUND_STORAGE_BARRIER.json')['passed']
  for folder in [C,R/'experiments/v1635_original_cached_backends']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     source[str(p.relative_to(R))]=sha(p)
  for n in ['AUTHORIZATION.json','TASKS_LOCKED.json','PILOT_TASK.json','LIMITS_DRAFT.json','PILOT_SPEC_AMENDMENT.json']:source[str((O/n).relative_to(R))]=sha(O/n)
  for n in ['analytical_rebuilt.so','COMPILE_RESULT.json','COMPILE_ONCE_CLAIM.json']:
   p=R/'runs/v1635_original_cached_backends'/n;source[str(p.relative_to(R))]=sha(p)
  assert read(R/'runs/v1635_original_cached_backends/COMPILE_RESULT.json')['exact_binary_match']
  assert all(sha(R/n)==h for n,h in source.items())
  for n in ['context.py','driver.py','runtime_binding.py','owner.py','source_owner.py','pilot_entry.py','work.py','quota.py','audit_binding.py','transforms.py','history_binding.py']:
   tree=ast.parse((C/n).read_text());old=ast.parse((R/'experiments/v1632_original_pilot_resources'/n).read_text())
   if n in ['work.py','quota.py','audit_binding.py','transforms.py','history_binding.py','pilot_entry.py','context.py','source_owner.py']:
    a=ast.dump(tree,include_attributes=False).replace('v1636_cached_original_runtime','v1632_original_pilot_resources');assert a==ast.dump(old,include_attributes=False),(n,'UNEXPECTED_AST_CHANGE')
  binding_ast=ast.parse((C/'runtime_binding.py').read_text());b=next(n for n in binding_ast.body if isinstance(n,ast.FunctionDef)and n.name=='bind')
  assert not any(isinstance(n,ast.Call)and ast.unparse(n.func).endswith(('.library','Reserve','Expander'))for n in ast.walk(b))
  assert 'brake_reserve.library=planner.library' in (C/'runtime_binding.py').read_text()
  driver=(C/'driver.py').read_text();assert driver.index('runtime.bind(')<driver.index('factory.create_vehicle')<driver.index("binding['owner'].navigate")
  import numpy as np,hashlib,subprocess
  helper=load('v1635_cached_seam',R/'experiments/v1635_original_cached_backends/cached_libraries.py')
  blocked=[]
  def forbid(*args,**kwargs):blocked.append(True);raise AssertionError('SOURCE_TARGET_NUMERICAL_OR_COMPILER_CALL_FORBIDDEN')
  def modules(output):
   answer=[]
   for relative in ['experiments/v1067_causal_replan_brake_reserve/planner.py','experiments/v1046_retreat_entry_timed_route/fast_predict.py']:
    path=R/relative;m=types.ModuleType('SOFTWARE_EXACT_ORIGINAL_LIBRARY');m.__file__=str(path)
    m.__dict__.update(C=path.parent,R=R,O=output,ctypes=ctypes,np=np,hashlib=hashlib,subprocess=types.SimpleNamespace(run=forbid),fcntl=fcntl,os=os,Path=Path)
    m.library=types.FunctionType(helper.original_code(path),vars(m),'library');answer.append(m)
   return answer
  def profile(frame,event,arg):
   if event=='call':
    filename=frame.f_code.co_filename
    assert not any(s in filename for s in ['/coupled_model.py','/coupled_control.py','/factory.py','/vehicle.py','/fast_predict.cpp']),('FORBIDDEN_MODEL_SOURCE_CALL',filename)
  sys.setprofile(profile)
  from quota import EvidenceQuota
  io=load('v1636_original_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
  root=O/'source_target';root.mkdir();quota=EvidenceQuota(root,read(O/'LIMITS_DRAFT.json'));quota.bind_external_names([]);quota.write_enforcement_active=True
  negatives=[]
  def refuse(label,fn):
   before=result['FFI_loads']
   try:fn()
   except (AssertionError,KeyError,FileNotFoundError):negatives.append(label)
   else:raise AssertionError('SOURCE_NEGATIVE_ACCEPTED:'+label)
   assert result['FFI_loads']==before
  realdll=ctypes.CDLL
  def dll(*a,**kw):result['FFI_loads']+=1;return realdll(*a,**kw)
  ctypes.CDLL=dll
  try:
   with io.OutputBoundary(root,quota.charge_write):
    quota.prepare_grant(4*1024**2,phase='STOPPED_EVENT_PREPARATION',valid_for_s=180,external_writers=[])
    positive=root/'positive';positive.mkdir();planner,fast=modules(positive)
    proof=helper.bind(positive,planner=planner,fast=fast,source=source)
    search=planner.library();expand=fast.library()
    assert result['FFI_loads']==2 and [len(search.search.argtypes),len(search.static_pose.argtypes),len(search.stop_lower.argtypes),len(expand.expand.argtypes)]==[19,7,10,12]
    assert search.search.restype is ctypes.c_int and search.static_pose.restype is search.stop_lower.restype is ctypes.c_double and expand.expand.restype is ctypes.c_int
    refuse('same_binding_no_retry',lambda:helper.bind(positive,planner=planner,fast=fast,source=source))
    for module,row in zip([planner,fast],proof['copies']):
     target=R/row['current'];original=target.read_bytes();target.unlink();refuse('missing_cache_before_dlopen',module.library)
     target.write_bytes(original+b'x');refuse('changed_cache_before_dlopen',module.library);target.unlink();target.write_bytes(original)
    for label,change in [('source_identity',lambda p,f,s:s.update({str(Path(p.__file__).relative_to(R)):'0'*64})),('function_code',lambda p,f,s:setattr(f,'library',lambda:None)),('output_identity',lambda p,f,s:setattr(p,'O',root)),('unregistered_binary',lambda p,f,s:s.pop('runs/v1635_original_cached_backends/analytical_rebuilt.so'))]:
     folder=root/label;folder.mkdir();p,f=modules(folder);registered=source.copy();change(p,f,registered)
     refuse(label,lambda:helper.bind(folder,planner=p,fast=f,source=registered))
    assert not blocked
    put(root/'CACHE_SOURCE_PROOF.json',dict(passed=True,copies=proof['copies'],signatures_checked=[19,7,10,12],negative_cases=negatives,FFI_loads=2,FFI_numerical_calls=0,original_runtime_imported=False,models=0))
   quota.write_enforcement_active=False
  finally:ctypes.CDLL=realdll;sys.setprofile(None)
  try:runpy.run_path(str(C/'driver.py'),run_name='__main__')
  except AssertionError as error:assert str(error)=='NEW_ORIGINAL_CONTRACT_PILOT_NOT_ADMITTED'
  else:raise AssertionError('UNADMITTED_DRIVER_EXECUTED')
  assert read(O/'CLI_REFUSAL.json')['models']==0
  put(O/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False))
  result.update(passed=True,source_members=len(source),negative_cases=len(negatives),cached_original_signatures=True,compiler_calls=0,FFI_loads=2,FFI_calls=0,original_runtime_imported=False,numerical_bodies_reused_unchanged=True,real_CLI_missing_admission_refused=True)
 except BaseException as error:
  sys.setprofile(None);result.update(first_error=repr(error),traceback=traceback.format_exc())
  put(O/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
 finally:
  result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
