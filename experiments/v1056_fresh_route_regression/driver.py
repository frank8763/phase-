"""Bounded true-start WE main and conditional repeat. No route substitution."""
import fcntl,signal,subprocess,traceback
from kernel import *
from audit import audit_native,compare
def main():
 with(O/'DRIVER_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started=time.time()),f)
 own=(O/'driver.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(O/'GUARD.bin').read_bytes();rows=[];attempts=[];error=None;repeat=None;passed=False;child=None;tasks=json.loads((C/'PHYSICAL_TASKS.json').read_text())
 def stop(*_):raise InterruptedError('ABSOLUTE_OR_EXTERNAL_STOP')
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining_root()-15))
 try:
  freeze=json.loads((C/'SOURCE_FREEZE.json').read_text())
  for i,task in enumerate(tasks):
   assert remaining_root()>(1300 if i==0 else 650),'INSUFFICIENT_UNCHANGED_ROOT_RESERVE';assert all(sha(R/p)==h for p,h in freeze['files'].items()),'SOURCE_CHANGED'
   receipt=dict(task_id=task['task_id'],window_sha256=sha(O/'ROUND_WINDOW.json'),source_sha256=sha(C/'SOURCE_FREEZE.json'));rp=O/(task['task_id']+'.AUTHORITY.json');dump(rp,receipt);attempts.append(task);dump(O/'ATTEMPTS.json',attempts);(R/'REVIEW_PENDING').unlink()
   try:
    with(O/(task['task_id']+'.console')).open('x')as log:
     child=subprocess.Popen([str(R/'run_phase.sh'),'experiments/v1056_fresh_route_regression/worker.py',str(C/('TASK_'+task['task_id']+'.json')),str(rp)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);start=Path('/proc',str(child.pid),'stat').read_text().rsplit(')',1)[1].split()[19];dump(O/'ACTIVE.json',dict(pid=child.pid,pid_start=start,kind='physics',task_id=task['task_id'],deadline=min(HARD_END-30,time.time()+620)));code=child.wait(timeout=min(620,remaining_root()-30))
   finally:
    if child is not None and child.poll()is None:
     os.killpg(child.pid,signal.SIGTERM)
     try:child.wait(5)
     except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(5)
    (R/'REVIEW_PENDING').write_bytes(guard)
   result=json.loads((Path(task['output'])/'RESULT.json').read_text());proof=audit_native(task);row=dict(task=task,result=result,audit=proof,passed=code==0 and result['passed']and proof['passed']);rows.append(row);dump(O/'RESULTS.json',rows);assert proof['safety_passed'],'SAFETY_OR_EVIDENCE_FAILURE';assert row['passed'],'FIRST_FUNCTIONAL_FAILURE_STOP'
  repeat=compare(*tasks);assert repeat['passed'],'FULL_REPEAT_MISMATCH';passed=True
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True,allowed_task_ids=[]));counts={k:0 for k in ['model_initializations','historical_replay_native','navigation_native','own_replay_native','private_mujoco_native']};unknown=[]
  for task in attempts:
   path=Path(task['output'])/'RESULT.json';r=json.loads(path.read_text())if path.exists()else{}
   for k in counts:
    value=r.get(k)
    if value is None:counts[k]=None;unknown.append(dict(task_id=task['task_id'],field=k))
    elif counts[k]is not None:counts[k]+=value
  done=dict(closed=True,fresh_west_east_main_and_repeat_passed=passed,combined_three_route_development_passed=False,rows=rows,repeat=repeat,error=error,counts=counts,unknown_counts=unknown,unexecuted_task_ids=[t['task_id']for t in json.loads((C/'TASKS.json').read_text())if t not in attempts],hard_deadline_unix=HARD_END,closed_unix=time.time(),guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,new24_executed=0,training_updates=0,hardware_steps=0);dump(O/'COMPLETION.json',done);report=R/'docs/RPCCR_FRESH_ROUTE_V1056_REPORT.md';report.write_text('# V1056 真实起点动态回归第一段\n\n'+json.dumps({k:v for k,v in done.items()if k not in ['rows','repeat']},indent=2,ensure_ascii=False)+'\n\n本批仅原WE真实t0主与成功条件完整重复；历史命令/状态恢复0。三路线总门尚未通过：NS动态交接未资格，EW规范初态被原统一预测储备拒绝，两路线本批未执行，不能报0/3失败率。固定24项未执行。开发提案库来自已观察WE，属于开发回归，不是未见任务。实际/自身重放/私有分账及功能/安全结论见RESULTS与各车独立审计。20:30硬截止不延长；原失败不升级；非实时/任意动态或递归安全保证。\n');dump(O/'ACTIVE.json',dict(kind='closed',models_authorized=False));cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_window=None);cur['v1056_fresh_start_closed']={k:v for k,v in done.items()if k not in ['rows','repeat']};dump(R/'CURRENT_EXPERIMENT.json',cur);print(json.dumps({k:v for k,v in done.items()if k not in ['rows','repeat']}),flush=True)
 try:
  with(O/'close.console').open('x')as log:subprocess.Popen([sys.executable,'-B',str(C/'close.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 except BaseException as e:dump(O/'CLOSURE_ERROR.json',dict(error=repr(e),models=0,raw_retained=True))
 return 0 if passed else 1
if __name__=='__main__':sys.exit(main())
