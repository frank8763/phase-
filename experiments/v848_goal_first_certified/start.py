"""One offline fixed-deadline night, three original routes, no conditional confirmation."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback,zipfile
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from common import *
from engine import Stage
lock=(ROOT/'campaign.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
with(ROOT/'LAUNCH_CLAIM.json').open('x')as out:json.dump(dict(pid=os.getpid(),started_unix=time.time(),attempts=1),out)
assert not(ROOT/'ROUND_WINDOW.json').exists()and not PHASE.exists(),'ONE_STAGE_NO_RETRY'
assert read(ROOT/'QUALIFICATION.json')['passed']and read(ROOT/'OPERATIONS_CHECK.json')['passed'];unchanged()
guard=(R/'REVIEW_PENDING').read_bytes();(ROOT/'REVIEW_PENDING.before').write_bytes(guard)
with(R/'runs/v648_static_unknown/execution.lock').open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert all(not(RAW/name).exists()for name in names())and all(not(RAW/f'v848_t0_slot{t["slot"]:02d}').exists()for t in tasks())
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});started=time.time();deadline=1794009600.;assert deadline-started>6500,'INSUFFICIENT_NIGHT_REMAINING';window=dict(started_unix=started,absolute_deadline_unix=deadline,round_closed=False,pid=os.getpid(),new24=0,old_deadlines_unchanged=True);dump(ROOT/'ROUND_WINDOW.json',window);dump(ROOT/'LEDGER.json',dict(status='STARTING',closed=False,active_simulation=False,new24=0,scientific_revisions=1))
inhibitor=None;final=None;status='STARTING';signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('CAMPAIGN_TERMINATED_NO_RETRY')))
try:
 with(ROOT/'inhibitor.console').open('x')as out:inhibitor=subprocess.Popen(['systemd-inhibit','--what=sleep:idle:handle-lid-switch','--mode=block','--who=Phase','--why=Bounded original three-route regression',sys.executable,'-B',str(C/'os_watch.py'),'--pid',str(os.getpid()),'--entrypoint',str(Path(__file__).resolve()),'--deadline',str(deadline+14400)],stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
 time.sleep(.5);assert inhibitor.poll()is None,'OS_INHIBITOR_FAILED_STOP'
 dump(ROOT/'INHIBITOR.json',dict(pid=inhibitor.pid,campaign_pid=os.getpid(),housekeeping_deadline=deadline+14400,absolute_model_deadline=deadline))
 current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_V848_THREE_ROUTE_REGRESSION',state='RUNNING_V848_THREE_ROUTE_REGRESSION',active_entrypoint=str((C/'start.py').relative_to(R)),active_pid=os.getpid(),active_run=str(PHASE.relative_to(R)),execution_window_closed=False,active_window=window,protocol=str((C/'PROTOCOL.md').relative_to(R)),decision_freeze=str((C/'CANDIDATE_FREEZE.json').relative_to(R)),source_revision='V848_GOAL_REFERENCE_AND_FIRST_CERTIFIED_NOMINAL',current_experiment='v848_goal_first_certified',report='docs/RPCCR_THREE_ROUTE_V848_20261106_PLAN.md');current['v848_goal_first_certified']=dict(authorization=str((ROOT/'AUTHORIZATION.json').relative_to(R)),ledger=str((ROOT/'LEDGER.json').relative_to(R)),closed=False,new24=0,absolute_deadline_unix=deadline);dump(R/'CURRENT_EXPERIMENT.json',current)
 dump(ROOT/'LEDGER.json',dict(status='RUNNING',closed=False,active_simulation=True,scientific_revisions=1,new24=0,model_deadline=deadline,new_navigation_max=6,true_t0_max=3))
 final=Stage(deadline).run();status='THREE_ROUTES_AND_THREE_COMPLETE_REPEATS_PASS'if final['combined_three_route_development_passed']and final['source_and_decompressed_sha_verified']else'STOPPED_THREE_ROUTE_REGRESSION_NOT_PASSED'
except BaseException as e:status='STOPPED_EXCEPTION';dump(ROOT/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
finally:
 (R/'REVIEW_PENDING').write_bytes(guard)
 if inhibitor is not None and inhibitor.poll()is None:
  os.killpg(inhibitor.pid,signal.SIGTERM)
  try:inhibitor.wait(timeout=3)
  except subprocess.TimeoutExpired:os.killpg(inhibitor.pid,signal.SIGKILL);inhibitor.wait()
 window.update(round_closed=True,status=status,closed_unix=time.time());dump(ROOT/'ROUND_WINDOW.json',window);dump(ROOT/'LEDGER.json',dict(status=status,closed=True,active_simulation=False,no_more_models_or_integrations=True,new24=0))
 summary=dict(status=status,stage=final,model_deadline_unix=deadline,scientific_revisions=1,new24=0,confirmation_requires_separate_user_instruction=True,training=0,network=0,Stage=0,automatic_restart=False,old_failures_and_deadlines_preserved=True);dump(ROOT/'COMPLETION.json',summary)
 current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',active_entrypoint=None,active_pid=None,active_run=None,active_window=None,execution_window_closed=True,requires_user_review_before_next_experiment=True,report='docs/RPCCR_THREE_ROUTE_V848_CAMPAIGN_20261106_REPORT.md');current.setdefault('v848_goal_first_certified',{}).update(closed=True,status=status);dump(R/'CURRENT_EXPERIMENT.json',current)
 report=R/'docs/RPCCR_THREE_ROUTE_V848_CAMPAIGN_20261106_REPORT.md';report.write_text('# V848三路线回归后台实际结果\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n用户明确只完成三路线，确认阶段另议。本轮不启动新24或其他实验；主/重复/失败/未执行和准确或未知原生私有重放见阶段独立终审。先前所有失败、源、窗口及归档保持。REVIEW_PENDING原字节恢复，后台停止。\n')
 with(R/'RESEARCH_STATUS.md').open('a')as out:out.write('\n- V848_THREE_ROUTE_REGRESSION CLOSED '+status+'；用户限定仅三路线，0新24，旧失败及截止保持，无自动后续实验。报告docs/RPCCR_THREE_ROUTE_V848_CAMPAIGN_20261106_REPORT.md。\n')
 print(json.dumps(summary),flush=True)
 try:
  target=R/'evidence/rpccr_three_route_v848_ops_20261106';target.mkdir(exist_ok=False);files={p for p in ROOT.rglob('*')if p.is_file()and not p.is_symlink()and p.suffix not in ['.lock','.pyc']and'__pycache__'not in p.parts and p.name not in ['campaign.console','night.console']and not p.is_relative_to(ROOT/'qualification')and not p.is_relative_to(PHASE)};files.update(p for p in C.iterdir()if p.is_file());files.update([report,R/'CURRENT_EXPERIMENT.json'])
  for name in ['finalize.console','transport.console','FINALIZED.json','FINAL_INDEPENDENT_AUDIT.json']:
   p=PHASE/name
   if p.exists():files.add(p)
  inventory=[]
  with zipfile.ZipFile(target/'OPERATIONS_SNAPSHOT.zip','x',compression=zipfile.ZIP_DEFLATED)as z:
   for p in sorted(files):
    data=p.read_bytes();name=str(p.relative_to(R));z.writestr(name,data);inventory.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
  with zipfile.ZipFile(target/'OPERATIONS_SNAPSHOT.zip')as z:
   for record in inventory:
    data=z.read(record['path']);assert len(data)==record['bytes']and hashlib.sha256(data).hexdigest()==record['sha256']
  dump(target/'MANIFEST.json',dict(status='OPERATIONS_SOURCE_AND_DECOMPRESSED_SHA_VERIFIED',inventory=inventory,new_models=0,new_integrations=0,raw_deleted=False));dump(ROOT/'CLOSED_OPERATIONS_ARCHIVE.json',dict(archive=str(target.relative_to(R)),source_snapshot_SHA_verified=True))
 except BaseException as e:dump(ROOT/'CLOSURE_ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
