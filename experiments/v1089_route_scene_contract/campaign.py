"""Offline, fixed overnight development gate then locked confirmation; no tuning."""
import sys,os,json,time,signal,subprocess,hashlib,fcntl,traceback,datetime
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];CORE=R/'experiments/rpccr_execution_core'
sys.path.insert(0,str(CORE));from fresh_campaign import same_complete
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def used():
 seen=set();total=0
 for base,dirs,names in os.walk(R/'runs',followlinks=False):
  dirs[:]=[d for d in dirs if not Path(base,d).is_symlink()]
  for name in names:
   p=Path(base,name)
   if not p.is_symlink():
    st=p.stat();key=st.st_dev,st.st_ino
    if key not in seen:seen.add(key);total+=st.st_size
 return total
def main():
 cfg=json.loads(Path(sys.argv[1]).read_text());O=Path(cfg['run_root']);guard=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert json.loads((O/'QUALIFICATION.json').read_text())['passed'];authority=json.loads((O/'AUTHORIZATION.json').read_text());assert authority['models_authorized']and authority['temporary_limit_bytes']==8*1024**3
 freeze=json.loads(Path(cfg['source_freeze']).read_text())['files'];assert all(sha(R/p)==h for p,h in freeze.items());tasks=json.loads(Path(cfg['task_table']).read_text());assert len(tasks)==55
 assert json.loads((R/'runs/v1087_ns_repeat_after_shutdown/COMPLETION.json').read_text())['passed']and json.loads((R/'records/nav2_v1087_20261112/REMOTE_VERIFIED.json').read_text())['passed']
 own=(O/'driver.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(R/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(O/'ROUND_WINDOW.json').exists();end=authority['absolute_deadline_unix'];now=time.time();assert end>now+2000;boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();window=dict(started_unix=now,started_monotonic=time.monotonic(),absolute_deadline_unix=end,hard_stop_monotonic=time.monotonic()+end-now,boot_id=boot,old_windows_unchanged=True)
 dump(O/'ROUND_WINDOW.json',window);(O/'GUARD.bin').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=True,absolute_deadline_unix=end,allowed_task_ids=[t['task_id']for t in tasks]));rows=[];attempted=[];pairs=[];error=None;child=None;development=False;confirmed=False
 def remaining():
  assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot,'CROSS_BOOT_AUTHORITY_REJECTED'
  return min(end-time.time(),window['hard_stop_monotonic']-time.monotonic())
 def halt(*_):raise TimeoutError('FIXED_NIGHT_DEADLINE_OR_STOP')
 def stop_child():
  nonlocal child
  if child is not None and child.poll()is None:
   try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=3)
   except BaseException:
    try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
    except ProcessLookupError:pass
  child=None
 def run(task):
  nonlocal child
  assert remaining()>(130 if task['kind']=='t0'else 1850),'INSUFFICIENT_COMPLETE_TASK_AND_AUDIT_TIME'
  assert used()+128*1024**2<=authority['temporary_limit_bytes'],'TEMPORARY8GIB_STOP'
  assert all(sha(R/p)==h for p,h in freeze.items()),'SOURCE_CHANGED';out=Path(task['output']);assert not out.exists();path=O/(task['task_id']+'.json');dump(path,task);attempted.append(task['task_id']);dump(O/'ATTEMPTS.json',attempted)
  assert(R/'REVIEW_PENDING').read_bytes()==guard;(R/'REVIEW_PENDING').unlink()
  try:
   with(O/(task['task_id']+'.console')).open('x')as f:
    script=C/('t0.py'if task['kind']=='t0'else'worker.py');child=subprocess.Popen([str(R/'run_phase.sh'),str(script.relative_to(R)),str(path)],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'ACTIVE.json',dict(pid=child.pid,starttime=Path('/proc/'+str(child.pid)+'/stat').read_text().split()[21],task_id=task['task_id'],stage='t0'if task['kind']=='t0'else'navigation'));code=child.wait(timeout=min(100 if task['kind']=='t0'else 905,remaining()-10))
  finally:stop_child();(R/'REVIEW_PENDING').write_bytes(guard)
  rp=out/'RESULT.json';rp=rp if rp.exists()else out/'physics/paired/ENTRY_FAILURE_RESULT.json';result=json.loads(rp.read_text())if rp.exists()else dict(passed=False,missing_result=True);row=dict(task=task,result=result,returncode=code);rows.append(row);dump(O/'RESULTS.json',rows);assert code==0 and result['passed'],'FIRST_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE'
  if task['kind']=='t0':return row
  if task.get('stage')=='confirmation':
   import numpy as np
   pre=next(t for t in tasks if t['task_id']==task['preflight_task_id']);pp=Path(pre['output'])/'physics';npth=out/'physics';assert json.loads((pp/'SETUP.json').read_text())['model_sha256']==json.loads((npth/'SETUP.json').read_text())['model_sha256'];assert np.array_equal(np.load(pp/'INITIAL_STATE.npz')['state'],np.load(npth/'INITIAL_STATE.npz')['state']),'T0_MAIN_INITIAL_STATE_MISMATCH'
  with(O/(task['task_id']+'.audit.console')).open('x')as f:
   child=subprocess.Popen([sys.executable,'-B',str(C/'audit.py'),str(path)],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'ACTIVE.json',dict(pid=child.pid,starttime=Path('/proc/'+str(child.pid)+'/stat').read_text().split()[21],task_id=task['task_id'],stage='zero_model_full_audit'));code=child.wait(timeout=min(900,remaining()-10))
  stop_child();assert code==0,'FIRST_INDEPENDENT_EVIDENCE_FAILURE';row['audit']=json.loads((out/'FINAL_INDEPENDENT_AUDIT.json').read_text());assert row['audit']['passed'];dump(O/'RESULTS.json',rows)
  if task['kind']=='repeat':
   base=next(t for t in tasks if t['task_id']==task['repeat_of']);pair=dict(task_id=task['task_id'],**same_complete(base,task));pairs.append(pair);dump(O/'COMPLETE_REPEATS.json',pairs)
  return row
 signal.signal(signal.SIGALRM,halt);signal.signal(signal.SIGTERM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining()))
 try:
  for task in tasks[:4]:run(task)
  development=all(r['audit']['passed']for r in rows)and len(pairs)==2;assert development
  dump(O/'THREE_ROUTE_GATE.json',dict(passed=True,science='same V1085_entry/V1087',NS_main_reused_readonly='v1085_entry',NS_repeat='v1087',remaining_two_pairs=pairs,EW_declared_start=[4.,-1.9],not_original_EW_start=True,new24_denominator_includes_development=False))
  # Archive development gate before consuming any confirmation model.
  dump(O/'DEVELOPMENT_AUDIT.json',dict(passed=True,all_four_full_audits=True,repeat_pairs=pairs,NS_original_failed_batch_preserved=True))
  spec=__import__('importlib.util',fromlist=['']).spec_from_file_location('development_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');arc=__import__('importlib.util',fromlist=['']).module_from_spec(spec);spec.loader.exec_module(arc)
  files=[p for t in tasks[:4]for p in arc.walk(t['output'])if not any(x in p.parts for x in ['cache','frozen_original'])]
  files.extend([O/'THREE_ROUTE_GATE.json',O/'DEVELOPMENT_AUDIT.json',C/'TASKS.json',C/'SOURCE_FREEZE.json'])
  baseline=used();target=O/'development_cloud'
  record,inventory=arc.package(R,files,target,'v1089-development',budget_check=lambda:baseline+sum(p.stat().st_size for p in target.glob('*')if p.is_file())+1024**2<=authority['temporary_limit_bytes'])
  dump(O/'DEVELOPMENT_FINALIZED.json',dict(passed=True,all_source_decompressed_sha_verified=True,parts_reassembled_sha_verified=True,archive=record,source_members=len(inventory),models=0,integrations=0))
  # Full task worst-case budget is reserved; otherwise the fixed pool stays unexecuted.
  # Observed per-task qualification envelope is less than the hard caps; use registered
  # 24t0 + 24main +3repeat at 1100s each including audit, with per-task hard caps unchanged.
  required=24*100+27*1100+180
  assert remaining()>=required,'INSUFFICIENT_FIXED_CONFIRMATION_WINDOW'
  for task in tasks[4:28]:run(task)
  for task in tasks[28:52]:run(task)
  mains=[r for r in rows if r['task'].get('stage')=='confirmation'and r['task']['kind']=='main'];assert len(mains)==24
  assert len({r['task']['seed']for r in mains})==24 and all(r['result']['passed']and r['audit']['passed']for r in mains)
  for task in tasks[52:]:run(task)
  confirmed=len(pairs)==5 and all(p['passed']for p in pairs)
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
 finally:
  stop_child();(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True));dump(O/'AUTHORIZATION.json',dict(models_authorized=False,closed=True,original_deadline_unix=end,no_extension=True));signal.setitimer(signal.ITIMER_REAL,0)
 keys=['vehicle_initializations','historical_replay_native','new_actual_native','own_replay_native','replay_state_initializations','private_mujoco_native','training_updates','analytical_prediction_native']
 def counts(selected):return {k:sum(r['result'][k]for r in selected)if all(r['result'].get(k)is not None for r in selected)else None for k in keys}
 confirmation_mains=[r for r in rows if r['task'].get('stage')=='confirmation'and r['task']['kind']=='main'];full_pool=len(confirmation_mains)==24
 unchanged=all(sha(R/p)==h for p,h in freeze.items());summary=dict(closed=True,passed=development and confirmed and unchanged and error is None,version='v1089',three_route_development_passed=development,confirmation_passed=confirmed and unchanged,error=error,attempted=attempted,unexecuted=[t['task_id']for t in tasks if t['task_id']not in attempted],complete_repeats=pairs,counts=counts(rows),development_counts=counts([r for r in rows if r['task'].get('stage')=='development']),confirmation_t0_counts=counts([r for r in rows if r['task']['kind']=='t0']),confirmation_main_counts=counts(confirmation_mains),confirmation_repeat_counts=counts([r for r in rows if r['task'].get('stage')=='confirmation'and r['task']['kind']=='repeat']),confirmation_mains_executed=len(confirmation_mains),full24_denominator_reportable=full_pool,source_unchanged=unchanged,guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,old_NS_main_and_repeat_preserved=True,lockstep_not_realtime=True,raw_retained=True)
 dump(O/'COMPLETION.json',summary);(R/cfg['report']).write_text('# V1089 overnight route validation and conditional confirmation\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\nEW uses declared north-shifted start. Partial confirmation never reported as a full24 success rate. Source/model/control gates retained; no realtime or hardware claim.\n')
 x=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());x.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_completed=summary,latest_report=cfg['report'],next_scope='Review closed overnight result; no automatic new model');dump(R/'CURRENT_EXPERIMENT.json',x)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- FINAL V1089 overnight: development='+str(development)+' confirmation='+str(confirmed)+'; '+json.dumps(summary['counts'])+'; old failures preserved. See '+cfg['report']+'.\n')
 print(json.dumps(summary),flush=True)
 try:
  with(O/'finalize.console').open('x')as log:p=subprocess.run([sys.executable,'-B',str(C/'finalize.py'),str(O/'CONFIG.json')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=300)
  dump(O/'ARCHIVE_RESULT.json',dict(returncode=p.returncode,models=0,raw_retained=True))
 except BaseException as e:dump(O/'ARCHIVE_RESULT.json',dict(error=repr(e),models=0,raw_retained=True))
if __name__=='__main__':main()
