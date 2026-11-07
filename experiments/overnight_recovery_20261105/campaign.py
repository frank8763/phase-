"""Offline single finite stage, bounded independently of Codex/network."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/overnight_recovery_20261105';own=repo/'experiments/v830_ranked_return_development'
auth=read(repo/'RPCCR_OVERNIGHT_RECOVERY_AUTHORIZATION_20261105.json');deadline=auth['absolute_deadline_unix'];cfg=read(own/'BATCH.json');stage=repo/cfg['output']
lock=(root/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not(root/'ROUND_WINDOW.json').exists(),'ALREADY_STARTED_NO_RETRY'
assert read(root/'PREPARED.json')['status']=='ONE_CANDIDATE_FROZEN_AND_ZERO_MODEL_QUALIFIED'
guard=(repo/'REVIEW_PENDING').read_bytes();(root/'REVIEW_PENDING.before').write_bytes(guard)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
window=dict(started_unix=time.time(),absolute_deadline_unix=deadline,pid=os.getpid(),round_closed=False,training_updates=0,stage_access=0,real_robot=0)
dump(root/'ROUND_WINDOW.json',window);ledger=read(root/'LEDGER.json');active=None;status='PREPARING';final=None
signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('CAMPAIGN_OUTER_STOP')))
try:
 freeze=read(own/'CANDIDATE_FREEZE.json');assert sha(own/'CANDIDATE_FREEZE.json')==read(root/'PREPARED.json')['source_freezes'][own.name]
 assert all(sha(repo/n)==h for n,h in freeze['files'].items()),'FREEZE_CHANGED'
 assert time.time()+cfg['minimum_start_budget_s']+3<deadline
 with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(root/'inhibitor.console').open('x')as stream:
  inhibitor=subprocess.Popen(['systemd-inhibit','--what=sleep:idle','--mode=block','--who=Phase','--why=Bounded offline Phase development',sys.executable,'-B',str(common/'hold_awake.py'),'--pid',str(os.getpid()),'--deadline',str(deadline+1900)],stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 time.sleep(.5);assert inhibitor.poll()is None,'SLEEP_INHIBITOR_UNAVAILABLE'
 dump(root/'INHIBITOR.json',dict(pid=inhibitor.pid,campaign_pid=os.getpid(),deadline_unix=deadline+1900,models=0,network_calls=0))
 ledger.update(status='RUNNING_V830',scientific_candidates_started=1,models_started=True,active_simulation=True,current_stage=own.name);dump(root/'LEDGER.json',ledger)
 current=read(repo/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_OVERNIGHT_RECOVERY',state='RUNNING_OVERNIGHT_RECOVERY',current_experiment=own.name,active_entrypoint=str(own.relative_to(repo)/'execute.py'),active_run=cfg['output']+'/'+cfg['window'],protocol=str(own.relative_to(repo)/'PROTOCOL.md'),report=cfg['report'],decision_freeze=str(own.relative_to(repo)/'CANDIDATE_FREEZE.json'),source_revision='V830_COMPLETE_RANKED_RETURN_ORIGINAL_ACTIONS',execution_window_closed=False,active_automation=None)
 current['overnight_recovery_20261105']=dict(authorization='RPCCR_OVERNIGHT_RECOVERY_AUTHORIZATION_20261105.json',ledger=str((root/'LEDGER.json').relative_to(repo)),absolute_deadline_unix=deadline,closed=False,new_confirmation=0);dump(repo/'CURRENT_EXPERIMENT.json',current)
 with(stage/'driver.console').open('x')as stream:
  active=subprocess.Popen([sys.executable,'-B',str(own/'execute.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  dump(root/'ACTIVE.json',dict(stage=own.name,pid=active.pid,absolute_deadline_unix=deadline));current['active_pid']=active.pid;dump(repo/'CURRENT_EXPERIMENT.json',current)
  try:code=active.wait(timeout=max(1,deadline-time.time())+1900)
  finally:
   if active.poll()is None:
    os.killpg(active.pid,signal.SIGTERM)
    try:active.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(active.pid,signal.SIGKILL);active.wait()
   active=None
 assert code==0 and(stage/'FINALIZED.json').exists(),'STAGE_OR_FINALIZER_FAILED_NO_RETRY'
 final=read(stage/'FINALIZED.json');assert final['source_and_decompressed_sha_verified']
 status='FIXED_DEVELOPMENT_VERIFIED_NOT_NEW24_ACCEPTANCE'if final['development_passed']else'STOPPED_DEVELOPMENT_NOT_PASSED'
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
finally:
 (repo/'REVIEW_PENDING').write_bytes(guard)
 # Final independent audit supplies exact totals; absent totals stay unknown.
 audit=read(stage/'FINAL_INDEPENDENT_AUDIT.json')if(stage/'FINAL_INDEPENDENT_AUDIT.json').exists()else{}
 summary=dict(status=status,stage=own.name,final=final,main_gate=audit.get('main_gate'),navigation_native=audit.get('navigation_native'),private_native=audit.get('private_native'),replay_native=audit.get('replay_native'),complete_repeats=audit.get('complete_repeats'),new_confirmation=0,old_V828_NOT_PASSED_preserved=True,no_automatic_new_candidates=True,network_calls=0)
 dump(root/'COMPLETION.json',summary);window.update(round_closed=True,status=status,elapsed_s=time.time()-window['started_unix']);dump(root/'ROUND_WINDOW.json',window)
 ledger.update(status=status,closed=True,active_simulation=False,current_stage=None,no_more_models_or_integrations=True,final=final);dump(root/'LEDGER.json',ledger)
 current=read(repo/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_pid=None,execution_window_closed=True,requires_user_review_before_next_experiment=True);current.setdefault('overnight_recovery_20261105',{}).update(closed=True,status=status);dump(repo/'CURRENT_EXPERIMENT.json',current)
 (repo/'docs/RPCCR_OVERNIGHT_RECOVERY_20261105_REPORT.md').write_text('# 无人值守返回搜索开发实际结果\n\n状态：'+status+'。\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n两次V828失败现为开发样本；原三路线也属开发，完整重复另计。今晚新24确认0，不能称动态验收通过。原V828及所有旧失败/截止保持。准确或未知积分以本批独立终审为准，null不填0。源、风险、模型、329/657覆盖和完整328尾门不减。REVIEW_PENDING恢复，不自动修补、新候选、新池或训练。报告见 '+cfg['report']+'。\n')
 dump(root/'ACTIVE.json',dict(completed=True,status=status))
 # Closed operation metadata, including previously active logs, in a separate nonrecursive archive.
 try:
  from close_ops import close_ops
  close_ops(repo,root,own)
 except BaseException as error:dump(root/'CLOSURE_ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
print(json.dumps(dict(status=status,finalized=final is not None,new_confirmation=0)),flush=True)
