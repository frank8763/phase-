"""Conservative sufficient obstruction witness, not a free-space feasibility test.

A FOUND witness rules out the stationary full-period union contract only.
UNKNOWN must never be interpreted as a free path or actuation permission.
Only the public static map and causal occupied-center convex polygon enter.
"""
import math
import numpy as np

def inside(point,polygon):
 edge=np.roll(polygon,-1,axis=0)-polygon;delta=point-polygon;cross=edge[:,0]*delta[:,1]-edge[:,1]*delta[:,0]
 return bool((cross>=-1e-10).all()or(cross<=1e-10).all())
def winding(point,curve):
 a=curve-point;b=np.roll(curve,-1,axis=0)-point;angle=np.arctan2(a[:,0]*b[:,1]-a[:,1]*b[:,0],(a*b).sum(axis=1)).sum()
 return int(round(angle/(2*math.pi)))
def distance(point,curve):
 a=curve;b=np.roll(curve,-1,axis=0);e=b-a;f=np.clip(((point-a)*e).sum(axis=1)/(e*e).sum(axis=1),0,1)
 return float(np.linalg.norm(point-a-f[:,None]*e,axis=1).min())
def select_contract(known,center_polygon,start_xy,goal_xy,required_raw,goal_radius=.45,inscribed_radius=.375,actor_radius=.1):
 base=dict(status='UNKNOWN_KEEP_ORIGINAL_ADMISSION',obstruction_proved=False,models=0,integrations=0,actuation_authority=False,physical_ready=False)
 if center_polygon is None:return base
 polygon=np.asarray(center_polygon,float);start=np.asarray(start_xy,float);goal=np.asarray(goal_xy,float)
 assert polygon.ndim==2 and polygon.shape[1]==2 and len(polygon)>=3 and np.isfinite(polygon).all()
 assert start.shape==goal.shape==(2,)and np.isfinite(np.r_[start,goal]).all()and 0<required_raw and 0<goal_radius and 0<inscribed_radius and actor_radius>=0
 # This witness requires a convex occupied center set. Refuse malformed or
 # nonconvex inputs rather than using the vertex chord as an occupied segment.
 edge=np.roll(polygon,-1,axis=0)-polygon
 if ((edge*edge).sum(axis=1)<=1e-20).any():return base
 delta=polygon[None,:,:]-polygon[:,None,:];side=edge[:,None,0]*delta[:,:,1]-edge[:,None,1]*delta[:,:,0]
 if not((side>=-1e-10).all()or(side<=1e-10).all()):return base
 u=polygon[np.argmax(polygon[:,1])];l=polygon[np.argmin(polygon[:,1])];static_r=inscribed_radius+required_raw-1e-8;actor_r=static_r+actor_radius
 for upper_index,upper in enumerate(known['known_rectangles']):
  x,y,hx,hy=map(float,upper)
  if not(x-hx<=u[0]<=x+hx and y>u[1]and x+hx<=5+hx*2):continue
  b=np.array([u[0],y]);top_end=np.array([min(5.,x+hx),y]);a=np.array([5.,y])
  if np.linalg.norm(a-top_end)>=2*static_r or np.linalg.norm(b-u)>=static_r+actor_r:continue
  for lower_index,lower in enumerate(known['known_rectangles']):
   xx,yy,hhx,hhy=map(float,lower)
   if not(xx-hhx<=l[0]<=xx+hhx and yy+hhy<l[1]):continue
   e=np.array([l[0],yy+hhy]);g=np.array([min(5.,xx+hhx),e[1]]);f=np.array([5.,e[1]])
   if np.linalg.norm(l-e)>=actor_r+static_r or np.linalg.norm(g-f)>=2*static_r:continue
   curve=np.array([a,top_end,b,u,l,e,g,f]);curve=np.array([point for i,point in enumerate(curve)if np.linalg.norm(point-curve[(i-1)%len(curve)])>1e-12])
   # Monotone left boundary, positive horizontal top/bottom chains, and the
   # right boundary make an explicit simple Jordan curve, without grid search.
   if not(b[0]<=top_end[0]<=5 and l[0]<=g[0]<=5 and u[1]>l[1]and max(b[0],u[0],l[0],e[0])<5):continue
   if winding(start,curve)!=0 or abs(winding(goal,curve))!=1 or distance(goal,curve)<=goal_radius:continue
   return dict(base,status='TIME_ALIGNED_OCCUPANCY_REQUIRED',obstruction_proved=True,full_cycle_route_ruled_out=True,real_moving_task_impossible=False,curve=curve.tolist(),upper_rectangle_index=upper_index,lower_rectangle_index=lower_index,static_forbidden_radius_m=static_r,actor_forbidden_radius_m=actor_r,goal_disk_distance_to_cut_m=distance(goal,curve),goal_radius_m=goal_radius,start_winding=winding(start,curve),goal_winding=winding(goal,curve),continuous_witness=True,safety_threshold_unchanged=True)
 return base
