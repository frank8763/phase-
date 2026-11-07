"""Robot-only exact projected support bounds for primitive collision geoms.
Cylinder support uses its actual axis, rather than a rotation-invariant sphere.
No environment obstacle geometry is read. Output encloses every active self geom.
"""
import numpy as np

def quaternion_matrices(q):
    w,x,y,z=np.moveaxis(np.asarray(q),-1,0)
    return np.stack([1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)],axis=-1).reshape(*q.shape[:-1],3,3)

class SelfGeometry:
    def __init__(self,model,mj):
        root=mj.mj_name2id(model,mj.mjtObj.mjOBJ_BODY,'mkmini_base');assert root>0
        bodies=set()
        for body in range(1,model.nbody):
            parent=body
            while parent and parent!=root:parent=int(model.body_parentid[parent])
            if parent==root:bodies.add(body)
        self.ids=np.array([i for i in range(model.ngeom)if int(model.geom_bodyid[i])in bodies and (model.geom_contype[i]!=0 or model.geom_conaffinity[i]!=0)],int)
        self.types=np.array(model.geom_type[self.ids]);self.sizes=np.array(model.geom_size[self.ids]);self.mj=mj
        allowed=[int(x)for x in [mj.mjtGeom.mjGEOM_BOX,mj.mjtGeom.mjGEOM_SPHERE,mj.mjtGeom.mjGEOM_CAPSULE,mj.mjtGeom.mjGEOM_CYLINDER]]
        assert all(int(x)in allowed for x in self.types)
    def bounds(self,positions,rotations,root_position,root_quaternion):
        positions=np.asarray(positions);rotations=np.asarray(rotations);root_position=np.asarray(root_position);root_quaternion=np.asarray(root_quaternion)
        yaw=np.arctan2(2*(root_quaternion[...,0]*root_quaternion[...,3]+root_quaternion[...,1]*root_quaternion[...,2]),1-2*(root_quaternion[...,2]**2+root_quaternion[...,3]**2));c=np.cos(yaw);s=np.sin(yaw)
        local=positions-root_position[:,None,:];centers=np.stack((c[:,None]*local[:,:,0]+s[:,None]*local[:,:,1],-s[:,None]*local[:,:,0]+c[:,None]*local[:,:,1]),axis=-1)
        rows=np.stack((c[:,None,None]*rotations[:,:,0,:]+s[:,None,None]*rotations[:,:,1,:],-s[:,None,None]*rotations[:,:,0,:]+c[:,None,None]*rotations[:,:,1,:]),axis=2)
        extents=np.empty_like(centers)
        for kind in np.unique(self.types):
            mask=self.types==kind;size=self.sizes[mask];R=rows[:,mask]
            if kind==int(self.mj.mjtGeom.mjGEOM_BOX):e=np.sum(abs(R)*size[None,:,None,:],axis=-1)
            elif kind==int(self.mj.mjtGeom.mjGEOM_SPHERE):e=np.broadcast_to(size[None,:,0,None],centers[:,mask].shape)
            elif kind==int(self.mj.mjtGeom.mjGEOM_CAPSULE):e=size[None,:,0,None]+size[None,:,1,None]*abs(R[:,:,:,2])
            else:
                axis=R[:,:,:,2];e=size[None,:,1,None]*abs(axis)+size[None,:,0,None]*np.sqrt(np.maximum(0,1-axis**2))
            extents[:,mask]=e
        return np.c_[np.min(centers-extents,axis=1),np.max(centers+extents,axis=1)]
    def actual(self,model,data):
        return self.bounds(data.geom_xpos[self.ids][None,:],data.geom_xmat[self.ids].reshape(1,-1,3,3),data.qpos[:3][None,:],data.qpos[3:7][None,:])[0]

def containment_margin(bounds,domain):
    bounds=np.asarray(bounds);domain=np.asarray(domain)
    return np.minimum(np.min(bounds[...,:2]-domain[:2],axis=-1),np.min(domain[2:]-bounds[...,2:],axis=-1))
