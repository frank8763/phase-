"""One isolated ABI load, introspection and pre-constructor refusals only."""
import ast,ctypes,fcntl,importlib.abc,os,runpy,sys,time,traceback
from context import C,O,R,put,read,sha,load
def main():
 start=time.monotonic();os.environ['MUJOCO_GL']='osmesa'
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
 import resource_policy
 resource_policy.apply();load('v1656_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory'}:raise AssertionError('ABI_NO_MODEL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 result=dict(passed=False,closed=False,source_only=True,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,author_constructor_calls=0,optimizer_calls=0,actual_runtime_qualified=False)
 source=read(R/'runs/v1649_error_stop_sensor_capture/SOURCE_FREEZE.json')['files'].copy()
 original=ctypes.CDLL
 try:
  assert read(O/'BUILD_RESULT.json')['passed']
  source.update(read(O/'BUILD_INPUTS.json')['files'])
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for p in [O/'BUILD_RESULT.json',O/'libphase_svg_bridge.so',R/'runs/v1649_error_stop_sensor_capture/CURRENT_SOURCE_REMOTE_RECOVERY.json']:
   source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items())
  def dll(*args,**kwargs):result['FFI_loads']+=1;return original(*args,**kwargs)
  ctypes.CDLL=dll
  binding=load('v1656_exact_abi',C/'binding.py');negatives=[]
  for label,path in [('bridge','runs/v1656_svg_solver_interface/libphase_svg_bridge.so'),('core','runs/v1655_svg_original_build_flags/libphase_svg_author_cpu.so')]:
   altered=source.copy();altered[path]='0'*64
   try:binding.inspect_library(altered)
   except AssertionError:negatives.append(label+'_source_mismatch_before_dlopen')
   else:raise AssertionError('CHANGED_BINARY_ACCEPTED')
   assert result['FFI_loads']==0
  lib=binding.inspect_library(source);assert result['FFI_loads']==1
  # Calls below are C ABI metadata and error paths. No valid configuration or
  # handle is supplied, so original author constructors/solve cannot execute.
  def call(fn,*args):result['FFI_calls']+=1;return fn(*args)
  assert call(lib.phase_svg_abi_version)==1
  assert call(lib.phase_svg_state_dimension)==5
  assert call(lib.phase_svg_control_dimension)==1
  assert call(lib.phase_svg_create,None,0,None,0)is None
  error=ctypes.create_string_buffer(256);call(lib.phase_svg_error,error,256);assert error.value==b'CONFIGURATION_SHAPE';negatives.append('invalid_configuration_before_author_constructor')
  assert call(lib.phase_svg_set_maps,None,0,0,0.,0.,0.,None,None,None,None)==-1
  call(lib.phase_svg_error,error,256);assert error.value==b'HANDLE_NOT_READY';negatives.append('missing_handle_before_gridmap')
  assert call(lib.phase_svg_solve,None,None,0,None,0,None)==-1
  call(lib.phase_svg_error,error,256);assert error.value==b'SOLVER_NOT_READY_OR_POISONED';negatives.append('missing_handle_before_optimizer')
  assert call(lib.phase_svg_call_counts,None,None,0)==-1;negatives.append('invalid_counter_handle')
  try:runpy.run_path(str(C/'entry.py'),run_name='__main__')
  except AssertionError as e:assert str(e)=='SVG_NUMERIC_ADMISSION_MISSING';negatives.append('actual_unadmitted_numeric_CLI')
  else:raise AssertionError('NUMERICAL_ENTRY_ACCEPTED')
  assert all(sha(R/n)==h for n,h in source.items())
  put(O/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False))
  result.update(passed=True,source_members=len(source),negative_cases=negatives,ABI_version=1,state_dimension=5,control_dimension=1,explicit_CDLL_load_calls=1,project_ELF_dependency='runs/v1655_svg_original_build_flags/libphase_svg_author_cpu.so',no_valid_author_configuration_or_handle_created=True,signatures_bound=True,real_numeric_CLI_refused=True)
 except BaseException as e:
  result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
 finally:
  ctypes.CDLL=original;result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
