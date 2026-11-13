"""Two fixed physical components, first failure stops; offline bounded owner."""
import sys,os,json,time,signal,subprocess,fcntl,traceback
from pathlib import Path
from common import C,R,O,dump,sha,remaining,source_ok,used,GUARD_SHA
def permitted(rows):return all(x['passed']for x in rows)
def command(task):return [str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(C/('TASK_'+task['task_id']+'.json'))]
def main():
 w=json.loads((O/'ROUND_WINDOW.json').read_text());guard=(O/'GUARD.bin').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD_SHA and source_ok()
 lock=(O/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 tasks=json.loads((C/'TASKS.json').read_text());rows=[];attempts=[];error=None;child=None
 def stop():
  nonlocal child
  if child is not None and child.poll()is None:
   try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=3)
   except BaseException:
    try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
    except ProcessLookupError:pass
  child=None
 def halt(*_):raise TimeoutError('ROOT90MIN_HARD_STOP')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining(w)))
 try:
  for task in tasks:
   assert permitted(rows)and source_ok()and remaining(w)>800,'GATE_SOURCE_OR_DEADLINE'
   assert used()+128*1024**2<=2*1024**3,'TEMPORARY2GIB_CAP'
   assert(R/'REVIEW_PENDING').read_bytes()==guard and not Path(task['output']).exists()
   attempts.append(task['task_id']);dump(O/'ATTEMPTS.json',attempts);(R/'REVIEW_PENDING').unlink()
   try:
    with(O/(task['task_id']+'.console')).open('x')as log:
     child=subprocess.Popen(command(task),cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
     dump(O/'ACTIVE.json',dict(pid=child.pid,starttime=Path('/proc',str(child.pid),'stat').read_text().split()[21],task_id=task['task_id'],stage='physical_component'))
     code=child.wait(timeout=min(755,remaining(w)-10))
   finally:stop();(R/'REVIEW_PENDING').write_bytes(guard)
   p=Path(task['output'])/'RESULT.json';result=json.loads(p.read_text())if p.exists()else dict(passed=False,missing_result=True)
   row=dict(task_id=task['task_id'],passed=False,returncode=code,result=result);rows.append(row);dump(O/'RESULTS.json',rows)
   if p.exists()and result.get('evidence_saved'):
    try:
     with(O/(task['task_id']+'.audit.console')).open('x')as log:
      child=subprocess.Popen([sys.executable,'-B',str(C/'audit.py'),str(C/('TASK_'+task['task_id']+'.json'))],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
      dump(O/'ACTIVE.json',dict(pid=child.pid,starttime=Path('/proc',str(child.pid),'stat').read_text().split()[21],task_id=task['task_id'],stage='zero_model_audit'))
      acode=child.wait(timeout=min(90,remaining(w)-5))
     auditfile=Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json';row['audit']=json.loads(auditfile.read_text())if auditfile.exists()else dict(passed=False,missing_audit=True)
     row['audit_returncode']=acode
    finally:stop()
   row['passed']=bool(code==0 and result['passed']and row.get('audit',{}).get('passed')and source_ok());dump(O/'RESULTS.json',rows)
   assert row['passed'],'FIRST_RESPONSE_SAFETY_OR_EVIDENCE_FAILURE'
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
 finally:
  stop();(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True));signal.setitimer(signal.ITIMER_REAL,0)
 keys=['vehicle_initializations','new_actual_native','own_replay_native','replay_state_initializations','private_mujoco_native','training_updates']
 counts={k:sum(row['result'][k]for row in rows)if len(rows)==len(attempts)and all(row['result'].get(k)is not None for row in rows)else None for k in keys}
 summary=dict(closed=True,passed=bool(error is None and len(rows)==2 and permitted(rows)),version='v1112',scope='two original static t0 parked-steering components only',attempted=attempts,unexecuted=[t['task_id']for t in tasks if t['task_id']not in attempts],counts=counts,error=error,source_unchanged=source_ok(),guard_original=sha(R/'REVIEW_PENDING')==GUARD_SHA,whole_route_passed=False,new24_executed=False,closed_unix=time.time())
 dump(O/'COMPLETION.json',summary)
 report=R/'docs/RPCCR_PARKED_MODE_RESPONSE_V1112_REPORT.md';report.write_text('# V1112 parked-mode measured response\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\nEach component compares the whole fixed prediction against actual qpos/encoders; first failure cancels the remaining tasks. Complete retained-stop and replay passing do not change a failed model-response outcome.\n')
 current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_completed=summary,latest_report=str(report.relative_to(R)));dump(R/'CURRENT_EXPERIMENT.json',current)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- FINAL V1112 parked-mode physical components: '+json.dumps(summary,ensure_ascii=False)+'\n')
 try:
  with(O/'finalize.console').open('x')as log:subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 except BaseException as e:dump(O/'ARCHIVE_ERROR.json',dict(error=repr(e),models=0,raw_retained=True))
 print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
