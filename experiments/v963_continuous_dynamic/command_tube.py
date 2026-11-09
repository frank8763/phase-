"""Finite command/stop admission; no simulator or privileged actor input.

The .04m/.035rad residuals are empirical platform qualification limits, NOT a
theorem about every state. Time includes measurement age and a bounded delivery
delay. A new observation is necessary to renew this finite permission.
"""
import math, sys
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(R/'experiments/v891_dynamic_consistency_software'),
                str(R/'experiments/v881_timing_accounting_continuation'),str(R/'experiments/v864_diagnosis'),str(R/'experiments/v855_renewal_worker')]
from support_envelope import NORMALS
from snapshot_geometry import field
from exact_footprint import pose_values

COMMIT_S = .2
BRAKE_S = 2.
SETTLE_S = .5
POSITION_RESIDUAL_M = .04
ANGLE_RESIDUAL_RAD = .035
DELIVERY_S = .05
MAX_BODY_SPEED = .13
MAX_BODY_YAW_RATE = .16
MAX_COMMAND_SPEED = .1
MAX_CURVATURE = .758770385
DT = .02
HALF = np.array([.44, .375])
RADIUS = float(np.linalg.norm(HALF))

def nominal(body, v, w, times):
    """Constant bounded command then stationary brake endpoint (residual covers stop)."""
    t = np.minimum(np.asarray(times, float), COMMIT_S)
    x, y, a = np.asarray(body[:3], float)
    angles = a + w*t
    if abs(w) < 1e-10:
        px, py = x + v*t*math.cos(a), y + v*t*math.sin(a)
    else:
        px, py = x + v/w*(np.sin(angles)-math.sin(a)), y-v/w*(np.cos(angles)-math.cos(a))
    return np.c_[px, py, angles]

def admit(packet, source, v, w, known, now):
    numbers = [*packet['body'], packet['sent_at'], source['source_age_s'], v, w, now]
    assert np.isfinite(numbers).all(), 'NONFINITE_COMMAND_CONTRACT'
    assert source['source_native_tick'] <= packet['native_tick'], 'FUTURE_COMMAND_SOURCE'
    body_age = now-packet['body_measured_at']
    assert 0 <= body_age <= .05, 'STALE_COMMAND_BODY'
    assert 0 <= source['source_age_s'] <= .2, 'STALE_COMMAND_SCAN'
    assert abs(v) <= MAX_COMMAND_SPEED+1e-10 and abs(w) <= abs(v)*MAX_CURVATURE+1e-9, 'UNQUALIFIED_COMMAND'
    assert abs(packet['body'][3]) <= MAX_BODY_SPEED and abs(packet['body'][4]) <= MAX_BODY_YAW_RATE, 'UNQUALIFIED_BODY_STATE'
    source_age=source['source_age_s']+max(0.,now-source.get('decision_at',now))
    assert source_age<=.2,'STALE_COMMAND_SCAN'
    times = np.arange(0., COMMIT_S+BRAKE_S+DT/2, DT)
    poses = nominal(packet['body'], v, w, times)
    # Translation/yaw residual, bounded observation/delivery motion and continuous
    # intersample motion. Separation uses unit normals, so additive distances are valid.
    delay = body_age+DELIVERY_S
    position_residual = POSITION_RESIDUAL_M if v*packet['body'][3]<0 else .02
    spatial = position_residual+RADIUS*ANGLE_RESIDUAL_RAD
    spatial += delay*(MAX_BODY_SPEED+RADIUS*MAX_BODY_YAW_RATE)
    spatial += DT*(MAX_BODY_SPEED+RADIUS*MAX_BODY_YAW_RATE+.08)
    static = float(np.min(pose_values(field(known), poses)))-spatial
    support = source['support_bounds']
    dynamic = None
    if support is not None:
        angles=poses[:,2]; forward=np.c_[np.cos(angles),np.sin(angles)]; left=np.c_[-np.sin(angles),np.cos(angles)]
        low=poses[:,:2]@NORMALS.T-HALF[0]*abs(forward@NORMALS.T)-HALF[1]*abs(left@NORMALS.T)
        high=np.asarray(support)[None,:]+.08*(source_age+delay+times[:,None])
        periodic=source.get('periodic')
        if periodic is not None:
            from periodic_support import bounds_from_vertices
            assert periodic['source_tick']<=source['source_native_tick'], 'FUTURE_PERIODIC_SOURCE'
            assert periodic['omega']==.32 and periodic['amplitude']==.25, 'PERIODIC_PRIOR_CHANGED'
            at=source['source_scan_sim_time']+source_age+delay+times
            high=np.minimum(high,bounds_from_vertices(periodic['vertices'],at))
        high=high+.1
        dynamic=float(np.min(np.max(low-high,axis=1)))-spatial
    terminal=None
    if source.get('periodic') is not None:
        from cycle_backup import terminal_bound
        terminal=terminal_bound(poses[-1],source['periodic'],spatial)
    return dict(passed=bool(static>=.155 and (dynamic is None or dynamic>=.155) and (terminal is None or terminal>=.155)),
                terminal_cycle_lower_m=terminal, terminal_cycle_qualified=terminal is not None and terminal>=.155,
                v=float(v), w=float(w), body_native_tick=packet['native_tick'],
                source_native_tick=source['source_native_tick'], body=list(packet['body']),
                body_age_s=body_age, source_age_s=source_age,
                static_lower_m=static, dynamic_lower_m=dynamic, spatial_reserve_m=spatial,
                issued_at=now, expires_at=now+COMMIT_S, commit_s=COMMIT_S,
                brake_s=BRAKE_S, residual_position_m=position_residual,
                residual_angle_rad=ANGLE_RESIDUAL_RAD,
                support_bounds=support, empirical_conditional_contract=True)
