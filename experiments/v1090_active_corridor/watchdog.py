"""Offline fail-closed watchdog, observing only this campaign's recorded PIDs."""
import os,sys,json,time,signal,fcntl,subprocess,hashlib
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1090_active_corridor'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
def read(name):return json.loads((O/name).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def alive(pid,start):
 try:
  parts=Path('/proc/'+str(pid)+'/stat').read_text().split()
  return parts[21]==str(start)and parts[2]!='Z'
 except FileNotFoundError:return False
def main():
 launch=read('LAUNCH.json');pid=launch['pid'];start=launch['starttime'];until=launch['absolute_deadline_unix'];boot=launch['boot_id']
 while time.time()<until+310:
  if(O/'COMPLETION.json').exists():return
  if not alive(pid,start):break
  if Path('/proc/sys/kernel/random/boot_id').read_text().strip()!=boot or time.time()>=until:
   os.kill(pid,signal.SIGTERM)
  time.sleep(2)
 else:return
 if(O/'COMPLETION.json').exists():return
 active=read('ACTIVE.json')if(O/'ACTIVE.json').exists()else {}
 if active.get('pid')and active.get('starttime')and alive(active['pid'],active['starttime']):
  os.killpg(active['pid'],signal.SIGTERM)
  for _ in range(30):
   if not alive(active['pid'],active['starttime']):break
   time.sleep(.1)
  if alive(active['pid'],active['starttime']):os.killpg(active['pid'],signal.SIGKILL)
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
 for _ in range(30):
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
  except BlockingIOError:time.sleep(.1)
 else:dump(O/'WATCHDOG_ERROR.json',dict(reason='PHASE_LOCK_NOT_IDLE',no_new_model=True));return
 guard=(O/'GUARD.bin').read_bytes();assert hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'AUTHORIZATION.json',dict(models_authorized=False,closed=True,reason='DRIVER_DISAPPEARED'));dump(O/'ACTIVE.json',dict(closed=True,interrupted=True))
 rows=read('RESULTS.json')if(O/'RESULTS.json').exists()else [];attempted=read('ATTEMPTS.json')if(O/'ATTEMPTS.json').exists()else [];tasks=json.loads((C/'TASKS.json').read_text());known={k:sum(r['result'].get(k,0)or 0 for r in rows)for k in ['vehicle_initializations','new_actual_native','own_replay_native','analytical_prediction_native']}
 development=(O/'DEVELOPMENT_FINALIZED.json').exists()and read('DEVELOPMENT_FINALIZED.json')['passed'];summary=dict(closed=True,passed=False,status='INTERRUPTED_UNKNOWN_IN_FLIGHT_COUNTS',version='v1090',three_route_development_passed=development,confirmation_passed=False,attempted=attempted,unexecuted=[t['task_id']for t in tasks if t['task_id']not in attempted],counts={k:None for k in known},completed_result_lower_bounds=known,error=dict(error='DRIVER_DISAPPEARED',active_task=active),no_model_restart=True,models_added_by_watchdog=0,integrations_added_by_watchdog=0)
 dump(O/'COMPLETION.json',summary);dump(O/'WATCHDOG_RECOVERY.json',summary);cfg=read('CONFIG.json');(R/cfg['report']).write_text('# V1090 driver interruption\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')
 x=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());x.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_completed=summary,latest_report=cfg['report']);dump(R/'CURRENT_EXPERIMENT.json',x);fcntl.flock(lock,fcntl.LOCK_UN)
 with(O/'watchdog_finalize.console').open('x')as log:
  subprocess.run([sys.executable,'-B',str(C/'finalize.py'),str(O/'CONFIG.json')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=300)
if __name__=='__main__':main()
