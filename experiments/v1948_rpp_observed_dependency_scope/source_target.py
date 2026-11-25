"""Necessary new RPP synchronous binding SOURCE check, no numerical calls."""
import ast,copy,fcntl,importlib.abc,os,runpy,subprocess,sys,time,traceback
from context import C,O,R,read,sha,put,load

def main():
 start=time.monotonic();assert os.sched_getaffinity(0)=={2};sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply();load('rpp_immutable_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,source_only=True,actual_runtime_qualified=False);files=read(R/'runs/v1923_dwa_five_checked_queue/SOURCE_FREEZE.json')['files'].copy()
 try:
  prior=R/'runs/v1923_dwa_five_checked_queue';assert read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  for n,h in read(O/'DWA_CLOSED_BARRIERS.json')['files'].items():assert sha(R/n)==h
  build=read(R/'runs/v1943_rpp_synchronous_native_api/BUILD_RESULT.json');assert build['build_passed']and build['DLL_loads']==0
  files.update(read(O/'INPUT_BINDING.json')['files'])
  for folder in [C,R/'experiments/v1943_rpp_synchronous_native_api']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [O/'INPUT_BINDING.json',O/'DWA_CLOSED_BARRIERS.json',O/'AUTHORIZATION.json',R/'runs/v1943_rpp_synchronous_native_api/BUILD_RESULT.json']:files[str(p.relative_to(R))]=sha(p)
  software=read(O/'INVENTORY_SOFTWARE_RESULT.json');assert software['passed']and len(software['negative_cases'])==6
  files[str((O/'INVENTORY_SOFTWARE_RESULT.json').relative_to(R))]=sha(O/'INVENTORY_SOFTWARE_RESULT.json')
  assert all(sha(R/n)==h for n,h in files.items())
  class Ban(importlib.abc.MetaPathFinder):
   def find_spec(self,name,*args):
    if name.split('.')[0]in {'numpy','mujoco','torch','jax','rclpy','factory','vehicle','kernel'}:raise AssertionError('RPP_SOURCE_NO_MODEL_IMPORT:'+name)
  sys.meta_path.insert(0,Ban());binding=load('rpp_sync_source_binding',C/'binding.py');bad=files.copy();bad[build['binary_path']]='0'*64;neg=[]
  try:binding.bind(bad,source_only=True)
  except AssertionError as e:assert str(e)=='RPP_SYNC_BINARY_CHANGED';neg.append('binary_before_dlopen')
  else:raise AssertionError('BAD_BINARY_ACCEPTED')
  try:binding.bind(files)
  except AssertionError as e:assert str(e)=='RPP_SYNC_NUMERICAL_ADMISSION_MISSING';neg.append('normal_binding_before_dlopen')
  else:raise AssertionError('UNADMITTED_BINDING_ACCEPTED')
  try:runpy.run_path(str(C/'entry.py'),run_name='__main__')
  except AssertionError as e:assert str(e)=='RPP_SYNC_NUMERICAL_ADMISSION_MISSING';neg.append('real_numeric_CLI')
  else:raise AssertionError('UNADMITTED_ENTRY_ACCEPTED')
  expected=dict(receipt_sha256='a'*64,public_map_sha256='b'*64,inflation_source_sha256='c'*64);grid=dict(source_receipt_sha256='a'*64,public_map_sha256='b'*64,inflation_source_sha256='c'*64,width=2,height=2,resolution=.05,origin=[0.,0.],cells=[0,0,0,0],footprint_xy=[[0.,0.]]*4);assert binding.validate_grid(grid,expected)
  for name,key,value in [('truth','actor_truth',[0,0]),('foreign_origin','source_receipt_sha256','d'*64),('short_grid','cells',[0]),('nonbyte_grid','cells',[0,0,0,256])]:
   g=copy.deepcopy(grid);g[key]=value
   try:binding.validate_grid(g,expected)
   except AssertionError:neg.append(name)
   else:raise AssertionError('BAD_GRID_ACCEPTED')
  ros=load('existing_qualified_ros_ns',R/'experiments/v856_nav2_foundation/ros_environment.py');env=ros.environment();env.update(ROS_DOMAIN_ID='194',ROS_LOG_DIR=str(O/'ros_logs'),CUDA_VISIBLE_DEVICES='');cmd=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'native_metadata.py')]);p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,timeout=60);(O/'native_metadata.console').write_bytes(p.stdout+p.stderr);assert p.returncode==0,('NATIVE_RPP_ABI_REFUSED',p.returncode)
  native=read(O/'NATIVE_METADATA_RESULT.json');assert native['passed']and native['controller_constructors']==native['solver_calls']==0
  assert all(sha(R/n)==h for n,h in files.items());put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False,namespace_ELF_files_SHA256=read(O/'INPUT_BINDING.json')['namespace_ELF_files_SHA256']));put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(prior.relative_to(R)),freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),recovery_path=str((prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),negative_cases=neg,explicit_DLL_loads=1,metadata_and_null_FFI_calls=6,controller_constructors=0,solver_calls=0,newELFdependencies_exact=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
