"""Fast real boundary/Popen regression; no TEB numerical library is loaded."""
import ast,fcntl,importlib.abc,json,os,subprocess,sys,time,traceback
from context import C,O,R,load,read,put,sha
def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1840_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*a):
   if name.split('.')[0]in {'numpy','mujoco','jax','torch','ctypes','kernel','factory','vehicle','planner','fast_predict'}:raise AssertionError('PROCESS_SOURCE_NO_NUMERICAL:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,optimizer_calls=0)
 files=read(R/'runs/v1834_teb_common_entry_gate/SOURCE_FREEZE.json')['files'].copy()
 try:
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    files[str(p.relative_to(R))]=sha(p)
  p=O/'EXACT_NATIVE_ALIASES.json';files[str(p.relative_to(R))]=sha(p)
  boundary=load('v1840_exact_original_output_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
  charged=[]
  def charge(p,size):
   assert p.is_relative_to(O)and size>=0;charged.append(dict(path=str(p.relative_to(O)),bytes=size));assert sum(x['bytes']for x in charged)<=1024**2
  native=O/'fixture_native'
  for name in ['build','tmp','build/empty_cwd','build/home']:(native/name).mkdir(parents=True,exist_ok=False)
  red=None
  with boundary.OutputBoundary(O,charge):
   try:subprocess.Popen(['/usr/bin/true'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   except AssertionError as error:
    assert str(error)=='BOUNDED_OUTPUT_PATH_ESCAPE';red=dict(reproduced=True,error=str(error),traceback=traceback.format_exc(),models=0)
   else:raise AssertionError('OLD_DEVNULL_BOUNDARY_BUG_NOT_REPRODUCED')
  put(O/'RED_REPRODUCTION.json',red);print('PROCESS_REPRO_RED '+json.dumps(dict(error=red['error'],models=0)),flush=True)
  # Run the actual future production spawn function, in the exact historical
  # readonly native namespace, with only a nonnumerical EOF/write-denial fixture.
  spawn=load('v1840_real_production_spawn',C/'spawn.py');namespace=load('v1840_exact_readonly_namespace',C/'namespace.py')
  argv=namespace.command([namespace.PYTHON,'-I','-B','-S',str(C/'child.py')],native);assert '--bind'not in argv
  for bad in ['nonempty','symlink']:
   path=native/('stdin_'+bad)
   if bad=='nonempty':path.write_bytes(b'not empty')
   else:path.symlink_to(native/'stdin_nonempty')
   try:spawn.spawn(argv,cwd=R,empty_stdin=path)
   except AssertionError as error:assert str(error)=='READONLY_EMPTY_STDIN_IDENTITY'
   else:raise AssertionError('BAD_STDIN_ALLOWED')
  with boundary.OutputBoundary(O,charge):
   empty=native/'stdin.empty';empty.write_bytes(b'')
   child=spawn.spawn(argv,cwd=R,empty_stdin=empty)
   output,_=child.communicate(timeout=10)
   assert child.returncode==0 and len(output)<16384
   lines=output.decode().splitlines();answer=json.loads(lines[-1]);assert answer['passed']and answer['stdin_eof']and answer['readonly_namespace']and answer['models']==answer['optimizer_calls']==0
  assert not(native/'build/empty_cwd/FORBIDDEN_CHILD_WRITE').exists()
  assert all(sha(R/n)==h for n,h in files.items())
  proof=dict(passed=True,old_real_Popen_DEVNULL_error_reproduced=True,production_spawn_same_original_boundaries_passed=True,exact_TEB_readonly_namespace_without_numerical_entry=True,raw_writable_descriptor_granted=False,fixture_only_not_actual=True,negative_cases=['DEVNULL_RDWR_escape','nonempty_stdin','symlink_stdin','child_write_denied'],charges=charged,child_output=answer)
  put(O/'PROCESS_BOUNDARY_PROOF.json',proof);put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False));result.update(passed=True,source_members=len(files),negative_cases=4)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
