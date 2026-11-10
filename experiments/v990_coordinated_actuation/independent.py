"""Independently decode four actuator targets; never call the allocator."""
import math
import numpy as np


def check(previous, command, limits, slew_per_second, dt=.01, curvature_cap=.758770385):
    previous = np.asarray(previous, float); command = np.asarray(command, float)
    limits = np.asarray(limits, float); rates = np.asarray(slew_per_second, float)
    assert previous.shape == command.shape == (4,) and limits.shape == (4, 2) and rates.shape == (4,)
    assert np.isfinite(command).all() and np.isfinite(previous).all()
    assert np.all(command >= limits[:, 0]-1e-10) and np.all(command <= limits[:, 1]+1e-10), 'AMPLITUDE'
    assert np.all(abs(command-previous) <= rates*dt+1e-10), 'RATE'
    left = math.tan(float(command[0]))
    right = math.tan(float(command[1]))
    kl = left/(.6+.27*left)
    kr = right/(.6-.27*right)
    assert abs(kl-kr) <= 1e-9, 'FRONT_ROLLING_CURVATURE_MISMATCH'
    k = (kl+kr)/2
    assert abs(k) <= curvature_cap+1e-9, 'CURVATURE_CAP'
    assert np.min(command[2:]) >= -1e-10, 'REAR_REVERSE'
    mean = float((command[2]+command[3])/2)
    expected = np.array([mean*(1-.27*k), mean*(1+.27*k)])
    residual = float(abs(command[2:]-expected).max())
    assert residual <= 1e-9, 'FRONT_REAR_ROLLING_CURVATURE_MISMATCH'
    pl = math.tan(float(previous[0])); pr = math.tan(float(previous[1]))
    pkl = pl/(.6+.27*pl); pkr = pr/(.6-.27*pr)
    assert abs(pkl-pkr) <= 1e-8, 'PREVIOUS_FRONT_MISMATCH'
    assert abs(math.atan(.6*k)-math.atan(.6*(pkl+pkr)/2)) <= .6*dt+1e-10, 'VIRTUAL_RATE'
    return dict(passed=True, common_curvature_m_inv=k, mean_rear_velocity_rad_s=mean,
                rear_compatibility_residual_rad_s=residual, models=0, integrations=0)
