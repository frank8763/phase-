"""Only arm one native fixed curve after all software startup/negative gates."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;S=R/'runs/v861_startup_gate';O=R/'runs/v858_nav2_verified/v861_curve';END=1794052800.
def main():
 assert json.loads((S/'SOFTWARE_COMPLETION.json').read_text())['gated_all_three_passed'];assert json.loads((S/'negative/RESULT.json').read_text())['passed'];assert END-time.time()>=180
 for path,h in json.loads((C/'PHYSICAL_FREEZE.json').read_text())['files'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==h
 O.mkdir(exist_ok=False);guard=(R/'REVIEW_PENDING').read_bytes();(O/'REVIEW_PENDING.before').write_bytes(guard)
 with(O/'CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time(),root_deadline_unix=END,maximum_native_actual=1600,maximum_replay=1600),f)
 p=None;status='ENTRY'
 try:
  (R/'REVIEW_PENDING').unlink()
  with(O/'curve.console').open('w')as f:p=subprocess.Popen([str(R/'run_phase.sh'),str((C/'curve.py').relative_to(R))],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);rc=p.wait(timeout=min(120.,END-10-time.time()))
  status='COMPLETE'if rc==0 else'NOT_PASSED'
 except BaseException as e:status='DRIVER_EXCEPTION';(O/'DRIVER_ERROR.json').write_text(json.dumps(dict(error=repr(e),traceback=traceback.format_exc()),indent=2)+'\n')
 finally:
  if p and p.poll()is None:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  (R/'REVIEW_PENDING').write_bytes(guard);(O/'COMPLETION.json').write_text(json.dumps(dict(closed=True,status=status,guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,closed_unix=time.time()),indent=2)+'\n')
if __name__=='__main__':main()
