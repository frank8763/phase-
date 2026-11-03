"""Public-map visibility potential only ranks already-safe concrete backup tails."""
import math,sys
from pathlib import Path
from types import SimpleNamespace
import cv2
import numpy as np
sys.path.insert(1,str(Path(__file__).resolve().parents[2]/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
from phase14_sensor_utils import ray_cast_distance
from renewal_state import decode
from recursive_domain import GRID,LOWER,AXIS
from free_certificate import free_samples
cv2.setNumThreads(1)
GOAL_BAND_M=.01

def future_possible(state):
    domain=decode(state['free_space_renewal']);steps=math.ceil(.12*3.28/GRID)
    return cv2.dilate(domain.possible.astype(np.uint8),np.ones((2*steps+1,2*steps+1),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=1).astype(bool)

def visibility_potential(terminal,field,possible):
    terminal=np.asarray(terminal);angles=np.r_[np.arange(32)*2*np.pi/32,np.linspace(-np.deg2rad(35),np.deg2rad(35),15)]+terminal[2]
    sensor=SimpleNamespace(robot_xy=np.asarray(terminal[:2],np.float32),map_min=-5.,map_max=5.,rect_obstacles=np.asarray(field.rectangles,np.float32),circle_obstacles=np.asarray(field.circles,np.float32))
    rays=[]
    for index,angle in enumerate(angles):
        raw=ray_cast_distance(sensor,float(angle),3.,.08);b=.06 if index<32 else .09
        rays.append([*terminal[:2],math.cos(angle),math.sin(angle),raw,b,.02 if index<32 else .03])
    points=free_samples(np.asarray(rays));covered=np.zeros_like(possible);r=.10
    for point in points:
        lo=np.maximum(0,np.ceil((point-r-LOWER)/GRID).astype(int));hi=np.minimum(len(AXIS)-1,np.floor((point+r-LOWER)/GRID).astype(int))
        if np.any(lo>hi):continue
        x=AXIS[lo[0]:hi[0]+1];y=AXIS[lo[1]:hi[1]+1];covered[lo[0]:hi[0]+1,lo[1]:hi[1]+1]|=(x[:,None]-point[0])**2+(y[None,:]-point[1])**2<r*r
    return int(np.sum(covered&possible))

def choose_backup(candidates,current_xy,goal_xy,field,state):
    assert candidates and state['center']is None and 'free_space_renewal'in state
    before=float(np.linalg.norm(np.asarray(current_xy)-goal_xy));progress=[before-float(np.linalg.norm(np.asarray(c['poses'])[-1,:2]-goal_xy))for c in candidates]
    best=max(progress);near=[i for i,p in enumerate(progress)if p>=best-GOAL_BAND_M-1e-12];possible=future_possible(state);scores={i:visibility_potential(np.asarray(candidates[i]['poses'])[-1],field,possible)for i in near}
    chosen=max(near,key=lambda i:(scores[i],candidates[i]['minimum_causal_predicted_clearance_m'],-i))
    metadata=dict(version='V724_GOAL_BAND_VISIBILITY',goal_band_m=GOAL_BAND_M,public_current_xy=np.asarray(current_xy).tolist(),public_goal_xy=np.asarray(goal_xy).tolist(),best_safe_goal_progress_m=best,
        selected_safe_index=chosen,selected_goal_progress_m=progress[chosen],selected_potential_visible_cells=scores[chosen],safe_candidate_count=len(candidates),
        candidates=[dict(safe_index=i,target=c['target'].tolist(),kind=c['recovery_kind'],terminal_pose=np.asarray(c['poses'])[-1].tolist(),goal_progress_m=progress[i],within_best_progress_band=i in near,potential_visible_cells=scores.get(i),minimum_causal_clearance_m=c['minimum_causal_predicted_clearance_m'])for i,c in enumerate(candidates)],
        safety_uses_future_measurement=False,visibility_scope='Known-map geometric potential only; dropout/unknown future never assumed free for admission.',future_model_horizon_s=3.28)
    return candidates[chosen],metadata
