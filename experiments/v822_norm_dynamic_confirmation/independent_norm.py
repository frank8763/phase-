"""Independent raw geometric lower bound; no online refinement imports."""
from types import SimpleNamespace
import numpy as np
from exact_footprint import pose_values

def radial_lower(base,poses,state,times):
    p=np.asarray(poses,float).reshape(-1,3);t=np.asarray(times,float).reshape(-1)
    bounds=np.asarray(state['outer_state_cells'],float);values=[]
    for cell in bounds:
        lo,hi=cell[:2];rect=np.r_[(lo+hi)/2,(hi-lo)/2]
        geometry=SimpleNamespace(half=base.half,center_local=base.center_local,rectangles=rect[None],
            circles=np.empty((0,3)),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-1e6,upper=1e6))
        # Distance to the current centre cell, then disk radius and the public
        # norm-speed displacement bound. Negative values remain conservative.
        values.append(pose_values(geometry,p)-.10-.08*t)
    return np.min(values,axis=0)

def static_field(protocol):
    b=np.asarray(protocol['footprint_bounds']);return SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,
        rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
