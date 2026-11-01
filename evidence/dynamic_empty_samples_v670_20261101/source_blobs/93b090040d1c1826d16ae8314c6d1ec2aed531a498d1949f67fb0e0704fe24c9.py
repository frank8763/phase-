"""Truth-only task construction certificate. Never imported by online navigation."""
import math,time
import numpy as np
from task_planner import search,wrap
from exact_footprint import build

def certify(world,start,goal,wheel_base,max_steer,F,initial_margin):
    begun=time.monotonic()
    if initial_margin<.15:return {'status':'INITIAL_MARGIN_INVALID','eligible':False,'navigation_steps':0}
    field=build(F,world);field.base_heuristic=F.base._heuristic_grid
    path,stats=search(field,start,goal,wheel_base,max_steer,guard=.17,budget=8.,resolution=.05,heading_bins=144,dense_requested_guard=False)
    result={'status':'REFERENCE_NOT_FOUND','eligible':False,'search':stats,'navigation_steps':0,'truth_scope':'t0 offline only; no planner input; absent reference does not establish impossibility'}
    if path is not None and stats['status']=='GLOBAL_GOAL_PATH':
        poses=[];remainders=[];b=np.asarray(world['footprint_bounds']);rho=max(np.linalg.norm([x,y])for x in b[[0,2]]for y in b[[1,3]])
        for a,z in zip(path[:-1],path[1:]):
            ds=float(np.linalg.norm(z[:2]-a[:2]));dy=wrap(z[2]-a[2]);n=max(1,math.ceil(ds/.01),math.ceil(abs(dy)/.01))
            for k in range(n):poses.append([*(a[:2]+(k+.5)/n*(z[:2]-a[:2])),a[2]+(k+.5)/n*dy]);remainders.append((ds+rho*abs(dy))/n/2)
        values=field.pose_values(poses);lower=float(np.min(values-np.asarray(remainders)));distance=float(np.linalg.norm(path[-1,:2]-goal))
        result.update(reference_path=path.tolist(),continuous_polygonal_pose_clearance_lower_bound_m=lower,reference_goal_distance_m=distance,scope='sample-centered pose interpolation Hausdorff bound, not dynamics or exact bicycle arc certificate')
        if lower>=.15 and distance<=.28 and stats['minimum_clearance_m']>=.155:result.update(status='GEOMETRIC_REFERENCE_CERTIFIED',eligible=True)
    result['elapsed_s']=time.monotonic()-begun
    return result
