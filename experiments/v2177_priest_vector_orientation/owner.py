"""One bounded CPU3 ideal mathematical worker. Source-bound closure on either outcome."""
from context import R,C,ROOT,O,read,put,sha,load,remaining
from pathlib import Path
import os,time,subprocess,traceback,signal,fcntl,json
from reservation import admission,idle

def fresh():
 assert read(ROOT/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 assert all(not(O/n).exists()for n in ['OWNER_ONCE.json','WORKER_ONCE.json','NUMERICAL_ADMISSION.json','COMPLETION.json','RESULT.json','OWNED_CHILD.json'])
 assert remaining(read(ROOT/'AUTHORIZATION.json'))>1500
 files=read(ROOT/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());admission();handles=idle();return files,handles

def main():
 assert os.sched_getaffinity(0)=={5};lock=(ROOT/'owner.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);files,handles=fresh()
 now=time.time();mono=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 with(O/'OWNER_ONCE.json').open('x')as f:json.dump(dict(unix=now,pid=os.getpid(),models=0,scope='FINITE_ORIENTATION_STATE_PROJECTION_ONLY'),f)
 put(O/'NUMERICAL_ADMISSION.json',dict(scope='FINITE_ORIENTATION_STATE_PROJECTION_ONLY',numerical_authorized=True,models_authorized=False,maximum_NLP_calls=2,worker_sha256=sha(C/'worker.py'),source_freeze_sha256=sha(ROOT/'SOURCE_FREEZE.json'),absolute_end_unix=now+600,hard_stop_monotonic=mono+600,boot_id=boot))
 for f in handles:f.close() # ideal math does not occupy plant locks
 from namespace import command
 argv=command(C/'worker.py',O);v=dict(closed=False,passed=False,models=0,physics=0,replay=0,actual=0,formal_tasks=0,NLP_returns=None,attempted_calls=None,inflight_unknown=None,internal_optimizer_work=None);p=None;i=None
 try:
  with(O/'worker.console').open('xb')as log:
   p=subprocess.Popen(['taskset','-c','3','nice','-n','19','ionice','-c','3',*argv],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=boot,CPU=3,scope='PURE_IDEAL_NLP_NO_PLANT');put(O/'OWNED_CHILD.json',i)
   while p.poll()is None:
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<now+610 and time.monotonic()<mono+610 and (O/'worker.console').stat().st_size<256*1024 and not(ROOT/'STOP').exists();time.sleep(.3)
   m=read(O/'RESULT.json');v.update(passed=bool(p.returncode==0 and m['passed']),machine_result_sha256=sha(O/'RESULT.json'),NLP_returns=m['NLP_returns'],attempted_calls=m['attempted_calls'],inflight_unknown=m['inflight_unknown'],machine_first_error=m.get('first_error'),attempted_case_ids=m['attempted_case_ids'],unexecuted_case_ids=m['unexecuted_positive_case_ids'],case_summaries=m['cases'])
 except BaseException as e:v.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if p is not None and p.poll()is None:
   assert Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]==i['start_ticks'];os.killpg(i['pgid'],signal.SIGTERM)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=5)
  allsource=all(sha(R/n)==h for n,h in files.items());v.update(closed=True,passed=bool(v['passed']and allsource),all_source_SHA_after=allsource,returncode=None if p is None else p.returncode,wall_s=time.monotonic()-mono,console_sha256=sha(O/'worker.console')if(O/'worker.console').exists()else None);put(O/'COMPLETION.json',v)
  put(O/'RUNTIME_CLOSED_REVIEW.json',dict(v,whole_navigation_passed=False,native_author_PRIEST=False,mathematical_component_only=True,machine_missing_is_not_zero_or_success=not(O/'RESULT.json').exists()))
 for args in [['archive','MATH'],['ref','MATH'],['deliver','MATH']]:
  with(ROOT/('IO_'+args[0]+'.console')).open('xb')as log:
   q=subprocess.run(['taskset','-c','5','nice','-n','19','/usr/bin/python3','-B',str(C/'evidence.py'),*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=625)
  assert q.returncode==0,args
 d=ROOT/'runtime_archives/MATH';assert read(d/'FULL_REMOTE_VERIFIED.json')['passed']and read(d/'TRANSPORT_CLEANUP.json')['passed'];handles=idle()
 put(O/'POST_MATH_STORAGE_BARRIER.json',dict(passed=True,scientific_navigation_passed=None,math_component_passed=v['passed'],runtime_proof_path=str((d/'FULL_REMOTE_VERIFIED.json').relative_to(R)),runtime_proof_sha256=sha(d/'FULL_REMOTE_VERIFIED.json'),index_path=str((d/'ARCHIVE_INDEX.json').relative_to(R)),index_sha256=sha(d/'ARCHIVE_INDEX.json'),cleanup_sha256=sha(d/'TRANSPORT_CLEANUP.json'),models=0,REVIEW_exact=True,plant_locks_idle=True));put(ROOT/'OWNER_CLOSED.json',dict(closed=True,pipeline_passed=True,math_passed=v['passed'],actual=0,formal_tasks=0));print(json.dumps(v))
if __name__=='__main__':main()
