"""One OS-only continuation into the never-started frozen stage, same existing12h deadline."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;ROOT=R/'runs/v842_os_identity_continuation_20261106';PREV=R/'runs/staged_audit_completion_20261106';O=R/'runs/v842_staged_long_navigation'
sys.path.insert(0,str(R/'experiments/staged_audit_completion_20261106'));from evidence_rules import read,dump,sha;from limits import can_transition;import engine
lock=(ROOT/'campaign.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
with(ROOT/'LAUNCH_CLAIM.json').open('x')as stream:json.dump(dict(pid=os.getpid(),started_unix=time.time(),launch_attempts=1),stream)
assert not(O/'development12').exists(),'PHYSICAL_STAGE_ALREADY_EXISTS_NO_RETRY'
assert read(ROOT/'QUALIFICATION.json')['passed']
claim=read(PREV/'DEVELOPMENT12_WINDOW_CLAIM.json');deadline=claim['absolute_deadline_unix'];pilot=read(PREV/'SUPPLEMENT_FINALIZED.json');assert can_transition(pilot)and time.time()+6500<deadline
def unchanged():
 assert all(sha(R/p)==h for p,h in read(C/'OPERATIONS_FREEZE.json')['files'].items()),'OS_OPERATIONS_SOURCE_CHANGED'
 frozen=read(R/'experiments/staged_audit_completion_20261106/DEVELOPMENT_FREEZE.json');assert all(sha(R/p)==h for p,h in frozen['files'].items()),'FROZEN_DEVELOPMENT_CHANGED'
 assert all(sha(R/x['path'])==x['sha256']for x in read(PREV/'ORIGINAL_EVIDENCE_FREEZE.json')),'ORIGINAL_PILOT_CHANGED'
unchanged();old_unchanged=engine.unchanged
def complete_unchanged():unchanged();old_unchanged()
engine.unchanged=complete_unchanged
guard=(R/'REVIEW_PENDING').read_bytes();(ROOT/'REVIEW_PENDING.before').write_bytes(guard)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});window=dict(started_unix=claim['started_unix'],absolute_deadline_unix=deadline,os_continuation_started_unix=time.time(),deadline_reset=False,round_closed=False,pid=os.getpid());dump(ROOT/'ROUND_WINDOW.json',window)
dump(ROOT/'LEDGER.json',dict(status='STARTING_OS_IDENTITY_CONTINUATION',closed=False,active_simulation=False,old_deadline_unchanged=deadline,new24=0,scientific_revisions=0))
inhibitor=None;final=None;status='STARTING';signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('CAMPAIGN_TERMINATED_NO_RESTART')))
try:
 with(ROOT/'inhibitor.console').open('x')as f:
  inhibitor=subprocess.Popen(['systemd-inhibit','--what=sleep:idle','--mode=block','--who=Phase','--why=Existing bounded Phase development window',sys.executable,'-B',str(C/'os_watch.py'),'--pid',str(os.getpid()),'--entrypoint',str(Path(__file__).resolve()),'--deadline',str(deadline+14400)],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 time.sleep(.5);assert inhibitor.poll()is None,'OS_IDENTITY_INHIBITOR_FAILED_STOP'
 dump(ROOT/'INHIBITOR.json',dict(pid=inhibitor.pid,campaign_pid=os.getpid(),housekeeping_deadline=deadline+14400,model_deadline=deadline))
 current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_V842_CONDITIONAL12H_OS_IDENTITY_CONTINUATION',state='RUNNING_V842_CONDITIONAL12H_OS_IDENTITY_CONTINUATION',active_entrypoint=str((C/'start.py').relative_to(R)),active_pid=os.getpid(),active_run='runs/v842_staged_long_navigation/development12',active_window=window,execution_window_closed=False,protocol=str((C/'PROTOCOL.md').relative_to(R)),report='docs/RPCCR_V842_AUDIT_SUPPLEMENT_20261106_REPORT.md');current['v842_os_identity_continuation_20261106']=dict(ledger=str((ROOT/'LEDGER.json').relative_to(R)),closed=False,original_deadline_unix=deadline);dump(R/'CURRENT_EXPERIMENT.json',current)
 dump(ROOT/'LEDGER.json',dict(status='RUNNING_CONDITIONAL12H',closed=False,active_simulation=True,scientific_revisions=0,model_deadline=deadline,new_navigation_max=3,new24=0))
 final=engine.stage_run('development12',deadline,pilot);status='TWO_OLD_FAILURES_AND_COMPLETE_REPEATS_PASS'if can_transition(final)else'STOPPED_CONDITIONAL12H_NOT_PASSED'
except BaseException as e:status='STOPPED_EXCEPTION';dump(ROOT/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
finally:
 (R/'REVIEW_PENDING').write_bytes(guard)
 if inhibitor is not None and inhibitor.poll()is None:
  os.killpg(inhibitor.pid,signal.SIGTERM)
  try:inhibitor.wait(timeout=3)
  except subprocess.TimeoutExpired:os.killpg(inhibitor.pid,signal.SIGKILL);inhibitor.wait()
 window.update(round_closed=True,status=status,closed_unix=time.time());dump(ROOT/'ROUND_WINDOW.json',window);dump(ROOT/'LEDGER.json',dict(status=status,closed=True,active_simulation=False,no_more_models_or_integrations=True))
 summary=dict(status=status,conditional12=final,pilot_supplement=pilot,deadline_reset=False,original_deadline_unix=deadline,prior_zero_model_startup_identity_failure_preserved=True,new24=0,scientific_revisions=0,training=0,network=0,Stage=0,automatic_restart=False);dump(ROOT/'COMPLETION.json',summary)
 current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',active_entrypoint=None,active_pid=None,active_run=None,active_window=None,execution_window_closed=True,requires_user_review_before_next_experiment=True,report='docs/RPCCR_V842_OS_IDENTITY_CONTINUATION_20261106_REPORT.md');current.setdefault('v842_os_identity_continuation_20261106',{}).update(closed=True,status=status);dump(R/'CURRENT_EXPERIMENT.json',current)
 report=R/'docs/RPCCR_V842_OS_IDENTITY_CONTINUATION_20261106_REPORT.md';report.write_text('# V842原截止内OS入口接续实际结果\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n原先导到达、原审核超时/计数FAIL与原OS身份启动失败均保留，所有实际主/重复/未执行及模型私有/重放以阶段独立审核分账，未知不填0。不是新24动态验收。原模型截止不延长或重置，不自动追加新候选/实验/训练/网络。\n')
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V842_OS_IDENTITY_CONTINUATION CLOSED '+status+'；沿用原01:38:10截止，不重置，原所有错误保持，自动任务外无追加实验。报告docs/RPCCR_V842_OS_IDENTITY_CONTINUATION_20261106_REPORT.md。\n')
 print(json.dumps(summary),flush=True)
 try:
  target=R/'evidence/rpccr_v842_os_identity_ops_20261106';target.mkdir(exist_ok=False);files={p for p in ROOT.rglob('*')if p.is_file()and p.suffix not in ['.lock','.pyc']and'__pycache__'not in p.parts};files.update(p for p in C.iterdir()if p.is_file());files.update([report,R/'CURRENT_EXPERIMENT.json'])
  for name in ['finalize.console','transport.console','FINALIZED.json','FINAL_INDEPENDENT_AUDIT.json']:
   p=O/'development12'/name
   if p.exists():files.add(p)
  inventory=[]
  with zipfile.ZipFile(target/'OPERATIONS_SNAPSHOT.zip','x',compression=zipfile.ZIP_DEFLATED)as z:
   for p in sorted(files):
    data=p.read_bytes();name=str(p.relative_to(R));z.writestr(name,data);inventory.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
  with zipfile.ZipFile(target/'OPERATIONS_SNAPSHOT.zip')as z:
   for row in inventory:
    data=z.read(row['path']);assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256']
  dump(target/'MANIFEST.json',dict(status='OPERATIONS_DECOMPRESSED_SHA_VERIFIED',inventory=inventory,raw_deleted=False));dump(ROOT/'CLOSED_OPERATIONS_ARCHIVE.json',dict(archive=str(target.relative_to(R)),source_snapshot_SHA_verified=True))
 except BaseException as e:dump(ROOT/'CLOSURE_ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
