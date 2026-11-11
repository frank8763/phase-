"""Offline, immutable relay. The only caller allowed to launch registered models."""
import fcntl,os,signal,subprocess,sys,traceback
from kernel import *
from audit import audit_native,compare

def pid_start(pid):
 try:return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:return None

def run_job(args,log_path,until,kind,task_id):
 remaining=min(until-time.time(),remaining_root()-10);assert remaining>1,'NO_JOB_RESERVE';child=None
 with Path(log_path).open('x')as log:
  child=subprocess.Popen([str(a)for a in args],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'ACTIVE.json',dict(pid=child.pid,pid_start=pid_start(child.pid),kind=kind,task_id=task_id,started=time.time(),deadline=until))
  try:return child.wait(timeout=max(.001,remaining))
  finally:
   if child.poll()is None:
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(5)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(5)

def run_model(task,script,reserve,full=False):
 assert remaining_root()>reserve,'INSUFFICIENT_MODEL_RESERVE';receipt=dict(task_id=task['task_id'],window_sha256=sha(O/'ROUND_WINDOW.json'),source_sha256=sha(C/'SOURCE_FREEZE.json'))
 if full:receipt['plan_sha256']=sha(O/'SELECTED_PLAN.json')
 attempts=json.loads((O/'MODEL_ATTEMPTS.json').read_text())if(O/'MODEL_ATTEMPTS.json').exists()else[];attempts.append(dict(task=task,full=full,at=time.time()));dump(O/'MODEL_ATTEMPTS.json',attempts)
 rp=O/(task['task_id']+'.AUTHORITY.json');dump(rp,receipt);tp=C/('TASK_'+task['task_id']+'.json');guard=(O/'GUARD.bin').read_bytes();(R/'REVIEW_PENDING').unlink()
 try:code=run_job([R/'run_phase.sh',Path('experiments/v1047_day_relay')/script,tp,rp],O/(task['task_id']+'.console'),min(HARD_END-30,time.time()+(930 if full else 330)),'physics',task['task_id'])
 finally:(R/'REVIEW_PENDING').write_bytes(guard)
 path=Path(task['output'])/'RESULT.json';assert path.exists(),'MISSING_MODEL_RESULT_UNKNOWN_COUNTS';result=json.loads(path.read_text());proof=audit_native(task,full);assert proof['safety_passed'],'SAFETY_OR_EVIDENCE_FAILURE';return dict(task=task,passed=code==0 and result['passed']and proof['passed'],result=result,audit=proof)

def main():
 with (O/'DRIVER_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started=time.time(),hard_deadline_unix=HARD_END),f)
 lock=(O/'relay.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(O/'GUARD.bin').read_bytes();rows=[];sources=[];error=None;repeat=None;reverse=False;goal=False
 def stop(*_):raise InterruptedError('ROOT_ABSOLUTE_OR_EXTERNAL_STOP')
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining_root()-15))
 try:
  freeze=json.loads((C/'SOURCE_FREEZE.json').read_text());assert all(sha(R/p)==h for p,h in freeze['files'].items()),'FROZEN_SOURCE_CHANGED'
  for task in json.loads((C/'REVERSE_TASKS.json').read_text()):
   row=run_model(task,'reverse_worker.py',400);rows.append(row);dump(O/'MODEL_RESULTS.json',rows)
   if not row['passed']:
    # Only this known prediction-response rejection may disable reverse while
    # preserving independent, already-qualified forward source work.
    assert row['result'].get('error')=="AssertionError('HELDOUT_NATIVE_RESPONSE_ERROR')",'UNEXPECTED_REVERSE_FUNCTIONAL_FAILURE';break
  reverse=len(rows)==3 and all(r['passed']for r in rows);dump(O/'REVERSE_QUALIFICATION.json',dict(passed=reverse,rows=rows,models=0,scope='three fixed reverse short responses only'))
  configs=json.loads((C/'CONFIGS.json').read_text())
  for config in configs:
   assert all(sha(R/p)==h for p,h in freeze['files'].items()),'FROZEN_SOURCE_CHANGED'
   if config['allow_reverse']and not reverse:sources.append(dict(id=config['id'],status='UNEXECUTED_REVERSE_NOT_QUALIFIED'));dump(O/'SOURCE_RESULTS.json',sources);continue
   if time.time()>=HARD_END-150:break
   cfg=C/'configs'/(config['id']+'.json');limit=min(HARD_END-30,time.time()+config['wall_s']+10);code=run_job([sys.executable,'-B',C/'source_job.py',cfg,str(limit-10)],O/(config['id']+'.console'),limit,'source',config['id']);result_path=O/'sources'/config['id']/'RESULT.json'
   if not result_path.exists():
    # A declared wallclock cap is a finite software result; unexpected errors
    # and missing accounting remain fatal evidence exceptions.
    ep=O/'sources'/config['id']/'ERROR.json';assert ep.exists(),'MISSING_SOURCE_EVIDENCE';e=json.loads(ep.read_text());assert 'ROOT_SOURCE_CAP'in e['error']or'FULL_STOP_AUDIT_TIME_CAP'in e['error'],'SOURCE_EXCEPTION '+e['error'];sources.append(dict(id=config['id'],status='SOURCE_WALL_CAP',error=e));dump(O/'SOURCE_RESULTS.json',sources);continue
   result=json.loads(result_path.read_text());sources.append(dict(id=config['id'],passed=result['passed'],status=result['status'],expanded=result.get('expanded'),best_goal_distance_m=result.get('best_goal_distance_m'),wall_s=result.get('wall_s')));dump(O/'SOURCE_RESULTS.json',sources)
   if not result['passed']:continue
   assert result['all_native_stop_audit']['passed'];dump(O/'SELECTED_PLAN.json',result)
   if time.time()>=HARD_END-1930:sources[-1]['physical_status']='UNEXECUTED_INSUFFICIENT_MAIN_REPEAT_RESERVE';dump(O/'SOURCE_RESULTS.json',sources);break
   tasks=json.loads((C/'FULL_TASKS.json').read_text());main=run_model(tasks[0],'full_worker.py',1930,True);rows.append(main);dump(O/'MODEL_RESULTS.json',rows);assert main['passed'],'MAIN_FUNCTIONAL_FAILURE_STOP'
   second=run_model(tasks[1],'full_worker.py',960,True);rows.append(second);dump(O/'MODEL_RESULTS.json',rows);assert second['passed'],'REPEAT_FUNCTIONAL_FAILURE_STOP';repeat=compare(tasks[0],tasks[1]);assert repeat['passed'],'COMPLETE_REPEAT_MISMATCH';goal=True;break
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));unknown=[];counts={k:0 for k in ['model_initializations','new_response_native','historical_replay_native','new_navigation_suffix_native','own_replay_native','private_mujoco_native']}
  attempts=json.loads((O/'MODEL_ATTEMPTS.json').read_text())if(O/'MODEL_ATTEMPTS.json').exists()else[]
  for attempt in attempts:
   task=attempt['task'];path=Path(task['output'])/'RESULT.json';result=json.loads(path.read_text())if path.exists()else{};row=dict(task=task,result=result)
   for k in counts:
    applicable=k not in (['new_response_native']if attempt['full']else['historical_replay_native','new_navigation_suffix_native'])
    value=result.get(k,None)if applicable else 0
    if k=='private_mujoco_native':value=0 # frozen worker contains no private model calls
    if value is None:unknown.append(dict(task=row['task']['task_id'],field=k));counts[k]=None
    elif counts[k]is not None:counts[k]+=value
  done=dict(closed=True,goal_continuation_and_repeat_passed=goal,reverse_qualified=reverse,rows=rows,sources=sources,repeat=repeat,error=error,counts=counts,unknown_counts=unknown,closed_unix=time.time(),hard_deadline_unix=HARD_END,guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,new24_executed=0)
  dump(O/'COMPLETION.json',done);dump(O/'ACTIVE.json',dict(kind='finalizing',models_authorized=False));cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_window=None);cur['v1047_relay_closed']=dict(goal_passed=goal,error=error,counts=counts,unknown_counts=unknown);dump(R/'CURRENT_EXPERIMENT.json',cur)
  report=R/'docs/RPCCR_DAY_RELAY_20261111_REPORT.md';report.write_text('# 2026-11-11日间离线接力实际结果\n\n'+json.dumps({k:v for k,v in done.items()if k not in ['rows','repeat']},indent=2,ensure_ascii=False)+'\n\n完整实际原生、资格、失败/未执行及重复分账见runs/v1047_day_relay_20261111/COMPLETION.json。原困难任务以保存态继续主与完整重复门为准，新24未执行；不得当新独立样本或实时/RAS保证。\n');print(json.dumps({k:v for k,v in done.items()if k not in ['rows','sources','repeat']}),flush=True)
  try:subprocess.run([sys.executable,'-B',str(C/'close.py')],cwd=R,timeout=300,check=True)
  except BaseException as e:dump(O/'CLOSURE_ERROR.json',dict(error=repr(e),models=0,raw_retained=True))
 return 0 if goal else 1
if __name__=='__main__':sys.exit(main())
