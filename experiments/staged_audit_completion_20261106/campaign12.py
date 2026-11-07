"""Previously authorized conditional12h; only a fully SHA-verified saved pilot unlocks it."""
import fcntl,json,os,signal,subprocess,sys,time,traceback,zipfile,hashlib
from pathlib import Path
from evidence_rules import dump,read,sha
from limits import can_transition
from engine import stage_run
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;ROOT=R/'runs/staged_audit_completion_20261106';O=R/'runs/v842_staged_long_navigation';W=R/'experiments/v842_staged_long_navigation'
lock=(ROOT/'campaign12.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not(ROOT/'DEVELOPMENT12_WINDOW_CLAIM.json').exists(),'ONLY_ONE_CONDITIONAL_WINDOW'
assert not(O/'development12').exists(),'NO_STAGE_RELAUNCH'
pilot=read(ROOT/'SUPPLEMENT_FINALIZED.json');assert can_transition(pilot),'SUPPLEMENT_ALL_GATES_REQUIRED'
assert read(ROOT/'DEVELOPMENT_OPERATIONS_CHECK.json')['passed']
assert all(sha(R/n)==h for n,h in read(C/'DEVELOPMENT_FREEZE.json')['files'].items())
guard=(R/'REVIEW_PENDING').read_bytes();(ROOT/'DEVELOPMENT_REVIEW_PENDING.before').write_bytes(guard)
with(R/'runs/v648_static_unknown/execution.lock').open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});start=time.time();deadline=start+43200
claim=dict(started_unix=start,absolute_deadline_unix=deadline,pilot_finalized_sha256=sha(ROOT/'SUPPLEMENT_FINALIZED.json'),pilot_archive=pilot['archive'],scientific_freeze_sha256=sha(W/'CANDIDATE_FREEZE.json'),operations_freeze_sha256=sha(C/'DEVELOPMENT_FREEZE.json'),launch_attempts=1)
with(ROOT/'DEVELOPMENT12_WINDOW_CLAIM.json').open('x')as f:json.dump(claim,f,indent=2)
window=dict(**claim,pid=os.getpid(),round_closed=False,stage2_started=True);dump(ROOT/'ROUND_WINDOW.json',window);dump(ROOT/'LEDGER.json',dict(status='RUNNING_CONDITIONAL12H',closed=False,active_simulation=True,scientific_revisions=0,pilot_new_navigation=0,new_navigation_max=3,new24=0))
current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_V842_CONDITIONAL12H_FROM_SUPPLEMENT',state='RUNNING_V842_CONDITIONAL12H_FROM_SUPPLEMENT',active_run=str((O/'development12').relative_to(R)),active_entrypoint=str((C/'campaign12.py').relative_to(R)),active_pid=os.getpid(),execution_window_closed=False,report='docs/RPCCR_V842_AUDIT_SUPPLEMENT_20261106_REPORT.md',protocol=str((C/'DEVELOPMENT_PROTOCOL.md').relative_to(R)),active_window=claim)
current['staged_audit_completion_20261106']=dict(ledger=str((ROOT/'LEDGER.json').relative_to(R)),pilot_supplement=str((ROOT/'SUPPLEMENT_FINALIZED.json').relative_to(R)),absolute_deadline_unix=deadline,closed=False);dump(R/'CURRENT_EXPERIMENT.json',current)
inhibitor=None;final=None;status='STARTING';signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('CONDITIONAL_CAMPAIGN_TERMINATED_NO_RESTART')))
try:
 with(ROOT/'development_inhibitor.console').open('x')as f:inhibitor=subprocess.Popen(['systemd-inhibit','--what=sleep:idle','--mode=block','--who=Phase','--why=Bounded conditional12h original two failure development',sys.executable,'-B',str(C/'hold_awake.py'),'--pid',str(os.getpid()),'--deadline',str(deadline+14400)],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 time.sleep(.5);assert inhibitor.poll()is None,'SLEEP_INHIBITOR_UNAVAILABLE'
 dump(ROOT/'DEVELOPMENT_INHIBITOR.json',dict(pid=inhibitor.pid,campaign_pid=os.getpid(),housekeeping_deadline_unix=deadline+14400,extends_model_window=False))
 final=stage_run('development12',deadline,pilot);status='TWO_OLD_FAILURES_AND_COMPLETE_REPEATS_PASS'if can_transition(final)else'STOPPED_CONDITIONAL12H_NOT_PASSED'
except BaseException as e:status='STOPPED_EXCEPTION';dump(ROOT/'DEVELOPMENT_ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
finally:
 (R/'REVIEW_PENDING').write_bytes(guard)
 if inhibitor is not None and inhibitor.poll()is None:
  os.killpg(inhibitor.pid,signal.SIGTERM)
  try:inhibitor.wait(timeout=3)
  except subprocess.TimeoutExpired:os.killpg(inhibitor.pid,signal.SIGKILL);inhibitor.wait()
 summary=dict(status=status,pilot_supplement=pilot,conditional12=final,scientific_revisions=0,new24=0,training=0,Stage=0,network=0,automatic_restart=False,old_batch_and_deadlines_preserved=True)
 dump(ROOT/'DEVELOPMENT_COMPLETION.json',summary);window.update(round_closed=True,status=status,elapsed_s=time.time()-start);dump(ROOT/'ROUND_WINDOW.json',window);dump(ROOT/'LEDGER.json',dict(status=status,closed=True,active_simulation=False,no_more_models_or_integrations=True))
 current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',active_run=None,active_entrypoint=None,active_pid=None,active_window=None,execution_window_closed=True,requires_user_review_before_next_experiment=True,report='docs/RPCCR_V842_CONDITIONAL12H_SUPPLEMENT_20261106_REPORT.md');current['staged_audit_completion_20261106'].update(closed=True,status=status);dump(R/'CURRENT_EXPERIMENT.json',current)
 report=R/'docs/RPCCR_V842_CONDITIONAL12H_SUPPLEMENT_20261106_REPORT.md';report.write_text('# V842补充审核后条件12小时实际结果\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n原先导闭批NOT_PASSED与两个审核超时原样保留，补充独立全门通过后只原两失败及完整重复开发；不是新24动态验收。实际积分以各阶段独立审核为准，未知不填0。\n')
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V842_AUDIT_SUPPLEMENT_CONDITIONAL12 CLOSED '+status+'；原失败和截止保持，无自动新24/候选/对照。报告docs/RPCCR_V842_CONDITIONAL12H_SUPPLEMENT_20261106_REPORT.md。\n')
 print(json.dumps(summary),flush=True)
 try:
  target=R/'evidence/rpccr_v842_conditional12_ops_20261106';target.mkdir(exist_ok=False);files={p for p in ROOT.rglob('*')if p.is_file()and not p.is_symlink()and p.suffix not in['.lock','.pyc']and '__pycache__'not in p.parts and not p.is_relative_to(ROOT/'reference')};files.update([report,R/'CURRENT_EXPERIMENT.json'])
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
  dump(target/'MANIFEST.json',dict(status='OPERATIONS_DECOMPRESSED_SHA_VERIFIED',inventory=inventory,new_models=0,new_integrations=0,raw_deleted=False));dump(ROOT/'DEVELOPMENT_OPERATIONS_ARCHIVE.json',dict(archive=str(target.relative_to(R)),source_snapshot_SHA_verified=True))
 except BaseException as e:dump(ROOT/'DEVELOPMENT_CLOSURE_ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
