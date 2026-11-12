"""One fixed revision, three real t0s, route mains and successful repeats."""
import sys,signal,subprocess,fcntl,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from resource_policy import apply
RESOURCE=apply()
from kernel import *
from audit import audit_native,compare
from budget import used,LIMIT
FUNCTIONAL=('FINITE_INFORMATION_CORRIDOR_LIMIT','STATIC_RENEWAL_LIMIT','NO_STATIC_RECOVERY_SOURCE','NO_NOMINAL_BRAKE_COMPATIBLE_STATIC_PREFIX','REAL_SENSOR_DISCOVERY_REQUIRED','FIRST_DISCOVERY_NOT_NORMAL_DRIVING','FIRST_DISCOVERY_DURING_STATIC_STOP','FIXED_EPOCH_LIMIT','FULL_OWN_REPLAY_RESERVE','EXECUTION_OR_REPLAY_RESERVE')
def main():
 with(O/'DRIVER_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),at=time.time()),f)
 own=(O/'driver.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(O/'GUARD.bin').read_bytes();tasks=json.loads((C/'TASKS.json').read_text());attempts=[];rows=[];preflights={};repeats=[];child=None;error=None;passed=False
 def terminate():
  nonlocal child
  if child is not None and child.poll()is None:
   try:os.killpg(child.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   try:child.wait(5)
   except subprocess.TimeoutExpired:
    try:os.killpg(child.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    child.wait(5)
  child=None
 def run(task):
  nonlocal child
  assert remaining_root()>(300 if task['kind']=='t0'else 1050),'INSUFFICIENT_ROOT_RESERVE';assert used()<LIMIT-400*1024**2,'TEMPORARY8GIB_STORAGE_STOP';receipt=dict(task_id=task['task_id'],task_sha256=sha(C/('TASK_'+task['task_id']+'.json')),source_sha256=sha(C/'SOURCE_FREEZE.json'),window_sha256=sha(O/'ROUND_WINDOW.json'),branch_id='A',task_deadline_unix=min(HARD_END-30,time.time()+(100 if task['kind']=='t0'else 900)));rp=O/(task['task_id']+'.AUTHORITY.json');dump(rp,receipt);attempts.append(task);dump(O/'ATTEMPTS.json',attempts);entry='t0_worker.py'if task['kind']=='t0'else'worker.py';assert(R/'REVIEW_PENDING').read_bytes()==guard;(R/'REVIEW_PENDING').unlink()
  try:
   with(O/(task['task_id']+'.console')).open('x')as log:
    child=subprocess.Popen([str(R/'run_phase.sh'),str((C/entry).relative_to(R)),str(C/('TASK_'+task['task_id']+'.json')),str(rp)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);start=Path('/proc',str(child.pid),'stat').read_text().rsplit(')',1)[1].split()[19];dump(O/'ACTIVE.json',dict(kind='physics',pid=child.pid,pid_start=start,task_id=task['task_id'],deadline=receipt['task_deadline_unix'],resource_policy=RESOURCE));code=child.wait(timeout=max(.001,min(receipt['task_deadline_unix']-time.time()+10,remaining_root()-15)))
  finally:terminate();(R/'REVIEW_PENDING').write_bytes(guard)
  path=Path(task['output'])/'RESULT.json'
  if not path.exists():
   fallback=Path(task['output'])/'physics/paired/ENTRY_FAILURE_RESULT.json';assert fallback.exists(),'DRIVER_CHILD_RESULT_MISSING';result=json.loads(fallback.read_text());assert not result['passed'];dump(path,result)
  result=json.loads(path.read_text())
  if task['kind']=='t0':preflights[task['task_id']]=result;dump(O/'PREFLIGHTS.json',preflights);assert code==0 and result['passed'],'PREFLIGHT_CONTRACT_FAILURE';return result
  proof=audit_native(task);row=dict(task=task,result=result,audit=proof,passed=bool(code==0 and result['passed']and proof['passed']));rows.append(row);dump(O/'RESULTS.json',rows);assert proof['safety_passed']and proof['prediction']['passed'],'SAFETY_STATE_CONTROL_OR_EVIDENCE_FAILURE'
  if not row['passed']:
   functional=any(x in result.get('error','')for x in FUNCTIONAL)
   if 'SOURCE_PRODUCER_FAILED'in result.get('error',''):
    files=sorted((Path(task['output'])/'refresh').glob('epoch*/RESULT.json'));failure=json.loads(files[-1].read_text())if files else{};functional=failure.get('error')=="AssertionError('NO_FULL_CYCLE_INFORMATION_CORRIDOR')"
   assert functional,'UNCLASSIFIED_OR_SOURCE_FAILURE'
  dump(O/'ACTIVE.json',dict(kind='between_tasks',last_task=task['task_id'],last_passed=row['passed'],models_authorized=True));return row
 def stop(*_):raise InterruptedError('ABSOLUTE_OR_EXTERNAL_STOP')
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining_root()-15))
 try:
  for task in tasks:
   if task['kind']=='t0':run(task)
  for case in ['NORTH_SOUTH','EAST_WEST','WEST_EAST']:
   task=next(t for t in tasks if t['case_id']==case and t['kind']=='main');row=run(task)
   if row['passed']:
    repeat=next(t for t in tasks if t['case_id']==case and t['kind']=='repeat');rep=run(repeat)
    if rep['passed']:comparison=compare(task,repeat);repeats.append(comparison);assert comparison['passed'],'FULL_REPEAT_MISMATCH'
  passed=len(rows)==6 and all(x['passed']for x in rows)and len(repeats)==3 and all(x['passed']for x in repeats)
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  terminate();signal.setitimer(signal.ITIMER_REAL,0);(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True,allowed_task_ids=[]));counts={k:0 for k in ['model_initializations','historical_replay_native','navigation_native','own_replay_native','private_mujoco_native']};unknown=[]
  for task in attempts:
   p=Path(task['output'])/'RESULT.json';result=json.loads(p.read_text())if p.exists()else{}
   for key in counts:
    value=result.get(key)
    if value is None:counts[key]=None;unknown.append(dict(task_id=task['task_id'],field=key))
    elif counts[key]is not None:counts[key]+=value
  returned=[(t,json.loads((Path(t['output'])/'RESULT.json').read_text())if(Path(t['output'])/'RESULT.json').exists()else{})for t in attempts]
  done=dict(main_attempted=sum(t['kind']=='main'for t in attempts),repeat_attempted=sum(t['kind']=='repeat'for t in attempts),main_navigation_known_started=sum(t['kind']=='main'and isinstance(r.get('navigation_native'),int)and r['navigation_native']>0 for t,r in returned),main_navigation_unknown=sum(t['kind']=='main'and r.get('navigation_native')is None for t,r in returned),closed=True,deadline_unix=HARD_END,closed_at=time.time(),combined_three_route_development_passed=passed,confirmation24_authorized=False,confirmation24_executed=False,main_executed=sum(x['task']['kind']=='main'for x in rows),main_successes=sum(x['task']['kind']=='main'and x['passed']for x in rows),repeat_executed=sum(x['task']['kind']=='repeat'for x in rows),complete_repeat_comparisons=repeats,counts=counts,unknown_counts=unknown,attempted_task_ids=[t['task_id']for t in attempts],unexecuted_task_ids=[t['task_id']for t in tasks if t not in attempts],error=error,guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,resource_policy=RESOURCE,training_updates=0,hardware_steps=0);dump(O/'COMPLETION.json',done);dump(O/'ACTIVE.json',dict(kind='closed',models_authorized=False));cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_window=None,execution_window_closed=True);cur['v1067_closed']=done;dump(R/'CURRENT_EXPERIMENT.json',cur)
  try:
   with(O/'finalize.console').open('x')as log:subprocess.Popen([sys.executable,'-B',str(C/'finalize_night.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  except BaseException as e:dump(O/'FINALIZE_START_ERROR.json',dict(error=repr(e),models=0,raw_retained=True))
if __name__=='__main__':main()
