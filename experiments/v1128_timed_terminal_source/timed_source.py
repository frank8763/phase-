"""Causal timed motion clearance with full-cycle stationary refuge checks."""
import sys,importlib.util,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'))
from bindings import ref,REQUIRED
from source import final_gate as cycle_final_gate,requests,initial,python_replay,digest,COUNTS
from solver import Solver as OriginalSolver
from time_geometry import interval_support
import numpy as np
NORMALS=np.c_[np.cos(np.arange(16)*np.pi/8),np.sin(np.arange(16)*np.pi/8)]
class Timed:
 def __init__(self,x):
  self.x=x;self.period=2*np.pi/.32;self.width=.025;self.edges=np.arange(0,self.period,self.width);p=x['source']['periodic'];assert p['omega']==.32 and p['amplitude']==.25;assert x['source']['source_native_tick']<=x['packet']['native_tick'];assert 0<=x['source']['source_age_s']<=.2
  self.bounds=interval_support(p['vertices'],self.edges-.075,self.edges+self.width+.075);self.start=float(x['packet']['sim_time']);self.static=ref._old.Geometry(x['setup']['known'],None)
 def components(self,poses,ticks):
  p=np.asarray(poses,float);ticks=np.asarray(ticks);assert p.ndim==2 and p.shape[1]==3 and ticks.shape==(len(p),)and np.isfinite(p).all()and np.all(ticks>=0)
  t=(self.start+.01*ticks)%self.period;ix=np.minimum((t/self.width).astype(int),len(self.edges)-1);yaw=p[:,2,None];proj=p[:,:2]@NORMALS.T-.44*abs(np.cos(yaw)*NORMALS[:,0]+np.sin(yaw)*NORMALS[:,1])-.375*abs(-np.sin(yaw)*NORMALS[:,0]+np.cos(yaw)*NORMALS[:,1]);dynamic=(proj-self.bounds[ix]-.1).max(axis=1);static=self.static.clearances(p)[0];return static,dynamic
 def clearances(self,poses,ticks):
  a,b=self.components(poses,ticks);return np.minimum(a,b)
class Solver(OriginalSolver):
 def __init__(self,x,path,gears,initial_guess=None):
  super().__init__(x,path,gears,initial_guess);self.timed=Timed(x);self.terminal=np.asarray(x['safe_terminal_pose'],float)
 def constraint_terms(self,ss,events):
  # Exact min over every native; no geometric guide O(native*path) work.
  minimum=self.timed.clearances(ss[:,:3],np.arange(len(ss)));bins=256;mapping=np.minimum(np.arange(len(ss))*bins//len(ss),bins-1);bounds=np.full(bins,np.inf);np.minimum.at(bounds,mapping,minimum);envelopes=[]
  for begin,moving,end in events[1:]:
   a,b=self.geometry.clearances(ss[begin-600:begin-599,:3]);envelopes.append(float(min(a[0],b[0]))-.02-np.hypot(.44,.375)*.1)
  goal_distance=float(np.linalg.norm(ss[-1,:2]-self.x['goal']));target_distance=float(np.linalg.norm(ss[-1,:2]-self.terminal[:2]));yaw=abs(math.atan2(math.sin(ss[-1,2]-self.terminal[2]),math.cos(ss[-1,2]-self.terminal[2])));a,b=self.geometry.clearances(ss[-1:,:3]);hold=float(min(a[0],b[0]));signed=np.r_[bounds-(REQUIRED+.001),np.array(envelopes)-(REQUIRED+float(self.x.get('mode_reserve',.015))),.30-goal_distance,.025-target_distance,.1-yaw,hold-(REQUIRED+.001)];report={'minimum_certified_raw_lower_m':float(minimum.min()),'coupled_mode_envelope_lower_m':envelopes,'terminal_goal_distance_m':goal_distance,'safe_terminal_distance_m':target_distance,'safe_terminal_yaw_error_rad':yaw,'terminal_full_cycle_raw_m':hold,'maximum_restoration_violation_m':float(np.maximum(0.,-signed).max()),'restoration_targets_met':bool((signed>=-1e-10).all()),'sampled_geometry_poses':len(ss),'explicit_inequality_count':len(signed),'geometry_type':'native causal timed; full-cycle parked and terminal'};return signed,report

def final_gate(x,ss,uu,rows):
 proof,rr=cycle_final_gate(x,ss,uu,rows);a,b=Timed(x).components(ss[:,:3],np.arange(len(ss)));low=float(np.minimum(a,b).min());full=ref._old.Geometry(x['setup']['known'],x['source']['periodic']);s,d=full.clearances(ss[-1:,:3]);terminal=np.asarray(x['safe_terminal_pose']);proof.update(minimum_timed_raw_m=low,minimum_static_m=float(a.min()),minimum_timed_dynamic_m=float(b.min()),terminal_full_cycle_raw_m=float(min(s[0],d[0])),old_full_cycle_motion_raw_m=proof['minimum_raw_m']);proof['minimum_raw_m']=low;proof['checks']['full_raw_geometry']=low>=REQUIRED;proof['checks']['terminal_full_cycle_hold']=float(min(s[0],d[0]))>=REQUIRED;proof['checks']['safe_terminal_position']=np.linalg.norm(ss[-1,:2]-terminal[:2])<=.025;proof['checks']['safe_terminal_heading']=abs(math.atan2(math.sin(ss[-1,2]-terminal[2]),math.cos(ss[-1,2]-terminal[2])))<=.1;proof['passed']=bool(all(proof['checks'].values()));return proof,rr
