"""One bounded isolated physical qualification, with exact review-guard restore."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/goal_renewal_20261105'
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
with(root/'launch.lock').open('a+')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(root/'V824_LAUNCH.json').exists()and not(repo/'runs/v824_goal_renewal_qualification').exists(),'ALREADY_STARTED_NO_RETRY'
 assert read(root/'V824_PREPARATION.json')['status']=='FIXED_OLD_CONTROLLER_INTERFACE_ZERO_MODEL_PASS'
 auth=read(repo/'RPCCR_GOAL_RENEWAL_AUTHORIZATION_20261105.json');started=time.time();deadline=min(started+1200,auth['absolute_deadline_unix']);assert deadline-started>1100
 with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as check:fcntl.flock(check,fcntl.LOCK_EX|fcntl.LOCK_NB)
 guard=repo/'REVIEW_PENDING';backup=guard.read_bytes();(root/'V824_REVIEW_PENDING.before').write_bytes(backup)
 launch=dict(started_unix=started,absolute_deadline_unix=deadline,root_deadline_unix=auth['absolute_deadline_unix'],pid=os.getpid(),started_once=True)
 dump(root/'V824_LAUNCH.json',launch);ledger=read(root/'LEDGER.json');ledger.update(status='V824_NATIVE_COMPONENT_RUNNING',qualification_started=True,candidates_started=1,master_pid=os.getpid(),active_simulation=True);dump(root/'LEDGER.json',ledger)
 env=dict(os.environ,PHASE_RENEWAL_STARTED=str(started),PHASE_RENEWAL_DEADLINE=str(deadline),PHASE_PROPOSAL_MODEL=str(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 child=None;code=None;error=None
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(TimeoutError('OUTER_TERMINATED')))
 try:
  guard.unlink()
  with(root/'v824_probe.console').open('x')as stream:
   child=subprocess.Popen([str(repo/'run_phase.sh'),str(own/'probe.py')],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
   try:code=child.wait(timeout=max(.1,deadline-time.time()))
   finally:
    if child.poll()is None:
     os.killpg(child.pid,signal.SIGTERM)
     try:child.wait(timeout=2)
     except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 except BaseException as e:error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
 finally:
  guard.write_bytes(backup);ledger=read(root/'LEDGER.json');ledger.update(status='V824_CLOSED_NEEDS_ZERO_MODEL_AUDIT',active_simulation=False,master_pid=None,qualification_exit=code,guard_restored=guard.read_bytes()==backup)
  if error:ledger['driver_error']=error
  dump(root/'LEDGER.json',ledger);dump(root/'V824_DRIVER_COMPLETION.json',dict(child_exit=code,error=error,guard_restored=guard.read_bytes()==backup,no_navigation_started=True))
 if code==0:
  with(root/'v824_saved_audit.console').open('x')as stream:
   p=subprocess.run([sys.executable,'-B',str(own/'audit_saved.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=240)
  ledger=read(root/'LEDGER.json');ledger.update(saved_audit_exit=p.returncode,status='V824_AUDIT_COMPLETE_NEEDS_ARCHIVE'if p.returncode==0 else'V824_SAVED_AUDIT_FAILED');dump(root/'LEDGER.json',ledger)
 print(json.dumps(read(root/'LEDGER.json')),flush=True)
