import hashlib,json,os,signal,subprocess,sys,time,traceback,fcntl
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v858_nav2_verified';END=1794052800.
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
 assert json.loads((OUT/'model_preflight/RESULT.json').read_text())['passed'];assert not(OUT/'COMPONENT_CLAIM.json').exists()
 for path,h in json.loads((C/'COMPONENT_FREEZE.json').read_text())['files'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==h
 lock=(OUT/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(OUT/'COMPONENT_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time()),f)
 guard=(R/'REVIEW_PENDING').read_bytes();end=min(END,time.time()+900);window=dict(started_unix=time.time(),absolute_deadline_unix=end,root_deadline_unix=END,round_closed=False);dump(OUT/'COMPONENT_WINDOW.json',window);p=None;status='ENTRY'
 try:
  (R/'REVIEW_PENDING').unlink()
  with(OUT/'component.console').open('w')as f:p=subprocess.Popen([str(R/'run_phase.sh'),str((C/'component_worker.py').relative_to(R))],cwd=R,env=dict(os.environ,PHASE_MODEL_ABSOLUTE_DEADLINE=str(end-5)),stdout=f,stderr=subprocess.STDOUT,start_new_session=True);rc=p.wait(timeout=end-time.time())
  result=json.loads((OUT/'component01/RESULT.json').read_text())if(OUT/'component01/RESULT.json').exists()else dict(status='INCOMPLETE_RESULT_COUNTS_UNKNOWN',passed=False);status=result['status'];dump(OUT/'COMPONENT_COMPLETION.json',dict(returncode=rc,result=result,closed=True))
 except BaseException as e:status='DRIVER_EXCEPTION';dump(OUT/'COMPONENT_DRIVER_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc()))
 finally:
  if p and p.poll()is None:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=4)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  (R/'REVIEW_PENDING').write_bytes(guard);window.update(round_closed=True,status=status,closed_unix=time.time(),guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard);dump(OUT/'COMPONENT_WINDOW.json',window);print(json.dumps(window),flush=True)
if __name__=='__main__':main()
