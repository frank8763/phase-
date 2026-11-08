"""Finite fixed-pose clearance certificate; not a vehicle braking/recovery policy."""
import math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v891_dynamic_consistency_software'))
from support_envelope import polygon,SPEED,RADIUS
from reproduce import intersects
def stationary_wait_certificate(safety_padded_body,causal_center_support,source_age_s,wait_s,latency_s):
    body=np.asarray(safety_padded_body,float);b=np.asarray(causal_center_support,float)
    if body.ndim!=2 or body.shape[1]!=2 or len(body)<3 or b.shape!=(16,):raise ValueError('INVALID_POSE_OR_ENCLOSURE')
    values=np.asarray([source_age_s,wait_s,latency_s],float)
    if not np.isfinite(body).all()or not np.isfinite(b).all()or not np.isfinite(values).all()or np.any(values<0):raise ValueError('INVALID_WAIT_CONTRACT')
    reach=b+RADIUS+SPEED*float(values.sum())
    admitted=not intersects(body,polygon(reach))
    return dict(passed=admitted,reason='FIXED_POSE_DISJOINT_FOR_FINITE_WAIT'if admitted else'WAIT_POSE_FORECAST_INTERSECTION_REQUIRES_DIFFERENT_POSE_OR_VERIFIED_EXIT',duration_s=float(wait_s),source_age_s=float(source_age_s),latency_s=float(latency_s),assumptions=['Supplied padded body contains all actual vehicle geometry and required clearance','Pose fixed throughout wait; braking/drift/pose errors must be bounded separately','Causal center set contains actor and declared Euclidean speed<=.08m/s remains valid','Finite declared waiting/latency interval only, no indefinite safety'],actor_truth_input=False,executable_vehicle_policy=False)
