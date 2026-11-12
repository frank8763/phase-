"""Complete recertification at fixed measured-pose checkpoints, zero plant imports."""
import sys,json,copy
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
import qualify_tracking as q
from path_tracking import complete_from_measurement,reference,request,MAX_ACTIVE,BLOCK,STOP_NATIVE
from prediction import Predictor,initial
from kernel import PARAMETERS
import numpy as np
rows=[]
for name,bias in [('lag',-.0012),('boost',.002)]:
 plant=q.ProxyPlant(q.setup,initial(q.root),PARAMETERS,bias=bias);progress=0;n=0;next_check=0;checks=[];stopped=False
 while n<MAX_ACTIVE:
  packet=q.packet_from_engine(plant,n)
  if n>=next_check:
   proof,*_=complete_from_measurement(q.setup,packet,q.source,progress,MAX_ACTIVE-n,q.offset);checks.append(dict(native=n,**proof));next_check+=160
  pred=Predictor(q.setup,initial(packet),PARAMETERS)
  if packet['speed_episode']:pred.high_speed_episode=True;pred.adapter._speed_episode=True
  rr=[];idx=progress
  for j in range(BLOCK):
   r,idx,done=request(pred.state,q.path,q.arc,idx)
   if done:break
   pred.step(*r);rr.append(r)
  if not rr:stopped=True;break
  for r in rr:plant.step(*r);n+=1
  progress=idx
 proof,*_=complete_from_measurement(q.setup,q.packet_from_engine(plant,n),q.source,progress,MAX_ACTIVE-n,q.offset);checks.append(dict(native=n,**proof))
 rows.append(dict(name=name,passed=stopped and all(c['passed']for c in checks),checks=checks))
result=dict(passed=all(r['passed']for r in rows),cases=rows,models=0,integrations=0,scope='Fixed proxy checkpoints; physical and global guarantees not established');(q.O/'ROLLING_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);assert result['passed']
