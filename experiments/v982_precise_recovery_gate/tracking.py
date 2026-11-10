"""Same committed analytical reference; finer conservative online observation guard."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('v981_frozen_reference_math', R/'experiments/v977_state_consistent_recovery/state_reference.py')
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)

GRID_M = .0005
POSITION_LIMIT_M = .04
HEADING_LIMIT_RAD = .035
# Keep an explicit reserve beyond half-grid displacement/curvature. Qualified
# independently on the fixed saved inputs; not a floating-point proof for all maps.
POSITION_NUMERICAL_RESERVE_M = 1e-5
HEADING_NUMERICAL_RESERVE_RAD = 1e-5


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def dense_reference(plan):
    initial = np.asarray(plan['initial_state'], float)
    targets = np.asarray(plan['edge_targets'], float)
    states = np.asarray(plan['state_path'], float)
    path = np.asarray(plan['path'], float)
    assert initial.shape == (4,) and targets.ndim == 1 and 1 <= len(targets) <= 12, 'INVALID_REFERENCE_SHAPE'
    assert np.isfinite(initial).all() and np.isfinite(targets).all(), 'NONFINITE_REFERENCE'
    assert abs(initial[3]) <= reference.MAX_DELTA+1e-10, 'INITIAL_CURVATURE_CHANGED'
    assert abs(targets).max() <= reference.MAX_DELTA+1e-12, 'TARGET_CURVATURE_CHANGED'
    n = round(reference.STEP/GRID_M)
    assert n == 200 and reference.EDGE_N == 8
    rows = [initial[None, :]]
    for target in targets:
        rows.append(reference.primitive(rows[-1][-1], float(target), np.arange(1, n+1)*GRID_M))
    dense = np.vstack(rows)
    coarse = dense[::25]
    assert states.shape == coarse.shape and np.isfinite(states).all(), 'INVALID_COMMITTED_STATE_REFERENCE'
    assert np.max(abs(states-coarse)) <= 1e-10, 'COMMITTED_CURVE_NOT_RECONSTRUCTIBLE'
    assert path.shape == states[:, :3].shape and np.isfinite(path).all(), 'INVALID_COMMITTED_PATH'
    assert np.max(abs(path-states[:, :3])) <= 1e-12, 'STATE_REFERENCE_PATH_MISMATCH'
    assert np.linalg.norm(np.diff(dense[:, :2], axis=0), axis=1).max() <= GRID_M+1e-10
    return dense[:, :3].copy()


class TrackingGuard:
    def __init__(self, plan):
        self.path = copy.deepcopy(plan['path'])
        self.path_sha256 = fingerprint(self.path)
        self.dense = dense_reference(plan)
        self.dense.flags.writeable = False
        self.dense_sha256 = hashlib.sha256(self.dense.tobytes()).hexdigest()
        self.mode = 'FOLLOW_ACCEPT_PENDING'
        self.last_proof = None

    def monitor_body(self, packet):
        assert fingerprint(self.path) == self.path_sha256, 'COMMITTED_REFERENCE_MUTATED'
        assert hashlib.sha256(self.dense.tobytes()).hexdigest() == self.dense_sha256, 'TRACKING_CERTIFICATE_MUTATED'
        if self.mode not in {'FOLLOW_RECOVERY', 'STOPPED_REPLAN'}:
            return
        pose = np.asarray(packet['body'][:3], float)
        assert pose.shape == (3,) and np.isfinite(pose).all(), 'NONFINITE_RECOVERY_OBSERVATION'
        squared = np.sum((self.dense[:, :2]-pose[:2])**2, axis=1)
        i = int(np.argmin(squared))
        position = math.sqrt(float(squared[i]))
        difference = pose[2]-float(self.dense[i, 2])
        heading = abs(math.atan2(math.sin(difference), math.cos(difference)))
        position_allowance = GRID_M/2+POSITION_NUMERICAL_RESERVE_M
        heading_allowance = reference.K*GRID_M/2+HEADING_NUMERICAL_RESERVE_RAD
        self.last_proof = dict(reference_index=i, reference_pose=self.dense[i].tolist(),
                               position_error_m=position, heading_error_rad=heading,
                               position_upper_m=position+position_allowance,
                               heading_upper_rad=heading+heading_allowance,
                               position_limit_m=POSITION_LIMIT_M, heading_limit_rad=HEADING_LIMIT_RAD,
                               maximum_arc_grid_m=GRID_M, reference_unchanged=True)
        assert position+position_allowance <= POSITION_LIMIT_M, 'ONLINE_RECOVERY_POSITION_ENVELOPE_FAILED'
        assert heading+heading_allowance <= HEADING_LIMIT_RAD, 'ONLINE_RECOVERY_HEADING_ENVELOPE_FAILED'
