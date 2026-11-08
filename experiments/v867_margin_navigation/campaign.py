"""One finite90min campaign: six static runs gate six dynamic runs, first failure stops."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v867_margin_navigation';sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from handshake import file_sha,verify_sources,require
from authority import authorized,digest
from audit import repeat_check

def dump(p,d):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');t.replace(p)
def stop(p):
 if p and p.poll()is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=6.)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def main():
 receipt=json.loads((O/'AUTHORIZATION.json').read_text());tasks=json.loads((C/'TASKS.json').read_text());freeze=file_sha(C/'SOURCE_FREEZE.json');require(receipt['models_authorized']is True and receipt['source_freeze_sha256']==freeze,'CAMPAIGN_NOT_AUTHORIZED');deadline=receipt['deadline_unix'];require(abs(deadline-receipt['started_unix']-5400)<1e-6,'90MIN_CHANGED');verify_sources(R,C/'SOURCE_FREEZE.json')
 lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(O/'CLAIM.json').open('x')as f:json.dump(dict(started_unix=time.time(),deadline_unix=deadline,source_freeze_sha256=freeze),f)
 guard=(R/'REVIEW_PENDING').read_bytes();require(hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66','GUARD_CHANGED')
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(KeyboardInterrupt('CAMPAIGN_TERMINATED')))
 rows=[];preflights=[];comparisons={};child=None;status='RUNNING';error=None
 def launch(task,preflight=False):
  nonlocal child
  require(deadline-time.time()>=300,'INSUFFICIENT_REMAINING_TIME');verify_sources(R,C/'SOURCE_FREEZE.json');require((R/'REVIEW_PENDING').read_bytes()==guard,'GUARD_NOT_RESTORED')
  require(sum(p.stat().st_size for base in [O,R/'runs/v858_nav2_verified/v867']if base.exists()for p in base.rglob('*')if p.is_file())<1200*1024**2,'TEMPORARY_EVIDENCE_LIMIT')
  auth=dict(receipt,run_id=task['run_id'],task_sha256=digest(task));authorized(task,auth,time.time(),freeze);prefix=('t0_'if preflight else'nav_')+task['task_id'];tp=O/(prefix+'.task.json');ap=O/(prefix+'.authorization.json');dump(tp,task);dump(ap,auth);dump(O/'ACTIVE.json',dict(kind='PREFLIGHT'if preflight else'NAVIGATION',task=task,started_unix=time.time()))
  if preflight:
   row=dict(task_id=task['task_id'],dynamic=task['dynamic'],attempted=True,initialization_attempted=None,native_integrations=0);preflights.append(row);dump(O/'PREFLIGHTS.json',preflights)
   try:
    (R/'REVIEW_PENDING').unlink()
    with(O/(prefix+'.console')).open('w')as f:
     child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'preflight.py').relative_to(R)),str(tp),str(ap)],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);child.wait(timeout=min(80.,deadline-3-time.time()))
   finally:stop(child);(R/'REVIEW_PENDING').write_bytes(guard)
   rp=R/'runs/v858_nav2_verified/v867/preflights'/task['task_id']/'RESULT.json';result=json.loads(rp.read_text())if rp.exists()else{};row.update(returncode=child.returncode,result=result,passed=child.returncode==0 and result.get('passed')is True,initialization_attempted=result.get('environment_initialization_attempted'),initialization_completed=result.get('environment_initialization_completed'));dump(O/'PREFLIGHTS.json',preflights);require(row['passed'],'FIRST_T0_FAILURE')
  else:
   row=dict(task_id=task['task_id'],run_id=task['run_id'],stage=task['stage'],case_id=task['case_id'],output=task['output'],attempted=True,started_unix=time.time());rows.append(row);dump(O/'RESULTS.json',rows)
   with(O/(prefix+'.console')).open('w')as f:
    child=subprocess.Popen([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);child.wait(timeout=min(250.,deadline-3-time.time()));row['returncode']=child.returncode
   p=Path(task['output']);result=json.loads((p/'RESULT.json').read_text())if(p/'RESULT.json').exists()else{};audit=json.loads((p/'INDEPENDENT_AUDIT.json').read_text())if(p/'INDEPENDENT_AUDIT.json').exists()else{}
   row.update(closed_unix=time.time(),passed=child.returncode==0 and audit.get('passed')is True,actual_native=result.get('actual_native'),replay_native=result.get('replay_native'),mujoco_private_native=result.get('private_native'),goal_distance_m=result.get('goal_distance_m'),minimum_clearance_m=result.get('minimum_actual_clearance_m'),bad_contacts=result.get('bad_contacts'),first_actor_detection=result.get('first_actor_detection'),postdiscovery_travel_m=audit.get('independently_recomputed_postdiscovery_travel_m'),model_initialization_attempted=result.get('environment_initialization_attempted'),model_initialization_completed=result.get('environment_initialization_completed'));dump(O/'RESULTS.json',rows);require(row['passed'],'FIRST_NAVIGATION_FUNCTIONAL_OR_EVIDENCE_FAILURE')
   if task['stage'].endswith('repeat'):
    main=next(t for t in tasks if t['stage']==task['stage'].replace('repeat','main')and t['case_id']==task['case_id']);comparison=repeat_check(main['output'],p);comparisons[task['task_id']]=comparison;dump(O/'REPEATS.json',comparisons);require(comparison['passed'],'REPEAT_INITIAL_MODEL_OR_FUNCTIONAL_FAILURE')
  verify_sources(R,C/'SOURCE_FREEZE.json')
 try:
  for dynamic in [False,True]:
   mains=[t for t in tasks if t['dynamic']==dynamic and t['stage'].endswith('main')]
   for task in mains:launch(task,True)
   for task in [t for t in tasks if t['dynamic']==dynamic]:launch(task)
   if not dynamic:dump(O/'STATIC_GATE.json',dict(passed=True,static_navigation=6,static_t0=3,full_navigation_repeats=3,own_control_replay_max_error_limit=1e-8,source_freeze_sha256=freeze,at=time.time()))
  status='THREE_STATIC_AND_THREE_DYNAMIC_DEVELOPMENT_WITH_FULL_RERUNS_PASSED'
 except BaseException as e:status='STOPPED_FIRST_FAILURE_OR_DEADLINE';error=dict(error=repr(e),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
 finally:
  stop(child);(R/'REVIEW_PENDING').write_bytes(guard)
  summary=dict(status=status,passed=status=='THREE_STATIC_AND_THREE_DYNAMIC_DEVELOPMENT_WITH_FULL_RERUNS_PASSED',closed=True,error=error,attempted_navigation=len(rows),unexecuted_navigation=len(tasks)-len(rows),rows=rows,preflights=preflights,repeats=sorted(comparisons),actual_native=sum(x['actual_native']for x in rows)if all(x.get('actual_native')is not None for x in rows)else None,replay_native=sum(x['replay_native']for x in rows)if all(x.get('replay_native')is not None for x in rows)else None,dynamic_navigation=len([x for x in rows if x['stage'].startswith('dynamic')]),static_navigation=len([x for x in rows if x['stage'].startswith('static')]),new24=0,training=0,real_robot=0,guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,root_deadline_unix=deadline,closed_unix=time.time());dump(O/'COMPLETION.json',summary)
  window=json.loads((O/'ROUND_WINDOW.json').read_text());window.update(closed=True,status=status,closed_unix=time.time());dump(O/'ROUND_WINDOW.json',window)
  state=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());state.update(status='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_window=None,execution_window_closed=True);state['v867_margin_navigation'].update(status=status,closed=True,models_authorized=False,actual_native=summary['actual_native'],replay_native=summary['replay_native']);dump(R/'CURRENT_EXPERIMENT.json',state)
  try:
   with(O/'finalize.console').open('w')as f:result=subprocess.run([sys.executable,'-B',str(C/'finalize_local.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180);dump(O/'FINALIZE_PROCESS.json',dict(returncode=result.returncode,model_integrations=0))
  except BaseException as e:dump(O/'FINALIZE_ERROR.json',dict(error=repr(e),model_integrations=0))
  print(json.dumps(summary),flush=True)
 return 0 if summary['passed']else 1
if __name__=='__main__':sys.exit(main())
