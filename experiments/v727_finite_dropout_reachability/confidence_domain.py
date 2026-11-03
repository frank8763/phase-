"""Finite-task confidence reachability, conditional on the declared dropout model."""
import math,hashlib
import cv2
import numpy as np
from recursive_domain import RecursiveDomain,GRID,LOWER,AXIS,HALF_DIAGONAL,SLACK,exclusion,canonical_distance
MAX_PUBLIC_STEPS=1200
RAYS_PER_PACKET=47
DROPOUT_UPPER=.05
TASK_ERROR_BUDGET=1e-8
MAX_OPPORTUNITIES=(MAX_PUBLIC_STEPS+1)*RAYS_PER_PACKET
MISS_THRESHOLD=math.ceil(math.log(TASK_ERROR_BUDGET/MAX_OPPORTUNITIES)/math.log(DROPOUT_UPPER))
ERROR_UPPER=MAX_OPPORTUNITIES*DROPOUT_UPPER**MISS_THRESHOLD
IMPOSSIBLE=255
assert MISS_THRESHOLD==10 and ERROR_UPPER<=TASK_ERROR_BUDGET
cv2.setNumThreads(1)

def sample_points(xy,angle,maximum,clip):
    origin=np.asarray(xy,np.float32);direction=np.asarray([math.cos(angle),math.sin(angle)],np.float32);samples=[];d=0.
    while d<maximum-clip-SLACK:
        samples.append((origin+d*direction).astype(float));d+=.08
    return np.asarray(samples),origin.astype(float),direction.astype(float)

def ray_cell_patch(xy,angle,maximum,clip):
    """Whole cells covered by an actual pre-clipping ray-march sample, not a line."""
    samples,origin,direction=sample_points(xy,angle,maximum,clip)
    assert len(samples)>0
    effective=.10-HALF_DIAGONAL-SLACK
    lo=np.maximum(0,np.ceil((samples.min(axis=0)-effective-LOWER)/GRID).astype(int));hi=np.minimum(len(AXIS)-1,np.floor((samples.max(axis=0)+effective-LOWER)/GRID).astype(int))
    if np.any(lo>hi):return None
    x=AXIS[lo[0]:hi[0]+1,None];y=AXIS[None,lo[1]:hi[1]+1]
    projected=((x-origin[0])*direction[0]+(y-origin[1])*direction[1])/(float(direction@direction)*.08)
    index=np.clip(np.rint(projected).astype(int),0,len(samples)-1)
    mask=(x-samples[index,0])**2+(y-samples[index,1])**2<effective**2
    return (slice(lo[0],hi[0]+1),slice(lo[1],hi[1]+1)),mask

def opportunities(packet):
    total=np.zeros((len(AXIS),len(AXIS)),np.uint8);nonmaximum=np.zeros_like(total,bool);max_rays=0
    for tag,count,clip in [('lidar',32,.06),('depth',15,.09)]:
        z=np.asarray(packet[tag],float);maximum=float(packet[tag+'_max_range'])
        assert z.shape==(count,) and np.all(np.isfinite(z))and np.all((z>=0)&(z<=1))and maximum==3.
        angles=(np.arange(count)*2*np.pi/count if tag=='lidar'else np.linspace(-np.deg2rad(35),np.deg2rad(35),count))+packet['yaw']
        for value,angle in zip(z,angles):
            patch=ray_cell_patch(packet['xy'],float(angle),maximum,clip)
            if patch is None:continue
            slices,mask=patch;total[slices]+=mask
            if value<1.:nonmaximum[slices]|=mask
            else:max_rays+=1
    return total,nonmaximum,max_rays

def counter_step(previous,total,nonmaximum,free,steps):
    if previous is None:prior=np.zeros(total.shape,np.uint8)
    else:prior=cv2.erode(previous,np.ones((2*steps+1,2*steps+1),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=0)
    alive=prior<IMPOSSIBLE
    updated=np.minimum(prior.astype(np.uint16)+total,MISS_THRESHOLD).astype(np.uint8)
    updated[nonmaximum&alive]=0
    updated[(~alive)|free|(updated>=MISS_THRESHOLD)]=IMPOSSIBLE
    updated[[0,-1],:]=0;updated[:,[0,-1]]=0
    return updated

class ConfidenceDomain(RecursiveDomain):
    def __init__(self,origin):
        super().__init__(origin);self.cost=None;self.updates=0
    def update(self,packet):
        assert packet['step']==self.updates and self.updates<=MAX_PUBLIC_STEPS,'REUSED_PACKET_OR_FINITE_RISK_BUDGET_EXCEEDED'
        now=float(packet['time']);free,rays,samples=exclusion(packet,self.origin)
        if self.time is None:assert abs(now)<1e-12;steps=0
        else:
            dt=now-self.time;assert 0.<dt<.081,'NONCAUSAL_OR_MISSING_TIME_STEP'
            steps=math.ceil(.12*dt/GRID)
        total,nonmaximum,max_rays=opportunities(packet)
        self.cost=counter_step(self.cost,total,nonmaximum,free,steps);self.possible=self.cost<IMPOSSIBLE
        self.time=now;self.updates+=1;self.distance=canonical_distance(self.possible)
        self.last=dict(time=now,updates=self.updates,reliable_rays=rays,reliable_samples=samples,propagation_cells_per_axis=steps,retained_possible_cells=int(self.possible.sum()),maximum_range_rays=max_rays,
            consecutive_required_misses=MISS_THRESHOLD,maximum_task_ray_opportunities=MAX_OPPORTUNITIES,conditional_task_error_upper=ERROR_UPPER,
            risk_model='Independent clipped sensor dropout <=.05 per ray; geometry/state predictable before its noise; no arbitrary correlated outage guarantee.',
            counter_sha256=hashlib.sha256(self.cost.tobytes()).hexdigest(),confidence_not_deterministic=True,hidden_world_geometry_used=False)
        return self.last
