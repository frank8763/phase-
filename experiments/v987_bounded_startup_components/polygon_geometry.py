"""Vectorized rectangle-to-causal-convex-set distance. No model/truth input."""
import math
import numpy as np
from support_envelope import polygon

def distances(poses,poly):
    p=np.asarray(poses,float);q=np.asarray(poly,float)
    assert p.ndim==2 and p.shape[1]==3 and len(q)>=3 and np.isfinite(p).all()and np.isfinite(q).all()
    c=np.cos(p[:,2]);s=np.sin(p[:,2]);dx=q[None,:,0]-p[:,None,0];dy=q[None,:,1]-p[:,None,1]
    local=np.stack([c[:,None]*dx+s[:,None]*dy,-s[:,None]*dx+c[:,None]*dy],axis=2)
    box=np.array([[-.44,-.375],[.44,-.375],[.44,.375],[-.44,.375]])
    corners=np.stack([p[:,None,0]+c[:,None]*box[None,:,0]-s[:,None]*box[None,:,1],p[:,None,1]+s[:,None]*box[None,:,0]+c[:,None]*box[None,:,1]],axis=2)
    edge=np.roll(q,-1,axis=0)-q;n=np.c_[-edge[:,1],edge[:,0]];length=np.sum(edge*edge,axis=1);assert np.all(length>1e-24)
    qp=q@n.T;bp=corners@n.T
    sep=np.any((bp.min(axis=1)>qp.max(axis=0))|(bp.max(axis=1)<qp.min(axis=0)),axis=1)
    sep |= np.any((local.min(axis=1)>[.44,.375])|(local.max(axis=1)<[-.44,-.375]),axis=1)
    # Vertex of center polygon to solid local rectangle.
    a=np.linalg.norm(np.maximum(abs(local)-[.44,.375],0.),axis=2).min(axis=1)
    # Rectangle corner to each center-polygon segment.
    delta=corners[:,:,None,:]-q[None,None,:,:];t=np.clip(np.sum(delta*edge,axis=3)/length,0.,1.)
    b=np.linalg.norm(delta-t[:,:,:,None]*edge,axis=3).min(axis=(1,2))
    return np.where(sep,np.minimum(a,b),0.)

def terminal_values(poses,prior,reserve):
    from cycle_backup import cycle_upper
    return distances(poses,polygon(cycle_upper(prior)+1e-6))-.1-reserve-2e-6

def route_check(points,prior):
    from snapshot_geometry import dense
    samples=dense(points);value=float(terminal_values(samples,prior,.06).min());gap=.005+math.hypot(.44,.375)*.005
    return dict(passed=value-gap>=.155,lower_m=value-gap,sample_lower_m=value,gap_reserve_m=gap,samples=len(samples),geometry_only=True)
