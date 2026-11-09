"""Time-window nominal corridor scheduling; no dynamics or physical models."""
import heapq,math,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments/v936_rpccr_corridor_search'))
from corridor_search import Geometry,primitive,K,STEP,EDGE_N,SPATIAL,GAP,REQUIRED,RHO
from support_envelope import NORMALS
DT=.1;HORIZON=90.;ARRIVAL_JITTER=.25;BRAKE_TUBE=2.2

def swept_many(vertices,starts,ends):
 rows=[];starts=np.asarray(starts);ends=np.asarray(ends);assert np.all(ends>=starts)
 for data in vertices:
  p=np.asarray(data);a=p[:,1];b=p[:,2];phase=np.arctan2(a,b)
  first=p[None,:,0]+np.sin(.32*starts[:,None])*a+np.cos(.32*starts[:,None])*b
  last=p[None,:,0]+np.sin(.32*ends[:,None])*a+np.cos(.32*ends[:,None])*b
  upper=np.maximum(first,last);lower=np.minimum(first,last)
  for offset,ismax in[(0.,True),(math.pi,False)]:
   turn=np.ceil((.32*starts[:,None]-phase-offset)/(2*math.pi));at=(phase+offset+2*math.pi*turn)/.32;inside=at<=ends[:,None]+1e-12;value=p[None,:,0]+(1 if ismax else-1)*np.hypot(a,b)
   if ismax:upper=np.where(inside,np.maximum(upper,value),upper)
   else:lower=np.where(inside,np.minimum(lower,value),lower)
  rows.append((upper.max(axis=1)+2e-7,-lower.min(axis=1)+2e-7))
 return np.column_stack([x[0]for x in rows]+[x[1]for x in rows])

def build_dense(path):
 dense=[list(path[0])]
 for a,b in zip(path,path[1:]):
  dx,dy=np.asarray(b[:2])-a[:2];forward=dx*math.cos(a[2])+dy*math.sin(a[2]);direction=1 if forward>=0 else-1;angle=math.atan2(math.sin(b[2]-a[2]),math.cos(b[2]-a[2]));curvature=angle/(STEP*direction)
  assert abs(curvature)<=K+1e-8
  segment=primitive(a,direction,curvature,np.linspace(STEP/EDGE_N,STEP,EDGE_N));assert np.max(abs(segment[-1]-b))<1e-8;dense.extend(segment.tolist())
 return np.asarray(dense)

def schedule(path,known,prior,origin):
 begun=time.monotonic();dense=build_dense(path);times=np.arange(0,HORIZON+DT/2,DT);absolute=origin+times
 # Swept source interval includes designed timing deviation and full finite stop.
 support=swept_many(prior['vertices'],absolute-ARRIVAL_JITTER,absolute+BRAKE_TUBE+ARRIVAL_JITTER)+.1
 theta=dense[:,2,None];angles=np.arctan2(NORMALS[:,1],NORMALS[:,0])[None,:]
 low=dense[:,:2]@NORMALS.T-.44*abs(np.cos(theta-angles))-.375*abs(np.sin(theta-angles))
 lower=np.max(low[:,None,:]-support[None,:,:],axis=2)-SPATIAL-GAP-.08*DT/2
 safe=lower>=.155;geometry=Geometry(known,None);static=geometry.clearances(dense)[0]-SPATIAL-GAP;safe &= static[:,None]>=.155
 nodes=len(path);limit=len(times);score=np.full((nodes,limit),np.inf);parents={};heap=[];expanded=0
 if safe[0,0]:score[0,0]=0;heapq.heappush(heap,(0.,0,0))
 endpoint=None
 while heap:
  cost,i,t=heapq.heappop(heap)
  if cost>score[i,t]+1e-10:continue
  expanded+=1
  if i==nodes-1:endpoint=(i,t);break
  # Wait maintains the entire finite stopwindow at this actual reference pose.
  if t+1<limit and safe[i*EDGE_N,t]and safe[i*EDGE_N,t+1]:
   nxt=(i,t+1);nc=cost+DT
   if nc<score[nxt]:score[nxt]=nc;parents[nxt]=(i,t);heapq.heappush(heap,(nc,*nxt))
  if i+1<nodes:
   for ticks in[10,20]:
    if t+ticks>=limit:continue
    samples=np.arange(EDGE_N+1);indices=i*EDGE_N+samples;clock=t+np.round(samples*ticks/EDGE_N).astype(int)
    if not np.all(safe[indices,clock]):continue
    nxt=(i+1,t+ticks);nc=cost+ticks*DT
    if nc<score[nxt]:score[nxt]=nc;parents[nxt]=(i,t);heapq.heappush(heap,(nc,*nxt))
 result=dict(passed=False,models=0,integrations=0,expanded=expanded,nominal_reference_nodes=nodes,dense_reference_poses=len(dense),horizon_s=HORIZON,timing_step_s=DT,arrival_jitter_design_s=ARRIVAL_JITTER,original_finite_stop_s=BRAKE_TUBE,minimum_static_lower_m=float(static.min()),feasible_pose_time_cells=int(safe.sum()),wall_s=time.monotonic()-begun,scope='Time-dependent complete nominal reference with finite stopping occupancy. Arrival jitter is not qualified actual tracking; no physical acceptance.')
 if endpoint is None:return dict(result,status='NO_QUALIFIED_SCHEDULE_WITHIN_FIXED_HORIZON',schedule=[])
 sequence=[]
 while endpoint!=(0,0):sequence.append(endpoint);endpoint=parents[endpoint]
 sequence.append((0,0));sequence.reverse();out=[dict(reference_index=i,arrival_s=t*DT,pose=path[i])for i,t in sequence];minimum=min(float(lower[i*EDGE_N,t])for i,t in sequence)
 return dict(result,passed=True,status='FINITE_TIME_CORRIDOR_FOUND',schedule=out,arrival_s=sequence[-1][1]*DT,minimum_dynamic_schedule_node_lower_m=minimum,nominal_wait_s=sum((b[1]-a[1])*DT for a,b in zip(sequence,sequence[1:])if a[0]==b[0]))
