"""No-model subprocess used to exercise real supervisor process boundaries."""
import json
from pathlib import Path
import sys
import time

role,mode,directory=sys.argv[1:];out=Path(directory)
if role=='ros':
    time.sleep(.08)
    if mode not in ['missing_receipt','native_fault','hang']:
        (out/'ROS_RESULT.json').write_text(json.dumps(dict(passed=mode=='success',action_status=4 if mode=='success' else 6,error_code=104)))
    if mode in ['native_fault','hang']:time.sleep(10)
    raise SystemExit(0 if mode=='success' else 1)
if mode=='native_fault':
    (out/'RESULT.json').write_text(json.dumps(dict(closed=True,passed=False,error='NATIVE_SAFETY_ANOMALY')))
    raise SystemExit(1)
if mode=='hang':time.sleep(10)
until=time.monotonic()+3
while not (out/'STOP_AFTER_CURRENT_PREFIX.json').exists():
    assert time.monotonic()<until
    time.sleep(.005)
# Simulates expensive serialization after a functional/control rejection.
time.sleep(.16)
(out/'RESULT.json').write_text(json.dumps(dict(closed=True,passed=mode=='success',evidence_saved=True,complete_stop=True,replay={'passed':True})))
raise SystemExit(0 if mode=='success' else 1)
