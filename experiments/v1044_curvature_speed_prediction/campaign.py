"""Unattended fixed three-response campaign; first failure stops all dependents."""
import hashlib,importlib.util,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1044_curvature_speed_prediction'
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def permitted(rows):return all(row['passed']for row in rows)
def main():
 assert not(O/'CAMPAIGN_CLAIM.json').exists();dump(O/'CAMPAIGN_CLAIM.json',dict(pid=os.getpid(),started=time.time()));end=json.loads((O/'ROUND_WINDOW.json').read_text())['absolute_deadline_unix'];guard=(R/'REVIEW_PENDING').read_bytes();rows=[];error=None;child=None
 spec=importlib.util.spec_from_file_location('v1044_exact_saved_audit',C/'audit.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);audit=module.audit
 tasks=json.loads((C/'TASKS.json').read_text())
 try:
  for task in tasks:
   assert permitted(rows),'FIRST_FAILURE_STOP';assert time.time()<end-400,'ROOT_RESERVE'
   rp=O/(task['task_id']+'.AUTHORIZATION.json');dump(rp,dict(task_id=task['task_id'],window_sha256=sha(O/'ROUND_WINDOW.json'),source_sha256=sha(C/'SOURCE_FREEZE.json')))
   with (O/(task['task_id']+'.console')).open('x')as log:
    (R/'REVIEW_PENDING').unlink()
    try:
     child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(C/('TASK_'+task['task_id']+'.json')),str(rp)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
     dump(O/'ACTIVE.json',dict(task_id=task['task_id'],pid=child.pid,deadline=min(end,time.time()+330)));child.wait(timeout=min(330,end-time.time()))
    finally:(R/'REVIEW_PENDING').write_bytes(guard)
   result_path=Path(task['output'])/'RESULT.json';result=json.loads(result_path.read_text())if result_path.exists()else dict(passed=False,error='MISSING_WORKER_RESULT',model_initializations=None,navigation_native=None,own_replay_native=None,private_mujoco_native=0)
   try:proof=audit(task,save=True)if result.get('evidence_saved')and result.get('navigation_native')==500 else dict(passed=False,error='INCOMPLETE_RESPONSE')
   except BaseException as e:proof=dict(passed=False,error=repr(e),traceback=traceback.format_exc())
   rows.append(dict(task_id=task['task_id'],passed=child.returncode==0 and result['passed']and proof['passed'],result=result,audit=proof));dump(O/'RESULTS.json',rows)
   assert rows[-1]['passed'],'FIRST_FAILURE_STOP '+task['task_id']
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  if child is not None and child.poll()is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(5)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(5)
  (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
  done=dict(closed=True,passed=error is None and len(rows)==3 and permitted(rows),rows=rows,error=error,unexecuted=[t['task_id']for t in tasks if t['task_id']not in [r['task_id']for r in rows]],guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,closed_unix=time.time(),absolute_deadline_unix=end,navigation_acceptance=False)
  dump(O/'COMPLETION.json',done);print(json.dumps({k:v for k,v in done.items()if k!='rows'}),flush=True)
 return 0 if done['passed']else 1
if __name__=='__main__':sys.exit(main())
