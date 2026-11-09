"""One registered true initial snapshot, no native integrations or controls."""
import fcntl
import json
import os
import signal
import sys
import time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(C))
from authority import authorized,sha
task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text())
deadline=authorized(task,receipt,time.time(),sha(C/'SOURCE_FREEZE.json'),preflight=True)
assert 'preflight_output'in task
out=Path(task['preflight_output']);assert not out.exists(),'PREFLIGHT_ALREADY_ATTEMPTED'
lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
cpus=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpus[3]})
def halt(*args):raise TimeoutError('PREFLIGHT_OR_ROOT_DEADLINE')
signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt)
signal.setitimer(signal.ITIMER_REAL,min(60.,deadline-20-time.time()))
from physical import create_vehicle
vehicle=create_vehicle(out,task);scan=vehicle.scan();summary=vehicle.finish()
assert vehicle.count==0 and vehicle.d.time==0. and not vehicle.commands and not vehicle.rows
assert vehicle.first_detection is None and summary['minimum_actual_clearance_m']>=.15 and summary['bad_contacts']==0
result=dict(passed=True,actual_native=0,replay_native=0,private_native=0,models_initialized=1,summary=summary,
    scan=scan,body=list(vehicle.body()),steering=vehicle.steering_sample().tolist(),task_id=task['task_id'])
(out/'PREFLIGHT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result));signal.setitimer(signal.ITIMER_REAL,0)
