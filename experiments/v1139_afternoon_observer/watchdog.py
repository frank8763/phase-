"""Recorded-PID-only offline deadline and crash guard recovery; never start models."""
import sys,os,time,signal,fcntl
from afternoon_tools import *
def alive(pid,start):
 try:
  r=Path('/proc',str(pid),'stat').read_text().split();return r[21]==str(start)and r[2]!='Z'
 except FileNotFoundError:return False

def main():
 launch=json.loads((O/'LAUNCH_RECEIPT.json').read_text());w=json.loads((O/'ROUND_WINDOW.json').read_text());pid=launch['master_pid'];start=launch['master_proc_start']
 while alive(pid,start)and not(O/'COMPLETION.json').exists():
  try:stop=remaining(w)<=0
  except BaseException:stop=True
  if stop:
   os.kill(pid,signal.SIGTERM)
   for _ in range(50):
    if not alive(pid,start):break
    time.sleep(.1)
   if alive(pid,start):os.kill(pid,signal.SIGKILL)
   break
  time.sleep(2)
 if(O/'COMPLETION.json').exists():return
 a=json.loads((O/'ACTIVE.json').read_text())if(O/'ACTIVE.json').exists()else{}
 if a.get('pid')and a.get('proc_start')and alive(a['pid'],a['proc_start']):
  os.killpg(a['pid'],signal.SIGTERM)
  for _ in range(50):
   if not alive(a['pid'],a['proc_start']):break
   time.sleep(.1)
  if alive(a['pid'],a['proc_start']):os.killpg(a['pid'],signal.SIGKILL)
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
 for _ in range(30):
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
  except BlockingIOError:time.sleep(.1)
 else:dump(O/'WATCHDOG_ERROR.json',{'error':'PHYSICAL_LOCK_NOT_IDLE','no_new_model':True});return
 guard=(O/'GUARD.bin').read_bytes();assert hashlib.sha256(guard).hexdigest()==GUARD_SHA;(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',{'models_authorized':False,'closed':True});dump(O/'ACTIVE.json',{'closed':True,'interrupted':True});attempts=json.loads((O/'ATTEMPTS.json').read_text())if(O/'ATTEMPTS.json').exists()else[];rows=[]
 for t in attempts:
  p=Path(t['output'])/'RESULT.json';rows.append({'task':t['task_id'],'result':json.loads(p.read_text())if p.exists()else None})
 summary={'closed':True,'passed_afternoon_components':False,'status':'DRIVER_INTERRUPTED_NO_MODEL_RESTART','last_active':a,'attempted':[t['task_id']for t in attempts],'persisted_results':rows,'unknown_inflight_counts':True,'counts':{k:None for k in ['vehicle_initializations','new_actual_native','own_replay_native','analytical_prediction_native']},'guard_original':True,'old_deadlines_and_failures_preserved':True,'original_goal_or24_passed':False,'no_automatic_restart':True};dump(O/'WATCHDOG_RECOVERY.json',summary);dump(O/'COMPLETION.json',summary);report=R/'docs/RPCCR_AFTERNOON_OBSERVER_V1139_REPORT.md';report.write_text('# V1139 interrupted\n\n```json\n'+encode(summary)+'```\n');cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,active_zero_model_diagnostic=None,next_physical_authorized=False,latest_completed=summary);dump(R/'CURRENT_EXPERIMENT.json',cur)
if __name__=='__main__':main()
