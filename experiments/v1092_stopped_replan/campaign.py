"""Configured fresh navigation root, full audit and conditional exact repeat."""
import sys,json,time,os,fcntl,signal,subprocess,hashlib,traceback,gzip
from pathlib import Path
CORE=Path(__file__).resolve().parent;R=CORE.parents[1];sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def same_complete(a,b):
 import numpy as np
 x=np.load(Path(a['output'])/'physics/NATIVE_TRACE.npz');y=np.load(Path(b['output'])/'physics/NATIVE_TRACE.npz');error=0.
 for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
  assert x[k].shape==y[k].shape;error=max(error,float(abs(x[k]-y[k]).max())if x[k].size else 0.)
 sa=json.loads((Path(a['output'])/'physics/SETUP.json').read_text());sb=json.loads((Path(b['output'])/'physics/SETUP.json').read_text());assert sa['model_sha256']==sb['model_sha256'];assert np.array_equal(np.load(Path(a['output'])/'physics/INITIAL_STATE.npz')['state'],np.load(Path(b['output'])/'physics/INITIAL_STATE.npz')['state']);assert error<=1e-8
 ra=json.loads((Path(a['output'])/'RESULT.json').read_text())if(Path(a['output'])/'RESULT.json').exists()else json.loads((Path(a['output'])/'physics/paired/ENTRY_FAILURE_RESULT.json').read_text());rb=json.loads((Path(b['output'])/'RESULT.json').read_text())if(Path(b['output'])/'RESULT.json').exists()else json.loads((Path(b['output'])/'physics/paired/ENTRY_FAILURE_RESULT.json').read_text());assert ra['physical']['first_actor_detection']==rb['physical']['first_actor_detection']
 with gzip.open(Path(a['output'])/'physics/CONTACTS.json.gz','rt')as f:ac=json.load(f)
 with gzip.open(Path(b['output'])/'physics/CONTACTS.json.gz','rt')as f:bc=json.load(f)
 assert len(ac)==len(bc)and all(len(x)==len(y)and all(list(i[:3])==list(j[:3])and abs(i[3]-j[3])<=1e-8 for i,j in zip(x,y))for x,y in zip(ac,bc));return dict(passed=True,maximum_state_ctrl_mocap_error=error,complete_length=len(x['qpos']))
def main():
 assert len(sys.argv)==2 and Path(sys.argv[1]).is_absolute();cfg=json.loads(Path(sys.argv[1]).read_text());O=Path(cfg['run_root']);C=Path(cfg['batch_source']);guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert json.loads((O/'QUALIFICATION.json').read_text())['passed']and json.loads((O/'REGRESSION.json').read_text())['passed'];freeze=json.loads(Path(cfg['source_freeze']).read_text())['files'];assert all(sha(R/p)==h for p,h in freeze.items());own=(O/'driver.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not(O/'ROUND_WINDOW.json').exists();wall=time.time();mono=time.monotonic();w=dict(started_unix=wall,started_monotonic=mono,absolute_deadline_unix=wall+5400,hard_stop_monotonic=mono+5400,duration_s=5400,old_windows_unchanged=True,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip());dump(O/'ROUND_WINDOW.json',w);tasks=json.loads(Path(cfg['task_table']).read_text());dump(O/'APPROVAL.json',dict(models_authorized=True,absolute_deadline_unix=w['absolute_deadline_unix'],allowed_task_ids=[t['task_id']for t in tasks]));(O/'GUARD.bin').write_bytes(guard);rows=[];attempted=[];error=None;child=None;repeat=None
 def halt(*_):raise TimeoutError('ROOT_HARD_DEADLINE_OR_STOP')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,5400)
 try:
  for task in tasks:
   seen=set();temporary_bytes=0
   for base,dirs,names in os.walk(R/'runs',followlinks=False):
    dirs[:]=[d for d in dirs if not Path(base,d).is_symlink()]
    for name in names:
     p=Path(base,name)
     if not p.is_symlink():
      st=p.stat();identity=(st.st_dev,st.st_ino)
      if identity not in seen:temporary_bytes+=st.st_size;seen.add(identity)
   assert temporary_bytes+128*1024**2<=2*1024**3,'TEMPORARY_BUDGET'
   assert min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())>2150;assert(R/'REVIEW_PENDING').read_bytes()==guard;assert not Path(task['output']).exists();path=O/(task['task_id']+'.json');dump(path,task);attempted.append(task['task_id']);dump(O/'ATTEMPTS.json',attempted);(R/'REVIEW_PENDING').unlink()
   try:
    with(O/(task['task_id']+'.console')).open('x')as log:child=subprocess.Popen([str(R/'run_phase.sh'),str((CORE/cfg['worker']).relative_to(R)),str(path)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'ACTIVE.json',dict(pid=child.pid,task_id=task['task_id']));code=child.wait(timeout=1205)
   finally:
    if child is not None and child.poll()is None:
     try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=3)
     except BaseException:
      try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
      except ProcessLookupError:pass
    child=None;(R/'REVIEW_PENDING').write_bytes(guard)
   out=Path(task['output']);rp=out/'RESULT.json';rp=rp if rp.exists()else out/'physics/paired/ENTRY_FAILURE_RESULT.json';result=json.loads(rp.read_text())if rp.exists()else dict(passed=False,missing_result=True);row=dict(task=task,result=result,returncode=code);rows.append(row);dump(O/'RESULTS.json',rows);assert code==0 and result['passed'],'FIRST_FUNCTIONAL_OR_SAFETY_FAILURE'
   a=subprocess.run([sys.executable,'-B',str(CORE/cfg['audit']),str(path)],cwd=R,capture_output=True,text=True,timeout=cfg['audit_timeout_s']);(O/(task['task_id']+'.audit.console')).write_text(a.stdout+a.stderr);assert a.returncode==0,'FIRST_INDEPENDENT_EVIDENCE_FAILURE';row['audit']=json.loads((out/'FINAL_INDEPENDENT_AUDIT.json').read_text());dump(O/'RESULTS.json',rows)
  assert all(sha(R/p)==h for p,h in freeze.items()),'FROZEN_SOURCE_CHANGED'
  repeat=same_complete(tasks[0],tasks[1])
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
 finally:
  (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True));signal.setitimer(signal.ITIMER_REAL,0)
 passed=error is None and len(rows)==2 and all(x.get('audit',{}).get('passed')for x in rows)and repeat['passed'];summary=dict(closed=True,passed=passed,version=cfg['version'],scope='Fresh canonical WE navigation main plus conditional full repeat; eight stopped finite episodes maximum',attempted=attempted,unexecuted=[t['task_id']for t in tasks if t['task_id']not in attempted],error=error,complete_repeat=repeat,counts={k:sum(x['result'][k]for x in rows)if all(x['result'].get(k)is not None for x in rows)else None for k in ['vehicle_initializations','historical_replay_native','new_actual_native','own_replay_native','replay_state_initializations','private_mujoco_native','training_updates','analytical_prediction_native']},guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,source_unchanged=all(sha(R/p)==h for p,h in freeze.items()),whole_route_passed=passed,new24_executed=False);dump(O/'COMPLETION.json',summary);print(json.dumps(summary),flush=True);x=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());x.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_completed=summary,latest_report=cfg['report']);dump(R/'CURRENT_EXPERIMENT.json',x);(R/cfg['report']).write_text('# Fresh canonical WE stopped finite-replan validation\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\nThis is one observed WE developmental route from canonical t0, not three-route or24 confirmation. Empirical speed envelope is conditional, not global recursive safety.\n');
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- FINAL '+cfg['version']+' fresh WE navigation: passed='+str(passed)+'; counts='+json.dumps(summary['counts'])+'; single WE main+repeat gate only; three-route/24 not executed. See '+cfg['report']+'.\n')
 try:
  with(O/'closure.console').open('x')as log:q=subprocess.run([sys.executable,'-B',str(C/'finalize.py'),str(O/'CONFIG.json')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=180)
  dump(O/'ARCHIVE_RESULT.json',dict(returncode=q.returncode,models=0,raw_retained=True))
 except BaseException as e:dump(O/'ARCHIVE_RESULT.json',dict(error=repr(e),models=0,raw_retained=True))
if __name__=='__main__':main()
