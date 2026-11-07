"""Continuous lower bounds from verified ray prefixes, never from max-range values."""
import math
import numpy as np
import cv2
cv2.setNumThreads(1)
GRID=.025
LOWER=-6.
UPPER=6.
ACTOR_RADIUS=.10
SLACK=1e-4
SPEED=.08  # Declared maximum Euclidean speed, not an inferred observed velocity
AXIS=LOWER+np.arange(round((UPPER-LOWER)/GRID)+1)*GRID
CELL_RHO=GRID/math.sqrt(2)

def reliable_rays(packet):
    rows=[]
    for tag,b,sigma in [('lidar',.06,.02),('depth',.09,.03)]:
        z=np.clip(np.asarray(packet[tag],float),0.,1.)*packet[tag+'_max_range'];R=float(packet[tag+'_max_range'])
        angles=(np.arange(len(z))*2*np.pi/len(z) if tag=='lidar' else np.linspace(-np.deg2rad(35),np.deg2rad(35),len(z)))+packet['yaw']
        for angle,d in zip(angles[(z>.05)&(z<R)],z[(z>.05)&(z<R)]):
            rows.append([*packet['xy'],np.cos(angle),np.sin(angle),d,b,sigma])
    return np.asarray(rows,float).reshape(-1,7)

def free_samples(rays):
    points=[]
    for ray in rays:
        # Match the frozen loop's floating point addition and float32 vector math.
        origin=np.asarray(ray[:2],np.float32);direction=np.asarray(ray[2:4],np.float32);d=0.
        while d<=3.:
            if d>=ray[4]-ray[5]-SLACK:break
            points.append((origin+d*direction).astype(float));d+=.08
    return np.unique(np.asarray(points,float).reshape(-1,2),axis=0)

def body_points(poses,half=(.44,.375)):
    poses=np.asarray(poses,float).reshape(-1,3)
    ax=[np.linspace(-h,h,math.ceil(2*h/.08)+1) for h in half]
    x,y=np.meshgrid(*ax,indexing='ij');local=np.c_[x.ravel(),y.ravel()]
    c,s=np.cos(poses[:,2]),np.sin(poses[:,2])
    points=poses[:,None,:2]+np.stack((c[:,None]*local[None,:,0]-s[:,None]*local[None,:,1],s[:,None]*local[None,:,0]+c[:,None]*local[None,:,1]),axis=-1)
    cover=.5*math.hypot(ax[0][1]-ax[0][0],ax[1][1]-ax[1][0])
    return points,cover

class Certificate:
    def __init__(self,packet,origin):
        self.time=float(packet['time']);self.origin=np.asarray(origin,float)
        xx,yy=np.meshgrid(AXIS,AXIS,indexing='ij')
        radius=max(0.,3.-SPEED*self.time)
        excluded=np.hypot(xx-self.origin[0],yy-self.origin[1])+CELL_RHO < radius-SLACK
        self.rays=reliable_rays(packet);self.samples=free_samples(self.rays)
        effective=ACTOR_RADIUS-SLACK-CELL_RHO
        for point in self.samples:
            lo=np.maximum(0,np.ceil((point-effective-LOWER)/GRID).astype(int));hi=np.minimum(len(AXIS)-1,np.floor((point+effective-LOWER)/GRID).astype(int))
            if np.any(lo>hi):continue
            sx=AXIS[lo[0]:hi[0]+1];sy=AXIS[lo[1]:hi[1]+1]
            excluded[lo[0]:hi[0]+1,lo[1]:hi[1]+1]|=(sx[:,None]-point[0])**2+(sy[None,:]-point[1])**2<effective**2
        excluded[[0,-1],:]=False;excluded[:,[0,-1]]=False
        self.excluded=excluded
        self.distance=cv2.distanceTransform(excluded.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)*GRID

    def point_lower(self,points,absolute_times):
        p=np.asarray(points,float).reshape(-1,2);times=np.broadcast_to(absolute_times,np.asarray(points).shape[:-1]).reshape(-1)
        assert np.all(times>=self.time-1e-10),'NONCAUSAL_FUTURE_PACKET'
        idx=np.rint((p-LOWER)/GRID).astype(int);valid=((idx>=0)&(idx<len(AXIS))).all(axis=1);safe=np.clip(idx,0,len(AXIS)-1)
        nearest=LOWER+safe*GRID;d=self.distance[safe[:,0],safe[:,1]].astype(float)-np.linalg.norm(nearest-p,axis=1)-CELL_RHO-SLACK
        d[~valid]=0.
        return (np.maximum(0.,d)-SPEED*np.maximum(0.,times-self.time)).reshape(np.asarray(points).shape[:-1])

    def body_lower(self,poses,absolute_times):
        pts,cover=body_points(poses)
        return np.min(self.point_lower(pts,np.asarray(absolute_times)[:,None]),axis=1)-cover-ACTOR_RADIUS

def old_lower(poses,absolute_times,origin):
    p=np.asarray(poses,float).reshape(-1,3);local=np.array([[-.44,-.375],[-.44,.375],[.44,-.375],[.44,.375]])
    c,s=np.cos(p[:,2]),np.sin(p[:,2]);corners=p[:,None,:2]+np.stack((c[:,None]*local[None,:,0]-s[:,None]*local[None,:,1],s[:,None]*local[None,:,0]+c[:,None]*local[None,:,1]),axis=-1)
    return np.maximum(0.,3.-SPEED*np.asarray(absolute_times))-np.linalg.norm(corners-origin,axis=2).max(axis=1)-ACTOR_RADIUS

def combined_lower(certificates,poses,absolute_times,origin):
    result=old_lower(poses,absolute_times,np.asarray(origin))
    for certificate in certificates:result=np.maximum(result,certificate.body_lower(poses,absolute_times))
    return result
