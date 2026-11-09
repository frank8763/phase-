"""Distance to the same outer center polygon; no new dynamics assumption."""
import math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'experiments/v920_native_ingress'),str(R/'experiments/v891_dynamic_consistency_software')]
from cycle_backup import cycle_upper
from support_envelope import polygon

def convex_distance(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float)
    assert a.ndim==b.ndim==2 and a.shape[1]==b.shape[1]==2 and len(a)>=3 and len(b)>=3 and np.isfinite(a).all()and np.isfinite(b).all(),'INVALID_POLYGON'
    separated=False
    for p in [a,b]:
        e=np.roll(p,-1,axis=0)-p;n=np.c_[-e[:,1],e[:,0]];n=n[np.linalg.norm(n,axis=1)>1e-12]
        assert len(n)>=3,'DEGENERATE_POLYGON'
        aa=a@n.T;bb=b@n.T
        separated |= bool(np.any(aa.min(axis=0)>bb.max(axis=0))or np.any(bb.min(axis=0)>aa.max(axis=0)))
    if not separated:return 0.
    def to_edges(p,q):
        d=np.roll(q,-1,axis=0)-q;length=np.sum(d*d,axis=1);assert np.all(length>1e-24),'DEGENERATE_EDGE'
        t=np.clip(np.sum((p[:,None,:]-q[None,:,:])*d[None,:,:],axis=2)/length,0.,1.)
        return float(np.linalg.norm(p[:,None,:]-q[None,:,:]-t[:,:,None]*d[None,:,:],axis=2).min())
    return min(to_edges(a,b),to_edges(b,a))

def rectangle(pose):
    x,y,a=pose;c,s=math.cos(a),math.sin(a)
    return np.array([[-.44,-.375],[.44,-.375],[.44,.375],[-.44,.375]])@np.array([[c,s],[-s,c]])+np.array([x,y])

def terminal_from_polygon(pose,center,reserve):
    assert math.isfinite(reserve)and reserve>=0
    return convex_distance(rectangle(pose),center)-.1-reserve-2e-6

def terminal(pose,prior,reserve):
    return terminal_from_polygon(pose,polygon(cycle_upper(prior)+1e-6),reserve)
