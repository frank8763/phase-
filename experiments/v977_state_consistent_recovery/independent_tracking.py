"""Saved-body nearest-reference envelopes; no planner, controller or model imports."""
import math
import numpy as np


def check(path, actual, maximum_gap_m):
    path=np.asarray(path,float);actual=np.asarray(actual,float)
    assert path.ndim==actual.ndim==2 and path.shape[1]==actual.shape[1]==3
    assert len(path)>=2 and len(actual)>0 and np.isfinite(path).all() and np.isfinite(actual).all()
    assert 0<maximum_gap_m<=.0125+1e-9
    position=heading=0.
    for start in range(0,len(actual),128):
        block=actual[start:start+128]
        distance=np.linalg.norm(block[:,None,:2]-path[None,:,:2],axis=2)
        closest=np.argmin(distance,axis=1)
        position=max(position,float(distance[np.arange(len(block)),closest].max()))
        angle=block[:,2]-path[closest,2]
        heading=max(heading,float(abs(np.arctan2(np.sin(angle),np.cos(angle))).max()))
    allowance=.758770385*maximum_gap_m/2
    return dict(passed=position<=.04 and heading+allowance<=.035,
                maximum_position_error_m=position,maximum_heading_error_rad=heading,
                conservative_reference_sampling_heading_allowance_rad=allowance,
                unchanged_position_limit_m=.04,unchanged_heading_limit_rad=.035,
                native_or_peer_samples=len(actual),models=0,integrations=0)
