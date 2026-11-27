"""One nonphysical CPU3 worker, then source-bound evidence closure, no plant locks."""
from context import R,C,ROOT,O,P,read,put,sha,load
from pathlib import Path
import os,time,subprocess,traceback,signal,fcntl,json

def main():
 assert os.sched_getaffinity(0)=={5};assert read(ROOT/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];lock=(ROOT/'owner.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(O/'OWNER_ONCE.json').exists()and not(O/'COMPLETION.json').exists();files=read(ROOT/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items())
 from reservation import admission
 admission();now=time.time();mono=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();auth=read(ROOT/'AUTHORIZATION.json');assert auth['absolute_end_unix']-now>1000
 put(O/'OWNER_ONCE.json',dict(unix=now,pid=os.getpid(),models=0,scope='IDEAL_MATH_ONLY_NO_PLANT_LOCK_OR_CURRENT_MUTATION'))
 put(O/'NUMERICAL_ADMISSION.json',dict(scope='FINITE_IDEAL_PCBF_COORDINATE_TRANSFORM_ONLY',numerical_authorized=True,models_authorized=False,worker_sha256=sha(C/'worker.py'),source_freeze_sha256=sha(ROOT/'SOURCE_FREEZE.json'),absolute_end_unix=now+600,hard_stop_monotonic=mono+600,boot_id=boot))
 os.environ.setdefault('PHASE_FILTER_METHOD','PSF');ns=load('original_readonly_Phase_mounts',R/'experiments/v2151_psf_wrapper_identity_binding/run_phase.py');argv=ns.namespace(C/'worker.py',O)
 v=dict(closed=False,passed=False,models=0,physics=0,replay=0,actual=0,formal_tasks=0,NLP_returns=None,internal_optimizer_work=None);p=None;i=None
 try:
  with(O/'worker.console').open('xb')as log:
   p=subprocess.Popen(['taskset','-c','3','nice','-n','19','ionice','-c','3',*argv],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=boot,CPU=3,scope='PURE_IDEAL_NLP_NO_MODEL');put(O/'OWNED_CHILD.json',i)
   while p.poll()is None:
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<now+610 and time.monotonic()<mono+610 and (O/'worker.console').stat().st_size<256*1024 and not(ROOT/'STOP').exists();time.sleep(.2)
   m=read(O/'RESULT.json');v.update(passed=bool(p.returncode==0 and m['passed']),machine_result_sha256=sha(O/'RESULT.json'),NLP_returns=m['NLP_returns'],attempted_calls=m['attempted_calls'],inflight_unknown=m['inflight_unknown'],machine_first_error=m.get('first_error'),all_source_SHA_after=all(sha(R/n)==h for n,h in files.items()),case_summaries=m['cases'])
 except BaseException as e:v.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if p is not None and p.poll()is None:
   assert Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]==i['start_ticks'];os.killpg(i['pgid'],signal.SIGTERM)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=5)
  v.update(closed=True,returncode=None if p is None else p.returncode,wall_s=time.monotonic()-mono);put(O/'COMPLETION.json',v)
 # Completed/non-success raw is recovered regardless of scientific result.
 for args in [['archive','MATH'],['ref','MATH'],['deliver','MATH']]:
  with(ROOT/('IO_'+args[0]+'.console')).open('xb')as log:
   r=subprocess.run(['taskset','-c','5','nice','-n','19','/usr/bin/python3','-B',str(C/'evidence.py'),*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=625)
  assert r.returncode==0,args
 d=ROOT/'runtime_archives/MATH';assert read(d/'FULL_REMOTE_VERIFIED.json')['passed']and read(d/'TRANSPORT_CLEANUP.json')['passed'];put(O/'POST_MATH_STORAGE_BARRIER.json',dict(passed=True,scientific_navigation_passed=None,case_pipeline_passed=v['passed'],runtime_proof_sha256=sha(d/'FULL_REMOTE_VERIFIED.json'),models=0));put(ROOT/'OWNER_CLOSED.json',dict(closed=True,pipeline_passed=v['passed'],math_result_path=str((O/'RESULT.json').relative_to(R)),actual=0,formal_tasks=0));print(json.dumps(v))
if __name__=='__main__':main()
