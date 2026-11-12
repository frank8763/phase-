"""Locate whether any timing can certify the existing complete static profile."""
import sys,importlib.abc,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1076_complete_goal_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
import numpy as np
from kernel import predict,Geometry,REQUIRED,ref
from recovery_source import forecast_packet
x=json.loads((R/'runs/v1069_retained_goal_corridor/ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());s,u,r,m=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=1001)],tail=False);packet=forecast_packet(x['packet'],s[-1],m[-1],1001)
s,u,rr,m=predict(x['setup'],packet,x['actions'],tail=False);g=Geometry(x['setup']['known'],x['source']['periodic'],packet['sim_time']);norm=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)];pose=s[::25,:3];front=np.c_[np.cos(pose[:,2]),np.sin(pose[:,2])];left=np.c_[-np.sin(pose[:,2]),np.cos(pose[:,2])];base=pose[:,:2]@norm.T-.44*abs(front@norm.T)-.375*abs(left@norm.T)-.1;values=(base[:,None,:]-g.support[None,:,:]).max(axis=2);best=values.max(axis=1);worst=int(best.argmin());indices=np.flatnonzero(best<REQUIRED);result=dict(models=0,integrations=0,static_profile_native=len(rr),worst_best_phase_raw_m=float(best[worst]),required_raw_m=REQUIRED,impossible_pose_samples=len(indices),first_impossible=None if not len(indices)else dict(profile_tick=int(indices[0]*25),pose=pose[indices[0]].tolist(),best_any_phase_raw=float(best[indices[0]])),worst=dict(profile_tick=worst*25,pose=pose[worst].tolist()),static_goal_upper_m=float(np.linalg.norm(s[-1,:2]-x['goal']))+.08,any_phase_profile_passed=bool(not len(indices)));(O/'PATH_TIMING_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');np.savez_compressed(O/'PATH_PHASE_DIAGNOSIS.npz',pose=pose,lower_bounds=values,phase_start=g.edges,states=s,controls=u,requests=rr);print(json.dumps(result),flush=True)
