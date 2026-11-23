"""Actual production namespace seam tested without real DLL or numerical calls."""
import ast,ctypes,fcntl,importlib.abc,json,runpy,sys,time,traceback
from context import C,O,R,put,read,sha,load,fixed_input

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
 import resource_policy
 resource_policy.apply();load('v1661_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory'}:raise AssertionError('SOURCE_NO_NUMERICAL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(R/'runs/v1658_svg_bounded_numeric/SOURCE_FREEZE.json')['files'].copy();original=ctypes.CDLL
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,author_constructor_calls=0,optimizer_calls=0)
 try:
  assert read(R/'runs/v1658_svg_bounded_numeric/POST_ROUND_STORAGE_BARRIER.json')['passed']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for folder,names in [(O,['INPUT.json','MAPS.json','CONFIG.json','PREPARATION_CHECKPOINT.json']),
   (R/'runs/v1658_svg_bounded_numeric',['SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','POST_ROUND_STORAGE_BARRIER.json','RUNTIME_CLOSED_REVIEW.json'])]:
   for name in names:p=folder/name;source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items());fixed_input()
  for name in ['INPUT.json','MAPS.json','CONFIG.json','transaction.py','context.py']:
   before=(R/'runs/v1658_svg_bounded_numeric'/name)if name.endswith('.json')else R/'experiments/v1658_svg_bounded_numeric'/name
   after=(O/name)if name.endswith('.json')else C/name
   assert sha(before)==sha(after),'UNCHANGED_INPUT_OR_TRANSACTION'
  proof=read(R/'runs/v1658_svg_bounded_numeric/SOURCE_QUALIFICATION.json');assert proof['passed']and len(proof['software_dispatch_cases'])==9 and len(proof['negative_cases'])==9
  seam=load('v1661_production_namespace',C/'binding_scope.py');previous=sys.modules['context'];seen=[]
  class Symbol:
   def __call__(self,*args):raise AssertionError('NO_FFI_CALL_IN_SOURCE')
  class FakeDLL:
   def __getattr__(self,name):value=Symbol();setattr(self,name,value);return value
  def fake_dll(path):seen.append(path);return FakeDLL()
  ctypes.CDLL=fake_dll
  bound=seam.load_bound(source);assert sys.modules['context']is previous
  assert bound.O==R/'runs/v1656_svg_solver_interface'
  library=bound.inspect_library(source)
  assert seen==[str(R/'runs/v1656_svg_solver_interface/libphase_svg_bridge.so')]
  assert len(library.phase_svg_create.argtypes)==4 and len(library.phase_svg_solve.argtypes)==6
  negatives=[]
  for path in ['experiments/v1656_svg_solver_interface/context.py','experiments/v1656_svg_solver_interface/binding.py']:
   bad=source.copy();bad[path]='0'*64
   try:seam.load_bound(bad)
   except AssertionError:negatives.append(path+'_SHA_refusal')
   else:raise AssertionError('CHANGED_BINDING_ACCEPTED')
   assert sys.modules['context']is previous
  def failing_loader(name,path):
   if path.name=='binding.py':raise RuntimeError('INJECTED_IMPORT_FAILURE')
   return load(name,path)
  try:seam.load_bound(source,loader=failing_loader)
  except RuntimeError:negatives.append('namespace_restored_after_import_failure')
  else:raise AssertionError('IMPORT_FAULT_NOT_RAISED')
  assert sys.modules['context']is previous
  try:runpy.run_path(str(C/'entry.py'),run_name='__main__')
  except AssertionError as e:assert str(e)=='SVG_NUMERIC_ADMISSION_MISSING';negatives.append('actual_missing_admission_CLI')
  else:raise AssertionError('NUMERIC_CLI_ACCEPTED')
  assert all(sha(R/n)==h for n,h in source.items())
  (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source,source_only=True,numerical_admission=False),sort_keys=True,separators=(',',':'))+'\n')
  result.update(passed=True,source_members=len(source),negative_cases=negatives,fake_CDLL_factory_calls=len(seen),actual_CDLL_calls=0,production_namespace_scope_checked=True,old_software_cases_reused_by_SHA=True,old_source_proof_sha256=sha(R/'runs/v1658_svg_bounded_numeric/SOURCE_QUALIFICATION.json'),unchanged_input_config_transaction=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());(O/'FAILED_SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source)))
 finally:
  ctypes.CDLL=original;result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
