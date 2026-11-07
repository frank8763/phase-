"""Fixed saved GPU candidates and original Phase modules, never a navigation launch."""
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace, MethodType

import numpy as np

REPO = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parent
ROOT = REPO / 'runs/v845_gpu_native_qualification'
W = REPO / 'experiments/v842_staged_long_navigation'
PAIR = REPO / 'runs/v842_staged_long_navigation/v843_main_slot02/paired'
CELL = PAIR / 'geometry_memory'
GPU = REPO / 'runs/v844_gpu_proposal_qualification'
STEPS = (374, 683, 893, 1198)
for name in ['runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1',
             'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1',
             'runtime/mk-mini/training/phase14_lidar_depth_nav/envs',
             'experiments/v733_early_low_translation_scan',
             'experiments/v753_coupled_progress_repaired']:
    sys.path.insert(0, str(REPO / name))
sys.path.insert(0, str(W))


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False,
                                    default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x.item()) + '\n')
    temporary.replace(path)


def unchanged():
    freeze = read(OWN / 'FREEZE.json')['files']
    assert all(sha(REPO / name) == value for name, value in freeze.items()), 'NATIVE_FROZEN_INPUT_CHANGED'


def poses(qpos):
    q = np.asarray(qpos)
    return np.c_[q[:, :2], np.arctan2(2 * (q[:, 3]*q[:, 6] + q[:, 4]*q[:, 5]),
                                     1 - 2 * (q[:, 5]**2 + q[:, 6]**2))]


def dense_poses(initial, values):
    boundaries = np.vstack((initial, values))
    delta = np.diff(boundaries, axis=0)
    delta[:, 2] = (delta[:, 2] + np.pi) % (2*np.pi) - np.pi
    dense = np.empty((len(values)*2 + 1, 3))
    dense[::2] = boundaries
    dense[1::2] = boundaries[:-1] + .5 * delta
    return dense


def fields(protocol, state, refined=True):
    from independent_norm import static_field
    from exact_footprint import pose_values
    import motion_tracker
    base = static_field(protocol)
    field = SimpleNamespace(**base.__dict__)
    field.pose_values = MethodType(pose_values, field)
    if refined:
        motion_tracker.install_time_gate(field, state, 'predictive', protocol['known_circles'], protocol['known_rectangles'])
    else:
        motion_tracker.original_install_time_gate(field, state, 'predictive', protocol['known_circles'], protocol['known_rectangles'])
    return base, field
