"""Offline fixed branches and gated confirmation. Never edits frozen science."""
import sys,signal,subprocess,fcntl,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from resource_policy import apply
RESOURCE=apply()
from kernel import *
from audit import audit_native,compare
from decisions import can_continue_after_failure,three_gate,confirmation_gate
RAW=R/'runs/v858_nav2_verified/v1062';BUDGET=8*1024**3

def budget():return sum(p.stat().st_size for root in [RAW,O]for p in root.rglob('*')if p.is_file()and not p.is_symlink())
def main():
 with(O/'DRIVER_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),at=time.time()),f)
 own=(O/'driver.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(O/'GUARD.bin').read_bytes();tasks=json.loads((C/'TASKS.json').read_text());branches=json.loads((C/'BRANCHES.json').read_text());pool=json.loads((C/'CONFIRMATION_POOL.json').read_text());attempts=[];rows=[];candidate_summaries=[];preflights={};selected=None;error=None;confirmation=[];confirmation_repeats=[];confirmed=False;child=None
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
 def run(task,branch_id=None):
  nonlocal child
  assert remaining_root()>1200 if task['kind']!='t0'else remaining_root()>300,'INSUFFICIENT_FIXED_ROOT_RESERVE';assert budget()<BUDGET-400*1024**2,'TEMPORARY8GIB_STORAGE_STOP'
  receipt=dict(task_id=task['task_id'],task_sha256=sha(C/('TASK_'+task['task_id']+'.json')),source_sha256=sha(C/'SOURCE_FREEZE.json'),window_sha256=sha(O/'ROUND_WINDOW.json'),branch_id=branch_id,task_deadline_unix=min(HARD_END-30,time.time()+(100 if task['kind']=='t0'else 900)))
  if task['task_id'].startswith('t0_confirm')or task['kind'].startswith('confirm'):receipt['gate_sha256']=sha(O/'THREE_ROUTE_GATE.json')
  rp=O/(task['task_id']+'.AUTHORITY.json');dump(rp,receipt);attempts.append(task);dump(O/'ATTEMPTS.json',attempts);entry='t0_worker.py'if task['kind']=='t0'else'worker.py';assert(R/'REVIEW_PENDING').read_bytes()==guard;(R/'REVIEW_PENDING').unlink()
  try:
   with(O/(task['task_id']+'.console')).open('x')as log:
    child=subprocess.Popen([str(R/'run_phase.sh'),str((C/entry).relative_to(R)),str(C/('TASK_'+task['task_id']+'.json')),str(rp)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);start=Path('/proc',str(child.pid),'stat').read_text().rsplit(')',1)[1].split()[19];dump(O/'ACTIVE.json',dict(kind='physics',pid=child.pid,pid_start=start,task_id=task['task_id'],branch_id=branch_id,deadline=receipt['task_deadline_unix'],resource_policy=RESOURCE));code=child.wait(timeout=max(.001,min(receipt['task_deadline_unix']-time.time()+10,remaining_root()-15)))
  finally:terminate();(R/'REVIEW_PENDING').write_bytes(guard)
  path=Path(task['output'])/'RESULT.json';assert path.exists(),'DRIVER_CHILD_RESULT_MISSING';result=json.loads(path.read_text())
  if task['kind']=='t0':
   preflights[task['task_id']]=result;dump(O/'PREFLIGHTS.json',preflights);assert code==0 and result['passed'],'PREFLIGHT_SAFETY_OR_INITIAL_CONTRACT_FAILURE';return result
  proof=audit_native(task);row=dict(task=task,result=result,audit=proof,passed=code==0 and result['passed']and proof['passed']);rows.append(row);dump(O/'RESULTS.json',rows);assert proof['safety_passed']and proof['prediction']['passed'],'SAFETY_STATE_CONTROL_COVERAGE_OR_EVIDENCE_FAILURE'
  if not row['passed']:assert can_continue_after_failure(result,proof),'UNCLASSIFIED_OR_EVIDENCE_FAILURE'
  dump(O/'ACTIVE.json',dict(kind='between_tasks',last_task=task['task_id'],last_passed=row['passed'],models_authorized=True));return row
 def stop(*_):raise InterruptedError('ABSOLUTE_OR_EXTERNAL_STOP')
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining_root()-15))
 try:
  for task in tasks:
   if task['task_id'].startswith('t0_dev_'):run(task)
  for branch in branches:
   br=[];repeats=[]
   for case in ['NORTH_SOUTH','EAST_WEST','WEST_EAST']:
    task=next(t for t in tasks if t['branch_id']==branch['id']and t['case_id']==case and t['kind']=='main');main_row=run(task,branch['id']);br.append(main_row)
    if main_row['passed']:
     repeat_task=next(t for t in tasks if t['branch_id']==branch['id']and t['case_id']==case and t['kind']=='repeat');rep=run(repeat_task,branch['id']);br.append(rep)
     if rep['passed']:
      comparison=compare(task,repeat_task);repeats.append(comparison);assert comparison['passed'],'COMPLETE_REPEAT_STATE_CONTACT_DISCOVERY_MISMATCH'
   passed=three_gate(br,repeats);summary=dict(branch=branch,passed=passed,task_ids=[x['task']['task_id']for x in br],functional_failures=[x['task']['task_id']for x in br if not x['passed']],repeat_comparisons=repeats);candidate_summaries.append(summary);dump(O/'CANDIDATE_RESULTS.json',candidate_summaries)
   if not passed and any(any(reason in row['result'].get('error','')for reason in ['REAL_SENSOR_DISCOVERY_REQUIRED','NO_COMPLETE_OBSERVATION_APPROACH'])for row in br if not row['passed']):raise RuntimeError('BRANCH_INVARIANT_PREFIX_FAILURE_NO_IDENTICAL_RETRIES')
   if passed:
    selected=branch['id'];dump(O/'THREE_ROUTE_GATE.json',dict(passed=True,selected_branch_id=selected,course_id='V1061_EW_START_NORTH_010',same_candidate_six_actual_tasks_passed=True,all_independent_audits_passed=True,all_three_complete_repeats_passed=True,source_sha256=sha(C/'SOURCE_FREEZE.json'),at=time.time()));break
  if selected is None:raise RuntimeError('FOUR_FIXED_CANDIDATES_EXHAUSTED_NO_THREE_ROUTE_PASS')
  assert remaining_root()>24*110+1200,'INSUFFICIENT_TIME_FOR_CONFIRMATION_PREFLIGHTS_AND_ONE_TASK'
  for task in tasks:
   if task['task_id'].startswith('t0_confirm'):run(task,selected)
  failures=0
  for task in tasks:
   if task['kind']!='confirm_main':continue
   row=run(task,selected);confirmation.append(row);failures+=int(not row['passed']);dump(O/'CONFIRMATION_RESULTS.json',confirmation)
   if failures>=2:raise RuntimeError('CONFIRMATION_SECOND_FUNCTIONAL_FAILURE_STOP')
  assert confirmation_gate(confirmation,pool),'CONFIRMATION_FULL24_DIRECTION_ROUTE_GATE_FAILED'
  for task in tasks:
   if task['kind']!='confirm_repeat':continue
   base=next(x for x in confirmation if x['task']['slot']==task['slot']);assert base['passed'],'FIXED_REPEAT_BASELINE_FUNCTIONAL_FAILURE';row=run(task,selected);assert row['passed'],'FIXED_CONFIRMATION_REPEAT_FUNCTIONAL_FAILURE';comparison=compare(base['task'],task);assert comparison['passed'],'FIXED_CONFIRMATION_REPEAT_MISMATCH';confirmation_repeats.append(dict(task=task,comparison=comparison));dump(O/'CONFIRMATION_REPEATS.json',confirmation_repeats)
  confirmed=True
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  terminate();signal.setitimer(signal.ITIMER_REAL,0);(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True,allowed_task_ids=[]));counts={k:0 for k in ['model_initializations','historical_replay_native','navigation_native','own_replay_native','private_mujoco_native']};unknown=[]
  for task in attempts:
   p=Path(task['output'])/'RESULT.json';result=json.loads(p.read_text())if p.exists()else{}
   for key in counts:
    value=result.get(key)
    if value is None:counts[key]=None;unknown.append(dict(task_id=task['task_id'],field=key))
    elif counts[key]is not None:counts[key]+=value
  done=dict(closed=True,deadline_unix=HARD_END,closed_at=time.time(),selected_branch_id=selected,combined_three_route_development_passed=selected is not None,confirmation_passed=confirmed,confirmation_main_executed=len(confirmation),confirmation_main_successes=sum(x['passed']for x in confirmation),confirmation_full24_executed=len(confirmation)==24,fixed_confirmation_complete_repeats=len(confirmation_repeats),candidate_results=candidate_summaries,counts=counts,unknown_counts=unknown,attempted_task_ids=[t['task_id']for t in attempts],unexecuted_task_ids=[t['task_id']for t in tasks if t not in attempts],error=error,temporary_bytes=budget(),guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,resource_policy=RESOURCE,training_updates=0,hardware_steps=0);dump(O/'COMPLETION.json',done);dump(O/'ACTIVE.json',dict(kind='closed',models_authorized=False));cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_window=None);cur['v1062_three_route_night_closed']=done;dump(R/'CURRENT_EXPERIMENT.json',cur);report=R/'docs/RPCCR_THREE_ROUTE_NIGHT_V1062_REPORT.md';report.write_text('# V1062 通宵三路线与条件24项\n\n'+json.dumps(done,ensure_ascii=False,indent=2)+'\n\n未执行不计失败率；开发/重复不混确认分母。新课程EW北移0.10m，原任务拒绝与旧失败保持。仅公开周期单actor/已知地图、发现前较弱反应式条件；非实时、任意遮挡、多actor、递归安全或实机保证。离线停止后原始数据保留，远端备份回读前不删除。\n')
  try:
   with(O/'finalize.console').open('x')as log:subprocess.Popen([sys.executable,'-B',str(C/'finalize_night.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  except BaseException as e:dump(O/'FINALIZE_START_ERROR.json',dict(error=repr(e),models=0,raw_retained=True))
if __name__=='__main__':main()
