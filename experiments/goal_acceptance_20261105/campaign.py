"""One immutable16h campaign, no retry or scientific repair loops."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/goal_acceptance_20261105';lp=root/'LEDGER.json';cp=repo/'CURRENT_EXPERIMENT.json';auth=read(repo/'RPCCR_GOAL_ACCEPTANCE_AUTHORIZATION_20261105.json');deadline=auth['absolute_deadline_unix']
lock=(root/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not(root/'ROUND_WINDOW.json').exists();assert read(root/'PREPARED.json')['status']=='BOTH_STAGES_FROZEN_AND_ZERO_MODEL_QUALIFIED'
assert(repo/'REVIEW_PENDING').exists();guard=(repo/'REVIEW_PENDING').read_bytes();(root/'REVIEW_PENDING.before').write_bytes(guard);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
window=dict(started_unix=time.time(),absolute_deadline_unix=deadline,pid=os.getpid(),round_closed=False,training_updates=0,stage_access=0,real_robot=0);dump(root/'ROUND_WINDOW.json',window)
day=read(lp);status='RUNNING';active=None;stages=[]
signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('CAMPAIGN_TERMINATED')))
try:
 for name in ['v827_goal_route_validation','v828_goal_dynamic_confirmation']:
  own=repo/'experiments'/name;assert sha(own/'CANDIDATE_FREEZE.json')==read(root/'PREPARED.json')['source_freezes'][name];cfg=read(own/'BATCH.json');freeze=read(own/'CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items()),'FROZEN_SOURCE_CHANGED'
  if cfg['confirmation']:
   dep=read(repo/cfg['dependency']/'FINALIZED.json');assert dep['combined_three_route_development_passed']and dep['source_and_decompressed_sha_verified'],'THREE_ROUTE_DEPENDENCY_FAILED'
  assert time.time()+cfg['minimum_start_budget_s']+3<deadline,'INSUFFICIENT_REMAINING_FULL_STAGE_BUDGET'
  assert(repo/'REVIEW_PENDING').read_bytes()==guard,'GUARD_NOT_RESTORED'
  with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
  counter='confirmation_batches_started'if cfg['confirmation']else'development_batches_started';assert day[counter]==0,'STAGE_ALREADY_STARTED';day[counter]+=1;day.update(status='RUNNING_'+name,current_stage=name,active_simulation=True);dump(lp,day)
  stage=repo/cfg['output']
  with(stage/'driver.console').open('x')as stream:
   active=subprocess.Popen([sys.executable,'-B',str(own/'execute.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
   dump(root/'ACTIVE.json',dict(stage=name,pid=active.pid,absolute_deadline_unix=deadline))
   current=read(cp);current.update(status='RUNNING_GOAL_ACCEPTANCE',state='RUNNING_GOAL_ACCEPTANCE',current_experiment=name,active_entrypoint=str(own.relative_to(repo)/'execute.py'),active_run=cfg['output']+'/'+cfg['window'],active_pid=active.pid,execution_window_closed=False,protocol=str(own.relative_to(repo)/'PROTOCOL.md'),active_automation=day.get('automation_id'));current['goal_acceptance_20261105']=dict(authorization='RPCCR_GOAL_ACCEPTANCE_AUTHORIZATION_20261105.json',ledger=str(lp.relative_to(repo)),absolute_deadline_unix=deadline,active_stage=name,algorithm='V826',closed=False);dump(cp,current)
   try:code=active.wait(timeout=min(cfg['batch_cap_s'],deadline-time.time())+1800)
   finally:
    if active.poll()is None:
     os.killpg(active.pid,signal.SIGTERM)
     try:active.wait(timeout=5)
     except subprocess.TimeoutExpired:os.killpg(active.pid,signal.SIGKILL);active.wait()
    active=None
  assert code==0 and(stage/'FINALIZED.json').exists(),'STAGE_DRIVER_OR_FINALIZATION_FAILED'
  final=read(stage/'FINALIZED.json');stages.append(dict(stage=name,final=final,final_audit=cfg['output']+'/FINAL_INDEPENDENT_AUDIT.json'));dump(root/'STAGES.json',stages)
  assert final['source_and_decompressed_sha_verified'],'ARCHIVE_NOT_VERIFIED'
  if not(final['confirmation_passed']if cfg['confirmation']else final['combined_three_route_development_passed']):status='STOPPED_STAGE_NOT_PASSED';break
 else:status='FINITE_FULL_FIELD_DYNAMIC_CONFIRMATION_PASS'
except BaseException as e:
 status='STOPPED_EXCEPTION';dump(root/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
finally:
 (repo/'REVIEW_PENDING').write_bytes(guard);window.update(round_closed=True,status=status,elapsed_s=time.time()-window['started_unix']);dump(root/'ROUND_WINDOW.json',window);day.update(status=status,closed=True,current_stage=None,active_simulation=False,no_more_models_or_integrations=True,stage_results=stages,needs_review_commit_and_single_bounded_sync=True);dump(lp,day)
 current=read(cp);current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_pid=None,execution_window_closed=True,requires_user_review_before_next_experiment=True);current.setdefault('goal_acceptance_20261105',{}).update(closed=True,status=status,active_stage=None)
 if status=='FINITE_FULL_FIELD_DYNAMIC_CONFIRMATION_PASS':current.update(finite_full_field_dynamic_acceptance_passed=True,finite_full_field_dynamic_acceptance_scope='original19-static map/three registered routes/single norm.08 small actor/reactive3m discovery; V826 algorithm')
 dump(cp,current);dump(root/'COMPLETION.json',dict(status=status,stages=stages,no_automatic_new_experiments=True,confirmation_started=(repo/'runs/v828_goal_dynamic_confirmation/ROUND_WINDOW.json').exists(),confirmation_unexecuted_main_if_not_started=(24 if not(repo/'runs/v828_goal_dynamic_confirmation/ROUND_WINDOW.json').exists()else None)))
 (repo/'docs/RPCCR_GOAL_ACCEPTANCE_20261105_REPORT.md').write_text('# V826算法动态验收实际结果\n\n状态：'+status+'。\n\n'+'\n'.join('- '+x['stage']+'：'+x['final']['status']+'，报告 '+x['final']['report']for x in stages)+'\n\n尚无V828 ROUND_WINDOW即24确认及3固定重复全部未执行，不报0/24。V826旧南北主复用参照、V827开发及所有重复与V828新24分开记账；未执行不计失败率。原V826 NOT_PASSED及全部旧失败保持。准确或未知积分见各独立终审；未有FINALIZED的阶段不称审核完成。REVIEW_PENDING恢复，不自动修订/换池/比较/训练。限定单地图单慢速actor及较弱发现前反应式条件，不宣称任意遮挡/多actor/实时/全面优势。\n')
 dump(root/'ACTIVE.json',dict(completed=True,status=status))
print(json.dumps(dict(status=status,stages=len(stages))),flush=True)
