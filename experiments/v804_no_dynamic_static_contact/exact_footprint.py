"""Input-only Euclidean rectangle clearance, including diagonal corner separation.
The legacy SAT separation is a conservative lower bound, not Euclidean distance.
"""
from types import MethodType
import numpy as np

def pose_values(self,poses):
    p=np.asarray(poses,float).reshape(-1,3);c,s=np.cos(p[:,2]),np.sin(p[:,2]);hx,hy=self.half
    center=p[:,:2]+np.column_stack((c*self.center_local[0]-s*self.center_local[1],s*self.center_local[0]+c*self.center_local[1]))
    ex,ey=abs(c)*hx+abs(s)*hy,abs(s)*hx+abs(c)*hy
    result=np.minimum.reduce((center[:,0]-ex-self.config.lower,self.config.upper-center[:,0]-ex,center[:,1]-ey-self.config.lower,self.config.upper-center[:,1]-ey))
    if len(self.rectangles):
        rect=self.rectangles;rx,ry=rect[:,2],rect[:,3];delta=rect[None,:,:2]-center[:,None,:]
        sep=np.maximum.reduce((abs(delta[:,:,0])-rx-ex[:,None],abs(delta[:,:,1])-ry-ey[:,None],abs(delta[:,:,0]*c[:,None]+delta[:,:,1]*s[:,None])-hx-rx*abs(c[:,None])-ry*abs(s[:,None]),abs(-delta[:,:,0]*s[:,None]+delta[:,:,1]*c[:,None])-hy-rx*abs(s[:,None])-ry*abs(c[:,None])))
        signs=np.array([[-1,-1],[-1,1],[1,1],[1,-1]])
        local=signs*self.half
        corners=center[:,None,:]+np.stack((c[:,None]*local[None,:,0]-s[:,None]*local[None,:,1],s[:,None]*local[None,:,0]+c[:,None]*local[None,:,1]),axis=-1)
        offset=abs(corners[:,None,:,:]-rect[None,:,None,:2])-rect[None,:,None,2:]
        d1=np.linalg.norm(np.maximum(offset,0),axis=-1).min(axis=-1)
        rc=rect[:,None,:2]+signs[None,:,:]*rect[:,None,2:];rd=rc[None,:,:,:]-center[:,None,None,:]
        transformed=np.stack((rd[:,:,:,0]*c[:,None,None]+rd[:,:,:,1]*s[:,None,None],-rd[:,:,:,0]*s[:,None,None]+rd[:,:,:,1]*c[:,None,None]),axis=-1)
        d2=np.linalg.norm(np.maximum(abs(transformed)-self.half,0),axis=-1).min(axis=-1)
        distance=np.where(sep>0,np.minimum(d1,d2),sep)
        result=np.minimum(result,distance.min(axis=1))
    for points,extra in ((self.circles,0.),(self.sensor_points,self.sensor_extra)):
        if not len(points):continue
        d=points[None,:,:2]-center[:,None,:]
        local=np.stack((d[:,:,0]*c[:,None]+d[:,:,1]*s[:,None],-d[:,:,0]*s[:,None]+d[:,:,1]*c[:,None]),axis=-1)
        residual=abs(local)-self.half;inside=residual.max(axis=-1);distance=np.where(inside<=0,inside,np.linalg.norm(np.maximum(residual,0),axis=-1))
        radii=points[None,:,2]if points.shape[1]==3 else extra
        result=np.minimum(result,(distance-radii).min(axis=1))
    return result

def build(F,world):
    field=F.FootprintMap(world);field.pose_values=MethodType(pose_values,field);return field
