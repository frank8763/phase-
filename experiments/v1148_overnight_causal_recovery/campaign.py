"""Frozen finite overnight queue; physical pair gates all recovery source jobs."""
from night_tools import *
import signal,subprocess,fcntl,traceback,gzip
import numpy as np

def repeat_check(first,second):
 a=Path(first);b=Path(second);x=np.load(a/'physics/NATIVE_TRACE.npz');y=np.load(b/'physics/NATIVE_TRACE.npz');same=all(x[k].shape==y[k].shape for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']);error=max(float(abs(x[k]-y[k]).max())if x[k].size else 0. for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat'])if same else None
 exact={name:json.loads(gzip.open(a/'physics'/name,'rt').read())==json.loads(gzip.open(b/'physics'/name,'rt').read())for name in ['CONTACTS.json.gz','SENSORS.json.gz']};model=sha(a/'physics/scene_model.mjb')==sha(b/'physics/scene_model.mjb');initial=sha(a/'physics/INITIAL_STATE.npz')==sha(b/'physics/INITIAL_STATE.npz');checkpoints=np.array_equal(np.load(a/'CHECKPOINT_INTEGRATION.npz')['state'],np.load(b/'CHECKPOINT_INTEGRATION.npz')['state']);ra=json.loads((a/'RESULT.json').read_text());rb=json.loads((b/'RESULT.json').read_text());discovery=ra['physical']['first_actor_detection']==rb['physical']['first_actor_detection']
 return dict(passed=bool(same and error<=1e-8 and all(exact.values())and model and initial and checkpoints and discovery),same_complete_lengths=same,maximum_qpos_qvel_ctrl_mocap_error=error,contacts_and_sensors=exact,model=model,initial=initial,full_checkpoint_state_identical=checkpoints,actual_discovery_identical=discovery)

def main():
 assert not(O/'DRIVER_STARTED.json').exists()and source_ok();guard=(O/'GUARD.bin').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD_SHA
 lock=(O/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);dump(O/'DRIVER_STARTED.json',dict(pid=os.getpid(),proc_start=Path('/proc/self/stat').read_text().split()[21]));rows=[];child=None;reason='FINITE_QUEUE_COMPLETE';error=None;pair=None;pair_pass=False;winner=None
 def stop():
  nonlocal child
  if child and child.poll()is None:
   try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
   except BaseException:
    try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
    except ProcessLookupError:pass
  child=None
 def halt(*_):raise TimeoutError('OVERNIGHT_ABSOLUTE_0900_STOP')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining()-5))
 def job(name,script,args,limit,physical=False):
  nonlocal child
  assert source_ok()and used()+128*1024**2<2*1024**3,'SOURCE_OR_STORAGE_CHANGED';assert remaining()>limit+60,'INSUFFICIENT_ROOT_REMAINDER';assert(R/'REVIEW_PENDING').read_bytes()==guard
  if physical:(R/'REVIEW_PENDING').unlink()
  command=[str(R/'run_phase.sh'),str((C/script).relative_to(R)),*map(str,args)]if physical else[sys.executable,'-B',str(C/script),*map(str,args)]
  try:
   with(O/(name+'.console')).open('x')as log:
    child=subprocess.Popen(command,cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'ACTIVE.json',dict(stage=name,pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],physical=physical));code=child.wait(timeout=min(limit,remaining()-30))
  finally:stop();(R/'REVIEW_PENDING').write_bytes(guard)
  return code
 try:
  assert all(json.loads((O/name).read_text())['passed']for name in ['QUALIFICATION.json','ISOLATED_QUALIFICATION.json','SOFTWARE_ENTRY_QUALIFIED.json'])
  tasks=json.loads((C/'TASKS.json').read_text())
  for task in tasks:
   if remaining()<7400:reason='PHYSICAL_ROOT_TIME_RESERVE';return
   code=job(task['task_id'],'component_worker.py',[C/('TASK_'+task['task_id']+'.json')],7300,True);path=Path(task['output'])/'RESULT.json';r=json.loads(path.read_text())if path.exists()else None;row=dict(stage=task['task_id'],returncode=code,result=r);rows.append(row);dump(O/'RESULTS.json',rows)
   if code!=0 or not r or not r['passed']:reason='FIRST_PHYSICAL_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE';return
   acode=job(task['task_id']+'_audit','component_audit.py',[C/('TASK_'+task['task_id']+'.json')],75);path=Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json';row['audit']=json.loads(path.read_text())if path.exists()else None;row['audit_returncode']=acode;dump(O/'RESULTS.json',rows)
   if acode!=0 or not row['audit']or not row['audit']['passed']:reason='INDEPENDENT_PHYSICAL_AUDIT_FAILURE';return
  pair=repeat_check(tasks[0]['output'],tasks[1]['output']);dump(O/'COMPLETE_REPEAT.json',pair);assert pair['passed'],'COMPLETE_PHYSICAL_REPEAT_MISMATCH';pair_pass=True
  code=job('actual_source','post_actual.py',[],330);assert code==0 and json.loads((O/'actual_source/RESULT.json').read_text())['passed'],'ACTUAL_SOURCE_OR_DUAL_EVIDENCE_FAILURE'
  for profile in json.loads((C/'PROFILES.json').read_text()):
   if remaining()<180:reason='RECOVERY_ROOT_TIME_RESERVE';break
   # Subprocess enforces a shorter root-bound budget itself; there is no new clock.
   limit=min(3660,int(remaining()-90));code=job(profile['name'],'primitive_search.py',[C/('JOB_'+profile['name']+'.json')],limit);path=Path(profile['output'])/'RESULT.json';r=json.loads(path.read_text())if path.exists()else None;rows.append(dict(stage=profile['name'],returncode=code,result=r));dump(O/'RESULTS.json',rows)
   assert code==0 and r and r['error']is None,'RECOVERY_OPERATION_MODEL_OR_EVIDENCE_FAILURE'
   if r['passed']:
    assert remaining()>700,'SOURCE_AUDIT_ROOT_RESERVE'
    acode=job(profile['name']+'_independent_audit','source_audit.py',[C/('JOB_'+profile['name']+'.json')],630);apath=Path(profile['output'])/'FINAL_INDEPENDENT_AUDIT.json';independent=json.loads(apath.read_text())if apath.exists()else None;rows[-1]['independent_audit']=independent;dump(O/'RESULTS.json',rows)
    assert acode==0 and independent and independent['passed'],'SOURCE_INDEPENDENT_AUDIT_FAILURE'
    if winner is None:winner=dict(profile=profile['name'],output=profile['output'],result=r,independent_audit=independent)
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc());reason='EXCEPTION_OR_ROOT_DEADLINE';dump(O/'ERROR.json',error)
 finally:
  stop();(R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True))
  physical=[r for r in rows if r['stage']in ['component_main','component_repeat']];counts={k:sum(r['result'][k]for r in physical)if physical and all(r['result']and r['result'].get(k)is not None for r in physical)else None for k in ['models','new_actual_native','historical_reconstruction_native','new_component_native','own_replay_native']}
  result=dict(closed=True,physical_refresh_main_and_complete_repeat_passed=pair_pass,goal_software_qualified=winner is not None,winner=winner,stop_reason=reason,error=error,physical_counts=counts,stages=rows,complete_repeat=pair,unexecuted_physical=[t['task_id']for t in json.loads((C/'TASKS.json').read_text())if t['task_id']not in [r['stage']for r in rows]],unexecuted_software=[t['name']for t in json.loads((C/'PROFILES.json').read_text())if t['name']not in [r['stage']for r in rows]],original_goal_physical_passed=False,same_version_three_routes_passed=False,new24_executed=False,new24_denominator=None,guard_original=sha(R/'REVIEW_PENDING')==GUARD_SHA,source_unchanged=source_ok(),absolute_deadline_unix=json.loads((O/'ROUND_WINDOW.json').read_text())['absolute_deadline_unix'],closed_unix=time.time(),network_delivery_pending=True)
  dump(O/'COMPLETION.json',result);dump(O/'LEDGER.json',result);report=R/'docs/RPCCR_OVERNIGHT_CAUSAL_V1148_REPORT.md';report.write_text('# V1148通宵因果交接与时空恢复开发\n\n```json\n'+encode(result)+'```\n\n本轮主与完整重复仅为交接组件，不是整路。8固定软件分支均保留；不通过与未执行不混分母。新目标region选择保留原[4,-2]/.45和所有安全门，不能把自由终端姿态称为换目标。所有候选仍需完整停车后备。未启动物理目标/三路线/24、训练或实体机。旧失败和所有旧截止不改，全部物理仅run_phase CPU2低优先级，Stage隔离。必要原始记录远端SHA回读前不删除。\n')
  current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=str(report.relative_to(R)),latest_overnight_result=result);dump(R/'CURRENT_EXPERIMENT.json',current)
  with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V1148独立明早09截止闭批：physical_refresh_pair='+str(pair_pass)+', goal_software='+str(winner is not None)+', reason='+reason+', counts='+encode(counts).strip()+'；原goal物理/同版本三路线/24未执行，guard恢复，旧窗不改。docs/RPCCR_OVERNIGHT_CAUSAL_V1148_REPORT.md。\n')
  files=[]
  for root in [C,O,R/'runs/v858_nav2_verified/v1148']:
   if root.exists():
    for p in root.rglob('*'):
     if p.is_file()and not p.is_symlink()and p.name not in ['campaign.console','watchdog.console','LOCAL_MANIFEST.json']:files.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
  files.append(dict(path=str(report.relative_to(R)),bytes=report.stat().st_size,sha256=sha(report)));dump(O/'LOCAL_MANIFEST.json',dict(files=files,readback_verified=all(sha(R/p['path'])==p['sha256']for p in files),remote_verified=False,raw_retained=True));print(encode(result),flush=True)

if __name__=='__main__':main()
