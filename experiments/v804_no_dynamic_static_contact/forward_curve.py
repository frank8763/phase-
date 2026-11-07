"""Early smooth forward proposal using only the already computed causal path.
No actor, future measurements, custom task waypoint or user-painted pixels.
"""
import math,numpy as np

def propose(path,current,field,wheel_base,max_steer):
 source=np.asarray(path,float);meta=dict(schema='V786_EARLY_FORWARD_HERMITE_01',selected=False,original_path=source.tolist(),hidden_world_geometry_used=False,source='current causal geometric path, actual public robot pose, registered vehicle steering bound')
 if len(source)<5 or np.any(source[:,3]!=1)or abs(current[2])>=math.pi/3:return source,dict(meta,reason='NOT_REGISTERED_FORWARD_GEOMETRY')
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(source[:,:2],axis=0),axis=1))];k=int(np.argmin(abs(arc-.5*arc[-1])));end=source[k];dx=float(end[0]-current[0])
 if dx<1. or np.any(np.diff(source[:k+1,0])<-.001)or abs(end[2])>=math.pi/3:return source,dict(meta,reason='NO_MONOTONE_FORWARD_PREFIX')
 n=math.ceil(dx/.01)+1;x=np.linspace(current[0],end[0],n);u=(x-current[0])/dx;ya=float(current[1]);yb=float(end[1]);da=math.tan(float(current[2]));db=math.tan(float(end[2]));y=(2*u**3-3*u**2+1)*ya+(u**3-2*u**2+u)*dx*da+(-2*u**3+3*u**2)*yb+(u**3-u**2)*dx*db
 slope=((6*u**2-6*u)*ya+(3*u**2-4*u+1)*dx*da+(-6*u**2+6*u)*yb+(3*u**2-2*u)*dx*db)/dx
 second=((12*u-6)*ya+(6*u-4)*dx*da+(-12*u+6)*yb+(6*u-2)*dx*db)/(dx*dx);yaw=np.arctan(slope);prefix=np.c_[x,y,yaw,np.ones(n)];curvature=np.abs(second)/(1+slope*slope)**1.5
 # Convex second derivative bound and max |slope| give a continuous intersample Hausdorff bound.
 max_second=float(max(abs(second[0]),abs(second[-1])));max_slope=float(max(abs(da),abs(db),np.max(abs(slope)))+max_second*(dx/(n-1))*.5);step=dx/(n-1);hausdorff=.5*step*(math.sqrt(1+max_slope**2)+math.hypot(.44,.375)*max_second)
 minimum=float(field.pose_values(prefix[:,:3]).min());continuous=minimum-hausdorff;bound=math.tan(max_steer)/wheel_base
 meta.update(guide_anchor_index=k,guide_anchor=end.tolist(),sample_count=n,minimum_prefix_static_clearance_m=minimum,between_sample_bound_m=hausdorff,continuous_static_clearance_lower_m=continuous,maximum_sample_curvature=float(curvature.max()),continuous_curvature_upper=max_second,steering_curvature_limit=bound)
 # Use the more conservative continuous second-derivative bound, not just sampled curvature.
 if continuous<.18 or max_second>bound+1e-10:return source,dict(meta,reason='CONTINUOUS_GEOMETRY_OR_CURVATURE_REJECT')
 dense_arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(prefix[:,:2],axis=0),axis=1))];samples=np.r_[np.arange(0,dense_arc[-1],.04),dense_arc[-1]];resampled=np.c_[np.interp(samples,dense_arc,prefix[:,0]),np.interp(samples,dense_arc,prefix[:,1]),np.interp(samples,dense_arc,prefix[:,2]),np.ones(len(samples))];combined=np.vstack([resampled,source[k+1:]]);meta.update(selected=True,reason='KNOWN_MAP_FORWARD_PREFIX_QUALIFIED',unchanged_suffix_points=len(source)-k-1,dense_prefix=prefix.tolist(),returned_prefix_count=len(resampled),returned_arc_spacing_m=.04)
 return combined,meta
