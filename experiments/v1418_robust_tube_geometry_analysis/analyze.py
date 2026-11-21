"""Read one frozen failed branch; no Predictor/model/integration entry."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import time
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;B=R/'runs/v1417_complete_timed_witness'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def support(rp,normals):
 cs,sn=math.cos(rp[2]),math.sin(rp[2]);values=[]
 for x,y in [(-.14,-.375),(-.14,.375),(.74,-.375),(.74,.375)]:
  X=x*cs-y*sn;Y=x*sn+y*cs;A=X*normals[:,0]+Y*normals[:,1];B=-Y*normals[:,0]+X*normals[:,1]
  v=A*math.cos(.1)+abs(B)*math.sin(.1);v=np.where(abs(np.arctan2(B,A))<=.1,np.hypot(A,B),v);values.append(v)
 return normals@rp[:2]+np.max(values,axis=0)+.02

def nearest_on_segment(point,a,b):
 t=float(np.clip(np.dot(point-a,b-a)/np.dot(b-a,b-a),0,1));return a+t*(b-a),t

def point_pair(rp,poly,yaw):
 theta=rp[2]+yaw;rotation=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
 local=np.array([[-.14,-.375],[.74,-.375],[.74,.375],[-.14,.375]]);box=local@rotation.T+rp[:2];choices=[]
 for j,a in enumerate(box):
  for k,b in enumerate(poly):
   q,t=nearest_on_segment(a,b,poly[(k+1)%len(poly)]);choices.append((float(np.linalg.norm(q-a)),a,q,dict(robot_corner=j,polygon_edge=k,polygon_edge_fraction=t)))
 for k,q in enumerate(poly):
  for j,a in enumerate(box):
   p,t=nearest_on_segment(q,a,box[(j+1)%4]);choices.append((float(np.linalg.norm(q-p)),p,q,dict(polygon_vertex=k,robot_edge=j,robot_edge_fraction=t)))
 distance,p,q,labels=min(choices,key=lambda row:row[0]);shift=.02*(q-p)/distance;shifted=p+shift
 # Convex combinations of edge endpoints prove point membership without a solver.
 assert abs(np.linalg.norm(shift)-.02)<1e-12 and -.1<=yaw<=.1
 return dict(yaw_delta=yaw,translation_delta=shift.tolist(),robot_before_translation=p.tolist(),robot_after_translation=shifted.tolist(),polygon_point=q.tolist(),distance_upper_m=float(np.linalg.norm(q-shifted)),membership=labels)

def main():
 os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));started=time.monotonic();assert not(O/'RESULT.json').exists()
 inputs=[B/'COMPLETION.json',B/'model/CURRENT_INPUT.json',B/'model/SETUP.json',B/'model/branches/INDEX.json',B/'model/branches/branches.xor.gz',R/'experiments/v1414_current_timed_geometry/geometry.py',R/'experiments/v1407_lossless_branch_stream/stream.py',C/'analyze.py',C/'PROTOCOL.md']
 hashes={str(p.relative_to(R)):sha(p)for p in inputs};assert read(B/'COMPLETION.json')['closed']and not read(B/'COMPLETION.json')['passed']
 current=read(B/'model/CURRENT_INPUT.json');index=read(B/'model/branches/INDEX.json');reader=load('v1418_branch_reader',inputs[-3]).BranchReader(B/'model/branches',index,np);states,ctrl=reader.read(index['branches'][0]);reader.finish()
 Geo=load('v1418_original_geometry',R/'experiments/v1414_current_timed_geometry/geometry.py').Geometry
 geometry=Geo(read(B/'model/SETUP.json')['known'],current['causal_snapshot'],origin_native=current['origin']['native_tick'],origin_sim_time=current['origin']['sim_time'])
 tick=current['origin']['native_tick'];rp=np.c_[states[:,0]-.3*np.cos(states[:,2]),states[:,1]-.3*np.sin(states[:,2]),states[:,2]]
 n64=np.c_[np.cos(np.arange(64)*math.tau/64),np.sin(np.arange(64)*math.tau/64)]
 lows=np.array([np.max(np.min(geometry.polygon(tick+i)@n64.T,axis=0)-support(p,n64))for i,p in enumerate(rp)])
 worst=int(np.argmin(lows));pose=rp[worst];poly=geometry.polygon(tick+worst);witness=min((point_pair(pose,poly,yaw)for yaw in [-.1,0.,.1]),key=lambda d:d['distance_upper_m'])
 sampled={}
 for count in [64,256,4096]:
  angles=np.arange(count)*math.tau/count;normals=np.c_[np.cos(angles),np.sin(angles)];sampled[str(count)]=float(np.max(np.min(poly@normals.T,axis=0)-support(pose,normals)))
 upper=witness['distance_upper_m'];assert sampled['4096']<=upper+1e-10 and upper<.22-1e-8
 assert all(sha(R/p)==h for p,h in hashes.items())and time.monotonic()-started<120
 result=dict(passed=True,models=0,analytical_native=0,physical_native=0,actual_replay_native=0,scientific_revision_added=False,source_hashes=hashes,input_sha256=current['input_sha256'],snapshot_sha256=current['causal_snapshot_sha256'],branch_raw_sha256=index['branches'][0]['raw_sha256'],complete_saved_branch_SHA_CRC_pass=True,worst_point_native=tick+worst,worst_point_rear_pose=pose.tolist(),sampled_normal_separation_lower_m=sampled,explicit_envelope_polygon_point_pair=witness,distance_upper_numerical_allowance_m=1e-10,upper_below_gate=True,same_polygon_full_envelope_cannot_pass_by_normal_refinement=True,actual_actor_point_reachability_not_established=True,actual_collision_not_established=True,global_infeasibility_not_established=True,wall_s=time.monotonic()-started)
 temporary=O/'RESULT.json.tmp';temporary.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');temporary.replace(O/'RESULT.json');print(json.dumps({k:v for k,v in result.items()if k!='source_hashes'}))
if __name__=='__main__':main()
