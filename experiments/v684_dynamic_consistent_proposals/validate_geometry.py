"""Pure target geometry check, no environment and no integration."""
import os,json,hashlib
from pathlib import Path
import numpy as np
from consistent_targets import target_from_geometry
repo=Path(os.environ['PHASE_REPO']);out=repo/'runs/v684_dynamic_consistent_proposals';p=out/'GEOMETRY_VALIDATION.json';assert not p.exists();limit=.42722137342572125;worst=0.;maxfront=maxrear=0.;count=0
for steer in np.linspace(-.6108652381980153,.6108652381980153,1001):
 for wheel in [-12.,-4.,0.,4.,12.]:
  command=target_from_geometry(.6,.54,limit,steer,wheel);maxfront=max(maxfront,float(abs(command[:2]).max()));maxrear=max(maxrear,float(abs(command[2:]).max()));curvature=np.tan(np.clip(steer,-limit,limit))/.6
  if abs(curvature)>1e-10:
   radii=np.asarray([.6/np.tan(command[0])+.27,.6/np.tan(command[1])-.27]);worst=max(worst,float(np.max(abs(radii*curvature-1))))
   if wheel:worst=max(worst,float(abs((command[3]-command[2])/(.54*(command[3]+command[2])/2)-curvature)));assert command[2]*command[3]>0
  else:assert np.max(abs(command[:2]))==0 and command[2]==command[3]==wheel
  assert maxfront<=.52+1e-12 and maxrear<=20.;count+=1
assert worst<=1e-10
base=repo/'runs/v680_dynamic_later_stop_reserve/dev47_95000011_laterstop/paired/geometry_memory';decisions=[json.loads(s)for s in(base/'control_decisions.jsonl').read_text().splitlines()];old=[c for d in decisions if d['stage']=='NOMINAL'and d['candidate_role']=='ORDINARY'for c in d['candidates']];turn=[c for c in old if max(abs(x)for x in c['target_command'][:2])>1e-9];example=next(c['target_command']for c in turn if max(abs(x)for x in c['target_command'][:2])<.52 and c['target_command'][2]*c['target_command'][3]>0 and abs(c['target_command'][2]-c['target_command'][3])>.1);lf,rf,lr,rr=example;front_radius=(.6/np.tan(lf)+.27+.6/np.tan(rf)-.27)/2;rear_radius=.54*(lr+rr)/(2*(rr-lr));result={'status':'PASS','robot_integrations':0,'grid_targets':count,'maximum_circle_consistency_error':worst,'maximum_target_front_angle':maxfront,'maximum_target_rear_speed':maxrear,'old_targets':len(old),'old_turn_targets':len(turn),'old_counter_rotating_rear_targets':sum(c['target_command'][2]*c['target_command'][3]<0 for c in turn),'old_front_targets_beyond_range':sum(max(abs(x)for x in c['target_command'][:2])>.52 for c in turn),'old_unsaturated_example':example,'front_to_rear_target_radius_ratio':float(front_radius/rear_radius),'source_sha256':hashlib.sha256((Path(__file__).parent/'consistent_targets.py').read_bytes()).hexdigest(),'scope':'target geometry, not native reachability or navigation; old actual commands remain legal and audited'};p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
