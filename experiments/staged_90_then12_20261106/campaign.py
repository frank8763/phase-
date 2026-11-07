"""User-authorized offline pilot90 -> conditional new12h; never retries or extends a stage."""
import fcntl,json,os,signal,subprocess,sys,time,traceback,zipfile,hashlib
from pathlib import Path
from evidence_rules import dump,read,sha
from limits import can_transition
from engine import stage_run,unchanged
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v842_staged_long_navigation';O=R/'runs/v842_staged_long_navigation';ROOT=R/'runs/staged_90_then12_20261106';A=read(R/'RPCCR_STAGED_90_THEN12_AUTHORIZATION_20261106.json');deadline=A['stage1_absolute_deadline_unix']
lock=(ROOT/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not(ROOT/'ROUND_WINDOW.json').exists(),'ONE_LAUNCH_NO_RETRY'
guard=(R/'REVIEW_PENDING').read_bytes();(ROOT/'REVIEW_PENDING.before').write_bytes(guard);window=dict(started_unix=A['stage1_started_unix'],stage1_absolute_deadline_unix=deadline,pid=os.getpid(),round_closed=False,stage2_started=False);dump(ROOT/'ROUND_WINDOW.json',window);ledger=read(ROOT/'LEDGER.json');inhibitor=None;first=None;second=None;status='STARTING'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('CAMPAIGN_TERMINATED_NO_RESTART')))
def current(phase):
 c=read(R/'CURRENT_EXPERIMENT.json');c.update(status=phase,state=phase,current_experiment=W.name,decision_freeze=str((W/'CANDIDATE_FREEZE.json').relative_to(R)),source_revision='V842_BUDGET_ONLY_V841_IDENTICAL_DECISIONS',active_run=str(O.relative_to(R)),active_entrypoint=str((C/'campaign.py').relative_to(R)),active_pid=os.getpid(),execution_window_closed=False,protocol=str((W/'PROTOCOL.md').relative_to(R)),active_automation=None,report='docs/RPCCR_STAGED_90_THEN12_20261106_PLAN.md');c['staged_90_then12_20261106']=dict(authorization='RPCCR_STAGED_90_THEN12_AUTHORIZATION_20261106.json',ledger=str((ROOT/'LEDGER.json').relative_to(R)),stage1_absolute_deadline_unix=deadline,closed=False,stage2_started=window['stage2_started']);dump(R/'CURRENT_EXPERIMENT.json',c);ledger.update(status=phase,active_simulation=True);dump(ROOT/'LEDGER.json',ledger)
try:
 unchanged();assert read(ROOT/'ZERO_MODEL_QUALIFICATION.json')['passed']and time.time()+500<deadline
 with(R/'runs/v648_static_unknown/execution.lock').open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(ROOT/'inhibitor.console').open('x')as f:inhibitor=subprocess.Popen(['systemd-inhibit','--what=sleep:idle','--mode=block','--who=Phase','--why=Bounded pilot and conditional12h offline development',sys.executable,'-B',str(C/'hold_awake.py'),'--pid',str(os.getpid()),'--deadline',str(deadline+43200+14400)],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 time.sleep(.5);assert inhibitor.poll()is None,'SLEEP_INHIBITOR_UNAVAILABLE'
 dump(ROOT/'INHIBITOR.json',dict(pid=inhibitor.pid,campaign_pid=os.getpid(),os_only_deadline=deadline+43200+14400,extends_model_deadlines=False))
 current('RUNNING_V842_PILOT90');ledger.update(stage1_started=True);dump(ROOT/'LEDGER.json',ledger);first=stage_run('pilot90',deadline);dump(ROOT/'PILOT_FINAL.json',first)
 if not can_transition(first):status='STOPPED_PILOT_NOT_PASSED_NO12H';raise StopIteration
 # Exactly one independent12h clock, written only after the pilot FINALIZED/SHA gate.
 references={str(p.relative_to(R)):sha(p)for d in[O/'pilot_main02',O/'pilot90']for p in d.rglob('*')if p.is_file()and p.suffix not in['.pyc','.lock']and '__pycache__'not in p.parts};dump(ROOT/'PILOT_REFERENCE_FREEZE.json',dict(files=references,pilot_archive=first['archive']))
 start12=time.time();deadline12=start12+43200
 with(ROOT/'DEVELOPMENT12_WINDOW_CLAIM.json').open('x')as f:json.dump(dict(started_unix=start12,absolute_deadline_unix=deadline12,pilot_finalized_sha256=sha(O/'pilot90/FINALIZED.json'),pilot_archive=first['archive'],reference_freeze_sha256=sha(ROOT/'PILOT_REFERENCE_FREEZE.json'),launch_attempts=1),f,indent=2)
 window.update(stage2_started=True,stage2_started_unix=start12,stage2_absolute_deadline_unix=deadline12);dump(ROOT/'ROUND_WINDOW.json',window);current('RUNNING_V842_CONDITIONAL12H');ledger.update(stage2_started=True);dump(ROOT/'LEDGER.json',ledger);second=stage_run('development12',deadline12,first);dump(ROOT/'DEVELOPMENT12_FINAL.json',second);status='TWO_OLD_FAILURES_AND_COMPLETE_REPEATS_PASS'if can_transition(second)else'STOPPED12H_DEVELOPMENT_NOT_PASSED'
except StopIteration:pass
except BaseException as e:status='STOPPED_EXCEPTION';dump(ROOT/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
finally:
 (R/'REVIEW_PENDING').write_bytes(guard)
 if inhibitor is not None and inhibitor.poll()is None:
  os.killpg(inhibitor.pid,signal.SIGTERM)
  try:inhibitor.wait(timeout=3)
  except subprocess.TimeoutExpired:os.killpg(inhibitor.pid,signal.SIGKILL);inhibitor.wait()
 dump(ROOT/'INHIBITOR_END.json',dict(pid=None if inhibitor is None else inhibitor.pid,returncode=None if inhibitor is None else inhibitor.returncode,scope='bounded housekeeping only'))
 summary=dict(status=status,pilot=first,conditional12=second,stage2_started=window['stage2_started'],new24=0,scientific_revisions=0,training=0,network_calls=0,stage_access=0,automatic_restart=False,old_failures_and_deadlines_preserved=True)
 dump(ROOT/'COMPLETION.json',summary);window.update(round_closed=True,status=status,elapsed_s=time.time()-window['started_unix']);dump(ROOT/'ROUND_WINDOW.json',window);ledger.update(status=status,closed=True,active_simulation=False,no_more_models_or_integrations=True);dump(ROOT/'LEDGER.json',ledger)
 c=read(R/'CURRENT_EXPERIMENT.json');c.update(status='REVIEW_PENDING',state='REVIEW_PENDING',active_run=None,active_entrypoint=None,active_pid=None,execution_window_closed=True,requires_user_review_before_next_experiment=True,report='docs/RPCCR_STAGED_90_THEN12_20261106_REPORT.md');c.setdefault('staged_90_then12_20261106',{}).update(closed=True,status=status,stage2_started=window['stage2_started']);dump(R/'CURRENT_EXPERIMENT.json',c)
 report=R/'docs/RPCCR_STAGED_90_THEN12_20261106_REPORT.md';report.write_text('# 90分钟先导与条件12小时开发实际报告\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n各阶段独立审核中的导航/私有/完整重放为准确或未知账目；内部初始化次数未知。先导主、完整重复、第二旧失败主、条件重复、新24未执行分别记账。算法V841不变，原全部安全/因果/控制门保持。旧失败与原件保持，REVIEW_PENDING原字节恢复。不自动三路线、新24、对照或训练；闭批不延长重跑。\n')
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- STAGED_90_THEN12_20261106 CLOSED '+status+'；12小时实际启动='+str(window['stage2_started'])+'。报告docs/RPCCR_STAGED_90_THEN12_20261106_REPORT.md，旧失败/原截止保持；无自动新24或下一候选。\n')
 print(json.dumps(summary),flush=True)
 try:
  target=R/'evidence/rpccr_staged_90_then12_ops_20261106';assert not target.exists();target.mkdir();files={p for p in ROOT.rglob('*')if p.is_file()and not p.is_symlink()and p.suffix not in['.lock','.pyc']and '__pycache__'not in p.parts};files.update([R/'CURRENT_EXPERIMENT.json',report,R/'RPCCR_STAGED_90_THEN12_AUTHORIZATION_20261106.json'])
  for s in ['pilot90','development12']:
   for n in ['finalize.console','transport.console','FINALIZED.json','FINAL_INDEPENDENT_AUDIT.json']:
    p=O/s/n
    if p.exists():files.add(p)
  inventory=[]
  with zipfile.ZipFile(target/'OPERATIONS_SNAPSHOT.zip','x',compression=zipfile.ZIP_DEFLATED)as z:
   for p in sorted(files):
    b=p.read_bytes();name=str(p.relative_to(R));z.writestr(name,b);inventory.append(dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
  with zipfile.ZipFile(target/'OPERATIONS_SNAPSHOT.zip')as z:
   for x in inventory:
    b=z.read(x['path']);assert len(b)==x['bytes']and hashlib.sha256(b).hexdigest()==x['sha256']
  dump(target/'MANIFEST.json',dict(status='OPERATIONS_SNAPSHOT_DECOMPRESSED_SHA_VERIFIED',inventory=inventory,new_models=0,new_integrations=0,raw_deleted=False));dump(ROOT/'CLOSED_OPERATIONS_ARCHIVE.json',dict(archive=str(target.relative_to(R)),sources=len(inventory),source_snapshot_SHA_verified=True))
 except BaseException as e:dump(ROOT/'CLOSURE_ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
