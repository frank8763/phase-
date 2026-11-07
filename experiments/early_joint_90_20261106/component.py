"""Exactly one saved native qualification, then immutable audit/archive."""
import fcntl,os,signal,subprocess,sys,time,traceback
from evidence_rules import dump,read,sha

def run_component(repo,root,deadline):
 own=repo/'experiments/v841_early_joint';stage=repo/'runs/v841_early_joint/qualification';started=time.time();cap=min(started+600,deadline)
 assert cap-started>=599 and not stage.exists()and not(root/'COMPONENT_LAUNCH.json').exists()
 assert sha(own/'INPUT_FREEZE.json')==read(root/'PREPARED.json')['qualification_freeze']
 guard=(repo/'REVIEW_PENDING').read_bytes();dump(root/'COMPONENT_LAUNCH.json',dict(started_unix=started,absolute_deadline_unix=cap,attempts=1));code=None;error=None;process=None
 env=dict(os.environ,PHASE_ESCAPE_STARTED=str(started),PHASE_ESCAPE_DEADLINE=str(cap),PHASE_MODEL_ABSOLUTE_DEADLINE=str(cap),PHASE_PRIVATE_NATIVE_CAP='200000',PHASE_SAVE_ALL_REFERENCE_CANDIDATES='1',PHASE_PROPOSAL_MODEL=str(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
 try:
  (repo/'REVIEW_PENDING').unlink()
  with(root/'component.console').open('x')as stream:
   process=subprocess.Popen([str(repo/'run_phase.sh'),str(own/'qualify_probe.py')],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
   dump(root/'ACTIVE.json',dict(stage='saved295',pid=process.pid,absolute_deadline_unix=cap))
   try:code=process.wait(timeout=max(.01,cap-time.time()))
   finally:
    if process.poll()is None:
     os.killpg(process.pid,signal.SIGTERM)
     try:process.wait(timeout=2)
     except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
 except BaseException as e:error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
 finally:
  (repo/'REVIEW_PENDING').write_bytes(guard);dump(root/'COMPONENT_DRIVER_COMPLETION.json',dict(exit_code=code,error=error,guard_original_bytes_restored=True,model_restarted=False))
 assert(stage/'COMPLETION.json').exists()and read(stage/'ROUND_WINDOW.json')['round_closed'],'COMPONENT_ENTRY_OR_CLOSE_FAILURE_NO_RETRY'
 with(stage/'finalize.console').open('x')as stream:p=subprocess.run([sys.executable,'-B',str(own/'qualify_finalize.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=1200)
 assert p.returncode==0 and(stage/'FINALIZED.json').exists(),'COMPONENT_FINALIZER_FAILED'
 final=read(stage/'FINALIZED.json');assert final['source_and_decompressed_sha_verified'];return final
