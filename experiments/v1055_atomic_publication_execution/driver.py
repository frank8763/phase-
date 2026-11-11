"""One immutable main and conditional repeat; fixed user20:30, offline safe."""
import fcntl,signal,subprocess,traceback
from kernel import *
from audit import audit_native,compare
def main():
 with(O/'DRIVER_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started=time.time(),hard_deadline_unix=HARD_END),f)
 own=(O/'driver.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(O/'GUARD.bin').read_bytes();rows=[];error=None;repeat=None;goal=False;child=None;attempts=[]
 def stop(*_):raise InterruptedError('ABSOLUTE_OR_EXTERNAL_STOP')
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining_root()-15))
 try:
  freeze=json.loads((C/'SOURCE_FREEZE.json').read_text());assert all(sha(R/p)==h for p,h in freeze['files'].items())
  for i,task in enumerate(json.loads((C/'FULL_TASKS.json').read_text())):
   assert remaining_root()>(1930 if i==0 else 960),'INSUFFICIENT_MAIN_REPEAT_RESERVE';assert all(sha(R/p)==h for p,h in freeze['files'].items()),'FROZEN_SOURCE_CHANGED'
   receipt=dict(task_id=task['task_id'],window_sha256=sha(O/'ROUND_WINDOW.json'),source_sha256=sha(C/'SOURCE_FREEZE.json'),plan_sha256=sha(O/'SELECTED_PLAN.json'));rp=O/(task['task_id']+'.AUTHORITY.json');dump(rp,receipt);attempts.append(task);dump(O/'MODEL_ATTEMPTS.json',attempts);(R/'REVIEW_PENDING').unlink()
   try:
    with(O/(task['task_id']+'.console')).open('x')as log:
     child=subprocess.Popen([str(R/'run_phase.sh'),'experiments/v1055_atomic_publication_execution/full_worker.py',str(C/('TASK_'+task['task_id']+'.json')),str(rp)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);start=Path('/proc',str(child.pid),'stat').read_text().rsplit(')',1)[1].split()[19];dump(O/'ACTIVE.json',dict(pid=child.pid,pid_start=start,kind='physics',task_id=task['task_id'],deadline=min(HARD_END-30,time.time()+930)));code=child.wait(timeout=min(930,remaining_root()-30))
   finally:
    if child is not None and child.poll()is None:
     os.killpg(child.pid,signal.SIGTERM)
     try:child.wait(5)
     except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(5)
    (R/'REVIEW_PENDING').write_bytes(guard)
   result=json.loads((Path(task['output'])/'RESULT.json').read_text());proof=audit_native(task,True);rows.append(dict(task=task,result=result,audit=proof,passed=code==0 and result['passed']and proof['passed']));dump(O/'MODEL_RESULTS.json',rows);assert proof['safety_passed'],'SAFETY_OR_EVIDENCE_FAILURE';assert rows[-1]['passed'],'FUNCTIONAL_FAILURE_STOP'
  tasks=json.loads((C/'FULL_TASKS.json').read_text());repeat=compare(*tasks);assert repeat['passed'],'COMPLETE_REPEAT_MISMATCH';goal=True
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));counts={k:0 for k in ['model_initializations','historical_replay_native','new_navigation_suffix_native','own_replay_native','private_mujoco_native']};unknown=[]
  for task in attempts:
   p=Path(task['output'])/'RESULT.json';r=json.loads(p.read_text())if p.exists()else{}
   for k in counts:
    value=0 if k=='private_mujoco_native'else r.get(k)
    if value is None:unknown.append(dict(task=task['task_id'],field=k));counts[k]=None
    elif counts[k]is not None:counts[k]+=value
  done=dict(closed=True,goal_continuation_and_repeat_passed=goal,reverse_qualified=True,rows=rows,repeat=repeat,error=error,counts=counts,unknown_counts=unknown,closed_unix=time.time(),hard_deadline_unix=HARD_END,guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,new24_executed=0,old_brake_only_contract_preserved=False);dump(O/'COMPLETION.json',done);dump(O/'ACTIVE.json',dict(kind='closed',models_authorized=False));cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_window=None);cur['v1055_atomic_execution_closed']=dict(goal_passed=goal,error=error,counts=counts,unknown_counts=unknown);dump(R/'CURRENT_EXPERIMENT.json',cur)
  report=R/'docs/RPCCR_ATOMIC_EXECUTION_V1055_REPORT.md';report.write_text('# V1055原子发布与原困难任务实际续行结果\n\n'+json.dumps({k:v for k,v in done.items()if k not in ['rows','repeat']},indent=2,ensure_ascii=False)+'\n\n同原困难任务保存态续行主及完整重复。新的移动后备合同替代中间每原生立即刹停合同，不追认旧失败；不是新独立导航样本或24项验收，也不是实时/任意运动/递归安全/RAS保证。来源资格、全部实际安全/跟踪与重复证据见本轮目录。\n');print(json.dumps({k:v for k,v in done.items()if k not in ['rows','repeat']}),flush=True)
  try:subprocess.run([sys.executable,'-B',str(C/'close.py')],cwd=R,timeout=300,check=True)
  except BaseException as e:dump(O/'CLOSURE_ERROR.json',dict(error=repr(e),raw_retained=True,models=0))
 return 0 if goal else 1
if __name__=='__main__':sys.exit(main())
