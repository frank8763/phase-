"""Observed surface returns to a conservative causal single-actor center ball.

No actor anchor, phase, axis, current truth or future truth is an input.
The public class is one diameter.20 actor with speed<=.08m/s, original
range noise clipped.06 and sampled ray backend step<=.04. This supplies
a deliberately loose center ball, not a velocity estimator or guarantee.
"""
import math
import numpy as np


def static_ranges(xy,yaw,known):
    angles=yaw+np.arange(32)*math.tau/32
    directions=np.c_[np.cos(angles),np.sin(angles)]
    ranges=np.full(32,3.)
    for x,y,hx,hy in known['known_rectangles']:
        a=np.array([x-hx,y-hy])-xy;b=np.array([x+hx,y+hy])-xy
        safe=np.where(abs(directions)<1e-12,1e-12,directions)
        lo=a/safe;hi=b/safe
        enter=np.maximum(np.minimum(lo,hi).max(axis=1),0.);exit=np.maximum(lo,hi).min(axis=1)
        valid=exit>=enter;ranges[valid]=np.minimum(ranges[valid],enter[valid])
    for x,y,r in known['known_circles']:
        delta=xy-[x,y];b=directions@delta;c=delta@delta-r*r;disc=b*b-c
        entry=-b-np.sqrt(np.maximum(disc,0.));valid=(disc>=0)&(entry>=0)
        ranges[valid]=np.minimum(ranges[valid],entry[valid])
    for axis in [0,1]:
        for boundary in [-5.,5.]:
            with np.errstate(divide='ignore',invalid='ignore'):t=(boundary-xy[axis])/directions[:,axis]
            valid=t>=0;ranges[valid]=np.minimum(ranges[valid],t[valid])
    return ranges,directions


class CausalBall:
    def __init__(self,known,horizon_s=1.5):
        assert 0<horizon_s<=3.
        self.known=known;self.horizon=horizon_s;self.last=None;self.center=None;self.last_tick=-1;self.records=[]

    def update(self,*,native_tick,sim_time,center_body,ranges):
        assert native_tick>=self.last_tick and abs(sim_time-native_tick*.01)<1e-7,'CAUSAL_TIME_MISMATCH'
        if native_tick==self.last_tick:return False
        self.last_tick=native_tick
        xy=np.asarray(center_body[:2],float);yaw=float(center_body[2]);ranges=np.asarray(ranges,float)
        assert ranges.shape==(32,) and np.isfinite(ranges).all() and ((ranges>=0)&(ranges<=3)).all()
        expected,directions=static_ranges(xy,yaw,self.known)
        ids=np.where((ranges<2.94)&(ranges+.12<expected))[0]
        if not len(ids):return False
        # First novel ray in fixed published angular order; no truth association.
        ray=int(ids[0]);point=xy+ranges[ray]*directions[ray]
        self.center=point;self.last=sim_time
        self.records.append(dict(native_tick=native_tick,sim_time=sim_time,ray=ray,range=float(ranges[ray]),point=point.tolist(),known_static_range=float(expected[ray])))
        return True

    def occupied_ball(self,sim_time):
        if self.center is None:return None
        assert sim_time>=self.last-1e-8
        # Observed surface→center .10 + noise.06 + backend.04 + position/.01
        # geometry margin .04 = .24; actor radius.10, then causal age/future.
        radius=.24+.10+.08*(max(0.,sim_time-self.last)+self.horizon)
        return self.center.copy(),radius

    def raster(self,grid,sim_time):
        data=np.asarray(grid['data'],dtype=np.int8).reshape(grid['height'],grid['width']).copy()
        ball=self.occupied_ball(sim_time)
        if ball is None:return data
        center,radius=ball;h=grid['resolution'];x=grid['origin'][0]+(np.arange(grid['width'])+.5)*h;y=grid['origin'][1]+(np.arange(grid['height'])+.5)*h
        dx=np.maximum(abs(x-center[0])-h/2,0.);dy=np.maximum(abs(y-center[1])-h/2,0.)
        data[dy[:,None]**2+dx[None,:]**2<=radius**2+1e-12]=100
        return data
