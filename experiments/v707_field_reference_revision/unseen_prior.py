"""Public controlled-course initial exclusion prior; never read actor truth."""
import numpy as np
ORIGIN=np.array([-4.,-2.])
INITIAL_CENTER_CLEAR_RADIUS=3.
COORDINATE_SPEED=.12
ACTOR_RADIUS=.10

def set_public_origin(xy):
 global ORIGIN
 value=np.asarray(xy,float)
 assert value.shape==(2,) and np.isfinite(value).all()
 ORIGIN=value.copy()

def state_at(now):
 return {'center':None,'velocity':[0.,0.],'age_s':0.,'observed_this_frame':False,'time':float(now),'hidden_world_geometry_used':False,'certified_unknown_rays':0,'information_mode':'UNSEEN_PRIOR','initial_clear_center_radius_m':INITIAL_CENTER_CLEAR_RADIUS,'initial_clear_origin_xy':ORIGIN.tolist(),'radial_speed_bound_m_s':float(np.sqrt(2)*COORDINATE_SPEED),'prior_time_origin':0.,'prior_source':'preregistered controlled-course startup clearing, not inferred from missing returns','scope':'unseen actor occupies complement of shrinking initial exclusion disk'}

def clearance(field,poses,state,times):
 assert state['information_mode']=='UNSEEN_PRIOR'
 p=np.asarray(poses,float).reshape(-1,3);times=np.asarray(times,float).reshape(-1)
 c,s=np.cos(p[:,2]),np.sin(p[:,2]);center=p[:,:2]+np.c_[c*field.center_local[0]-s*field.center_local[1],s*field.center_local[0]+c*field.center_local[1]]
 corners=np.array([[-1,-1],[-1,1],[1,1],[1,-1]])*field.half
 rotated=center[:,None,:]+np.stack((c[:,None]*corners[None,:,0]-s[:,None]*corners[None,:,1],s[:,None]*corners[None,:,0]+c[:,None]*corners[None,:,1]),axis=-1)
 farthest=np.linalg.norm(rotated-np.asarray(state['initial_clear_origin_xy']),axis=2).max(axis=1)
 radius=np.maximum(0,state['initial_clear_center_radius_m']-state['radial_speed_bound_m_s']*(state['time']+times-state['prior_time_origin']))
 return radius-farthest-ACTOR_RADIUS
