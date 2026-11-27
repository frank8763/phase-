"""One source-qualified detached owner; no inline numerical launcher."""
from context import R,C,SOURCE as S,O,read,put,sha,remaining,predecessors_closed
from pathlib import Path
import fcntl,os,subprocess,time,json
def check():
 assert os.sched_getaffinity(0)=={5}
 assert(S/'POST_SOURCE_STORAGE_BARRIER.json').is_file(),'SOURCE_REMOTE_RECOVERY_NOT_READY'
 assert read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 assert all(not(S/n).exists()for n in ['DISPATCH_ONCE.json','LAUNCH_IDENTITY.json'])
 assert all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual'])
 a=read(S/'AUTHORIZATION.json');assert a['scope']=='ORIENTATION_PROJECTION_CP_COMPONENT'and remaining(a)>6900,'NEW_SOURCE_WINDOW_RESERVE_NOT_EXTENDED'
 predecessors_closed();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 files=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items())
 from reserved_census import admission
 return admission()
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 with(S/'dispatch.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);budget=check();handles=[]
  for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
   f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);handles.append(f)
  # Atomic once record survives Popen errors: no hidden automatic retry.
  with(S/'DISPATCH_ONCE.json').open('x')as f:json.dump(dict(unix=time.time(),source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'),models=0,budget=budget),f)
  for f in handles:f.close()
  with(S/'owner.console').open('xb')as log:
   p=subprocess.Popen(['taskset','-c','5','nice','-n','19','ionice','-c','3','/usr/bin/python3','-B',str(C/'owner.py')],cwd=R,env=dict(os.environ,PHASE_FILTER_METHOD='PROJ',PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),source_commit=read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['source_commit'],unix=time.time())
  put(S/'LAUNCH_IDENTITY.json',i);print(json.dumps(i))
if __name__=='__main__':main()
