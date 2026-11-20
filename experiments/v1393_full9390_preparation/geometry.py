"""Full rectangle support over rear2cm/yaw0.1 against the saved all-time ball."""
import math
import numpy as np

class Geometry:
    def __init__(self,known,ball):
        self.normals=np.c_[np.cos(np.arange(64)*math.tau/64),np.sin(np.arange(64)*math.tau/64)]
        self.radius=math.hypot(.74,.375);self.corners=[(-.14,-.375),(-.14,.375),(.74,-.375),(.74,.375)]
        assert len(ball)==3 and all(math.isfinite(x) for x in ball) and ball[2]>=0.
        obstacles=[]
        for x,y,hx,hy in known['known_rectangles']:
            assert hx>0 and hy>0
            obstacles.append(x*self.normals[:,0]+y*self.normals[:,1]-hx*abs(self.normals[:,0])-hy*abs(self.normals[:,1]))
        for x,y,radius in [*known['known_circles'],ball]:
            assert radius>=0.
            obstacles.append(x*self.normals[:,0]+y*self.normals[:,1]-radius)
        self.obstacle_minimum=np.asarray(obstacles);assert np.isfinite(self.obstacle_minimum).all()

    def margins(self,states):
        a=np.asarray(states,dtype=float);assert a.ndim==2 and a.shape[1]>=3 and len(a)>0 and np.isfinite(a).all()
        yaw=a[:,2];rear=a[:,:2]-.3*np.c_[np.cos(yaw),np.sin(yaw)]
        maximum=np.full((len(a),64),-math.inf)
        for x,y in self.corners:
            X=x*np.cos(yaw)-y*np.sin(yaw);Y=x*np.sin(yaw)+y*np.cos(yaw)
            A=X[:,None]*self.normals[:,0]+Y[:,None]*self.normals[:,1]
            B=-Y[:,None]*self.normals[:,0]+X[:,None]*self.normals[:,1]
            at=np.arctan2(B,A);value=np.where(abs(at)<=.1,np.hypot(A,B),A*math.cos(.1)+abs(B)*math.sin(.1));maximum=np.maximum(maximum,value)
        support=rear@self.normals.T+maximum+.02
        obstacle=np.min(np.max(self.obstacle_minimum[None,:,:]-support[:,None,:],axis=2),axis=1)
        # Four world planes are included exactly among the64 normals.
        world=np.min(5-support[:,[0,16,32,48]],axis=1)
        return np.minimum(obstacle,world)

    def tube(self,states):
        a=np.asarray(states,dtype=float);margins=self.margins(a)
        rear=a[:,:2]-.3*np.c_[np.cos(a[:,2]),np.sin(a[:,2])]
        interpolation=float(np.max(np.linalg.norm(np.diff(rear,axis=0),axis=1)+self.radius*abs(np.diff(a[:,2])))) if len(a)>1 else 0.
        return float(np.min(margins))-interpolation
