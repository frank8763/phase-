"""Discrete range-consistent static circle hypotheses from causal sensor packets.
Models the frozen .08m ray march and bounded noise explicitly. Hypothesis search
is finite and local: its envelope is not a certified continuous confidence set.
Unexplained observations remain in the occupied point map.
"""
from collections import deque
import numpy as np
from planner import PointMemory
from multi_circle_memory import components,fit_surface

def measured_rays(env):
    origin=np.asarray(env.robot_xy,float);yaw=float(env.robot_yaw);rows=[]
    for name,values,R,b,sigma in [('lidar',env.phase17c_last_lidar,float(env.phase17c_lidar_max_range),.06,.02),('depth',env.phase17c_last_depth,float(env.phase17c_depth_max_range),.09,.03)]:
        values=np.clip(np.asarray(values,float).reshape(-1),0,1);z=values*R
        angle=(np.arange(len(z))*2*np.pi/len(z)if name=='lidar'else np.linspace(-np.deg2rad(35),np.deg2rad(35),len(z)))+yaw
        hit=(z>.05)&(z<R-b-1e-5)
        for a,distance in zip(angle[hit],z[hit]):rows.append([*origin,np.cos(a),np.sin(a),distance,b,sigma])
    return np.asarray(rows,float).reshape(-1,7)

def known_filter(points,rect,circ):
    mask=np.min(np.abs(np.abs(points)-5.),axis=1)>.14
    for x,y,hx,hy in rect:mask&=np.linalg.norm(np.maximum(np.abs(points-[x,y])-[hx,hy],0),axis=1)>.14
    for x,y,r in circ:mask&=np.abs(np.linalg.norm(points-[x,y],axis=1)-r)>.14
    return mask

def assess(theta,rays):
    losses=[];violations=[]
    for start in range(0,len(theta),128):
        t=theta[start:start+128];delta=t[:,None,:2]-rays[None,:,:2];along=np.sum(delta*rays[None,:,2:4],axis=-1)
        disc=t[:,None,2]**2-(np.sum(delta**2,axis=-1)-along**2);half=np.sqrt(np.maximum(disc,0));entry=along-half
        sample=np.ceil(np.maximum(entry,0)/.08-1e-7)*.08
        hit=(disc>=0)&(entry>0)&(sample<=along+half+1e-6)
        error=sample-rays[None,:,4];bad=(~hit)|(np.abs(error)>rays[None,:,5]+5e-5)
        loss=np.mean(np.minimum((error/rays[None,:,6])**2,100)+100*(~hit),axis=1)
        losses.extend(loss);violations.extend(bad.sum(axis=1))
    return np.asarray(losses),np.asarray(violations)

def fit_ranges(rays,initial):
    # Deterministic subsampling controls development compute. Every final
    # admissible hypothesis is then checked against all retained observations.
    selected=rays[::max(1,len(rays)//500)]
    offsets=np.array(np.meshgrid(np.arange(-6,7),np.arange(-6,7),np.arange(-5,6),indexing='ij')).reshape(3,-1).T*.02
    theta=np.asarray(initial)[None,:]+offsets;theta=theta[(theta[:,2]>=.04)&(theta[:,2]<=.7)]
    for resolution in [.005,.00125]:
        loss,bad=assess(theta,selected);order=np.lexsort((loss,bad))[:12]
        offsets=np.array(np.meshgrid(np.arange(-2,3),np.arange(-2,3),np.arange(-2,3),indexing='ij')).reshape(3,-1).T*resolution
        theta=(theta[order,None,:]+offsets[None,:,:]).reshape(-1,3);theta=theta[(theta[:,2]>=.04)&(theta[:,2]<=.7)]
        theta=np.unique(np.round(theta,8),axis=0)
    loss,bad=assess(theta,rays);valid=theta[bad==0]
    if not len(valid):return None,{'status':'NO_RANGE_CONSISTENT_HYPOTHESIS','best_violations':int(bad.min()),'rays':len(rays)}
    accepted_loss=loss[bad==0];best=valid[int(np.argmin(accepted_loss))]
    envelope=float(np.max(np.linalg.norm(valid[:,:2]-best[:2],axis=1)+valid[:,2]))+.005
    return np.r_[best[:2],envelope],{'status':'RANGE_CONSISTENT_DISCRETE_ENVELOPE','center':best[:2].tolist(),'fitted_radius_m':float(best[2]),'envelope_radius_m':envelope,'feasible_hypotheses':len(valid),'rays':len(rays),'best_loss':float(accepted_loss.min()),'grid_last_step_m':.00125,'grid_allowance_m':.005,'continuous_parameter_coverage':'NOT_CERTIFIED'}

class RangeCircleMemory:
    def __init__(self):self.frames=deque(maxlen=200);self.point_memory=PointMemory();self.tracks=[];self.last_fit=-999;self.last_stats=[]
    def update(self,env,rect,circ,step):
        rays=measured_rays(env);points=rays[:,:2]+rays[:,4,None]*rays[:,2:4]
        mask=known_filter(points,rect,circ);rays=rays[mask];points=points[mask]
        raw=self.point_memory.update(points,rect,circ,step,persist=True)
        if len(rays):self.frames.append(rays)
        if len(self.frames)>=12 and (step-self.last_fit>=20 or not len(self.tracks)):
            self.last_fit=step;all_rays=np.vstack(self.frames);corrected=all_rays[:,:2]+(all_rays[:,4,None]-.04)*all_rays[:,2:4];records=[]
            for ids in components(corrected,.20):
                if len(ids)<30:continue
                subset=all_rays[ids];estimate,shape=fit_surface(corrected[ids])
                if estimate is None:continue
                initial=np.r_[shape['center'],shape['radius_m']]
                model,record=fit_ranges(subset,initial);records.append(record)
                if model is None:continue
                distances=[np.linalg.norm(x[:2]-model[:2])for x in self.tracks]
                if distances and min(distances)<.35:self.tracks[int(np.argmin(distances))]=model
                else:self.tracks.append(model)
            self.last_stats=records
        remaining=np.ones(len(raw),bool)
        for model in self.tracks:remaining &= np.linalg.norm(raw-model[:2],axis=1)>model[2]+.12
        return np.asarray(self.tracks).reshape(-1,3),raw[remaining],{'status':'CAUSAL_RANGE_CIRCLE_MAP','models':np.asarray(self.tracks).reshape(-1,3).tolist(),'fits':self.last_stats,'retained_unmodeled_points':int(remaining.sum()),'hidden_geometry_used':False,'parameter_set_scope':'finite local hypothesis search, not a formal safety certificate'}
