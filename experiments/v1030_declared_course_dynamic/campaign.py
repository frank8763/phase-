"""Single bounded offline sequence; frozen source, never repairs/retries science."""
import hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
N=Path(__file__).resolve().parent;R=N.parents[1];C=N;O=R/'runs/v1030_declared_course_dynamic'

def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def select_next(rows,task):
    assert task['task_id']in ['dynamic_we','repeat_dynamic_we']
    return not rows or all(row['passed']for row in rows)

def repeat_check(first,second):
 import numpy as np
 b,r=Path(first),Path(second);setups=[json.loads((p/'physics/SETUP.json').read_text())for p in [b,r]]
 for setup in setups:
  actor=setup['actor'];certificate=actor['swept_envelope_reference'];certificate.pop('elapsed_s',None);certificate['search'].pop('wall_s',None)
 a=np.load(b/'physics/NATIVE_TRACE.npz');z=np.load(r/'physics/NATIVE_TRACE.npz');errors={}
 for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
  errors[key]=None if a[key].shape!=z[key].shape else float(abs(a[key]-z[key]).max())if a[key].size else 0.
 initials=[np.load(p/'physics/INITIAL_STATE.npz')['state']for p in [b,r]]
 discovery=[json.loads((p/'CAUSAL_EVIDENCE.json').read_text())['first']for p in [b,r]]
 return dict(passed=setups[0]==setups[1]and np.array_equal(initials[0],initials[1])and discovery[0]==discovery[1]and all(v is not None and v<=1e-8 for v in errors.values()),
  maximum_errors=errors,same_model_and_setup=setups[0]==setups[1],same_initial_state=bool(np.array_equal(initials[0],initials[1])),same_causal_discovery=discovery[0]==discovery[1])

def main():
 frozen=json.loads((N/'SOURCE_FREEZE.json').read_text());assert all(sha(R/name)==digest for name,digest in frozen['files'].items()),'ENTRY_SOURCE_CHANGED';window=json.loads((O/'ROUND_WINDOW.json').read_text());end=window['absolute_deadline_unix'];assert not(O/'CAMPAIGN_CLAIM.json').exists();dump(O/'CAMPAIGN_CLAIM.json',dict(pid=os.getpid(),started=time.time(),single_launch=True));guard=(R/'REVIEW_PENDING').read_bytes();rows=[];error=None;child=None
 try:
  sys.path.insert(0,str(C));from audit import audit
  tasks=json.loads((C/'TASKS.json').read_text())
  for task in tasks:
   if not select_next(rows,task):break
   assert time.time()<end-1300,'NO_COMPLETE_TASK_AND_REPLAY_RESERVE'
   assert sum(p.stat().st_size for p in (R/'runs/v858_nav2_verified/v1024').rglob('*')if p.is_file()and not p.is_symlink())<1536*1024**2,'TEMPORARY_CACHE_CAP'
   receipt=dict(task_id=task['task_id'],window_sha256=sha(O/'ROUND_WINDOW.json'),source_freeze_sha256=sha(C/'SOURCE_FREEZE.json'));rp=O/(task['task_id']+'.AUTHORIZATION.json');dump(rp,receipt)
   (R/'REVIEW_PENDING').unlink();log=(O/(task['task_id']+'.console')).open('x')
   try:
    child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(C/('TASKS_'+task['task_id']+'.json')),str(rp)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    dump(O/'ACTIVE.json',dict(task_id=task['task_id'],pid=child.pid,started_unix=time.time(),absolute_deadline_unix=end))
    until=min(end-30,time.time()+1230)
    while child.poll()is None:
     if time.time()>=until:
      os.killpg(child.pid,signal.SIGTERM)
      try:child.wait(10)
      except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(5)
      raise TimeoutError('TASK_OR_ROOT_ABSOLUTE_STOP')
     time.sleep(.25)
   finally:log.close();(R/'REVIEW_PENDING').write_bytes(guard)
   path=Path(task['output'])/'RESULT.json';result=json.loads(path.read_text())if path.exists()else dict(passed=False,navigation_native=None,own_replay_native=None,model_initializations=None,error='WORKER_DIED_WITHOUT_RESULT')
   try:proof=audit(task)if path.exists()and result.get('evidence_saved')else dict(passed=False,error='MISSING_SAVED_RESULT')
   except BaseException as error:proof=dict(passed=False,error=repr(error),original_audit_exception_preserved=True)
   passed=child.returncode==0 and result['passed']and proof['passed'];row=dict(task_id=task['task_id'],passed=passed,result=result,independent_audit=proof)
   if task['task_id']=='repeat_dynamic_we':row['repeat']=repeat_check(tasks[0]['output'],task['output']);row['passed']=row['passed']and row['repeat']['passed']
   rows.append(row);dump(O/'RESULTS.json',rows)
   if not row['passed']:raise AssertionError('FIRST_FAILURE_STOP '+task['task_id'])
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  if child is not None and child.poll()is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(10)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
  (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(R/'runs/v1030_declared_course_dynamic/APPROVAL.json',dict(models_authorized=False,closed=True))
  done=dict(closed=True,passed=error is None and len(rows)==2 and all(x['passed']for x in rows),rows=rows,error=error,unexecuted=[x['task_id']for x in json.loads((C/'TASKS.json').read_text())if x['task_id']not in [r['task_id']for r in rows]],guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,absolute_deadline_unix=end,closed_unix=time.time())
  dump(O/'COMPLETION.json',done);print(json.dumps(dict(closed=True,passed=done['passed'],error=error,unexecuted=done['unexecuted'])),flush=True)
  # All physical processes closed. Only bounded zero-model publication follows.
  try:
   subprocess.run([sys.executable,'-B',str(N/'close.py')],cwd=R,timeout=600,check=True)
  except BaseException as e:dump(O/'CLOSURE_PENDING.json',dict(error=repr(e),models_authorized=False,raw_retained=True))
 return 0 if done['passed']else 1
if __name__=='__main__':sys.exit(main())
