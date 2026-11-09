"""Bounded forward reference construction for an orientation-free goal region.

Reference geometry only. Never authorizes controls or invents sensor successors.
The original task accepts any final yaw; keep .08m inner endpoint and .20m RPP
position tolerance. Fixed family is specified before physical execution.
"""
import math
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'experiments/v945_rpccr_observation_liveness'),
             str(ROOT/'experiments/v864_diagnosis'),str(ROOT/'experiments/v891_dynamic_consistency_software')]
from snapshot_geometry import field
from exact_footprint import pose_values
from polygon_geometry import terminal_values, route_check

K=.758770385
ENDPOINT_OFFSETS=((0.,0.),)+tuple((.08*math.cos(a),.08*math.sin(a))for a in np.arange(16)*2*math.pi/16)
FINAL_YAWS=tuple(np.arange(-4,5)*math.pi/16)
TANGENT_FACTORS=(.3,.5,.7)
MAX_PROPOSALS=len(ENDPOINT_OFFSETS)*len(FINAL_YAWS)*len(TANGENT_FACTORS)**2


def curve(start, end, angle, f1, f2):
    start=np.asarray(start,float);end=np.asarray(end,float)
    length=float(np.linalg.norm(end-start[:2]));t=np.linspace(0.,1.,401)[:,None]
    p0=start[:2];p1=p0+length*f1*np.array([math.cos(start[2]),math.sin(start[2])])
    p3=end;p2=p3-length*f2*np.array([math.cos(angle),math.sin(angle)])
    points=(1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3
    d=3*(1-t)**2*(p1-p0)+6*(1-t)*t*(p2-p1)+3*t*t*(p3-p2)
    dd=6*(1-t)*(p2-2*p1+p0)+6*t*(p3-2*p2+p1)
    speed=np.linalg.norm(d,axis=1)
    if speed.min()<1e-6:return None
    curvature=(d[:,0]*dd[:,1]-d[:,1]*dd[:,0])/speed**3
    if np.max(abs(curvature))>K:return None
    # k' = cross(d,j)/|d|^3 - 3 cross(d,dd)(d.dd)/|d|^5.
    # dd is affine: its norm is bounded by the interval endpoint norms.
    # Any point is <=h/2 from an endpoint; |d| >= min(endpoint |d|)-A*h/2.
    # Thus |k'| <= |j|/v_min^2 + 3*A^2/v_min^3 on each interval.
    h=1./400
    acceleration=np.linalg.norm(dd,axis=1)
    bound_a=np.maximum(acceleration[:-1],acceleration[1:])
    minimum_speed=np.minimum(speed[:-1],speed[1:])-bound_a*h/2
    if minimum_speed.min()<=0:return None
    jerk=float(np.linalg.norm(6*(p3-3*p2+3*p1-p0)))
    derivative_bound=jerk/minimum_speed**2+3*bound_a**2/minimum_speed**3
    interval_bound=np.maximum(abs(curvature[:-1]),abs(curvature[1:]))+derivative_bound*h/2
    certified_k=float(interval_bound.max())
    if certified_k>K:return None
    poses=np.c_[points,np.unwrap(np.arctan2(d[:,1],d[:,0]))]
    return poses,dict(maximum_sampled_curvature=float(abs(curvature).max()),
        continuous_curvature_upper=certified_k,curvature_interval_proof=True,
        minimum_parameter_speed=float(speed.min()),endpoint_yaw_rad=angle,
        tangent_factors=[f1,f2],length_m=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum()))


def construct(start, goal, known, prior):
    assert len(start)==3 and len(goal)==2 and np.isfinite([*start,*goal]).all()
    static=field(known);reject=dict(curvature_or_degenerate=0,static=0,dynamic=0)
    best=None;qualified=0;worst_margin=-math.inf
    # A geometric reference is not a new physical response qualification.
    for offset in ENDPOINT_OFFSETS:
        end=np.asarray(goal)+offset
        for angle in FINAL_YAWS:
            for f1 in TANGENT_FACTORS:
                for f2 in TANGENT_FACTORS:
                    proposal=curve(start,end,angle,f1,f2)
                    if proposal is None:reject['curvature_or_degenerate']+=1;continue
                    poses,metadata=proposal
                    # Dense pose interpolation and its conservative .005m/rad
                    # gap are checked again by the unchanged route gate below.
                    raw_static=float(pose_values(static,poses).min())
                    raw_dynamic=float(terminal_values(poses,prior,.06).min())
                    gap=.005+math.hypot(.44,.375)*.005
                    margin=min(raw_static,raw_dynamic)-gap
                    worst_margin=max(worst_margin,margin)
                    if raw_static-gap<.15:reject['static']+=1;continue
                    if raw_dynamic-gap<.155:reject['dynamic']+=1;continue
                    from navigation_policy import require_forward_path
                    require_forward_path(poses)
                    final=route_check(poses,prior)
                    if not final['passed']:reject['dynamic']+=1;continue
                    qualified+=1
                    record=dict(path=poses.tolist(),static_lower_m=raw_static-gap,
                        dynamic_lower_m=raw_dynamic-gap,route_guard=final,**metadata)
                    rank=(record['length_m'],-margin)
                    if best is None or rank<best[0]:best=(rank,record)
    return dict(passed=best is not None,reference=None if best is None else best[1],
        fixed_proposal_count=MAX_PROPOSALS,qualified_references=qualified,rejections=reject,
        best_combined_sample_margin_m=worst_margin,models=0,integrations=0,
        physical_ready=False,scope='Forward reference geometry with conservative continuous curvature bound; no physical response or arrival qualification.')
