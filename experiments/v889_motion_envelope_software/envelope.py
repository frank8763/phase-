"""Causal bounded-return single-actor position enclosure; no model or actor truth."""
import math
import numpy as np
RADIUS=.10
SPEED=.08
NOISE=.06
EPS=.0001
HORIZON=1.5
MAP_LATENCY_RESERVE=1.0
NORMALS=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
def clip(poly,n,b):
    result=[]
    for a,z in zip(poly,np.roll(poly,-1,axis=0)):
        da=float(a@n-b);dz=float(z@n-b)
        if da<=0:result.append(a)
        if (da<0<dz)or(dz<0<da):result.append(a+(z-a)*da/(da-dz))
    return np.asarray(result).reshape(-1,2)
def packet_only(packet):
    if not set(packet).issuperset({'native_tick','time','xy','yaw','ranges'}):raise ValueError('MISSING_MEASURED_SCAN_POSE')
    ranges=np.asarray(packet['ranges'],float)
    if ranges.shape!=(32,)or not np.isfinite(ranges).all()or np.any(ranges<0)or np.any(ranges>3.00001):raise ValueError('INVALID_ORIGINAL_SCAN')
    if not np.isfinite([*packet['xy'],packet['yaw'],packet['time']]).all():raise ValueError('NONFINITE_SCAN_POSE')
    return ranges
class Envelope:
    def __init__(self,known,lidar):
        self.known=known;self.lidar=lidar;self.bounds=None;self.when=None;self.last_hit=None;self.latest=None;self.rows=[]
    def update(self,packet):
        from types import SimpleNamespace
        z=packet_only(packet);now=float(packet['time'])
        if self.when is not None and now<=self.when:raise ValueError('NONCAUSAL_OR_DUPLICATE_SCAN')
        origin=np.asarray(packet['xy'],np.float32);yaw=float(packet['yaw'])
        known_env=SimpleNamespace(robot_xy=origin,robot_yaw=yaw,map_min=-5.,map_max=5.,rect_obstacles=np.asarray(self.known['known_rectangles'],np.float32),circle_obstacles=np.asarray(self.known['known_circles'],np.float32))
        expected=self.lidar(known_env,32,3.).astype(float)*3.
        # A strict positive return earlier than every bounded-noise known return
        # must come from the sole unknown actor. No-return/dropout creates no hit.
        used=np.flatnonzero((z>0.)&(z<3.-NOISE-EPS)&(z+NOISE<expected-EPS))
        if self.bounds is None:
            lower=np.asarray([-5.,-5.]);upper=np.asarray([5.,5.])
        else:
            dt=now-self.when
            lower=self.bounds[0]-SPEED*dt;upper=self.bounds[1]+SPEED*dt
        if self.bounds is not None or len(used):
            polygon=np.asarray([[lower[0],lower[1]],[upper[0],lower[1]],[upper[0],upper[1]],[lower[0],upper[1]]])
            for i in used:
                direction=np.asarray([math.cos(yaw+2*math.pi*i/32),math.sin(yaw+2*math.pi*i/32)],np.float32).astype(float)
                a=origin.astype(float)+max(0.,z[i]-NOISE)*direction;b=origin.astype(float)+(z[i]+NOISE)*direction
                for normal,bound in zip(NORMALS,np.maximum(NORMALS@a,NORMALS@b)+RADIUS+EPS):
                    polygon=clip(polygon,normal,float(bound))
                    if not len(polygon):raise ValueError('RANGE_MOTION_ENCLOSURE_EMPTY')
                if z[i]-NOISE>.08+EPS:
                    bound=-float(direction@origin.astype(float))-(z[i]-NOISE-.04)*float(direction@direction)+EPS
                    polygon=clip(polygon,-direction,bound)
                    if not len(polygon):raise ValueError('FIRST_HIT_ENCLOSURE_EMPTY')
            self.bounds=np.asarray([polygon.min(axis=0)-5e-7,polygon.max(axis=0)+5e-7])
        self.when=now
        if len(used):self.last_hit=now
        self.latest=dict(time=now,native_tick=packet['native_tick'],information_mode='TRACKED'if self.bounds is not None else 'UNSEEN_REACTIVE',certified_unknown_rays=used.tolist(),position_lower=None if self.bounds is None else self.bounds[0].tolist(),position_upper=None if self.bounds is None else self.bounds[1].tolist(),last_hit_time=self.last_hit,geometry_truth_used=False)
        self.rows.append(self.latest.copy());return self.latest
    def rectangle(self,now,horizon=HORIZON,latency=MAP_LATENCY_RESERVE):
        if self.bounds is None:return None
        age=float(now)-self.when
        if age<-.00001 or horizon<0 or latency<0:raise ValueError('INVALID_FORECAST_TIME')
        pad=RADIUS+SPEED*(max(0.,age)+horizon+latency)
        return [*(self.bounds[0]-pad),*(self.bounds[1]+pad)]
def raster(rect,width=1000,height=1000,resolution=.01,origin=(-5.,-5.)):
    grid=np.zeros((height,width),np.int8)
    if rect is not None:
        lo=np.floor((np.asarray(rect[:2])-origin)/resolution).astype(int);hi=np.floor((np.asarray(rect[2:])-origin)/resolution).astype(int)
        lo=np.maximum(lo,0);hi=np.minimum(hi,[width-1,height-1])
        if np.all(lo<=hi):grid[lo[1]:hi[1]+1,lo[0]:hi[0]+1]=100
    return grid
