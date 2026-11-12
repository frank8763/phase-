"""Single90min root, two sequential rounds, restore review on every exit."""
import subprocess,fcntl,signal,traceback
from common import *
paths();from resource_policy import apply
RESOURCE=apply();guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert json.loads((O/'QUALIFICATION.json').read_text())['passed'];assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());own=(O/'driver.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not(O/'ROUND_WINDOW.json').exists();tasks=json.loads((C/'TASKS.json').read_text());wall=time.time();mono=time.monotonic();w=dict(started_unix=wall,started_monotonic=mono,absolute_deadline_unix=wall+5400,hard_stop_monotonic=mono+5400,duration_s=5400,old_windows_unchanged=True,scope='Two moving turn-return tests; both complete saved audits permit only original remaining3555 under this root');dump(O/'ROUND_WINDOW.json',w);dump(O/'APPROVAL.json',dict(models_authorized=True,absolute_deadline_unix=wall+5400,allowed_task_ids=[t['task_id']for t in tasks]));(O/'GUARD.bin').write_bytes(guard);rows=[];attempted=[];child=None;error=None
def halted(*_):raise TimeoutError('ABSOLUTE_ROOT_DEADLINE_OR_STOP')
signal.signal(signal.SIGTERM,halted);signal.signal(signal.SIGALRM,halted);signal.setitimer(signal.ITIMER_REAL,max(.001,w['absolute_deadline_unix']-time.time()))
try:
 for index,task in enumerate(tasks):
  if index==2:
   assert len(rows)==2 and all(x.get('audit',{}).get('passed')for x in rows),'MISSING_TWO_REAL_COMPONENTS'
   dump(O/'TWO_COMPONENT_GATE.json',dict(passed=True,source_sha256=sha(C/'SOURCE_FREEZE.json'),actual_task_ids=[x['task_id']for x in rows]))
  budget=905 if task['kind']=='remaining'else 305
  assert time.time()<w['absolute_deadline_unix']-budget-60 and time.monotonic()<w['hard_stop_monotonic']-budget-60;assert(R/'REVIEW_PENDING').read_bytes()==guard;assert not(Path(task['output'])).exists();path=O/(task['task_id']+'.json');dump(path,task);attempted.append(task['task_id']);dump(O/'ATTEMPTS.json',attempted);(R/'REVIEW_PENDING').unlink()
  try:
   with(O/(task['task_id']+'.console')).open('x')as log:
    child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(path)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'ACTIVE.json',dict(pid=child.pid,task_id=task['task_id']));code=child.wait(timeout=budget)
  finally:
   if child is not None and child.poll()is None:
    try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=3)
    except BaseException:
     try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
     except ProcessLookupError:pass
   child=None;(R/'REVIEW_PENDING').write_bytes(guard)
  result_path=Path(task['output'])/'RESULT.json';fallback=Path(task['output'])/'physics/paired/ENTRY_FAILURE_RESULT.json';result_path=result_path if result_path.exists()else fallback
  result=json.loads(result_path.read_text())if result_path.exists()else dict(passed=False,vehicle_initializations=None,new_actual_native=None,own_replay_native=None,missing_result=True);row=dict(task_id=task['task_id'],worker_returncode=code,result=result);rows.append(row);dump(O/'RESULTS.json',rows);assert code==0 and result['passed'],'FIRST_ACTUAL_RESPONSE_FAILURE'
  audit=subprocess.run([sys.executable,'-B',str(C/'audit_one.py'),str(path)],cwd=R,capture_output=True,text=True,timeout=45);(O/(task['task_id']+'.audit.console')).write_text(audit.stdout+audit.stderr);assert audit.returncode==0,'FIRST_SAVED_AUDIT_FAILURE';row['audit']=json.loads((Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json').read_text());dump(O/'RESULTS.json',rows)
except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
finally:
 (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,batch_closed=True));dump(O/'ACTIVE.json',dict(closed=True))
passed=error is None and len(rows)==3 and all(x.get('audit',{}).get('passed')for x in rows);summary=dict(closed=True,passed=passed,both_rounds_passed=passed,attempted=attempted,unexecuted=[t['task_id']for t in tasks if t['task_id']not in attempted],error=error,counts={k:sum(x['result'].get(k,0)for x in rows)if all(x['result'].get(k)is not None for x in rows)else None for k in ['vehicle_initializations','new_actual_native','own_replay_native','replay_state_initializations','private_mujoco_native','historical_replay_native','training_updates']},guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,source_unchanged=all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items()),whole_route_passed=False,new24_executed=False,saved_NS_remaining_completed=passed);dump(O/'COMPLETION.json',summary);signal.setitimer(signal.ITIMER_REAL,0);print(json.dumps(summary),flush=True)
pointer=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());pointer.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,v1080_turn_return_remaining=summary,latest_report='docs/RPCCR_TURN_RETURN_V1080_REPORT.md');dump(R/'CURRENT_EXPERIMENT.json',pointer)
(R/'docs/RPCCR_TURN_RETURN_V1080_REPORT.md').write_text('# V1080 two sequential rounds\n\nClosed; passed='+str(passed)+'\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\nComponents and saved-prefix continuation only; no fresh whole-route or24 acceptance. Raw evidence retained pending remote verified archival.\n')
with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- FINAL V1080 two sequential rounds closed: passed='+str(passed)+'; counts='+json.dumps(summary['counts'])+'; no new whole-route/24 acceptance; raw evidence retained for verified archival. See docs/RPCCR_TURN_RETURN_V1080_REPORT.md.\n')
