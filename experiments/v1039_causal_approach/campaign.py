"""One frozen child, deadline, original guard restoration and no model retries."""
import hashlib,importlib.util,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1039_causal_approach'
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not(O/'CAMPAIGN_CLAIM.json').exists();dump(O/'CAMPAIGN_CLAIM.json',dict(pid=os.getpid(),started=time.time()));guard=(R/'REVIEW_PENDING').read_bytes();task=json.loads((C/'TASK.json').read_text());end=json.loads((O/'ROUND_WINDOW.json').read_text())['absolute_deadline_unix'];child=None;error=None;result={};proof={}
 rp=O/'TASK_AUTHORITY.json';dump(rp,dict(window_sha256=sha(O/'ROUND_WINDOW.json'),source_sha256=sha(C/'SOURCE_FREEZE.json')))
 try:
  assert time.time()<end-1200,'ROOT_RESERVE';(R/'REVIEW_PENDING').unlink()
  with (O/'worker.console').open('x')as log:
   child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(C/'TASK.json'),str(rp)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'ACTIVE.json',dict(pid=child.pid,started=time.time(),deadline=min(end,time.time()+930)));child.wait(timeout=min(930,end-time.time()))
  p=Path(task['output'])/'RESULT.json';result=json.loads(p.read_text())if p.exists()else dict(passed=False,model_initializations=None,historical_replay_native=None,new_component_native=None,own_replay_native=None,error='MISSING_WORKER_RESULT')
  if result.get('evidence_saved'):
   s=importlib.util.spec_from_file_location('v1039_exact_independent_audit',C/'audit.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);proof=m.audit(task,save=True)
  assert child.returncode==0 and result.get('passed')and proof.get('passed'),'COMPONENT_OR_AUDIT_FAILED'
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  if child is not None and child.poll()is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(5)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(5)
  (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
  p=Path(task['output'])/'RESULT.json'
  if not result and p.exists():result=json.loads(p.read_text())
  done=dict(closed=True,passed=error is None,result=result,audit=proof,error=error,guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,closed_unix=time.time(),absolute_deadline_unix=end,original_goal_arrival_claim=False);dump(O/'COMPLETION.json',done);print(json.dumps({k:v for k,v in done.items()if k not in ['result','audit']}),flush=True)
 return 0 if done['passed']else 1
if __name__=='__main__':sys.exit(main())
