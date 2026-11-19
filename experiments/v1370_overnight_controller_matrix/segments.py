"""Ordered single-gear paths; current-pose and latest-field cusp admission.

Uses only the registered path, measured vehicle pose and causal occupancy.
No command sign is flipped. Original controller and native gear guard remain.
"""
import math
from types import SimpleNamespace
import numpy as np
from observed_route import geometry


def split(path):
    p = np.asarray(path, float)
    assert p.ndim == 2 and p.shape[1] == 4 and len(p) >= 2 and np.isfinite(p).all(), 'SEGMENT_BAD_PATH'
    assert np.isin(p[:, 3], [-1., 1.]).all(), 'SEGMENT_BAD_GEAR'
    result = []; start = 0; gear = int(p[1, 3])
    for i in range(2, len(p)):
        if int(p[i, 3]) != gear:
            result.append(dict(gear=gear, poses=p[start:i, :3].tolist()))
            start = i-1; gear = int(p[i, 3])
    result.append(dict(gear=gear, poses=p[start:, :3].tolist()))
    assert all(len(s['poses']) >= 2 for s in result), 'SEGMENT_EMPTY_EDGE'
    # Every original edge appears exactly once; the cusp pose is shared.
    assert sum(len(s['poses'])-1 for s in result) == len(p)-1
    return result


def direction_allowed(v, gear):
    assert gear in [-1, 1]
    return abs(v) < .005 or v*gear > 0.


def validate(segment, body, known, ball, guard=.22):
    """Geometric admission, not a physical dynamics/tracking certificate.

The original path is left intact. A stopped feedback tracker may be up to
12cm/0.20rad from its cusp. Both that actual pose and the interpolated capture
gap must meet the SAME22cm latest-field planning gate before resubmission.
"""
    poses = np.asarray(segment['poses'], float)
    if poses.ndim != 2 or poses.shape[1] != 3 or len(poses) < 2 or not np.isfinite(poses).all():
        return False, dict(reason='SEGMENT_MALFORMED')
    rear = np.array([body[0]-.3*math.cos(body[2]), body[1]-.3*math.sin(body[2]), body[2]])
    distance = float(np.linalg.norm(rear[:2]-poses[0, :2]))
    heading = abs(math.atan2(math.sin(rear[2]-poses[0, 2]), math.cos(rear[2]-poses[0, 2])))
    if distance > .12 or heading > .20:
        return False, dict(reason='CUSP_CAPTURE_OUTSIDE_REGISTERED_BOUND', start_distance_m=distance, start_heading_rad=heading)
    circles = list(known['known_circles'])
    if ball is not None: circles.append([*ball[0], ball[1]])
    field = SimpleNamespace(half=np.array([.44, .375]), center_local=np.array([.3, 0.]),
                            rectangles=np.array(known['known_rectangles']), circles=np.array(circles),
                            sensor_points=[], sensor_extra=0., config=SimpleNamespace(lower=-5., upper=5.))
    dense = []
    for a, b in zip(np.vstack([rear, poses[:-1]]), poses):
        angle = math.atan2(math.sin(b[2]-a[2]), math.cos(b[2]-a[2]))
        count = max(5, int(math.ceil(np.linalg.norm(b[:2]-a[:2])/.008)), int(math.ceil(abs(angle)/.006)))
        for t in np.linspace(0., 1., count, endpoint=False):
            dense.append([a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1]), a[2]+t*angle])
    dense.append(poses[-1]); minimum = float(np.min(geometry.pose_values(field, dense)))
    return minimum >= guard-1e-8, dict(reason='LATEST_FIELD_SEGMENT_AND_CAPTURE_GAP_CHECK',
                                       minimum_clearance_m=minimum, required_m=guard,
                                       start_distance_m=distance, start_heading_rad=heading,
                                       samples=len(dense), dynamics_certificate=False)
