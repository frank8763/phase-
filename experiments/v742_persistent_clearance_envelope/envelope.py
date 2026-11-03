"""Deterministic persistent lower-distance certificates; no actor access."""
import math
import numpy as np
from recursive_domain import AXIS,GRID,LOWER,HALF_DIAGONAL,SLACK,SPEED
from free_certificate import body_points,old_lower

class Envelope:
    def __init__(self,origin):
        self.origin=np.asarray(origin,float).copy();self.time=None;self.lower=None
    def update(self,domain):
        assert np.array_equal(domain.origin,self.origin)
        fresh=np.maximum(0.,domain.distance-HALF_DIAGONAL-SLACK)
        if self.time is None:
            assert abs(domain.time)<1e-12,'ENVELOPE_MUST_BEGIN_FROM_ACTUAL_T0'
            self.lower=fresh.copy()
        else:
            dt=float(domain.time-self.time);assert 0.<dt<.081,'NONCAUSAL_OR_MISSING_PACKET'
            previous=self.lower;self.lower=np.maximum(fresh,np.maximum(0.,previous-SPEED*dt))
            assert np.all(self.lower>=previous-SPEED*dt-1e-12)
        self.time=float(domain.time);assert np.all(self.lower>=fresh)
    def copy(self):
        out=Envelope(self.origin);out.time=self.time;out.lower=self.lower.copy();return out
    def point_lower(self,points,times):
        p=np.asarray(points,float);flat=p.reshape(-1,2);t=np.broadcast_to(times,p.shape[:-1]).reshape(-1)
        assert self.time is not None and np.all(t>=self.time-1e-10),'FUTURE_PACKET_OR_NONCAUSAL_QUERY'
        ids=np.rint((flat-LOWER)/GRID).astype(int);valid=((ids>=0)&(ids<len(AXIS))).all(axis=1);ids=np.clip(ids,0,len(AXIS)-1);g=LOWER+ids*GRID
        value=np.maximum(0.,self.lower[ids[:,0],ids[:,1]]-np.linalg.norm(g-flat,axis=1));value[~valid]=0.
        return(value-SPEED*np.maximum(0.,t-self.time)).reshape(p.shape[:-1])
    def body_lower(self,poses,times):
        points,cover=body_points(poses);result=self.point_lower(points,np.asarray(times)[:,None]).min(axis=1)-cover-.10
        return np.maximum(result,old_lower(poses,times,self.origin))
