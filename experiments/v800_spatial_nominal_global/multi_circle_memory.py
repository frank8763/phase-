"""Static multi-object memory using causal range endpoints and circle shape priors.
No environment model, obstacle IDs, centers, radii, or true object counts are read.
Unmodeled returns remain as occupied points. This is an empirical map estimate.
"""
from collections import deque
import numpy as np
from planner import PointMemory

def components(points,distance=.20):
    points=np.asarray(points,float).reshape(-1,2);cells={}
    for i,p in enumerate(points):cells.setdefault(tuple(np.floor(p/distance).astype(int)),[]).append(i)
    seen=np.zeros(len(points),bool);groups=[]
    for initial in range(len(points)):
        if seen[initial]:continue
        seen[initial]=True;stack=[initial];group=[]
        while stack:
            i=stack.pop();group.append(i);cx,cy=np.floor(points[i]/distance).astype(int)
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    for j in cells.get((cx+dx,cy+dy),[]):
                        if not seen[j]and np.sum((points[i]-points[j])**2)<=distance**2:seen[j]=True;stack.append(j)
        groups.append(np.asarray(group,int))
    return groups

def fit_surface(points):
    points=np.asarray(points,float);points=points[::max(1,len(points)//600)]
    if len(points)<20:return None,{'status':'TOO_FEW_POINTS','n':len(points)}
    A=np.c_[2*points,np.ones(len(points))];raw=np.linalg.lstsq(A,np.sum(points**2,axis=1),rcond=None)[0]
    radius=np.sqrt(max(.001,raw[2]+raw[:2]@raw[:2]));params=np.r_[raw[:2],np.clip(radius,.04,.8)]
    for _ in range(25):
        delta=params[:2]-points;length=np.maximum(np.linalg.norm(delta,axis=1),1e-9);residual=length-params[2]
        weight=1/np.sqrt(1+(residual/.025)**2);jac=np.c_[delta/length[:,None],-np.ones(len(points))]
        change=np.linalg.solve(jac.T@(weight[:,None]*jac)+1e-5*np.eye(3),-jac.T@(weight*residual));change*=min(1.,.1/max(np.linalg.norm(change),1e-9));params+=change;params[2]=np.clip(params[2],.04,.8)
        if np.linalg.norm(change)<1e-6:break
    radial=np.linalg.norm(points-params[:2],axis=1);residual=radial-params[2]
    angle=np.sort(np.arctan2(points[:,1]-params[1],points[:,0]-params[0]));coverage=2*np.pi-np.max(np.diff(np.r_[angle,angle[0]+2*np.pi]));rmse=float(np.sqrt(np.mean(np.minimum(residual**2,.09**2))))
    stats={'coverage_rad':float(coverage),'robust_rmse_m':rmse,'center':params[:2].tolist(),'radius_m':float(params[2]),'points':len(points)}
    if coverage<1.9 or rmse>.055 or params[2]>=.75:return None,{'status':'MODEL_REJECTED',**stats}
    radius=max(float(params[2])+.035,float(np.quantile(radial,.9))+.01)
    return np.r_[params[:2],radius],{'status':'CYLINDER_ESTIMATE','envelope_radius_m':radius,**stats}

class MultiCircleMemory:
    def __init__(self):self.frames=deque(maxlen=120);self.tracks=[];self.points=PointMemory()
    def update(self,sensor,rect,circ,step,origin):
        raw=self.points.update(sensor,rect,circ,step,persist=True)
        fresh=PointMemory().update(sensor,rect,circ,step,persist=False);origin=np.asarray(origin,float)
        if len(fresh):
            d=fresh-origin;length=np.linalg.norm(d,axis=1);corrected=fresh-.04*d/np.maximum(length[:,None],1e-9);self.frames.append(corrected)
        stats=[]
        if len(self.frames)>=12:
            points=np.vstack(self.frames)
            # Voxel averaging prevents sensor density from defining the topology.
            keys=np.floor(points/.03).astype(int);unique,indices=np.unique(keys,axis=0,return_inverse=True);sums=np.zeros((len(unique),2));np.add.at(sums,indices,points);points=sums/np.bincount(indices)[:,None]
            for ids in components(points):
                estimate,record=fit_surface(points[ids]);stats.append(record)
                if estimate is None:continue
                distances=[np.linalg.norm(x[:2]-estimate[:2])for x in self.tracks]
                if distances and min(distances)<.35:self.tracks[int(np.argmin(distances))]=estimate
                else:self.tracks.append(estimate)
        remaining=np.ones(len(raw),bool)
        for estimate in self.tracks:
            # Only points explained by this observed surface can be replaced.
            remaining &= np.abs(np.linalg.norm(raw-estimate[:2],axis=1)-(estimate[2]-.035))>.14
        models=np.array(self.tracks).reshape(-1,3)
        return models,raw[remaining],{'status':'STATIC_MULTI_SURFACE_MAP','model_count':len(models),'unmodeled_points':int(remaining.sum()),'fits':stats,'shape_prior':'static_circles','hidden_geometry_used':False,'uncertainty_certificate':'NOT_CALIBRATED'}
