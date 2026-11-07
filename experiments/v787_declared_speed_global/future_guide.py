"""Causal outer projection for spatial proposals; never an execution certificate."""
import numpy as np
from motion_tracker import future_boxes,SPEED,RADIUS
HORIZON=6.56
def route_world(world,state):
    result=dict(world);result['sensor_points']=[]
    if state['center']is None:return result,{'status':'NO_DETECTION_NO_PROJECTION','hidden_world_geometry_used':False}
    times=np.linspace(0,HORIZON,17);lower,upper=future_boxes(state,times)
    padding=SPEED*float(np.max(np.diff(times)))/2+1e-5
    lo=lower.min(axis=0)-padding;hi=upper.max(axis=0)+padding
    center=(lo+hi)/2;half=(hi-lo)/2+RADIUS
    result['rectangles']=[*world['rectangles'],[*center,*half]]
    return result,{'status':'CAUSAL_GLOBAL_OUTER_PROJECTION','horizon_s':HORIZON,'sample_times_s':times.tolist(),'per_coordinate_between_sample_padding_m':padding,'projected_center_lower':lo.tolist(),'projected_center_upper':hi.tolist(),'radius_m':RADIUS,'hidden_world_geometry_used':False,'scope':'conservative spatial proposal only; native time gate unchanged'}
