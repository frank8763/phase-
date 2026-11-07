"""Experimental multi-frame cylinder surface model, from measured hits only.
Shape prior: one static circular obstacle in the single_event benchmark. The
reported uncertainty is empirical; it is not a calibrated safety certificate.
"""
from collections import deque
import numpy as np
from planner import PointMemory

class CircleMemory:
    def __init__(self):self.frames=deque(maxlen=120);self.last=None
    def update(self,sensor,rect,circ,step,origin):
        fresh=PointMemory().update(sensor,rect,circ,step,persist=False)
        origin=np.asarray(origin,float)
        if len(fresh):
            delta=fresh-origin;length=np.linalg.norm(delta,axis=1)
            # Frozen ray marcher returns first occupied sample at spacing .08m.
            # Mid-bin correction is a measurement-model estimate, not truth.
            points=fresh-.04*delta/np.maximum(length[:,None],1e-9)
            self.frames.append((step,points))
        if len(self.frames)<12:return None,{'status':'WARMUP','frames':len(self.frames)}
        points=np.vstack([x[1]for x in self.frames]);points=points[::max(1,len(points)//600)]
        A=np.c_[2*points,np.ones(len(points))];b=(points**2).sum(1);raw=np.linalg.lstsq(A,b,rcond=None)[0];center=raw[:2];radius=np.sqrt(max(.001,raw[2]+center@center))
        params=np.r_[center,np.clip(radius,.04,.8)]
        for _ in range(25):
            difference=params[:2]-points;distance=np.maximum(np.linalg.norm(difference,axis=1),1e-9)
            residual=distance-params[2];weights=1/np.sqrt(1+(residual/.025)**2)
            jacobian=np.c_[difference/distance[:,None],-np.ones(len(points))]
            delta=np.linalg.solve(jacobian.T@(weights[:,None]*jacobian)+1e-5*np.eye(3),-jacobian.T@(weights*residual))
            delta*=min(1.,.1/max(np.linalg.norm(delta),1e-9));params+=delta;params[2]=np.clip(params[2],.04,.8)
            if np.linalg.norm(delta)<1e-6:break
        center=params[:2];radius=float(params[2]);residual=np.linalg.norm(points-center,axis=1)-radius
        angle=np.sort(np.arctan2(points[:,1]-center[1],points[:,0]-center[0]));coverage=2*np.pi-np.max(np.diff(np.r_[angle,angle[0]+2*np.pi]))
        robust_rmse=float(np.sqrt(np.mean(np.minimum(residual**2,.09**2))))
        if coverage<1.9 or robust_rmse>.055 or radius>=.75:
            return None,{'status':'MODEL_REJECTED','coverage_rad':coverage,'rmse_m':robust_rmse,'radius_m':radius}
        # Explicit empirical surface allowance. Does not weaken the .15m robot
        # clearance rule, but changes the map estimate; needs held-out coverage.
        allowance=.035
        envelope_radius=max(radius+allowance,float(np.quantile(np.linalg.norm(points-center,axis=1),.9))+.01)
        envelope=np.r_[center,envelope_radius]
        self.last=envelope
        return envelope,{'status':'CYLINDER_ESTIMATE','center':center.tolist(),'radius_m':radius,'envelope_radius_m':envelope_radius,'allowance_m':allowance,'coverage_rad':coverage,'robust_rmse_m':robust_rmse,'frames':len(self.frames),'points':len(points),'shape_prior':'single_static_circle','uncertainty_certificate':'NOT_CALIBRATED','hidden_geometry_used':False}
