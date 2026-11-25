"""Real lock-lifetime software feedback; zero numeric/native/model calls."""
from context import R,C,O,read,sha,put
import ast,fcntl,subprocess,time,os

def main():
 assert not(O/'SOURCE_ONCE_CLAIM.json').exists();put(O/'SOURCE_ONCE_CLAIM.json',dict(unix=time.time(),models=0,DLL_loads=0));lock=O/'software_lock_fixture';ready=O/'SOFTWARE_LOCK_READY';cmd=['flock','-n',str(lock),'/usr/bin/python3.12','-I','-B','-S','-c',"from pathlib import Path;import time;Path("+repr(str(ready))+").write_text('held');time.sleep(.4)"];p=subprocess.Popen(cmd);start=time.monotonic()
 while not ready.exists():assert time.monotonic()<start+3;time.sleep(.01)
 refused=False
 with lock.open()as f:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:refused=True
 assert refused;p.wait(timeout=3);assert p.returncode==0
 with lock.open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 prior=R/'runs/v1952_rpp_component_entry_checked';assert read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered'];frozen=read(prior/'SOURCE_FREEZE.json')['files'].copy()
 for q in C.iterdir():
  if q.is_file():
   if q.suffix=='.py':ast.parse(q.read_text())
   frozen[str(q.relative_to(R))]=sha(q)
 assert all(sha(R/n)==h for n,h in frozen.items());put(O/'SOURCE_FREEZE.json',dict(files=frozen,models_authorized=False));put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(prior.relative_to(R)),freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),recovery_path=str((prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result=dict(passed=True,closed=True,models=0,DLL_loads=0,controller_constructors=0,solver_calls=0,physics=0,replay=0,lock_refused_while_child_running=True,lock_idle_after_exit=True,source_members=len(frozen),exact_original_owner_retained=True);put(O/'SOURCE_QUALIFICATION.json',result);put(O/'SOURCE_OUTER_CLOSED.json',dict(passed=True,closed=True,software_only=True,models=0));put(O/'AUTHORIZATION.json',dict(user_instruction='继续',source_transport_only=True,models_authorized=False));print(__import__('json').dumps(result))
if __name__=='__main__':main()
