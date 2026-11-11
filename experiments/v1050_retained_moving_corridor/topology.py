"""Finite geometric proposal search; never a physical admission certificate.

Rear reference accounts for the qualified lateral/yaw gain. Primitive collision
checks include interpolation reserve. Original actuator prediction must replace
every proposal before use. No simulator or true actor state is imported.
"""
import importlib.abc, importlib.util, heapq, json, math, sys, time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]; O=R/'runs/v1050_retained_moving_corridor'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0] in {'mujoco','torch','physical','vehicle','rclpy'}: raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1047_day_relay'))
from kernel import PARAMETERS, ref, REQUIRED, RHO
spec=importlib.util.spec_from_file_location('v1050_rs',R/'experiments/v1049_interval_corridor/third_party/reeds_shepp.py');rs=importlib.util.module_from_spec(spec);spec.loader.exec_module(rs)
def main():
 x=json.loads((R/'runs/v1047_day_relay_20261111/INPUT_SOURCE.json').read_text()); target=np.array([1.8200000476837156,-1.92146568250937,0.]);start=np.array(x['packet']['body'][:3]);ell=PARAMETERS['lateral_discrete'][0]/PARAMETERS['gain_a'];geo=ref._old.Geometry(x['setup']['known'],x['source']['periodic']);radius=1.65;step=.12
 def root(q):
  q=np.asarray(q);return np.c_[q[:,0]+ell*np.cos(q[:,2]),q[:,1]+ell*np.sin(q[:,2]),q[:,2]]
 def rear(q):return np.r_[q[:2]-ell*np.array([math.cos(q[2]),math.sin(q[2])]),q[2]]
 def key(q):return(round(q[0]/.04),round(q[1]/.04),round((q[2]%(2*math.pi))/.06))
 def h(q):return np.linalg.norm(root(q[None])[0,:2]-target[:2])+.35*abs(math.atan2(math.sin(q[2]),math.cos(q[2])))
 sr=rear(start);gr=rear(target);nodes=[(sr,-1,None)];best={key(sr):0.};heap=[(h(sr),0.,0)];begun=time.monotonic();expanded=0;answer=None;closest=math.inf;tested=0
 while heap and expanded<65000 and time.monotonic()-begun<110:
  _,cost,index=heapq.heappop(heap);q,parent,action=nodes[index]
  if cost>best.get(key(q),math.inf)+1e-9:continue
  expanded+=1;closest=min(closest,float(h(q)))
  if expanded%100==1:
   for p in sorted(rs.calc_paths(*q,*gr,1/radius,.005),key=lambda z:z.L):
    tested+=1;poses=root(np.c_[p.x,p.y,p.yaw]);a,b=geo.clearances(poses);minimum=float(np.minimum(a,b).min())
    if minimum>=REQUIRED+.0041:
     chain=[];j=index
     while nodes[j][1]>=0:chain.append(nodes[j][2]);j=nodes[j][1]
     answer=list(reversed(chain))+[dict(length=float(s),curvature=(1/radius if t=='L' else -1/radius if t=='R' else 0.)) for s,t in zip(p.lengths,p.ctypes)];break
   if answer is not None:break
  poses=[];actions=[]
  for sign in [1,-1]:
   for curvature in np.linspace(-1/radius,1/radius,5):
    distance=sign*np.linspace(0,step,25);yaw=q[2]+curvature*distance
    xx=q[0]+(np.sin(yaw)-math.sin(q[2]))/curvature if abs(curvature)>1e-12 else q[0]+distance*math.cos(q[2]);yy=q[1]-(np.cos(yaw)-math.cos(q[2]))/curvature if abs(curvature)>1e-12 else q[1]+distance*math.sin(q[2]);poses.append(np.c_[xx,yy,yaw]);actions.append(dict(length=float(sign*step),curvature=float(curvature)))
  poses=np.array(poses);a,b=geo.clearances(root(poses.reshape(-1,3)));minimum=np.minimum(a,b).reshape(10,25).min(axis=1)
  for i in np.flatnonzero(minimum>=REQUIRED+.0041):
   child=poses[i,-1];nc=cost+step*(1 if actions[i]['length']>0 else 1.5)+.015*abs(actions[i]['curvature'])*radius;mark=key(child)
   if nc>=best.get(mark,math.inf)-1e-10:continue
   best[mark]=nc;nodes.append((child,index,actions[i]));heapq.heappush(heap,(nc+1.7*h(child),nc,len(nodes)-1))
 merged=[]
 for a in answer or []:
  if merged and abs(merged[-1]['curvature']-a['curvature'])<1e-10 and merged[-1]['length']*a['length']>0:merged[-1]['length']+=a['length']
  else:merged.append(a.copy())
 result=dict(proposal_found=answer is not None,actions=merged,start_actual_pose=start.tolist(),target_proposal_pose=target.tolist(),expanded=expanded,generated=len(nodes),analytic_connectors_tested=tested,closest_heuristic=closest,wall_s=time.monotonic()-begun,models=0,integrations=0,physical_ready=False,radius_m=radius,rear_offset_m=ell)
 (O/'TOPOLOGY_STRAIGHT_ENTRY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
