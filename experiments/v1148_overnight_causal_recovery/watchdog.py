"""Only recorded Phase PIDs; restores guard after driver death, never models."""
from night_tools import *
import signal,fcntl

def alive(pid,start):
 try:
  row=Path('/proc',str(pid),'stat').read_text().split();return row[21]==str(start)and row[2]!='Z'
 except FileNotFoundError:return False

if __name__=='__main__':
 launch=json.loads((O/'LAUNCH_RECEIPT.json').read_text());pid=launch['pid'];start=launch['proc_start']
 while alive(pid,start)and not(O/'COMPLETION.json').exists():
  if remaining()<=0:
   os.kill(pid,signal.SIGTERM)
   for _ in range(50):
    if not alive(pid,start):break
    time.sleep(.1)
   if alive(pid,start):os.kill(pid,signal.SIGKILL)
   break
  time.sleep(2)
 if not(O/'COMPLETION.json').exists():
  active=json.loads((O/'ACTIVE.json').read_text())if(O/'ACTIVE.json').exists()else{}
  if active.get('pid')and alive(active['pid'],active['proc_start']):
   os.killpg(active['pid'],signal.SIGTERM);time.sleep(3)
   if alive(active['pid'],active['proc_start']):os.killpg(active['pid'],signal.SIGKILL)
  lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
  for _ in range(30):
   try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
   except BlockingIOError:time.sleep(.1)
  else:dump(O/'WATCHDOG_ERROR.json',dict(error='LOCK_NOT_IDLE',models_started=0));sys.exit(1)
  guard=(O/'GUARD.bin').read_bytes();assert hashlib.sha256(guard).hexdigest()==GUARD_SHA;(R/'REVIEW_PENDING').write_bytes(guard)
  task=json.loads((C/'TASK.json').read_text());p=Path(task['output'])/'RESULT.json';persisted=json.loads(p.read_text())if p.exists()else None
  result=dict(closed=True,passed=False,stop_reason='DRIVER_INTERRUPTED_NO_RESTART',persisted_result=persisted,unknown_inflight_counts=True,models=None,actual_native=None,own_replay_native=None,no_route_or_confirmation=True,guard_original=True)
  dump(O/'COMPLETION.json',result);dump(O/'APPROVAL.json',dict(closed=True,models_authorized=False));dump(O/'ACTIVE.json',dict(closed=True))
  current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_short_physical_result=result);dump(R/'CURRENT_EXPERIMENT.json',current)
