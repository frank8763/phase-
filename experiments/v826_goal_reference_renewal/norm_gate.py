"""Declared-course Euclidean speed refinement of tracked collision lower bounds.

For each causal current position cell C_j and every t >= 0, an actor moving
with ||v|| <= .08 is in C_j (+) B(.08*t). Distance to a fixed robot body is
1-Lipschitz, hence d(body,C_j)-radius-.08*t is a valid clearance lower bound.
Min over cells, min with static geometry, max with the original full bound.
No truth position, velocity or scene phase is used. The wider .12/axis class
is intentionally NOT claimed. Thresholds and original 328 native ticks remain.
"""
from types import MethodType
import numpy as np
from motion_tracker import paired_rectangle_clearance
from exact_footprint import pose_values

PUBLIC_NORM_SPEED=.08
RADIUS=.10

def radial_values(field,poses,state,times):
    p=np.asarray(poses,float).reshape(-1,3);t=np.asarray(times,float).reshape(-1)
    assert len(p)==len(t) and np.isfinite(p).all()and np.isfinite(t).all()and np.all(t>=-1e-10)
    cells=np.asarray(state['outer_state_cells'],float)
    assert cells.ndim==3 and cells.shape[1:]==(4,2)and 0<len(cells)<=256
    low,high=cells[:,0],cells[:,1];k=len(cells)
    current=paired_rectangle_clearance(field,np.repeat(p,k,axis=0),
        np.tile((low+high)/2,(len(p),1)),np.tile((high-low)/2,(len(p),1))).reshape(len(p),k)
    return current.min(axis=1)-PUBLIC_NORM_SPEED*np.maximum(0.,t)

def refine(field,state,mode,known_circles,known_rectangles):
    old_at_times=field.causal_values_at_times
    if state['center']is None:return field
    # Radius is already subtracted by paired_rectangle_clearance. Static
    # geometry must remain an upper cap on the clearance lower bound.
    from types import SimpleNamespace
    static=SimpleNamespace(half=field.half,center_local=field.center_local,
        rectangles=np.asarray(known_rectangles).reshape(-1,4),circles=np.asarray(known_circles).reshape(-1,3),
        sensor_points=[],sensor_extra=0.,config=field.config)
    def at_times(self,poses,times):
        poses=np.asarray(poses,float).reshape(-1,3);times=np.asarray(times,float).reshape(-1)
        original=old_at_times(poses,times)
        refined=np.minimum(pose_values(static,poses),radial_values(self,poses,state,times))
        answer=np.maximum(original,refined)
        assert np.isfinite(answer).all()
        return answer
    def current(self,poses):return at_times(self,poses,np.zeros(len(poses)))
    def trajectory(self,poses,dt):
        t=np.arange(1,len(poses)+1)*dt if mode=='predictive'else np.zeros(len(poses))
        return at_times(self,poses,t)
    field.original_causal_values_at_times=old_at_times
    field.causal_values_at_times=MethodType(at_times,field)
    field.pose_values=MethodType(current,field)
    field.trajectory_values=MethodType(trajectory,field)
    field.declared_norm_motion_class=dict(norm_speed_m_s=PUBLIC_NORM_SPEED,
        original_per_axis_speed_m_s=.12,original_broader_class_claimed=False,
        radius_m=RADIUS,hidden_world_geometry_used=False,
        source='Public declared course motion class; no actor config input.')
    return field
