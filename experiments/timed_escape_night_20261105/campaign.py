"""Offline single finite stage, bounded independently of Codex/network."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/timed_escape_night_20261105';own=repo/'experiments/v834_timed_escape_development'
auth=read(repo/'RPCCR_TIMED_ESCAPE_NIGHT_AUTHORIZATION_20261105.json');deadline=auth['absolute_deadline_unix'];cfg=read(own/'BATCH.json');stage=repo/cfg['output']
lock=(root/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not(root/'ROUND_WINDOW.json').exists(),'ALREADY_STARTED_NO_RETRY'
assert read(root/'PREPARED.json')['status']=='ONE_CANDIDATE_FROZEN_AND_ZERO_MODEL_QUALIFIED'
guard=(repo/'REVIEW_PENDING').read_bytes();(root/'REVIEW_PENDING.before').write_bytes(guard)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
component_final=None
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
 ledger.update(status='RUNNING_FIXED_V833_COMPONENT',candidates_started=1,active_simulation=True,current_stage='v833_timed_escape_qualification');dump(root/'LEDGER.json',ledger)
 current=read(repo/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_FORWARD_ESCAPE_COMPONENT',state='RUNNING_FORWARD_ESCAPE_COMPONENT',current_experiment='v833_timed_escape_qualification',active_entrypoint='experiments/v833_timed_escape_qualification/probe.py',active_run='runs/v833_timed_escape_qualification',active_pid=os.getpid(),execution_window_closed=False,protocol='experiments/v833_timed_escape_qualification/PROTOCOL.md',active_automation=None)
 current['timed_escape_night_20261105']=dict(authorization='RPCCR_TIMED_ESCAPE_NIGHT_AUTHORIZATION_20261105.json',ledger=str((root/'LEDGER.json').relative_to(repo)),absolute_deadline_unix=deadline,closed=False,new_confirmation=0);dump(repo/'CURRENT_EXPERIMENT.json',current)
 from component import run_component
 component_final=run_component(repo,root);dump(root/'COMPONENT_FINAL.json',component_final)
 if not component_final['component_passed']:status='STOPPED_FIXED_COMPONENT_NOT_PASSED';raise StopIteration(status)
 assert time.time()+cfg['minimum_start_budget_s']+3<deadline,'INSUFFICIENT_REMAINING_NAVIGATION_BUDGET'
 ledger.update(status='RUNNING_V834',active_simulation=True,current_stage=own.name);dump(root/'LEDGER.json',ledger)
 current=read(repo/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_OVERNIGHT_RECOVERY',state='RUNNING_OVERNIGHT_RECOVERY',current_experiment=own.name,active_entrypoint=str(own.relative_to(repo)/'execute.py'),active_run=cfg['output']+'/'+cfg['window'],protocol=str(own.relative_to(repo)/'PROTOCOL.md'),report=cfg['report'],decision_freeze=str(own.relative_to(repo)/'CANDIDATE_FREEZE.json'),source_revision='V834_RETURN_ONLY_JOINT_SPEED_BRAKE_GOAL_PROGRESS',execution_window_closed=False,active_automation=None)
 current['timed_escape_night_20261105']=dict(authorization='RPCCR_TIMED_ESCAPE_NIGHT_AUTHORIZATION_20261105.json',ledger=str((root/'LEDGER.json').relative_to(repo)),absolute_deadline_unix=deadline,closed=False,new_confirmation=0);dump(repo/'CURRENT_EXPERIMENT.json',current)
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
except StopIteration:pass
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
finally:
 (repo/'REVIEW_PENDING').write_bytes(guard)
 # Final independent audit supplies exact totals; absent totals stay unknown.
 audit=read(stage/'FINAL_INDEPENDENT_AUDIT.json')if(stage/'FINAL_INDEPENDENT_AUDIT.json').exists()else{}
 component_counts=read(repo/'runs/v833_timed_escape_qualification/COMPLETION.json')['counts']if(repo/'runs/v833_timed_escape_qualification/COMPLETION.json').exists()else None
 navigation_started=(stage/'ROUND_WINDOW.json').exists()
 if not navigation_started:audit=dict(main_gate=dict(passed=False,main_attempts=0,main_successes=0,planned_main=5,unexecuted_main=5,success_rate=None),navigation_native=0,private_native=0,replay_native=0,complete_repeats=0)
 summary=dict(status=status,component_counts=component_counts,navigation_started=navigation_started,stage=own.name,component_final=component_final,final=final,main_gate=audit.get('main_gate'),navigation_native=audit.get('navigation_native'),private_native=audit.get('private_native'),replay_native=audit.get('replay_native'),complete_repeats=audit.get('complete_repeats'),new_confirmation=0,old_V828_NOT_PASSED_preserved=True,no_automatic_new_candidates=True,network_calls=0)
 dump(root/'COMPLETION.json',summary);window.update(round_closed=True,status=status,elapsed_s=time.time()-window['started_unix']);dump(root/'ROUND_WINDOW.json',window)
 ledger.update(status=status,closed=True,active_simulation=False,current_stage=None,no_more_models_or_integrations=True,component_final=component_final,final=final);dump(root/'LEDGER.json',ledger)
 current=read(repo/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_pid=None,execution_window_closed=True,requires_user_review_before_next_experiment=True);current.setdefault('timed_escape_night_20261105',{}).update(closed=True,status=status);dump(repo/'CURRENT_EXPERIMENT.json',current)
 (repo/'docs/RPCCR_TIMED_ESCAPE_NIGHT_20261105_REPORT.md').write_text('# 无人值守返回搜索开发实际结果\n\n状态：'+status+'。\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n固定V833组件/实际分支/重复和V834导航分开记账。两次V828失败现为开发样本；原三路线也属开发，完整重复另计。今晚新24确认0，不能称动态验收通过。原V828及所有旧失败/截止保持。准确或未知积分以本批独立终审为准，null不填0。源、风险、模型、329/657覆盖和完整328尾门不减。唯一新增是仅保留后备返回时原21全拒后新145个固定速度—刹停时刻尾及完整尾目标进展.02门，普通准入不改。REVIEW_PENDING恢复，不自动修补、新候选、新池或训练。报告见 '+cfg['report']+'。\n')
 dump(root/'ACTIVE.json',dict(completed=True,status=status))
 # Closed operation metadata, including previously active logs, in a separate nonrecursive archive.
 try:
  from close_ops import close_ops
  close_ops(repo,root,own)
 except BaseException as error:dump(root/'CLOSURE_ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
print(json.dumps(dict(status=status,finalized=final is not None,new_confirmation=0)),flush=True)
