"""Pre-claim metadata correction only; unchanged native owners, no old retry."""
from pathlib import Path
import json,hashlib,os,subprocess,time,traceback
R=Path(__file__).resolve().parents[2];O=R/'runs/v1996_parallel_lock_bootstrap';S=R/'runs/v1993_parallel_compact_source';C=R/'experiments/v1993_parallel_compact_source'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 os.sched_setaffinity(0,{5});assert not(O/'ONCE.json').exists();prior=read(S/'PARALLEL_RESULT.json');assert prior['closed']and prior['first_error']=="FileNotFoundError(2, 'No such file or directory')";assert read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];put(O/'ONCE.json',dict(pid=os.getpid(),unix=time.time(),prior_failed_dispatch_sha256=sha(S/'PARALLEL_RESULT.json'),original_native_owner_sha256=sha(C/'owner.py'),late_outside_source_archive=True,source_commit=read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['source_commit']));jobs=[]
 for lane,cpu in [('MPPI',6),('SVG-MPPI',7)]:
  laneout=S/'lanes'/lane
  for n in ['OWNER_ONCE.json','ADMISSION.json','NATIVE_ONCE.json','OWNED_CHILD.json','RESULT.json','COMPLETION.json']:assert not(laneout/n).exists(),'ALGORITHM_ALREADY_CLAIMED_NO_RETRY'
  assert "owner.lock"in(laneout/'owner.console').read_text()and 'FileNotFoundError'in(laneout/'owner.console').read_text()
  for n in ['owner.lock','execution.lock']:
   p=laneout/n;assert not p.exists();p.touch(exist_ok=False)
 for lane,cpu in [('MPPI',6),('SVG-MPPI',7)]:
  f=(S/'lanes'/lane/'owner_first_actual.console').open('xb');p=subprocess.Popen(['taskset','-c',str(cpu),'/usr/bin/python3','-B',str(C/'owner.py')],cwd=R,env=dict(os.environ,PHASE_ALGORITHM_LANE=lane,PYTHONDONTWRITEBYTECODE='1'),stdout=f,stderr=subprocess.STDOUT);jobs.append((lane,p,f))
 for lane,p,f in jobs:p.wait(timeout=330);f.close()
 results={}
 for lane,p,_ in jobs:
  q=S/'lanes'/lane/'COMPLETION.json';results[lane]=read(q)if q.exists()else dict(closed=True,passed=False,result_missing=True,console_sha256=sha(S/'lanes'/lane/'owner_first_actual.console'),counts_unknown_not_zero=True)
 put(O/'RESULT.json',dict(closed=True,passed=all(v['passed']for v in results.values()),lanes=results,source_helper_sha256=sha(Path(__file__)),no_old_algorithm_operation_repeated=True,physics_native=0,formal_common_tasks=0));print(json.dumps({n:dict(passed=v['passed'],error=v.get('first_error')or(v.get('native_result')or{}).get('first_error'))for n,v in results.items()}))
if __name__=='__main__':main()
