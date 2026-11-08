"""16-normal outer position set, Euclidean speed propagation; no actor truth."""
import math,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v889_motion_envelope_software'))
from envelope import RADIUS,SPEED,NOISE,EPS,HORIZON,MAP_LATENCY_RESERVE,NORMALS,clip,packet_only

def polygon(bounds):
    # Axis normals are present; this initial rectangle bounds their intersection.
    b=np.asarray(bounds,float)
    p=np.asarray([[-b[8],-b[12]],[b[0],-b[12]],[b[0],b[4]],[-b[8],b[4]]])
    for n,v in zip(NORMALS,b):
        p=clip(p,n,float(v))
        if not len(p):raise ValueError('EMPTY_SUPPORT_ENCLOSURE')
    return p

class SupportEnvelope:
    def __init__(self,known,lidar):
        self.known=known;self.lidar=lidar;self.support=None;self.when=None
        self.last_hit=None;self.latest=None;self.rows=[]
    def update(self,packet):
        z=packet_only(packet);now=float(packet['time'])
        if self.when is not None and now<=self.when:raise ValueError('NONCAUSAL_OR_DUPLICATE_SCAN')
        origin=np.asarray(packet['xy'],np.float32);yaw=float(packet['yaw'])
        env=SimpleNamespace(robot_xy=origin,robot_yaw=yaw,map_min=-5.,map_max=5.,rect_obstacles=np.asarray(self.known['known_rectangles'],np.float32),circle_obstacles=np.asarray(self.known['known_circles'],np.float32))
        expected=self.lidar(env,32,3.).astype(float)*3.
        used=np.flatnonzero((z>0.)&(z<3.-NOISE-EPS)&(z+NOISE<expected-EPS))
        if self.support is not None:self.support=self.support+SPEED*(now-self.when)
        if len(used):
            p=polygon(self.support)if self.support is not None else np.asarray([[-5.,-5.],[5.,-5.],[5.,5.],[-5.,5.]])
            for i in used:
                d=np.asarray([math.cos(yaw+2*math.pi*i/32),math.sin(yaw+2*math.pi*i/32)],np.float32).astype(float)
                a=origin.astype(float)+max(0.,z[i]-NOISE)*d
                b=origin.astype(float)+(z[i]+NOISE)*d
                for n,v in zip(NORMALS,np.maximum(NORMALS@a,NORMALS@b)+RADIUS+EPS):
                    p=clip(p,n,float(v))
                    if not len(p):raise ValueError('RANGE_MOTION_ENCLOSURE_EMPTY')
                if z[i]-NOISE>.08+EPS:
                    v=-float(d@origin.astype(float))-(z[i]-NOISE-.04)*float(d@d)+EPS
                    p=clip(p,-d,v)
                    if not len(p):raise ValueError('FIRST_HIT_ENCLOSURE_EMPTY')
            # All 16 supports enclose the polygon; small outward numerical guard.
            self.support=np.max(NORMALS@p.T,axis=1)+5e-7
            self.last_hit=now
        self.when=now
        p=None if self.support is None else polygon(self.support)
        self.latest=dict(time=now,native_tick=packet['native_tick'],information_mode='TRACKED'if p is not None else 'UNSEEN_REACTIVE',certified_unknown_rays=used.tolist(),support_bounds=None if p is None else self.support.tolist(),position_polygon=None if p is None else p.tolist(),last_hit_time=self.last_hit,geometry_truth_used=False)
        self.rows.append(self.latest.copy());return self.latest
    def forecast(self,now,horizon=HORIZON,latency=MAP_LATENCY_RESERVE):
        if self.support is None:return None
        age=float(now)-self.when
        if age<-.00001 or horizon<0 or latency<0:raise ValueError('INVALID_FORECAST_TIME')
        return self.support+RADIUS+SPEED*(max(0.,age)+horizon+latency)

def raster_support(bounds,width=1000,height=1000,resolution=.01,origin=(-5.,-5.)):
    grid=np.zeros((height,width),np.int8)
    if bounds is None:return grid
    b=np.asarray(bounds,float);p=polygon(b)
    lo=np.maximum(np.floor((p.min(axis=0)-origin)/resolution).astype(int),0)
    hi=np.minimum(np.floor((p.max(axis=0)-origin)/resolution).astype(int),[width-1,height-1])
    if np.any(lo>hi):return grid
    # If a cell intersects the polytope, its centre satisfies all these relaxed
    # halfspaces. We retain every such cell (some extra cells are conservative).
    x=origin[0]+(np.arange(lo[0],hi[0]+1)+.5)*resolution
    y=origin[1]+(np.arange(lo[1],hi[1]+1)+.5)*resolution
    occupied=np.ones((len(y),len(x)),bool)
    for n,v in zip(NORMALS,b):occupied&=n[0]*x[None,:]+n[1]*y[:,None]<=v+.5*resolution*np.abs(n).sum()+1e-12
    grid[lo[1]:hi[1]+1,lo[0]:hi[0]+1]=occupied.astype(np.int8)*100
    return grid
