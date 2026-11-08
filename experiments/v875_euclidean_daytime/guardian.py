"""Offline detached guardian; one campaign launch, no model restart, absolute17:00 stop."""
import hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v875_euclidean_daytime';DEADLINE=1794128400.
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 guard=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert not(O/'GUARDIAN_CLAIM.json').exists()
 dump(O/'GUARDIAN_CLAIM.json',dict(pid=os.getpid(),started_unix=time.time(),deadline_unix=DEADLINE,no_restart=True));p=None;stopped=False
 try:
  with(O/'campaign.console').open('x')as f:
   p=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'LAUNCH_PID.json',dict(guardian_pid=os.getpid(),campaign_pid=p.pid,deadline_unix=DEADLINE))
   while p.poll()is None:
    if time.time()>=DEADLINE and not stopped:os.killpg(p.pid,signal.SIGTERM);stopped=True
    if time.time()>=DEADLINE+190:os.killpg(p.pid,signal.SIGKILL);p.wait();break
    time.sleep(1)
   dump(O/'GUARDIAN_RESULT.json',dict(closed=True,campaign_returncode=p.returncode,absolute_stop_sent=stopped,at=time.time()))
 finally:
  if p and p.poll()is None:os.killpg(p.pid,signal.SIGTERM)
  (R/'REVIEW_PENDING').write_bytes(guard)
  # No model restart on abnormal exit. Metadata records missing completion instead of inventing counts.
  if not(O/'COMPLETION.json').exists():dump(O/'ABNORMAL_EXIT.json',dict(error='CAMPAIGN_DISAPPEARED_WITHOUT_COMPLETION',actual_native=None,replay_native=None,models_restarted=0,at=time.time()))
if __name__=='__main__':main()
