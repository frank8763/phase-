"""Nominal target kinematics agree with the planner's ideal steering circle.
No obstacle input; real native prediction/admission remains mandatory.
"""
import math
import numpy as np
from control_contract import planner_steering_bound

def target_from_geometry(wheel_base,track_width,center_limit,steer,wheel):
    steer=float(np.clip(steer,-center_limit,center_limit));curvature=math.tan(steer)/wheel_base
    left=math.atan2(wheel_base*curvature,1-track_width*curvature/2)
    right=math.atan2(wheel_base*curvature,1+track_width*curvature/2)
    return np.asarray([left,right,wheel*(1-track_width*curvature/2),wheel*(1+track_width*curvature/2)])

def proposal_target(env,steer,wheel,mj):
    limit,_=planner_steering_bound(env,mj)
    assert abs(wheel)<=12.+1e-10
    return target_from_geometry(float(env.inner.wheel_base),float(env.inner.track_width),limit,steer,wheel)
