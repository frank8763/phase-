"""No-model planner failure injection for the real PlanningJob interface."""
import json
from pathlib import Path
import sys
import time
request,result=map(Path,sys.argv[1:3]);data=json.loads(request.read_text())
if data['mode']=='hang':time.sleep(30)
if data['mode']=='crash':raise SystemExit(3)
if data['mode']=='no_result':raise SystemExit(0)
time.sleep(.25)
value=dict(passed=True,request_id=data['request_id']+(1 if data['mode']=='foreign' else 0),models=0,physical_native=0,path=[[0,0,0,1]])
temp=result.with_suffix('.tmp');temp.write_text(json.dumps(value));temp.replace(result)
