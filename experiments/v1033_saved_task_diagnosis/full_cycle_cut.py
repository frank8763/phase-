"""Continuous separating-cycle witness for this saved full-cycle certificate.

This proves absence of a route under the saved spatial-union contract only.
It does not prove the real moving task or a time-aligned controller impossible.
No model imports, true actor positions, or sampled-grid connectivity argument.
"""
import importlib.abc,json,math,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1033_saved_task_diagnosis'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1023_dense_input_route'))
from geometry_model import ref,REQUIRED

def inside_polygon(p,poly):
 e=np.roll(poly,-1,axis=0)-poly;d=p-poly;c=e[:,0]*d[:,1]-e[:,1]*d[:,0];return bool((c>=-1e-9).all()or(c<=1e-9).all())
def in_rect(p,r):return bool((abs(p-np.asarray(r[:2]))<=np.asarray(r[2:])+1e-10).all())
def winding(p,poly):
 total=0.
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  a=a-p;b=b-p;total+=math.atan2(a[0]*b[1]-a[1]*b[0],a@b)
 return round(total/(2*math.pi))
def segment_distance(p,a,b):
 t=float(np.clip((p-a)@(b-a)/((b-a)@(b-a)),0,1));return float(np.linalg.norm(p-(a+t*(b-a))))
def build(known,polygon,start,goal,clearance=REQUIRED):
 upper=np.asarray(known['known_rectangles'][3]);lower=np.asarray(known['known_rectangles'][9]);u=polygon[np.argmax(polygon[:,1])];l=polygon[np.argmin(polygon[:,1])];rad=.375+clearance-1e-8;actor_rad=rad+.1
 a=np.array([5.,upper[1]]);b=np.array([u[0],upper[1]]);c=u.copy();d=l.copy();e=np.array([l[0],lower[1]+lower[3]]);g=np.array([lower[0]+lower[2],e[1]]);f=np.array([5.,e[1]]);curve=np.array([a,b,c,d,e,g,f])
 checks=dict(inscribed_disk_positive=rad>.375,upper_static_segment=in_rect(a,upper)and in_rect(b,upper),upper_bridge=inside_polygon(c,polygon)and np.linalg.norm(b-c)<rad+actor_rad,convex_actor_segment=inside_polygon(c,polygon)and inside_polygon(d,polygon),lower_bridge=inside_polygon(d,polygon)and in_rect(e,lower)and np.linalg.norm(d-e)<rad+actor_rad,lower_static_segment=in_rect(e,lower)and in_rect(g,lower),boundary_bridge=in_rect(g,lower)and np.linalg.norm(g-f)<2*rad,right_boundary=f[0]==a[0]==5.,simple_monotone_vertical_chain=bool(np.all(np.diff(curve[:5,1])<=1e-12)),start_outside=winding(start,curve)==0,goal_inside=abs(winding(goal,curve))==1,entire_original_goal_disk_inside=min(segment_distance(goal,x,y)for x,y in zip(curve,np.roll(curve,-1,axis=0)))>.45)
 return dict(passed=all(checks.values()),checks={k:bool(v)for k,v in checks.items()},curve=curve.tolist(),required_raw_clearance_m=clearance,inscribed_vehicle_radius_m=.375,static_forbidden_ball_radius_m=rad,actor_forbidden_ball_radius_m=actor_rad,upper_overlap_slack_m=float(rad+actor_rad-np.linalg.norm(b-c)),lower_overlap_slack_m=float(rad+actor_rad-np.linalg.norm(d-e)),boundary_overlap_slack_m=float(2*rad-np.linalg.norm(g-f)),distance_goal_to_curve_m=min(segment_distance(goal,x,y)for x,y in zip(curve,np.roll(curve,-1,axis=0))),start_winding=winding(start,curve),goal_winding=winding(goal,curve))

def main():
 p=R/'runs/v858_nav2_verified/v1024/dynamic_we';row=json.loads((p/'DYNAMIC_COMPLETE_PLAN.json').read_text());setup=json.loads((p/'physics/SETUP.json').read_text());geom=ref._old.Geometry(setup['known'],row['source']['periodic']);start=np.asarray(row['packet']['body'][:2]);goal=np.asarray(row['plan']['original_goal']);proof=build(setup['known'],geom.center_polygon,start,goal)
 assert proof['passed'],proof
 assert not build(setup['known'],geom.center_polygon,start,goal,clearance=.01)['passed']
 assert not build(setup['known'],geom.center_polygon,goal,start)['passed']
 samples=np.concatenate([np.asarray(a)[None,:]+np.linspace(0,1,33)[:,None]*(np.asarray(b)-a)for a,b in zip(proof['curve'],np.roll(proof['curve'],-1,axis=0))]);poses=np.array([[*x,yaw]for x in samples for yaw in np.linspace(-math.pi,math.pi,17)]);a,b=geom.clearances(poses);worst=float(np.minimum(a,b).max());assert worst<REQUIRED
 proof.update(models=0,integrations=0,source_native_tick=row['source']['source_native_tick'],continuous_witness=True,proof='A closed simple curve lies strictly inside the forbidden center set. The body rectangle contains a .375m disk at every yaw. Static/convex actor subsegments stay in convex obstacles; bridge subsegments are covered by endpoint forbidden balls with strict overlap. Start has winding0 and all original .45 goal disk winding1. Every continuous center path must cross this forbidden curve.',full_cycle_certificate_route_impossible=True,real_moving_task_impossible=False,reverse_or_more_expansions_cannot_fix_this_spatial_union=True,maximum_sampled_curve_raw_clearance_m=worst,all_3927_sampled_orientations_rejected=True,negative_cases=['reduce_clearance_invalidates_overlap','swap_start_goal_invalidates_winding'],next_required_change='time-aligned reachable occupancy and qualified input dynamics, or separately declared nonblocking course; never lower safety margins')
 (O/'FULL_CYCLE_SEPARATION_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items()if k not in ['curve','proof']}))
if __name__=='__main__':main()
