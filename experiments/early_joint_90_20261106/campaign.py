"""One 90-minute offline campaign: saved295 gate -> one main -> conditional repeat."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;own=repo/'experiments/v841_early_joint';root=repo/'runs/early_joint_90_20261106';auth=read(repo/'RPCCR_EARLY_JOINT_90_AUTHORIZATION_20261106.json');deadline=auth['absolute_deadline_unix']
lock=(root/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not(root/'ROUND_WINDOW.json').exists(),'NO_RESTART'
prepared=read(root/'PREPARED.json');assert prepared['status']=='ONE_CANDIDATE_FROZEN_AND_ZERO_MODEL_QUALIFIED'
guard=(repo/'REVIEW_PENDING').read_bytes();(root/'REVIEW_PENDING.before').write_bytes(guard);window=dict(started_unix=auth['model_window_started_unix'],absolute_deadline_unix=deadline,pid=os.getpid(),round_closed=False);dump(root/'ROUND_WINDOW.json',window);ledger=read(root/'LEDGER.json');status='STARTING';component=None;final=None;active=None;inhibitor=None
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('CAMPAIGN_TERMINATED')))
def current(phase):
 c=read(repo/'CURRENT_EXPERIMENT.json');c.update(status=phase,state=phase,current_experiment=own.name,active_run='runs/v841_early_joint',active_entrypoint=str(own.relative_to(repo)/'execute.py'),active_pid=os.getpid(),execution_window_closed=False,active_automation=None,protocol=str(own.relative_to(repo)/'PROTOCOL.md'));c['early_joint_90_20261106']=dict(absolute_deadline_unix=deadline,closed=False,ledger=str((root/'LEDGER.json').relative_to(repo)));dump(repo/'CURRENT_EXPERIMENT.json',c);ledger.update(status=phase,active_simulation=True);dump(root/'LEDGER.json',ledger)
try:
 assert time.time()+3600<deadline
 manifest=read(own/'CANDIDATE_FREEZE.json');assert sha(own/'CANDIDATE_FREEZE.json')==prepared['source_freezes'][own.name]and all(sha(repo/n)==h for n,h in manifest['files'].items()),'SOURCE_CHANGED'
 with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(root/'inhibitor.console').open('x')as stream:inhibitor=subprocess.Popen(['systemd-inhibit','--what=sleep:idle','--mode=block','--who=Phase','--why=One bounded 90-minute experiment',sys.executable,'-B',str(common/'hold_awake.py'),'--pid',str(os.getpid()),'--deadline',str(deadline+1900)],stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 time.sleep(.5);assert inhibitor.poll()is None,'INHIBITOR_FAILED'
 current('RUNNING_EARLY_JOINT_SAVED_QUALIFICATION')
 from component import run_component
 component=run_component(repo,root,deadline);dump(root/'COMPONENT_FINAL.json',component)
 if not component['component_passed']:status='STOPPED_SAVED_QUALIFICATION_NOT_PASSED';raise StopIteration
 assert time.time()+3003<deadline,'INSUFFICIENT_COMPLETE_STAGE_BUDGET'
 current('RUNNING_EARLY_JOINT_SINGLE_SCENE')
 with(repo/'runs/v841_early_joint/driver.console').open('x')as stream:
  active=subprocess.Popen([sys.executable,'-B',str(own/'execute.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  dump(root/'ACTIVE.json',dict(stage='main_then_conditional_repeat',pid=active.pid,absolute_deadline_unix=deadline))
  try:code=active.wait(timeout=max(1,deadline-time.time())+1900)
  finally:
   if active.poll()is None:
    os.killpg(active.pid,signal.SIGTERM)
    try:active.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(active.pid,signal.SIGKILL);active.wait()
 assert code==0,'DEVELOPMENT_OR_FINALIZER_FAILED_NO_RETRY';final=read(repo/'runs/v841_early_joint/FINALIZED.json');assert final['source_and_decompressed_sha_verified'];status='SINGLE_SCENE_AND_REPEAT_PASS'if final['development_passed']else'STOPPED_SINGLE_SCENE_NOT_PASSED'
except StopIteration:pass
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
finally:
 (repo/'REVIEW_PENDING').write_bytes(guard)
 if inhibitor is not None and inhibitor.poll()is None:
  os.killpg(inhibitor.pid,signal.SIGTERM)
  try:inhibitor.wait(timeout=3)
  except subprocess.TimeoutExpired:os.killpg(inhibitor.pid,signal.SIGKILL);inhibitor.wait()
 summary=dict(status=status,qualification=component,development=final,model_deadline_unix=deadline,new_confirmation=0,scientific_candidates=1,automatic_repair_or_retry=False,network_calls=0,training=0,stage_access=0)
 dump(root/'COMPLETION.json',summary);window.update(round_closed=True,status=status,elapsed_s=time.time()-window['started_unix']);dump(root/'ROUND_WINDOW.json',window);ledger.update(status=status,closed=True,active_simulation=False,no_more_models_or_integrations=True);dump(root/'LEDGER.json',ledger);dump(root/'ACTIVE.json',dict(completed=True,status=status))
 c=read(repo/'CURRENT_EXPERIMENT.json');c.update(status='REVIEW_PENDING',state='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_pid=None,execution_window_closed=True,requires_user_review_before_next_experiment=True);c['early_joint_90_20261106'].update(closed=True,status=status);dump(repo/'CURRENT_EXPERIMENT.json',c)
 report=repo/'docs/RPCCR_EARLY_JOINT_90_20261106_REPORT.md';report.write_text('# 90分钟提前联合开发实际报告\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n原295保存资格、完整主导航、条件完整重复分别记账；未执行不计失败分母。这里只是旧失败单场景开发，不是新24确认或递归安全保证。截止不延长；旧失败和原始证据保持。\n')
 with(repo/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- EARLY_JOINT_90_20261106 CLOSED '+status+'；原10060002单场景；详见docs/RPCCR_EARLY_JOINT_90_20261106_REPORT.md。无自动新候选或确认。\n')
 try:
  from close_ops import close_ops
  close_ops(repo,root,own)
 except BaseException as e:dump(root/'CLOSURE_ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
print(json.dumps(summary),flush=True)
