"""One admitted saved-candidate analytical propagation, no plant/optimizer."""
import ctypes,fcntl,importlib.abc,json,os,resource,sys,time,traceback
from pathlib import Path
from context import C,O,R,put,read,sha,load,validate,fixed_input

def main():
 assert os.environ.get('PHASE_REPO')==str(R)
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy
 resource_policy.apply();load('v1667_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'mujoco','torch','jax','OpenGL','rclpy','vehicle','factory'}:raise AssertionError('RESPONSE_NO_PLANT_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 def no_dll(*args,**kwargs):raise AssertionError('RESPONSE_NO_NEW_DLL_OR_CPP_OPTIMIZER')
 ctypes.CDLL=no_dll
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
 a=read(O/'NUMERIC_ADMISSION.json');freeze=read(O/'SOURCE_FREEZE.json');recovery=read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')
 validate(a,wall=time.time(),mono=time.monotonic(),boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),freeze_sha=sha(O/'SOURCE_FREEZE.json'),input_sha=sha(O/'INPUT.json'))
 assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and recovery['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json')
 assert read(O/'SOURCE_QUALIFICATION.json')['passed']and read(O/'SOURCE_OUTER_CLOSED.json')['passed']
 assert all(sha(R/n)==h for n,h in freeze['files'].items())
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 task=O/'numeric';task.mkdir()
 with(task/'ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 inp=fixed_input();charged=0;events=(task/'STEP_EVENTS.jsonl').open('x')
 def account(n,terminal=False):
  nonlocal charged
  cap=4*1024**2 if terminal else 3*1024**2
  assert charged+n<=cap,'RESPONSE_EVIDENCE_CAP';charged+=n
 def save(name,value):
  raw=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();account(2*((len(raw)+4095)//4096)*4096+8192,name=='RESULT.json');put(task/name,value)
 def arrays(data):
  account(len(data)+8192);assert not(task/'RAW_RESPONSE.npz').exists();(task/'RAW_RESPONSE.npz').write_bytes(data)
 def event(kind,i):
  raw=json.dumps([kind,i],separators=(',',':'))+'\n';account(len(raw));events.write(raw);events.flush()
 result=None
 try:result=load('v1676_DWA_original_response',C/'response.py').execute(inp,freeze['files'],save,arrays,event)
 except BaseException as e:
  result=dict(passed=False,closed=True,first_error=repr(e),traceback=traceback.format_exc(),constructor_attempts=None,response_step_attempts=None,physical_native=0,replay_native=0)
  try:save('SETUP_ERROR.json',result)
  except BaseException as secondary:result['secondary_save_error']=repr(secondary)
 finally:
  events.close();print(json.dumps(result,allow_nan=False));lock.close()
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
