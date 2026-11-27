"""Source-qualified file launcher; all guards before one detached owner."""
from common import *
import subprocess,fcntl

def main():
 assert os.sched_getaffinity(0)=={5};assert(S/'POST_SOURCE_STORAGE_BARRIER.json').is_file(),'SOURCE_REMOTE_RECOVERY_NOT_READY';assert read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
 assert not(S/'LAUNCH_IDENTITY.json').exists()and all(not(O/n).exists()for n in ['OWNER_ONCE.json','WORKER_ONCE.json','OWNED_CHILD.json','COMPLETION.json'])
 a=read(S/'AUTHORIZATION.json');assert time.time()+1500<a['absolute_end_unix'];assert read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered'];assert read(R/'runs/v2162_pcbf_conditioned_current100/components/PCBF/POST_COMPONENT_STORAGE_BARRIER.json')['passed']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  with(R/n).open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(S/'owner.console').open('xb')as log:
  p=subprocess.Popen(['taskset','-c','5','nice','-n','19','ionice','-c','3','/usr/bin/python3','-B',str(C/'owner.py')],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),source_commit=read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['source_commit'],unix=time.time());dump(S/'LAUNCH_IDENTITY.json',i);print(json.dumps(i))
if __name__=='__main__':main()
