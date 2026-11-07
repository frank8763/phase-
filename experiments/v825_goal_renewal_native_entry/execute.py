"""The sole pre-model metadata entry continuation, same original deadline."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/goal_renewal_20261105'
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
with(root/'launch.lock').open('a+')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(root/'V825_LAUNCH.json').exists()and not(repo/'runs/v825_goal_renewal_native_entry').exists(),'NO_SECOND_ENTRY_RETRY'
 assert read(root/'V825_PREPARATION.json')['status']=='FIXED_OLD_CONTROLLER_INTERFACE_ZERO_MODEL_PASS'
 assert read(root/'V824_ZERO_MODEL_ERROR_DIAGNOSIS.json')['status']=='OUTER_STEP_ONLY_ZERO_MODEL_MISMATCH_PROVEN'
 assert read(repo/'runs/v824_goal_renewal_qualification/COMPLETION.json')['counts']['old_replay_native']==0
 original=read(root/'V824_LAUNCH.json');started=original['started_unix'];deadline=original['absolute_deadline_unix'];assert deadline-time.time()>600,'NO_TIME_FOR_SAME_WINDOW_CONTINUATION'
 with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as check:fcntl.flock(check,fcntl.LOCK_EX|fcntl.LOCK_NB)
 guard=repo/'REVIEW_PENDING';backup=guard.read_bytes();(root/'V825_REVIEW_PENDING.before').write_bytes(backup)
 dump(root/'V825_LAUNCH.json',dict(started_unix=started,absolute_deadline_unix=deadline,pid=os.getpid(),same_original_component_window=True))
 ledger=read(root/'LEDGER.json');ledger.update(status='V825_SAME_WINDOW_COMPONENT_RUNNING',active_simulation=True,master_pid=os.getpid(),metadata_entry_exception=1,old_v824_failed=True);dump(root/'LEDGER.json',ledger)
 env=dict(os.environ,PHASE_RENEWAL_STARTED=str(started),PHASE_RENEWAL_DEADLINE=str(deadline),PHASE_PROPOSAL_MODEL=str(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 code=None;child=None;error=None
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(TimeoutError('OUTER_TERMINATED')))
 try:
  guard.unlink()
  with(root/'v825_probe.console').open('x')as stream:
   child=subprocess.Popen([str(repo/'run_phase.sh'),str(own/'probe.py')],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
   try:code=child.wait(timeout=max(.1,deadline-time.time()))
   finally:
    if child.poll()is None:
     os.killpg(child.pid,signal.SIGTERM)
     try:child.wait(timeout=2)
     except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 except BaseException as e:error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
 finally:
  guard.write_bytes(backup);ledger=read(root/'LEDGER.json');ledger.update(status='V825_CLOSED_NEEDS_ZERO_MODEL_AUDIT',active_simulation=False,master_pid=None,qualification_exit=code,guard_restored=guard.read_bytes()==backup)
  if error:ledger['driver_error']=error
  dump(root/'LEDGER.json',ledger);dump(root/'V825_DRIVER_COMPLETION.json',dict(child_exit=code,error=error,guard_restored=guard.read_bytes()==backup,no_navigation_started=True))
 if code==0:
  with(root/'v825_saved_audit.console').open('x')as stream:p=subprocess.run([sys.executable,'-B',str(own/'audit_saved.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=240)
  ledger=read(root/'LEDGER.json');ledger.update(saved_audit_exit=p.returncode,status='V825_AUDIT_COMPLETE_NEEDS_ARCHIVE'if p.returncode==0 else'V825_SAVED_AUDIT_FAILED');dump(root/'LEDGER.json',ledger)
 print(json.dumps(read(root/'LEDGER.json')),flush=True)
