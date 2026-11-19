"""Known-map recovery reserve, not a universal dynamic stopping proof.

The physical15cm and whole-route22cm gates are unchanged. This earlier
intervention monitors the actually measured footprint instead of waiting
until the controller's shorter collision margin has already been consumed.
"""
import math
from types import SimpleNamespace
import numpy as np
from observed_route import geometry

EARLY_MARGIN = .245
RECOVERY_MARGIN = .22


def check(known, body, v, w):
    assert len(body)==5 and np.isfinite([*body,v,w]).all(), 'RECOVERY_RESERVE_BAD_FEEDBACK'
    yaw=body[2]
    rear=np.array([body[0]-.3*math.cos(yaw),body[1]-.3*math.sin(yaw),yaw])
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),
        rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),
        sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    current=float(geometry.pose_values(field,[rear])[0])
    result=dict(current_known_clearance_m=current,early_intervention_m=EARLY_MARGIN,
                unchanged_recovery_margin_m=RECOVERY_MARGIN,
                empirical_monitor_not_stopping_certificate=True)
    if abs(v)<.005 or current>=EARLY_MARGIN:
        return True,dict(result,reason='ZERO_OR_RECOVERY_RESERVE_INTACT')
    # A stopped vehicle near the intervention boundary must still be allowed
    # to move along or away from the wall without consuming clearance. Only the current command is previewed; no
    # plant state, future actor truth, or stored command is substituted.
    times=np.linspace(0.,.5,11);angle=yaw+w*times
    if abs(w)>1e-10:
        poses=np.c_[rear[0]+v/w*(np.sin(angle)-math.sin(yaw)),
                    rear[1]-v/w*(np.cos(angle)-math.cos(yaw)),angle]
    else:
        poses=np.c_[rear[0]+v*times*math.cos(yaw),rear[1]+v*times*math.sin(yaw),angle]
    clearance=geometry.pose_values(field,poses)
    escape=bool(current>=RECOVERY_MARGIN and clearance.min()>=current-1e-8 and clearance[-1]>=current-1e-8)
    return escape,dict(result,reason='NONDECREASING_RECOVERY_COMMAND' if escape else 'EARLY_RECOVERY_BRAKE',
                       command_geometry_minimum_m=float(clearance.min()),
                       command_geometry_terminal_m=float(clearance[-1]),
                       preview_s=.5,actual_dynamics_certificate=False)
