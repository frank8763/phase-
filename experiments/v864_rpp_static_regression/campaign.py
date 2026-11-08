"""Five sequential fixed static runs; first failure stops, all physical work inherits the root deadline."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v864_rpp_static_regression';sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from handshake import file_sha,verify_sources,require
from authority import authorized,digest,DEADLINE
from audit import repeat_check
def dump(p,d):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');t.replace(p)
def main():
 receipt=json.loads((O/'AUTHORIZATION.json').read_text());tasks=json.loads((C/'TASKS.json').read_text());freeze=file_sha(C/'SOURCE_FREEZE.json');require(receipt['models_authorized']is True and receipt['source_freeze_sha256']==freeze,'CAMPAIGN_NOT_AUTHORIZED');require(receipt['deadline_unix']==DEADLINE,'DEADLINE_CHANGED');verify_sources(R,C/'SOURCE_FREEZE.json')
 lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(O/'CLAIM.json').open('x')as f:json.dump(dict(started_unix=time.time(),deadline_unix=DEADLINE,source_freeze_sha256=freeze),f)
 guard=(R/'REVIEW_PENDING').read_bytes();require(hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66','GUARD_CHANGED')
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(KeyboardInterrupt('CAMPAIGN_TERMINATED')))
 rows=[];comparisons={};child=None;status='RUNNING';error=None
 try:
  for slot,task in enumerate(tasks,1):
   require(time.time()<DEADLINE-300,'INSUFFICIENT_REMAINING_TIME');verify_sources(R,C/'SOURCE_FREEZE.json');require((R/'REVIEW_PENDING').read_bytes()==guard,'GUARD_NOT_RESTORED')
   # This batch stores at most five ~180s traces, below the user's2GiB temporary budget.
   require(sum(p.stat().st_size for base in [O,R/'runs/v858_nav2_verified/v864_static']if base.exists()for p in base.rglob('*')if p.is_file())<1024**3,'TEMPORARY_EVIDENCE_LIMIT')
   auth=dict(receipt,run_id=task['run_id'],task_sha256=digest(task));authorized(task,auth,time.time(),freeze)
   tp=O/f'{slot:02d}.task.json';ap=O/f'{slot:02d}.authorization.json';dump(tp,task);dump(ap,auth);dump(O/'ACTIVE.json',dict(slot=slot,task=task,started_unix=time.time()))
   row=dict(slot=slot,run_id=task['run_id'],case_id=task['case_id'],output=task['output'],attempted=True,started_unix=time.time());rows.append(row);dump(O/'RESULTS.json',rows)
   with(O/f'{slot:02d}.console').open('w')as f:
    child=subprocess.Popen([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
    child.wait(timeout=max(.01,min(250.,DEADLINE-3-time.time())));row['returncode']=child.returncode
   p=Path(task['output']);result=json.loads((p/'RESULT.json').read_text())if(p/'RESULT.json').exists()else{};audit=json.loads((p/'INDEPENDENT_AUDIT.json').read_text())if(p/'INDEPENDENT_AUDIT.json').exists()else{}
   row.update(closed_unix=time.time(),passed=child.returncode==0 and audit.get('passed')is True,actual_native=result.get('actual_native'),replay_native=result.get('replay_native'),private_mujoco_native=result.get('private_native'),goal_distance_m=result.get('goal_distance_m'),minimum_clearance_m=result.get('minimum_actual_clearance_m'),model_initialization_attempted=result.get('environment_initialization_attempted'),model_initialization_completed=result.get('environment_initialization_completed'))
   dump(O/'RESULTS.json',rows);require(row['passed'],'FIRST_STATIC_FUNCTIONAL_OR_EVIDENCE_FAILURE')
   if slot>=3:
    baselines={3:R/'runs/v858_nav2_verified/v863_rpp_static',4:Path(tasks[0]['output']),5:Path(tasks[1]['output'])};comparison=repeat_check(baselines[slot],p);comparisons[task['case_id']]=comparison;dump(O/'REPEATS.json',comparisons);require(comparison['passed'],'REPEAT_INITIAL_MODEL_OR_FUNCTIONAL_FAILURE')
   verify_sources(R,C/'SOURCE_FREEZE.json')
  status='THREE_STATIC_ROUTES_AND_FULL_RERUNS_PASSED'
 except BaseException as e:status='STOPPED_FIRST_FAILURE_OR_DEADLINE';error=dict(error=repr(e),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
 finally:
  if child and child.poll()is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=6.)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
  (R/'REVIEW_PENDING').write_bytes(guard)
  summary=dict(status=status,passed=status=='THREE_STATIC_ROUTES_AND_FULL_RERUNS_PASSED',closed=True,error=error,completed_items=len([x for x in rows if x.get('closed_unix')]),attempted_items=len(rows),unexecuted_items=len(tasks)-len(rows),rows=rows,repeats=sorted(comparisons),actual_native=sum(x['actual_native']for x in rows)if all(x.get('actual_native')is not None for x in rows)else None,replay_native=sum(x['replay_native']for x in rows)if all(x.get('replay_native')is not None for x in rows)else None,old_v863_actual_native=4569,old_v863_replay_native=4569,dynamic_navigation=0,new24=0,training=0,real_robot=0,guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,root_deadline_unix=DEADLINE,closed_unix=time.time())
  dump(O/'COMPLETION.json',summary);window=json.loads((O/'ROUND_WINDOW.json').read_text());window.update(closed=True,status=status,closed_unix=time.time());dump(O/'ROUND_WINDOW.json',window)
  state=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());state.update(status='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_window=None,execution_window_closed=True);state['v864_rpp_static_regression'].update(status=status,closed=True,models_authorized=False,actual_native=summary['actual_native'],replay_native=summary['replay_native']);dump(R/'CURRENT_EXPERIMENT.json',state)
  print(json.dumps(summary),flush=True)
 return 0 if summary['passed']else 1
if __name__=='__main__':sys.exit(main())
