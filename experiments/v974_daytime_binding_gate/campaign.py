"""One bounded daytime navigation and closure; never starts another gate."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v974_daytime_binding_gate'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import root_authorized,digest,read
from handshake import verify_sources
def dump(p,d):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');t.replace(p)
def main():
 lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);a=root_authorized();assert not(O/'CAMPAIGN_CLAIM.json').exists()
 dump(O/'CAMPAIGN_CLAIM.json',dict(pid=os.getpid(),at=time.time(),deadline_unix=a['deadline_unix']));guard=(R/'REVIEW_PENDING').read_bytes();(O/'REVIEW_PENDING.before').write_bytes(guard)
 task=read(C/'TASKS.json')[0];tp=O/'TASK.json';ap=O/'TASK_AUTHORIZATION.json';dump(tp,task);dump(ap,dict(a,run_id=task['run_id'],task_sha256=digest(task)))
 current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='V974_SINGLE_ROUTE_RUNNING',active_run=str(O.relative_to(R)),active_entrypoint=str(C.relative_to(R)/'campaign.py'),active_window=a,execution_window_closed=False);dump(R/'CURRENT_EXPERIMENT.json',current)
 child=None;error=None;status='NOT_PASSED';signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('DAYTIME_STOP')))
 try:
  verify_sources(R,C/'SOURCE_FREEZE.json');dump(O/'ACTIVE.json',dict(stage='one_original_WE_dynamic',at=time.time(),deadline_unix=a['deadline_unix']))
  with(O/'main.console').open('x')as f:
   child=subprocess.Popen([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],cwd=R,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'WORKER.json',dict(pid=child.pid));rc=child.wait(timeout=min(290,a['deadline_unix']-time.time()-20));child=None
  assert rc==0,'SINGLE_ROUTE_FUNCTION_SAFETY_OR_EVIDENCE_FAILURE'
  assert read(Path(task['output'])/'INDEPENDENT_AUDIT.json')['passed'];status='ONE_DYNAMIC_ROUTE_PASSED'
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  if child is not None and child.poll()is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
  (R/'REVIEW_PENDING').write_bytes(guard);(O/'AUTHORIZATION.before_close.json').write_bytes((O/'AUTHORIZATION.json').read_bytes());dump(O/'AUTHORIZATION.json',dict(a,models_authorized=False,closed_unix=time.time()))
  out=Path(task['output']);n=read(out/'RESULT.json')if(out/'RESULT.json').exists()else{};audit=read(out/'INDEPENDENT_AUDIT.json')if(out/'INDEPENDENT_AUDIT.json').exists()else{}
  d=dict(closed=True,status=status,error=error,task_id=task['task_id'],actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),goal_m=n.get('goal_distance_m'),independent_passed=audit.get('passed'),models_authorized=False,deadline_unix=a['deadline_unix'],closed_unix=time.time(),guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,automatic_followup=False)
  dump(O/'COMPLETION.json',d);current.update(status='REVIEW_PENDING',active_run=None,active_entrypoint=None,active_window=None,execution_window_closed=True,next_physical_authorized=False,v974_single_route=d);dump(R/'CURRENT_EXPERIMENT.json',current)
  with(O/'close.console').open('x')as f:
   try:subprocess.run([sys.executable,'-B',str(R/'experiments/v975_daytime_closure/close.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=480,check=True)
   except BaseException as e:dump(O/'CLOSE_ERROR.json',dict(error=repr(e),models=0))
 return 0 if status=='ONE_DYNAMIC_ROUTE_PASSED'else 1
if __name__=='__main__':sys.exit(main())
