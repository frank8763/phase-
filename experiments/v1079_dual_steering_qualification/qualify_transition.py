"""Next fixed turn-return component software checks; no physical authority."""
import sys,importlib.abc,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1079_dual_steering_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
import numpy as np
from kernel import ref,REQUIRED,checks,PARAMETERS
sys.path.insert(0,str(C));from steering_model import Predictor,initial
setup=json.loads((R/'runs/v858_nav2_verified/v1067/t0_dev_north_south/physics/SETUP.json').read_text());packet=json.loads((R/'runs/v1067_causal_replan_brake_reserve_preparation/NORTH_SOUTH_T0_METADATA.json').read_text())['packet'];rows=[]
for target in [-.42722137342572125,.42722137342572125]:
 rr=np.vstack([np.tile([.125,0.,0.],(200,1)),np.tile([.125,.125*math.tan(target)/.6,0.],(80,1)),np.tile([.125,0.,0.],(125,1)),np.zeros((2200,3))]);p=Predictor(setup,initial(packet),PARAMETERS);ss=[p.state.copy()];uu=[]
 for req in rr:s,u=p.step(*req);ss.append(s);uu.append(u)
 ss=np.asarray(ss);uu=np.asarray(uu);low=float(ref._old.Geometry(setup['known'],None).clearances(ss[:,:3])[0].min());cc,_=checks(ss,uu,rr,packet,setup,np.asarray(setup['case']['goal_xy']),low,REQUIRED);cc.pop('goal_upper');cc={k:bool(v)for k,v in cc.items()};rows.append(dict(target=target,passed=all(cc.values()),checks=cc,minimum_raw_m=low,native=len(rr),moving_straight_before_turn=200,turn_native=80,moving_return_straight_native=125,stop_native=2200))
result=dict(passed=all(x['passed']for x in rows),cases=rows,scope='Next two fixed .125 moving turn-return components software only, original NS t0',models=0,integrations=0,physical_window_opened=False,not_a_whole_route=True);(O/'NEXT_TRANSITION_PREFLIGHT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
