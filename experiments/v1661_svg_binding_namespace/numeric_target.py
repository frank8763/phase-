"""One real original SVGuidedMPPI constructor/solve; zero plant actions."""
import ctypes,fcntl,importlib.abc,json,os,resource,sys,time,traceback
from pathlib import Path
from context import C,O,R,put,read,sha,load,validate,fixed_input

def main():
 assert os.environ.get('PHASE_REPO')==str(R),'ISOLATION_REQUIRED'
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
 import resource_policy
 resource_policy.apply();load('v1661_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory'}:raise AssertionError('NUMERIC_NO_PLANT_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
 a=read(O/'NUMERIC_ADMISSION.json');freeze=read(O/'SOURCE_FREEZE.json');recovery=read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')
 validate(a,wall=time.time(),mono=time.monotonic(),boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),freeze_sha=sha(O/'SOURCE_FREEZE.json'),input_sha=sha(O/'INPUT.json'))
 assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and recovery['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json')
 assert read(O/'SOURCE_QUALIFICATION.json')['passed']and read(O/'SOURCE_OUTER_CLOSED.json')['passed']
 assert all(sha(R/n)==h for n,h in freeze['files'].items()),'NUMERIC_FROZEN_SOURCE_CHANGED'
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 task=O/'numeric';task.mkdir()
 with(task/'ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 inp,config,maps=fixed_input();charged=0
 def save(name,value):
  nonlocal charged
  data=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
  rounded=((len(data)+4095)//4096)*4096
  # 1MiB dedicated terminal allowance within 4MiB; charge all earlier writes twice.
  cap=4*1024**2 if name=='RESULT.json'else 3*1024**2
  assert charged+2*rounded+8192<=cap,'NUMERIC_EVIDENCE_BUDGET'
  charged+=2*rounded+8192;put(task/name,value)
 lib=None;result=None;loads=0
 try:
  # Frozen v1656 binding expects its own context O; reuse signature/identity code exactly.
  binding=load('v1661_production_binding_scope',C/'binding_scope.py').load_bound(freeze['files'])
  lib=binding.inspect_library(freeze['files']);loads=1
  transaction=load('v1661_numeric_transaction',C/'transaction.py')
  result=transaction.execute(lib,inp,config,maps,save)
 except BaseException as e:
  result=dict(passed=False,closed=True,first_error=repr(e),traceback=traceback.format_exc(),constructor_attempts=None,solve_attempts=None,internal_kinematic_rollout_steps=None,physical_native=0,replay_native=0)
  try:save('BINDING_OR_SETUP_ERROR.json',result)
  except BaseException as secondary:result['secondary_save_error']=repr(secondary)
 finally:
  result['explicit_CDLL_load_calls']=loads;print(json.dumps(result,allow_nan=False));lock.close()
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
