"""Bounded local fail-closed recovery of only recorded Phase campaign PIDs."""
import sys,os,json,time,signal,fcntl,hashlib
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def alive(pid,start):
    try:
        row=Path('/proc',str(pid),'stat').read_text().split();return row[21]==str(start)and row[2]!='Z'
    except FileNotFoundError:return False
def main():
    O=Path(sys.argv[1]);launch=json.loads((O/'LAUNCH.json').read_text());w=json.loads((O/'ROUND_WINDOW.json').read_text())
    while time.time()<w['absolute_deadline_unix']+310:
        if(O/'COMPLETION.json').exists():return
        if not alive(launch['pid'],launch['starttime']):break
        if time.time()>=w['absolute_deadline_unix']or Path('/proc/sys/kernel/random/boot_id').read_text().strip()!=w['boot_id']:os.kill(launch['pid'],signal.SIGTERM)
        time.sleep(2)
    else:return
    if(O/'COMPLETION.json').exists():return
    active=json.loads((O/'ACTIVE.json').read_text())if(O/'ACTIVE.json').exists()else{}
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
    else:dump(O/'WATCHDOG_ERROR.json',dict(error='PHASE_LOCK_NOT_IDLE'));return
    guard=(O/'GUARD.bin').read_bytes();assert hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True,interrupted=True))
    tasks=json.loads((C/'TASKS.json').read_text());attempted=json.loads((O/'ATTEMPTS.json').read_text())if(O/'ATTEMPTS.json').exists()else[]
    summary=dict(closed=True,passed=False,version='v1113',status='INTERRUPTED_UNKNOWN_IN_FLIGHT_COUNTS',error=dict(error='DRIVER_DISAPPEARED',active=active),attempted=attempted,unexecuted=[t['task_id']for t in tasks if t['task_id']not in attempted],counts={k:None for k in ['vehicle_initializations','new_actual_native','own_replay_native','analytical_prediction_native']},guard_original=True,no_model_restart=True,new24_executed=False)
    dump(O/'COMPLETION.json',summary);dump(O/'WATCHDOG_RECOVERY.json',summary)
    report='docs/RPCCR_PARKED_MODE_RESPONSE_V1113_REPORT.md';(R/report).write_text('# V1113 interrupted\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')
    x=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());x.update(status='REVIEW_PENDING',active_run=None,active_window=None,next_physical_authorized=False,latest_completed=summary);dump(R/'CURRENT_EXPERIMENT.json',x)
if __name__=='__main__':main()
