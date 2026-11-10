"""Independent fine midpoint reconstruction; no online certificate or model use."""
import importlib.util
import math
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('v981_independent_curve_only', R/'experiments/v977_state_consistent_recovery/saved_qualification.py')
independent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(independent)


def check(plan, actual):
    curve = independent.reconstruct(plan['initial_state'], plan['edge_targets'])[:, :3]
    path = np.asarray(plan['path'], float)
    assert path.shape == curve[::25].shape and np.max(abs(path-curve[::25])) < 1e-5, 'REFERENCE_NOT_INDEPENDENTLY_RECONSTRUCTIBLE'
    actual = np.asarray(actual, float)
    assert actual.ndim == 2 and actual.shape[1] == 3 and len(actual) > 0 and np.isfinite(actual).all(), 'INVALID_ACTUAL_TRACE'
    position = heading = 0.
    for pose in actual:
        distance = np.linalg.norm(curve[:, :2]-pose[:2], axis=1)
        index = int(np.argmin(distance))
        position = max(position, float(distance[index]))
        angle = pose[2]-curve[index, 2]
        heading = max(heading, abs(math.atan2(math.sin(angle), math.cos(angle))))
    position_upper = position+.00025+1e-5
    heading_upper = heading+.758770385*.00025+1e-5
    return dict(passed=position_upper <= .04 and heading_upper <= .035,
                maximum_position_error_m=position, maximum_heading_error_rad=heading,
                maximum_position_upper_m=position_upper, maximum_heading_upper_rad=heading_upper,
                unchanged_position_limit_m=.04, unchanged_heading_limit_rad=.035,
                independent_method='separate .5mm midpoint reconstruction', samples=len(actual),
                models=0, integrations=0)
