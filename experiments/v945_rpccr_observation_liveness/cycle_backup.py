"""All-phase stationary terminal geometry and immutable retained-tail permission.
Empirical pose envelope is monitored natively; this is not a reachability theorem.
"""
import math
import numpy as np
THRESHOLD=.155

def cycle_upper(prior):
    assert prior['omega']==.32 and prior['amplitude']==.25,'PERIODIC_CLASS_CHANGED'
    vertices=[np.asarray(p,float)for p in prior['vertices']]
    assert len(vertices)==8 and all(p.ndim==2 and p.shape[1]==3 and len(p)>0 and np.isfinite(p).all()for p in vertices),'INVALID_PERIODIC_SET'
    return np.array([np.max(p[:,0]+np.hypot(p[:,1],p[:,2]))for p in vertices]+[np.max(-p[:,0]+np.hypot(p[:,1],p[:,2]))for p in vertices])+2e-7

def terminal_bound(pose,prior,reserve):
    # Support normals are exactly the original 16 unit directions.
    angles=np.arange(16)*2*math.pi/16;normals=np.c_[np.cos(angles),np.sin(angles)]
    x,y,a=pose
    low=np.array([x,y])@normals.T-.44*abs(np.cos(angles-a))-.375*abs(np.sin(angles-a))
    original=float(np.max(low-cycle_upper(prior)-.1)-reserve)
    from polygon_geometry import terminal_values
    return max(original,float(terminal_values([pose],prior,reserve)[0]))

def retained_allowed(proof,elapsed):
    if not math.isfinite(elapsed) or elapsed<0:return False
    if proof.get('passed')is not True:return False
    if not math.isfinite(proof.get('body_age_s',math.nan)) or not 0<=proof['body_age_s']<=.05:return False
    if elapsed<=.2+2.+proof['body_age_s']+.05+1e-8:return True
    # Beyond the finite tail only stationary endpoint, qualified before dispatch.
    value=proof.get('terminal_cycle_lower_m')
    return proof.get('terminal_cycle_qualified')is True and isinstance(value,(int,float)) and math.isfinite(value) and value>=THRESHOLD


def stale_proposal_may_defer(error,proof,packet,now):
    # This never admits a new command. Native continues the immutable old proof.
    if str(error)!='STALE_COMMAND_BODY' or proof is None or packet is None:return False
    age=now-packet['body_measured_at']
    elapsed=(packet['native_tick']-proof['body_native_tick'])*.01
    return .05<age<=.2 and retained_allowed(proof,elapsed)
