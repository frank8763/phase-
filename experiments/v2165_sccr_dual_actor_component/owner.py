"""One CPU2 dual-actor worker under BOTH original locks, then exact evidence closure."""
from common import *
import fcntl,subprocess,signal,traceback

def main():
 assert os.sched_getaffinity(0)=={5};assert read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];assert not(O/'OWNER_ONCE.json').exists()and not(O/'COMPLETION.json').exists()
 own=(S/'owner.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB);locks=[]
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 auth=read(S/'AUTHORIZATION.json');assert time.time()+1500<auth['absolute_end_unix'];from reservation import admission
 admission();files=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items())
 now=time.time();mono=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();dump(O/'OWNER_ONCE.json',dict(pid=os.getpid(),unix=now,scope='DUAL_FROZEN_ACTOR_ONLY',CPU=2,both_original_global_locks_held=True))
 dump(O/'NUMERICAL_ADMISSION.json',dict(scope='SCCR_TWO_FROZEN_ACTORS_SAVED_COMPONENT_ONLY',models_authorized=True,physical_admission=False,training_updates=0,source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'),absolute_end_unix=now+600,hard_stop_monotonic=mono+600,boot_id=boot,maximum_direct_forward_calls_per_actor=3,maximum_reference_batch_forward_calls_per_actor=1,maximum_direct_actor_constructors=2,maximum_SB3_reference_policy_constructors=2))
 ns=load('exact_dual_actor_Phase_namespace',C/'namespace.py');cmd=ns.command(C/'worker.py',O)
 v=dict(closed=False,passed=False,physical_models=0,physics=0,replay=0,formal_tasks=0,learned_actor_counts=None,internal_torch_work=None);p=None;identity=None
 try:
  env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
  with(O/'worker.console').open('xb')as log:
   p=subprocess.Popen(['taskset','-c','2','nice','-n','19','ionice','-c','3',*cmd],cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   identity=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=boot,CPU=2);dump(O/'OWNED_CHILD.json',identity)
   while p.poll()is None:
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<now+610 and time.monotonic()<mono+610 and not(S/'STOP').exists();assert(O/'worker.console').stat().st_size<512*1024
    time.sleep(.2)
  result=read(O/'RESULT.json');v.update(passed=bool(p.returncode==0 and result['passed']),machine_result_sha256=sha(O/'RESULT.json'),machine_first_error=result['first_error'],learned_actor_counts={k:result.get(k)for k in ['explicit_direct_actor_constructors','explicit_SB3_reference_policy_constructors','weight_deserializations','direct_forward_calls','reference_batch_forward_calls','actor_final_counters','constructor_inflight','reference_inflight','forward_inflight']},all_source_SHA_after=all(sha(R/n)==h for n,h in files.items()))
 except BaseException as e:
  v.update(first_error=repr(e),traceback=traceback.format_exc())
  if(O/'INFERENCE_PROGRESS.json').exists():v['last_durable_progress']=read(O/'INFERENCE_PROGRESS.json');v['total_calls_unknown_if_inflight']=True
 finally:
  if p is not None and p.poll()is None:
   assert Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]==identity['start_ticks']and identity['boot_id']==boot;os.killpg(identity['pgid'],signal.SIGTERM)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(identity['pgid'],signal.SIGKILL);p.wait(timeout=5)
  v.update(closed=True,returncode=None if p is None else p.returncode,wall_s=time.monotonic()-mono,full_SCCR_qualified=False);dump(O/'COMPLETION.json',v)
 for args in [['archive','POLICY'],['ref','POLICY'],['deliver','POLICY']]:
  with(S/('IO_'+args[0]+'.console')).open('xb')as log:
   q=subprocess.run(['taskset','-c','5','nice','-n','19','/usr/bin/python3','-B',str(C/'evidence.py'),*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,timeout=625)
  assert q.returncode==0,args
 d=S/'runtime_archives/POLICY';assert read(d/'FULL_REMOTE_VERIFIED.json')['passed']and read(d/'TRANSPORT_CLEANUP.json')['passed'];assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 dump(O/'POST_POLICY_STORAGE_BARRIER.json',dict(passed=True,component_passed=v['passed'],whole_navigation_passed=False,physical_models=0,physical_native=0,runtime_proof_sha256=sha(d/'FULL_REMOTE_VERIFIED.json')));dump(S/'OWNER_CLOSED.json',dict(closed=True,component_passed=v['passed'],physical_native=0,full_SCCR_qualified=False));print(json.dumps(v))
if __name__=='__main__':main()
