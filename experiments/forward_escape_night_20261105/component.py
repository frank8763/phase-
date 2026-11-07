"""One fixed native component followed by zero-model audit/archive, no retries."""
import fcntl,os,signal,subprocess,sys,time,traceback
from pathlib import Path
from evidence_rules import dump,read,sha
def run_component(repo,root):
 own=repo/'experiments/v831_forward_escape_qualification';stage=repo/'runs/v831_forward_escape_qualification';auth=read(repo/'RPCCR_FORWARD_ESCAPE_NIGHT_AUTHORIZATION_20261105.json');started=time.time();deadline=min(started+1200,auth['absolute_deadline_unix'])
 assert deadline-started>=1199 and not stage.exists()and not(root/'COMPONENT_LAUNCH.json').exists(),'NO_COMPONENT_START_BUDGET_OR_ALREADY_STARTED'
 assert sha(own/'INPUT_FREEZE.json')==read(root/'PREPARED.json')['source_freezes'][own.name],'COMPONENT_FREEZE_CHANGED'
 with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
 guard=(repo/'REVIEW_PENDING').read_bytes();(root/'COMPONENT_REVIEW_PENDING.before').write_bytes(guard);dump(root/'COMPONENT_LAUNCH.json',dict(started_unix=started,absolute_deadline_unix=deadline,launch_attempts=1,new_global_navigation=0))
 env=dict(os.environ,PHASE_ESCAPE_STARTED=str(started),PHASE_ESCAPE_DEADLINE=str(deadline),PHASE_PROPOSAL_MODEL=str(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');process=None;code=None;error=None
 try:
  (repo/'REVIEW_PENDING').unlink()
  with(root/'component.console').open('x')as stream:
   process=subprocess.Popen([str(repo/'run_phase.sh'),str(own/'probe.py')],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
   dump(root/'ACTIVE.json',dict(stage=own.name,pid=process.pid,absolute_deadline_unix=deadline))
   try:code=process.wait(timeout=max(.01,deadline-time.time()))
   finally:
    if process.poll()is None:
     os.killpg(process.pid,signal.SIGTERM)
     try:process.wait(timeout=2)
     except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
 except BaseException as e:error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
 finally:
  (repo/'REVIEW_PENDING').write_bytes(guard);dump(root/'COMPONENT_DRIVER_COMPLETION.json',dict(exit_code=code,error=error,guard_original_bytes_restored=True,model_restarted=False))
 assert stage.exists()and(stage/'ROUND_WINDOW.json').exists(),'COMPONENT_NO_SCIENTIFIC_OUTPUT_PRESERVE_ENTRY_FAILURE'
 assert read(stage/'ROUND_WINDOW.json')['round_closed'],'COMPONENT_DID_NOT_CLOSE'
 with(stage/'finalize.console').open('x')as stream:p=subprocess.run([sys.executable,'-B',str(own/'finalize.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=1200)
 assert p.returncode==0 and(stage/'FINALIZED.json').exists(),'COMPONENT_FINALIZER_FAILED'
 final=read(stage/'FINALIZED.json');assert final['source_and_decompressed_sha_verified']
 return final
