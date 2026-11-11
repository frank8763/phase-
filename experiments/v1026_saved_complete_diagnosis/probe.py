"""Fixed V1025 last actual state, no new vehicle models or controls."""
import copy,importlib.abc,json,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1026_saved_complete_diagnosis';sys.path[:0]=[str(C),str(R/'experiments/v1023_dense_input_route')]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel());import input_route as m
P=R/'runs/v858_nav2_verified/v1024/dynamic_we';x=json.loads((P/'DYNAMIC_COMPLETE_PLAN.json').read_text());setup=json.loads((P/'physics/SETUP.json').read_text());base=m.ref._old.Geometry
geom=base(setup['known'],x['source']['periodic']);poly=geom.center_polygon
print(json.dumps(dict(polygon_vertices=len(poly),polygon_lower=poly.min(axis=0).tolist(),polygon_upper=poly.max(axis=0).tolist(),packet_body=x['packet']['body'])),flush=True)
mode=sys.argv[1];counter=dict(calls=0,poses=0,wall_s=0.,exact_poses=0)
class Measured(base):
 def clearances(self,poses):
  t=time.monotonic();result=super().clearances(poses);counter['calls']+=1;counter['poses']+=len(poses);counter['exact_poses']+=len(poses);counter['wall_s']+=time.monotonic()-t;return result
class StaticOnly(Measured):
 def __init__(self,known,prior):super().__init__(known,None)
class FastEquivalent(base):
 def clearances(self,poses):
  start=time.monotonic();poses=np.asarray(poses);static=m.ref._old.pose_values(self.static,poses)
  if self.center_polygon is None:dynamic=np.full(len(poses),np.inf)
  else:
   center=(self.center_polygon.max(axis=0)+self.center_polygon.min(axis=0))/2;radius=np.linalg.norm(self.center_polygon-center,axis=1).max()
   lower=np.linalg.norm(poses[:,:2]-center,axis=1)-radius-.1-m.RHO-2e-6;near=lower<m.REQUIRED
   dynamic=lower.copy();dynamic[near]=m.ref._old.distances(poses[near],self.center_polygon)-.1-2e-6;counter['exact_poses']+=int(near.sum())
  counter['calls']+=1;counter['poses']+=len(poses);counter['wall_s']+=time.monotonic()-start
  return static,dynamic
m.ref._old.Geometry=StaticOnly if mode=='static_counterfactual'else FastEquivalent if mode=='fast_safe_lower'else Measured
result=m.construct(x['packet'],x['source'],x['plan']['original_goal'],setup,time.time()+100,'post_detection_full_cycle')
result.update(mode=mode,counter=counter,models=0,integrations=0,diagnostic_only=True,dynamic_certificate=False)
(O/(mode+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['path','state_path','edge_targets','planned_body_requests','predicted_actuator_controls','heuristic']},ensure_ascii=False))
