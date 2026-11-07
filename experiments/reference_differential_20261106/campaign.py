"""Offline qualification -> development -> conditional fresh24, one fixed cutoff."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent
root=repo/'runs/reference_differential_20261106'
deadline=read(repo/'RPCCR_REFERENCE_DIFFERENTIAL_AUTHORIZATION_20261106.json')['absolute_deadline_unix']
master=(root/'campaign.lock').open('a+');fcntl.flock(master,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not(root/'ROUND_WINDOW.json').exists(),'ALREADY_STARTED_NO_RETRY'
prepared=read(root/'PREPARED.json');assert prepared['status']=='ONE_CANDIDATE_FROZEN_AND_ZERO_MODEL_QUALIFIED'
guard=(repo/'REVIEW_PENDING').read_bytes();(root/'REVIEW_PENDING.before').write_bytes(guard)
window=dict(started_unix=time.time(),absolute_deadline_unix=deadline,pid=os.getpid(),round_closed=False)
dump(root/'ROUND_WINDOW.json',window);ledger=read(root/'LEDGER.json')
status='PREPARING';inhibitor=None;active=None;component_final=None;stages=[]
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('CAMPAIGN_OUTER_STOP')))
def current_stage(name,phase):
 own=repo/'experiments'/name;current=read(repo/'CURRENT_EXPERIMENT.json')
 current.update(status=phase,state=phase,current_experiment=name,active_entrypoint=str(own.relative_to(repo)/('probe.py'if name.startswith('v838')else'execute.py')),active_run='runs/'+name,active_pid=os.getpid(),execution_window_closed=False,protocol=str(own.relative_to(repo)/'PROTOCOL.md'),active_automation=None)
 current['reference_differential_20261106']=dict(authorization='RPCCR_REFERENCE_DIFFERENTIAL_AUTHORIZATION_20261106.json',ledger=str((root/'LEDGER.json').relative_to(repo)),absolute_deadline_unix=deadline,closed=False)
 dump(repo/'CURRENT_EXPERIMENT.json',current);ledger.update(status=phase,active_simulation=True,current_stage=name,candidates_started=1);dump(root/'LEDGER.json',ledger)
def run_stage(name):
 global active
 own=repo/'experiments'/name;cfg=read(own/'BATCH.json');stage=repo/cfg['output']
 assert time.time()+cfg['minimum_start_budget_s']+3<deadline,'INSUFFICIENT_FULL_STAGE_BUDGET'
 current_stage(name,'RUNNING_DYNAMIC_CONFIRMATION'if cfg['confirmation']else'RUNNING_DYNAMIC_DEVELOPMENT')
 with(stage/'driver.console').open('x')as log:
  active=subprocess.Popen([sys.executable,'-B',str(own/'execute.py')],cwd=repo,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  dump(root/'ACTIVE.json',dict(stage=name,pid=active.pid,absolute_deadline_unix=deadline))
  try:code=active.wait(timeout=max(1.,deadline-time.time())+1900)
  finally:
   if active.poll()is None:
    os.killpg(active.pid,signal.SIGTERM)
    try:active.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(active.pid,signal.SIGKILL);active.wait()
   active=None
 assert code==0 and(stage/'FINALIZED.json').exists(),'STAGE_OR_FINALIZER_FAILED_NO_RETRY'
 final=read(stage/'FINALIZED.json');assert final['source_and_decompressed_sha_verified']
 stages.append(dict(stage=name,finalized=final));dump(root/'STAGES.json',stages)
 return final
try:
 for name,digest in prepared['source_freezes'].items():
  own=repo/'experiments'/name;manifest=own/('INPUT_FREEZE.json'if name.startswith('v838')else'CANDIDATE_FREEZE.json')
  assert sha(manifest)==digest and all(sha(repo/n)==h for n,h in read(manifest)['files'].items()),'SOURCE_FREEZE_CHANGED'
 assert time.time()+9000<deadline
 with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(root/'inhibitor.console').open('x')as log:
  inhibitor=subprocess.Popen(['systemd-inhibit','--what=sleep:idle','--mode=block','--who=Phase','--why=Bounded offline dynamic development',sys.executable,'-B',str(common/'hold_awake.py'),'--pid',str(os.getpid()),'--deadline',str(deadline+1900)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 time.sleep(.5);assert inhibitor.poll()is None,'SLEEP_INHIBITOR_UNAVAILABLE'
 dump(root/'INHIBITOR.json',dict(pid=inhibitor.pid,campaign_pid=os.getpid(),deadline_unix=deadline+1900,models=0))
 current_stage('v838_reference_differential_qualification','RUNNING_FIXED_NATIVE_QUALIFICATION')
 from component import run_component
 component_final=run_component(repo,root);dump(root/'COMPONENT_FINAL.json',component_final)
 if not component_final['component_passed']:status='STOPPED_FIXED_COMPONENT_NOT_PASSED';raise StopIteration(status)
 final=run_stage('v839_reference_differential_development')
 if not final['combined_three_route_development_passed']:status='STOPPED_DEVELOPMENT_NOT_PASSED';raise StopIteration(status)
 if time.time()+36003>=deadline:status='DEVELOPMENT_PASS_CONFIRMATION_NOT_STARTED_INSUFFICIENT_FULL_BUDGET';raise StopIteration(status)
 final=run_stage('v840_reference_differential_confirmation')
 status='FINITE_DYNAMIC_CONFIRMATION_PASS'if final['confirmation_passed']else'STOPPED_CONFIRMATION_NOT_PASSED'
except StopIteration:pass
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
finally:
 (repo/'REVIEW_PENDING').write_bytes(guard)
 if inhibitor is not None and inhibitor.poll()is None:
  os.killpg(inhibitor.pid,signal.SIGTERM)
  try:inhibitor.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(inhibitor.pid,signal.SIGKILL);inhibitor.wait()
 counts=read(repo/'runs/v838_reference_differential_qualification/COMPLETION.json')['counts']if(repo/'runs/v838_reference_differential_qualification/COMPLETION.json').exists()else None
 audits={}
 for name in ['v839_reference_differential_development','v840_reference_differential_confirmation']:
  p=repo/'runs'/name/'FINAL_INDEPENDENT_AUDIT.json'
  if p.exists():audits[name]=read(p)
 summary=dict(status=status,component_final=component_final,component_counts=counts,stages=stages,stage_accounts={name:{k:a.get(k)for k in ['status','main_gate','complete_repeats','navigation_native','private_native','replay_native','new_confirmation_tasks']}for name,a in audits.items()},development_started=(repo/'runs/v839_reference_differential_development/ROUND_WINDOW.json').exists(),confirmation_started=(repo/'runs/v840_reference_differential_confirmation/ROUND_WINDOW.json').exists(),old_failures_and_deadlines_preserved=True,additional_candidates=False,network_calls=0)
 dump(root/'COMPLETION.json',summary);window.update(round_closed=True,status=status,elapsed_s=time.time()-window['started_unix']);dump(root/'ROUND_WINDOW.json',window)
 ledger.update(status=status,closed=True,active_simulation=False,current_stage=None,no_more_models_or_integrations=True);dump(root/'LEDGER.json',ledger)
 current=read(repo/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_pid=None,execution_window_closed=True,requires_user_review_before_next_experiment=True);current.setdefault('reference_differential_20261106',{}).update(closed=True,status=status);dump(repo/'CURRENT_EXPERIMENT.json',current)
 dump(root/'ACTIVE.json',dict(completed=True,status=status))
 (repo/'docs/RPCCR_REFERENCE_DIFFERENTIAL_20261106_REPORT.md').write_text('# RP-CCR参考恢复与有限接续实际结果\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n资格、开发、完整重复、新确认及未执行分开。新增为原因果参考跟随完整尾与原328后额外8原生接续见证，不是递归可行或无限停车保证。原物理、控制、感知、329/657和全状态重放门保持。准确或未知积分以各批独立终审为准。未执行全24不报全分母率。旧失败、窗口和REVIEW_PENDING保持，不自动新候选、池、比较或训练。\n')
 try:
  from close_ops import close_ops
  close_ops(repo,root,repo/'experiments/v839_reference_differential_development')
 except BaseException as error:dump(root/'CLOSURE_ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
print(json.dumps(dict(status=status,stages=len(stages),confirmation_started=summary['confirmation_started'])),flush=True)
