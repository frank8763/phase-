"""Validate a complete static t0 reference through the original input predictor."""
import importlib.abc,json,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1022_full_route_planner';sys.path[:0]=[str(C),str(R/'experiments/v1004_planned_input_navigation')]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('NO_MODEL')
sys.meta_path.insert(0,NoModel());import full_route as m;from whole_input import predict,checks
route=sys.argv[1];plan=json.loads((O/(route+'_initial.static_geometry.json')).read_text());assert plan['passed']
pref=R/'runs/v858_nav2_verified/v1020/PREFLIGHTS'/route;p=json.loads((pref/'PREFLIGHT.json').read_text());setup=json.loads((pref/'SETUP.json').read_text());enc=p['steering']
packet=dict(body=p['body'],steering=dict(position=enc[:2],velocity=enc[2:]),controller_memory=dict(last_ctrl=[0.,0.,0.,0.],integral=0.))
start=time.monotonic();states,ctrl,requests=predict(setup,packet,plan['edge_targets']);a,b=m.ref._old.Geometry(setup['known'],None).clearances(states[:,:3]);raw=float(a.min());qualified,upper=checks(states,ctrl,requests,packet,setup,plan['original_goal'],raw,m.REQUIRED)
summary=dict(passed=all(qualified.values()),checks=qualified,models=0,integrations=0,planned_native_steps=len(requests),goal_upper_m=upper,minimum_full_static_raw_m=raw,required_raw_m=m.REQUIRED,
 wall_s=time.monotonic()-start,pre_detection_static_only=True,dynamic_certificate=False,physical_ready=False)
np.savez_compressed(O/(route+'_initial.whole_prediction.npz'),state=states,ctrl=ctrl,requests=requests)
(O/(route+'_initial.whole_prediction.json')).write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
