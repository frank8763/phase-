"""Causal outer reachability on continuous cells, with complete-cell exclusions."""
import math,sys
from pathlib import Path
import numpy as np
import cv2
from free_certificate import reliable_rays,free_samples,body_points,old_lower
cv2.setNumThreads(1)
GRID=.01
LOWER=-6.
UPPER=6.
AXIS=LOWER+np.arange(round((UPPER-LOWER)/GRID)+1)*GRID
HALF_DIAGONAL=GRID/math.sqrt(2)
SLACK=1e-4
RADIUS=.10
SPEED_AXIS=.12
SPEED=.08  # Declared course Euclidean speed cap; historical grid propagation remains conservative

def canonical_distance(possible):
    # The exact squared distance between lattice centres is integral. Canonicalize
    # OpenCV's sub-ULP square-root variations before exposing it to decisions.
    raw=cv2.distanceTransform((~possible).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE).astype(np.float64)
    squared=raw*raw;integer=np.rint(squared)
    assert float(np.max(abs(squared-integer)))<.25,'AMBIGUOUS_LATTICE_DISTANCE_ROUNDING'
    return np.sqrt(integer)*GRID

def exclusion(packet,origin):
    xx,yy=np.meshgrid(AXIS,AXIS,indexing='ij')
    # Original public initial clearing remains valid as an independently aged constraint.
    r=max(0.,3.-SPEED*float(packet['time']))
    free=np.hypot(xx-origin[0],yy-origin[1])+HALF_DIAGONAL<r-SLACK
    rays=reliable_rays(packet);samples=free_samples(rays);effective=RADIUS-SLACK-HALF_DIAGONAL
    for point in samples:
        lo=np.maximum(0,np.ceil((point-effective-LOWER)/GRID).astype(int));hi=np.minimum(len(AXIS)-1,np.floor((point+effective-LOWER)/GRID).astype(int))
        if np.any(lo>hi):continue
        sx=AXIS[lo[0]:hi[0]+1];sy=AXIS[lo[1]:hi[1]+1]
        free[lo[0]:hi[0]+1,lo[1]:hi[1]+1]|=(sx[:,None]-point[0])**2+(sy[None,:]-point[1])**2<effective**2
    free[[0,-1],:]=False;free[:,[0,-1]]=False
    return free,len(rays),len(samples)

def propagate(possible,dt):
    assert 0.<dt<.081,'NONCAUSAL_OR_MISSING_TIME_STEP'
    steps=int(math.ceil(SPEED_AXIS*dt/GRID))
    expanded=cv2.dilate(possible.astype(np.uint8),np.ones((2*steps+1,2*steps+1),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=1).astype(bool)
    expanded[[0,-1],:]=True;expanded[:,[0,-1]]=True
    return expanded,steps

class RecursiveDomain:
    def __init__(self,origin):self.origin=np.asarray(origin,float);self.time=None;self.possible=None;self.distance=None;self.last={}
    def update(self,packet):
        now=float(packet['time']);free,rays,samples=exclusion(packet,self.origin)
        if self.time is None:
            assert abs(now)<1e-12,'INITIAL_EXCLUSION_TIME_CHANGED'
            predicted=np.ones_like(free);steps=0
        else:predicted,steps=propagate(self.possible,now-self.time)
        self.possible=predicted&~free;self.possible[[0,-1],:]=True;self.possible[:,[0,-1]]=True
        self.distance=canonical_distance(self.possible)
        self.time=now;self.last=dict(time=now,reliable_rays=rays,reliable_samples=samples,propagation_cells_per_axis=steps,predicted_possible_cells=int(predicted.sum()),current_exclusion_cells=int(free.sum()),retained_possible_cells=int(self.possible.sum()),strict_temporal_intersection=True)
        return self.last
    def point_lower(self,points,times):
        p=np.asarray(points,float);flat=p.reshape(-1,2);t=np.broadcast_to(times,p.shape[:-1]).reshape(-1);assert np.all(t>=self.time-1e-10)
        ix=np.rint((flat-LOWER)/GRID).astype(int);valid=((ix>=0)&(ix<len(AXIS))).all(axis=1);ix=np.clip(ix,0,len(AXIS)-1);query=LOWER+ix*GRID
        lower=self.distance[ix[:,0],ix[:,1]].astype(float)-np.linalg.norm(query-flat,axis=1)-HALF_DIAGONAL-SLACK;lower[~valid]=0.
        if hasattr(self,'history_height'):
            historical=np.maximum(0.,self.history_height[ix[:,0],ix[:,1]].astype(np.float64)/1e6-SPEED*self.time-np.linalg.norm(query-flat,axis=1))
            historical[~valid]=0.;lower=np.maximum(lower,historical)
        return (np.maximum(0.,lower)-SPEED*np.maximum(0.,t-self.time)).reshape(p.shape[:-1])
    def original_body_lower(self,poses,times):
        points,cover=body_points(poses)
        value=self.point_lower(points,np.asarray(times)[:,None]).min(axis=1)-cover-RADIUS
        return np.maximum(value,old_lower(poses,times,self.origin))

    def body_lower(self,poses,times):
        from refined_body import refined
        return refined(self,poses,times)
