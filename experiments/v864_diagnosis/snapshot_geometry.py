"""Saved-state exact rectangle geometry and tracking metrics. No vehicle/model integration."""
import json,sys,math
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v864_diagnosis';p=R/'runs/v858_nav2_verified/v864_static/main_ns'
sys.path.insert(0,str(R/'experiments/v791_coherent_global_reference'));from exact_footprint import pose_values

def field(known,pad=0.):return SimpleNamespace(half=np.array([.44+pad,.375+pad]),center_local=np.zeros(2),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=np.empty((0,2)),sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
def dense(plan):
 rows=[]
 for a,b in zip(plan[:-1],plan[1:]):
  a=np.asarray(a);b=np.asarray(b);angle=math.atan2(math.sin(b[2]-a[2]),math.cos(b[2]-a[2]));n=max(1,int(math.ceil(max(np.linalg.norm(b[:2]-a[:2])/.01,abs(angle)/.01))))
  for t in np.linspace(0,1,n,endpoint=False):rows.append([*(a[:2]+t*(b[:2]-a[:2])),a[2]+t*angle])
 return np.array([*rows,plan[-1]])
def main():
 a=np.load(p/'physics/NATIVE_TRACE.npz');setup=json.loads((p/'physics/SETUP.json').read_text());plans=json.loads((p/'PLANS.json').read_text());commands=np.asarray(json.loads((p/'physics/BODY_COMMANDS.json').read_text()));q=a['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));f=field(setup['known']);padded=field(setup['known'],.15);errors=[];heading=[];j=0
 for i,cmd in enumerate(commands):
  while j+1<len(plans)and plans[j+1]['at']<=cmd[0]:j+=1
  path=np.asarray(plans[j]['path']);delta=path[1:,:2]-path[:-1,:2];offset=q[i,:2]-path[:-1,:2];t=np.clip(np.sum(offset*delta,axis=1)/np.maximum(np.sum(delta*delta,axis=1),1e-15),0,1);dist=np.linalg.norm(path[:-1,:2]+t[:,None]*delta-q[i,:2],axis=1);k=int(np.argmin(dist));errors.append(dist[k]);expected=path[k,2]+t[k]*math.atan2(math.sin(path[k+1,2]-path[k,2]),math.cos(path[k+1,2]-path[k,2]));heading.append(math.atan2(math.sin(yaw[i]-expected),math.cos(yaw[i]-expected)))
 refs=[]
 for item in plans:
  path=np.asarray(item['path']);d=dense(item['path']);forward=np.sum(np.diff(path[:,:2],axis=0)*np.c_[np.cos(path[:-1,2]),np.sin(path[:-1,2])],axis=1);refs.append(dict(at=item['at'],nodes=len(path),negative_projected_segments=int(np.sum(forward< -1e-4)),full_rectangle_min_distance_m=float(pose_values(f,d).min()),padded_rectangle_min_separation_m=float(pose_values(padded,d).min())))
 rows=[];last=np.asarray(plans[-1]['path']);pose=np.r_[q[-1,:2],yaw[-1]];local=last[:,:2]-pose[:2];c,s=math.cos(pose[2]),math.sin(pose[2]);local=local@np.array([[c,-s],[s,c]])
 for L in [.6,.3]:
  k=next((i for i,x in enumerate(local)if np.linalg.norm(x)>=L),len(local)-1);carrot=local[k]
  if k>0:
   aa=local[k-1];dd=local[k]-aa;roots=np.roots([dd@dd,2*(aa@dd),aa@aa-L*L]);tt=[float(x.real)for x in roots if abs(x.imag)<1e-9 and 0<=x.real<=1]
   if tt:carrot=aa+max(tt)*dd
  curvature=float(2*carrot[1]/(carrot@carrot));arcs=[]
  for velocity in [.08,.2]:
   # Continuous constant-curvature geometric circle, not an executable MuJoCo prediction.
   ss=np.linspace(0,min(1.5*velocity,float(np.linalg.norm(carrot))),61);theta=pose[2]+ss*curvature
   x=pose[0]+(np.sin(theta)-math.sin(pose[2]))/curvature if abs(curvature)>1e-12 else pose[0]+ss*c
   y=pose[1]-(np.cos(theta)-math.cos(pose[2]))/curvature if abs(curvature)>1e-12 else pose[1]+ss*s
   pp=np.c_[x,y,theta];arcs.append(dict(velocity=velocity,full_rectangle_min_distance_m=float(pose_values(f,pp).min()),padded_rectangle_min_separation_m=float(pose_values(padded,pp).min())))
  rows.append(dict(lookahead=L,carrot_base=carrot.tolist(),curvature=curvature,arcs=arcs))
 mask=commands[:,5]==0;moving=mask&(abs(commands[:,1])>.01)
 result=dict(models=0,integrations=0,scope='Saved geometry and explicit analytic circles only; cannot reproduce unsaved online costmap or prove a controller fix',references=refs,reference_negative_segments=sum(x['negative_projected_segments']for x in refs),cross_track_median_m=float(np.median(errors)),cross_track_p95_m=float(np.quantile(errors,.95)),cross_track_max_m=float(np.max(errors)),heading_error_rms_rad=float(np.sqrt(np.mean(np.asarray(heading)**2))),v_command_rms_error_m_s=float(np.sqrt(np.mean((commands[moving,1]-commands[moving,3])**2))),yaw_command_rms_error_rad_s=float(np.sqrt(np.mean((commands[moving,2]-commands[moving,4])**2))),terminal_pose=pose.tolist(),terminal_full_footprint_clearance_m=float(pose_values(f,[pose])[0]),terminal_padded_footprint_separation_m=float(pose_values(padded,[pose])[0]),last_reference_and_geometric_carrot_probes=rows)
 (O/'SAVED_GEOMETRY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='references'},indent=2))
if __name__=='__main__':main()
