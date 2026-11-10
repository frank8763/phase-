"""Same physical.04/.035 tracking gates, independent new response reference."""
import math
import numpy as np
from saved_qualification import reconstruct
from state_reference import GAIN,RATE_COUPLING,VIRTUAL_RATE,REFERENCE_SPEED,K
def check(plan,actual):
    curve=reconstruct(plan['initial_state'],plan['edge_targets'])[:,:3];path=np.asarray(plan['path'])
    assert path.shape==curve[::25].shape and abs(path-curve[::25]).max()<1e-5,'REFERENCE_NOT_RECONSTRUCTIBLE'
    actual=np.asarray(actual);position=heading=0.
    for pose in actual:
        distance=np.linalg.norm(curve[:,:2]-pose[:2],axis=1);i=int(np.argmin(distance));position=max(position,float(distance[i]))
        angle=pose[2]-curve[i,2];heading=max(heading,abs(math.atan2(math.sin(angle),math.cos(angle))))
    hbound=GAIN*K+abs(RATE_COUPLING)*VIRTUAL_RATE/REFERENCE_SPEED
    pu=position+.00025+1e-5;hu=heading+hbound*.00025+1e-5
    return dict(passed=pu<=.04 and hu<=.035,maximum_position_error_m=position,maximum_heading_error_rad=heading,
                maximum_position_upper_m=pu,maximum_heading_upper_rad=hu,unchanged_position_limit_m=.04,unchanged_heading_limit_rad=.035,
                independent_method='new response reference midpoint.5mm',samples=len(actual),models=0,integrations=0)
