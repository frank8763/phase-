"""Once CPU4/run_phase real nested PID binding qualification; no kernel load."""
import ast
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def put(p,value):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');t.replace(p)
class NoNumeric(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'jax','jaxlib','numpy','scipy','torch','mujoco','rclpy','vehicle','factory'}:raise AssertionError('NAMESPACE_ENTRY_NO_NUMERIC:'+name)
def main():
 assert sorted(os.sched_getaffinity(0))==[4]and os.environ['PHASE_REPO']==str(R)and time.time()+30<1795395600
 with(O/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(started_unix=time.time(),models=0),f)
 sys.meta_path.insert(0,NoNumeric());common=load('v1503_immutable_guard',R/'experiments/v1500_priest_thread_observation/common.py');common.guard(O);common=load('v1503_immutable_common',R/'experiments/v1500_priest_thread_observation/common.py');common.guard(O)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=common.read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
  original=R/'experiments/v1500_priest_thread_observation/sandbox.py';sandbox=load('v1503_exact_nested_sandbox',original);task=O/'task';task.mkdir();cmd=sandbox.command(task,mode='OPTIMIZER',scratch_bytes=2*1024**2);assert cmd[-1]==str(original.parent/'inner.py');cmd[-1]=str(C/'inner.py')
  result=dict(passed=False,closed=False,models=0,optimizer_calls=0)
  try:
   p=subprocess.run(cmd,capture_output=True,timeout=20);assert len(p.stdout)+len(p.stderr)<=65536;stdout=p.stdout.decode();child=json.loads(stdout);put(O/'NESTED_RESULT.json',child);(O/'nested.stderr').write_bytes(p.stderr)
   assert p.returncode==0 and child['passed']and child['all_target_helpers_joined'];assert child['JAX_author_imported']is False
   files={str(v.relative_to(R)):sha(v)for v in C.iterdir()if v.is_file()};files[str(original.relative_to(R))]=sha(original);files[str((original.parent/'common.py').relative_to(R))]=sha(original.parent/'common.py')
   put(O/'SOURCE_FREEZE.json',dict(files=files,source_namespace_only_qualified=True,numerical_or_model_admission=False));result.update(passed=True,namespace_ID_mismatch_demonstrated=True,old_visible_ESRCH_reproduced=True,correct_current_namespace_masks_all_CPU4=True,old_OS_byte_target_not_reexecuted=True,scope='EXACT_NESTED_PID_NAMESPACE_SOURCE_ONLY')
  except BaseException as error:result.update(error=repr(error),traceback=traceback.format_exc())
  finally:result['closed']=True;put(O/'QUALIFICATION.json',result)
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
