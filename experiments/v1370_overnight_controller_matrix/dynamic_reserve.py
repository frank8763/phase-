"""Command-aware empirical reserve against a causal all-future occupied disk.

The 25cm intervention boundary, 22cm route floor and 15cm physical gate
remain distinct. Between 22 and 25cm, allow only a nominal command whose
full rectangular footprint does not consume any additional clearance.
This geometric preview is not a plant stopping or recursive safety proof.
"""
import math
import numpy as np
from observed_route import nominal_clearance

EARLY_MARGIN = .25
RECOVERY_MARGIN = .22
PREVIEW_SECONDS = .5


def check(body, ball, v, w):
    assert len(body) == 5 and np.isfinite([*body, v, w]).all(), 'DYNAMIC_RESERVE_BAD_FEEDBACK'
    assert len(ball) == 3 and np.isfinite(ball).all() and ball[2] >= 0, 'DYNAMIC_RESERVE_BAD_BALL'
    current = nominal_clearance(body, ball[:2], ball[2])
    proof = dict(current_dynamic_clearance_m=current, early_intervention_m=EARLY_MARGIN,
                 unchanged_recovery_margin_m=RECOVERY_MARGIN,
                 empirical_monitor_not_stopping_certificate=True)
    if abs(v) <= 1e-10 and abs(w) <= 1e-10:
        return True, dict(proof, reason='EXACT_ZERO_BRAKE_COMMAND')
    if current > EARLY_MARGIN:
        return True, dict(proof, reason='DYNAMIC_RECOVERY_RESERVE_INTACT')
    yaw = body[2]
    rear = np.array([body[0]-.3*math.cos(yaw), body[1]-.3*math.sin(yaw)])
    times = np.linspace(0., PREVIEW_SECONDS, 11)
    angles = yaw + w*times
    if abs(w) > 1e-10:
        xs = rear[0] + v/w*(np.sin(angles)-math.sin(yaw))
        ys = rear[1] - v/w*(np.cos(angles)-math.cos(yaw))
    else:
        xs = rear[0] + v*times*math.cos(yaw)
        ys = rear[1] + v*times*math.sin(yaw)
    centers = np.c_[xs+.3*np.cos(angles), ys+.3*np.sin(angles), angles]
    values = np.array([nominal_clearance(p, ball[:2], ball[2]) for p in centers])
    allowed = bool(current >= RECOVERY_MARGIN and values.min() >= current-1e-8)
    return allowed, dict(proof, reason='NONDECREASING_DYNAMIC_COMMAND' if allowed else 'EARLY_DYNAMIC_BRAKE',
                         command_geometry_minimum_m=float(values.min()),
                         command_geometry_terminal_m=float(values[-1]),
                         preview_s=PREVIEW_SECONDS, preview_samples=len(values),
                         actual_dynamics_certificate=False)
