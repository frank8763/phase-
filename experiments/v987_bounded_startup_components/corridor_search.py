"""Bounded RP-CCR reference search with risk feasibility inside every edge.

Analytic Ackermann references only; not vehicle dynamics or actual-control proof.
"""
import heapq,math,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(Path(__file__).parent),str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v934_rpccr_certified_recovery'),str(R/'experiments/v864_diagnosis'),str(R/'experiments/v887_exact_lidar_software')]
from snapshot_geometry import field
from exact_footprint import pose_values
from cycle_backup import cycle_upper
from support_envelope import polygon
from polygon_geometry import distances
K=.758770385;STEP=.1;RES=.05;BINS=72;EDGE_N=8;MAX_EXPANSIONS=20000;WALL_S=90.;GOAL_RADIUS=.2
RHO=math.hypot(.44,.375)
# Exactly the maximum original .04 reversal + .035 yaw + .1s age/delivery
# reserve and original20ms intersample motion allowance; threshold unchanged.
SPATIAL=.04+RHO*.035+.1*(.13+RHO*.16)+.02*(.13+RHO*.16+.08)
GAP=.5*(STEP/EDGE_N+RHO*K*STEP/EDGE_N)
REQUIRED=.155+SPATIAL+GAP

def primitive(pose,direction,curvature,distances_):
 t=np.asarray(distances_,float)*direction;x,y,a=pose;theta=a+curvature*t
 if abs(curvature)<1e-12:return np.c_[x+t*math.cos(a),y+t*math.sin(a),theta]
 return np.c_[x+(np.sin(theta)-math.sin(a))/curvature,y-(np.cos(theta)-math.cos(a))/curvature,theta]

class Geometry:
 def __init__(self,known,prior):
  self.known=known;self.static=field(known);self.prior=prior
  self.center_polygon=None if prior is None else polygon(cycle_upper(prior)+1e-6)
 def clearances(self,poses):
  static=pose_values(self.static,poses)
  dynamic=np.full(len(poses),np.inf)if self.center_polygon is None else distances(poses,self.center_polygon)-.1-2e-6
  return static,dynamic
 def passes(self,poses):
  s,d=self.clearances(poses);return np.minimum(s,d)>=REQUIRED
 def heuristic(self,goal):
  # An optimistic 2D center map biases search; it never admits an SE2 edge.
  axis=np.arange(-5+RES/2,5,RES);xx,yy=np.meshgrid(axis,axis);q=np.c_[xx.ravel(),yy.ravel()];bound=np.minimum(5-abs(q[:,0]),5-abs(q[:,1]));inscribed=.375+.155+SPATIAL
  for x,y,hx,hy in self.known['known_rectangles']:
   delta=abs(q-[x,y])-[hx,hy];inside=delta.max(axis=1);distance=np.where(inside<=0,inside,np.linalg.norm(np.maximum(delta,0),axis=1));bound=np.minimum(bound,distance)
  for x,y,radius in self.known['known_circles']:bound=np.minimum(bound,np.linalg.norm(q-[x,y],axis=1)-radius)
  if self.center_polygon is not None:
   poly=self.center_polygon;edge=np.roll(poly,-1,axis=0)-poly;delta=q[:,None,:]-poly;factor=np.clip(np.sum(delta*edge,axis=2)/np.sum(edge*edge,axis=1),0,1);pd=np.linalg.norm(delta-factor[:,:,None]*edge,axis=2).min(axis=1)
   cross=edge[None,:,0]*delta[:,:,1]-edge[None,:,1]*delta[:,:,0];inside=(cross>=-1e-12).all(axis=1)|(cross<=1e-12).all(axis=1);pd[inside]=0;bound=np.minimum(bound,pd-.1)
  free=(bound>=inscribed).reshape(xx.shape);cost=np.full(free.shape,np.inf);heap=[]
  for y,x in np.argwhere(free&(np.hypot(xx-goal[0],yy-goal[1])<=GOAL_RADIUS)):
   cost[y,x]=0.;heapq.heappush(heap,(0.,int(y),int(x)))
  while heap:
   g,y,x=heapq.heappop(heap)
   if g>cost[y,x]+1e-12:continue
   for dy,dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
    ny,nx=y+dy,x+dx
    if not(0<=ny<len(axis)and 0<=nx<len(axis))or not free[ny,nx]:continue
    ng=g+RES*math.hypot(dx,dy)
    if ng<cost[ny,nx]:cost[ny,nx]=ng;heapq.heappush(heap,(ng,ny,nx))
  def h(pose):
   x=int((pose[0]+5)/RES);y=int((pose[1]+5)/RES);direct=max(0.,math.hypot(pose[0]-goal[0],pose[1]-goal[1])-GOAL_RADIUS)
   if not(0<=x<len(axis)and 0<=y<len(axis))or not math.isfinite(cost[y,x]):return direct+2.
   return max(direct,float(cost[y,x]))
  return h,dict(center_map_cells=int(free.size),center_free_cells=int(free.sum()),reachable_center_cells=int(np.isfinite(cost).sum()),heuristic_only_not_admission=True)

def search(start,goal,known,prior):
 begun=time.monotonic();start=np.asarray(start,float);goal=np.asarray(goal,float);assert start.shape==(3,)and goal.shape==(2,)and np.isfinite([*start,*goal]).all()
 geom=Geometry(known,prior);static,dynamic=geom.clearances(start[None,:]);initial=float(min(static[0],dynamic[0]));report=dict(passed=False,models=0,integrations=0,scope='Analytic risk-feasible reference corridor only; no physical tracking or arrival guarantee',required_clearance_m=REQUIRED,original_threshold_m=.155,unchanged_maximum_spatial_reserve_m=SPATIAL,edge_interpolation_reserve_m=GAP,start_raw_clearance_m=initial,max_expansions=MAX_EXPANSIONS,goal_inner_radius_m=GOAL_RADIUS)
 if initial<REQUIRED:return dict(report,status='START_CORRIDOR_UNQUALIFIED',expanded=0,wall_s=time.monotonic()-begun,path=[])
 heuristic,hproof=geom.heuristic(goal);report['heuristic']=hproof
 def key(p,gear,run):return(round(p[0]/RES),round(p[1]/RES),int(round((p[2]%(2*math.pi))*BINS/(2*math.pi)))%BINS,gear,min(run,3))
 nodes=[(start,-1,0,0,0.)];best={key(start,0,0):0.};heap=[(1.5*heuristic(start),0.,0)];expanded=0;end=None;best_goal=math.hypot(*(start[:2]-goal));rejected=0
 samples=np.linspace(STEP/EDGE_N,STEP,EDGE_N);controls=[(g,k)for g in [1]for k in[-K,0.,K]]
 while heap and expanded<MAX_EXPANSIONS and time.monotonic()-begun<WALL_S:
  _,g,index=heapq.heappop(heap);pose,parent,gear,run,node_g=nodes[index]
  if g>best.get(key(pose,gear,run),math.inf)+1e-10:continue
  expanded+=1;error=float(np.linalg.norm(pose[:2]-goal));best_goal=min(best_goal,error)
  if error<=GOAL_RADIUS:end=index;break
  edges=np.array([primitive(pose,direction,curvature,samples)for direction,curvature in controls]);admitted=geom.passes(edges.reshape(-1,3)).reshape(len(controls),EDGE_N).all(axis=1)
  for j,(direction,curvature)in enumerate(controls):
   if gear and gear!=direction and run<3:continue
   if not admitted[j]:rejected+=1;continue
   child=edges[j,-1];newrun=min(3,run+1)if gear==direction else 1;newg=g+STEP*(1. if direction>0 else 2.)+STEP*.15*abs(curvature)/K+(.4 if gear and direction!=gear else 0.)
   marker=key(child,direction,newrun)
   if newg>=best.get(marker,math.inf)-1e-10:continue
   best[marker]=newg;nodes.append((child,index,direction,newrun,newg));idx=len(nodes)-1;heapq.heappush(heap,(newg+1.5*heuristic(child),newg,idx))
 report.update(expanded=expanded,generated=len(nodes),risk_rejected_edges=rejected,best_goal_m=best_goal,wall_s=time.monotonic()-begun)
 if end is None:return dict(report,status='SEARCH_BUDGET_OR_OPEN_SET_EXHAUSTED_UNQUALIFIED',path=[])
 chain=[]
 while end!=-1:chain.append(end);end=nodes[end][1]
 chain.reverse();path=[nodes[i][0].tolist()for i in chain];directions=[nodes[i][2]for i in chain[1:]]
 # Independent dense verification is implemented by a separate qualification.
 return dict(report,passed=True,status='GEOMETRIC_CORRIDOR_FOUND',path=path,edge_directions=directions,nominal_length_m=STEP*len(directions),gear_changes=sum(a!=b for a,b in zip(directions,directions[1:])),path_goal_error_m=float(np.linalg.norm(np.asarray(path[-1][:2])-goal)))
