"""Causal bounded-noise interval tracking for the declared single circular actor.
Only sensor packets, known prior and public motion-class bounds enter this file.
"""
from collections import deque
from types import MethodType,SimpleNamespace
import numpy as np
from range_circle_memory import measured_rays
from empty_sample_contract import contract_box
RADIUS=.10
SPEED=.12
ACCEL=.04
EPS=1e-4
NORMALS=np.c_[np.cos(np.arange(16)*np.pi/8),np.sin(np.arange(16)*np.pi/8)]

def known_sample(ray,rect,circ):
    # Reproduce ONLY the known prior's 0.08m ray samples, without world truth.
    ds=np.arange(0.,3.000001,.08);origin=np.asarray(ray[:2],np.float32);direction=np.asarray(ray[2:4],np.float32)
    p=(origin[None,:]+ds.astype(np.float32)[:,None]*direction).astype(np.float64)
    hit=np.any((p < -5.)|(p > 5.),axis=1)
    for x,y,hx,hy in np.asarray(rect,np.float32).reshape(-1,4).astype(float):hit|=np.all(abs(p-[x,y])<=[hx,hy],axis=1)
    for x,y,r in np.asarray(circ,np.float32).reshape(-1,3).astype(float):hit|=np.sum((p-[x,y])**2,axis=1)<=r*r
    ids=np.flatnonzero(hit);return float(ds[ids[0]])if len(ids)else 3.

def capsule_constraints(rays,rect,circ):
    rows=[];bounds=[];used=0
    for ray in rays:
        origin=ray[:2];direction=ray[2:4];z,b=ray[4:6]
        if z+b>=known_sample(ray,rect,circ)-EPS:continue
        # A non-dropped return strictly earlier than every compatible known
        # return must come from the sole unknown actor. Its sampled hit point
        # is inside the disk and lies on this bounded range segment.
        a=origin+max(0.,z-b)*direction;c=origin+(z+b)*direction
        rows.extend(NORMALS);bounds.extend(np.maximum(NORMALS@a,NORMALS@c)+RADIUS+EPS);used+=1
        # First-hit information: for the unknown sampled hit P(D) and its
        # immediately previous sample Q(D-0.08), |P-C|<=r<|Q-C|.
        # Subtracting squared distances gives d.C > d.o+(D-0.04)|d|^2.
        # Use the smallest compatible D and conservative float slack.
        # No plane is added if a previous positive-range sample is uncertain.
        if z-b>.08+EPS:
            norm2=float(direction@direction)
            rows.append(-direction)
            bounds.append(-float(direction@origin)-(z-b-.04)*norm2+EPS)
    return np.asarray(rows).reshape(-1,2),np.asarray(bounds),used

def future_boxes(state,times):
    times=np.asarray(times,float).reshape(-1,1)
    lo=np.asarray(state['position_lower']);hi=np.asarray(state['position_upper'])
    vlo=np.asarray(state['velocity_lower']);vhi=np.asarray(state['velocity_upper'])
    lower=np.maximum(lo+times*vlo-.5*ACCEL*times**2,lo-SPEED*times)
    upper=np.minimum(hi+times*vhi+.5*ACCEL*times**2,hi+SPEED*times)
    return lower,upper

def clip_polygon(polygon,normal,bound):
    result=[]
    for first,last in zip(polygon,np.roll(polygon,-1,axis=0)):
        a=float(first@normal-bound);b=float(last@normal-bound)
        if a<=0:result.append(first)
        if (a<0<b)or(b<0<a):result.append(first+(last-first)*a/(a-b))
    return np.asarray(result).reshape(-1,2)

class Tracker:
    def __init__(self):
        self.frames=deque(maxlen=64);self.bounds=None;self.previous_time=None;self.last_observation=None
    def update(self,env,rect,circ,step):
        assert float(env.phase17c_lidar_max_range)==float(env.phase17c_depth_max_range)==3.
        return self.update_rays(measured_rays(env),rect,circ,float(env.data.time))
    def update_rays(self,rays,rect,circ,now):
        rays=np.asarray(rays,float).reshape(-1,7);obsA,obsb,used=capsule_constraints(rays,rect,circ)
        if self.bounds is None and not used:
            return [],{'center':None,'velocity':[0.,0.],'age_s':0.,'observed_this_frame':False,'time':now,'hidden_world_geometry_used':False,'certified_unknown_rays':0,'scope':'no actor detected; unobserved-space safety not certified'}
        if self.bounds is None:prior=np.array([[-5.,5.],[-5.,5.],[-SPEED,SPEED],[-SPEED,SPEED]])
        else:
            dt=now-self.previous_time;assert dt>0 and dt<.081,'NONCAUSAL_SENSOR_TIME'
            prior=self.bounds.copy();prior[:2,0]=self.bounds[:2,0]+dt*self.bounds[2:,0]-.5*ACCEL*dt*dt
            prior[:2,1]=self.bounds[:2,1]+dt*self.bounds[2:,1]+.5*ACCEL*dt*dt
            prior[2:,0]=np.maximum(-SPEED,self.bounds[2:,0]-ACCEL*dt);prior[2:,1]=np.minimum(SPEED,self.bounds[2:,1]+ACCEL*dt)
            prior[:2,0]=np.maximum(prior[:2,0],self.bounds[:2,0]-SPEED*dt)
            prior[:2,1]=np.minimum(prior[:2,1],self.bounds[:2,1]+SPEED*dt)
        # Every stored state is an outer interval. Intersect its independently
        # valid finite-time reachable bounds, without point-estimate confidence.
        for t,old in self.frames:
            dt=now-t
            prior[:2,0]=np.maximum(prior[:2,0],np.maximum(old[:2,0]+old[2:,0]*dt-.5*ACCEL*dt*dt,old[:2,0]-SPEED*dt))
            prior[:2,1]=np.minimum(prior[:2,1],np.minimum(old[:2,1]+old[2:,1]*dt+.5*ACCEL*dt*dt,old[:2,1]+SPEED*dt))
            prior[2:,0]=np.maximum(prior[2:,0],old[2:,0]-ACCEL*dt)
            prior[2:,1]=np.minimum(prior[2:,1],old[2:,1]+ACCEL*dt)
        assert np.all(prior[:,0]<=prior[:,1]),'MOTION_OUTER_INTERVAL_INCONSISTENT'
        lo,hi=prior[:2,0],prior[:2,1]
        polygon=np.array([[lo[0],lo[1]],[hi[0],lo[1]],[hi[0],hi[1]],[lo[0],hi[1]]])
        for normal,bound in zip(obsA,obsb):
            polygon=clip_polygon(polygon,normal,bound)
            if not len(polygon):raise RuntimeError('RANGE_MOTION_SET_INCONSISTENT')
        prior[:2,0]=polygon.min(axis=0)-5e-7;prior[:2,1]=polygon.max(axis=0)+5e-7
        prior[:2],empty_stats=contract_box(prior[:2],rays)
        # With bounded acceleration, terminal velocity differs from the
        # interval's average velocity by at most 0.5*a*duration per coordinate.
        for t,old in self.frames:
            dt=now-t
            prior[2:,0]=np.maximum(prior[2:,0],(prior[:2,0]-old[:2,1])/dt-.5*ACCEL*dt)
            prior[2:,1]=np.minimum(prior[2:,1],(prior[:2,1]-old[:2,0])/dt+.5*ACCEL*dt)
        assert np.all(prior[:,0]<=prior[:,1]),'VELOCITY_OUTER_INTERVAL_INCONSISTENT'
        self.bounds=prior;self.previous_time=now;self.frames.append((now,prior.copy()))
        if used:self.last_observation=now
        lo=prior[:2,0];hi=prior[:2,1];center=(lo+hi)/2;half=(hi-lo)/2
        state={'center':center.tolist(),'velocity':prior[2:].mean(axis=1).tolist(),'position_lower':lo.tolist(),'position_upper':hi.tolist(),'velocity_lower':prior[2:,0].tolist(),'velocity_upper':prior[2:,1].tolist(),'age_s':now-self.last_observation,'observed_this_frame':bool(used),'certified_unknown_rays':used,'empty_sample_contract':empty_stats,'retained_frames':len(self.frames),'time':now,'current_outer_rectangle':[*center,*(half+RADIUS)],'hidden_world_geometry_used':False,'scope':'bounded-noise capsule and reachable interval outer set under declared single-actor assumptions; not calibrated probability'}
        return [],state

def paired_rectangle_clearance(field,poses,centers,half):
    p=np.asarray(poses);c=np.cos(p[:,2]);s=np.sin(p[:,2]);hx,hy=field.half
    ego=p[:,:2]+np.c_[c*field.center_local[0]-s*field.center_local[1],s*field.center_local[0]+c*field.center_local[1]]
    delta=centers-ego;ex=abs(c)*hx+abs(s)*hy;ey=abs(s)*hx+abs(c)*hy;rx,ry=half[:,0],half[:,1]
    sep=np.maximum.reduce([abs(delta[:,0])-rx-ex,abs(delta[:,1])-ry-ey,abs(delta[:,0]*c+delta[:,1]*s)-hx-rx*abs(c)-ry*abs(s),abs(-delta[:,0]*s+delta[:,1]*c)-hy-rx*abs(s)-ry*abs(c)])
    signs=np.array([[-1,-1],[-1,1],[1,1],[1,-1]]);local=signs*field.half
    corners=ego[:,None,:]+np.stack([c[:,None]*local[None,:,0]-s[:,None]*local[None,:,1],s[:,None]*local[None,:,0]+c[:,None]*local[None,:,1]],axis=-1)
    d1=np.linalg.norm(np.maximum(abs(corners-centers[:,None,:])-half[:,None,:],0),axis=-1).min(axis=1)
    other=centers[:,None,:]+signs[None,:,:]*half[:,None,:];d=other-ego[:,None,:]
    transformed=np.stack([d[:,:,0]*c[:,None]+d[:,:,1]*s[:,None],-d[:,:,0]*s[:,None]+d[:,:,1]*c[:,None]],axis=-1)
    d2=np.linalg.norm(np.maximum(abs(transformed)-field.half,0),axis=-1).min(axis=1)
    return np.where(sep>0,np.minimum(d1,d2),sep)-RADIUS

def install_time_gate(field,state,mode,known_circles,known_rectangles):
    from exact_footprint import pose_values
    static=SimpleNamespace(half=field.half,center_local=field.center_local,rectangles=np.asarray(known_rectangles).reshape(-1,4),circles=np.asarray(known_circles).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=field.config)
    def trajectory_values(self,poses,dt):
        values=pose_values(static,poses)
        if state['center']is None:return values
        times=np.arange(1,len(poses)+1)*dt if mode=='predictive'else np.zeros(len(poses))
        lo,hi=future_boxes(state,times)
        return np.minimum(values,paired_rectangle_clearance(self,np.asarray(poses),(lo+hi)/2,(hi-lo)/2))
    field.trajectory_values=MethodType(trajectory_values,field)

def forecast_corridor_world(world,state,horizon=2.4,spacing=.4):
    result=dict(world)
    if state['center']is None:return result
    times=np.linspace(0,horizon,int(round(horizon/spacing))+1);lo,hi=future_boxes(state,times)
    # Global speed bound covers any centre motion between sample times, also
    # including the radius expansion of this forward reachable outer set.
    pad=(SPEED+ACCEL*horizon)*spacing/2
    result['rectangles']=[*world['rectangles'],*[[*(a+b)/2,*((b-a)/2+RADIUS+pad)]for a,b in zip(lo,hi)]]
    return result
