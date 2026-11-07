"""Independent saved controller/successor reconstruction; no online selector import."""
import math
import numpy as np


def expected_follow(c, limits, rate, require_progress=True):
    f = c['reference_following']; path = np.asarray(f['path'], float)
    assert f['lookahead_m'] in [.35, .55] and f['wheel_speed'] in [4., 8., 12.]
    assert f['drive_ticks'] in [160, 208, 240] and f['drive_ticks'] == c['brake_after_native_ticks']
    assert float(f['wheel_base']) == .60
    q = np.vstack((c['qpos'], c['one_cycle_continuation']['extra_qpos']))
    index = int(f['index']); last = np.asarray(c['prefix_command'], float).copy()
    target = np.r_[last[:2], 0., 0.]; commands = []; targets = []
    for tick in range(0, 328, 8):
        if tick < f['drive_ticks']:
            initial = np.asarray(c['initial_qpos'] if tick == 0 else q[tick-1])
            yaw = math.atan2(2*(initial[3]*initial[6]+initial[4]*initial[5]), 1-2*(initial[5]**2+initial[6]**2))
            end = index+1
            assert int(path[min(end, len(path)-1), 3]) == 1
            while end < len(path)-1 and int(path[end+1, 3]) == 1:
                end += 1
            begin = index
            while begin > 0 and int(path[begin-1, 3]) == 1:
                begin -= 1
            low, high = max(begin, index-12), min(end, index+40)
            index = low+int(np.argmin(np.linalg.norm(path[low:high+1, :2]-initial[:2], axis=1)))
            index = min(index, end-1); at = index+1; arc = 0.
            while at < end and arc < f['lookahead_m']:
                arc += float(np.linalg.norm(path[at+1, :2]-path[at, :2])); at += 1
            delta = path[at, :2]-initial[:2]
            offset = -math.sin(yaw)*delta[0]+math.cos(yaw)*delta[1]
            steer = float(np.clip(math.atan2(1.20*offset, max(float(delta@delta), .02)), -.42722137342572125, .42722137342572125))
            wheel = f['wheel_speed']
            if abs(steer) < 1e-9:
                target = np.array([0., 0., wheel, wheel])
            else:
                radius = .60/math.tan(abs(steer))
                near = math.atan2(.60, radius-.27); far = math.atan2(.60, radius+.27)
                target = np.array([near, far, wheel, wheel] if steer > 0 else [-far, -near, wheel, wheel])
            differential=8.0*wheel*math.tan(steer)*.54/1.20
            target[2:]=[wheel-differential,wheel+differential]
        else:
            target = target.copy(); target[2:] = 0.
        last = np.clip(np.clip(target, limits[:, 0], limits[:, 1]), last-rate, last+rate)
        commands.extend([last.copy() for _ in range(8)])
        targets.extend([target.copy() for _ in range(8)])
    assert np.max(abs(np.asarray(targets)-f['targets'])) <= 1e-12
    assert np.max(abs(np.asarray(commands)-np.vstack((c['controls'], c['one_cycle_continuation']['extra_controls'])))) <= 1e-12
    goal = np.asarray(f['goal_xy'])
    if require_progress and 'maneuver_contract'not in c:
        assert np.linalg.norm(np.asarray(c['prefix_initial_qpos'])[:2]-goal)-np.linalg.norm(np.asarray(c['qpos'])[-1, :2]-goal) >= .02-1e-10
        assert c['signed_longitudinal_displacement_m'] >= .02
    return np.asarray(commands)[:320]


def independent_values(poses, state, protocol):
    from independent_norm import static_field, radial_lower
    from exact_footprint import pose_values
    import importlib.util
    from pathlib import Path
    from types import SimpleNamespace
    import os
    repo = Path(os.environ.get('PHASE_REPO', Path(__file__).resolve().parents[2]))
    spec = importlib.util.spec_from_file_location('reference_audit_original_broad', repo/'experiments/v812_soft_global_reference/motion_tracker.py')
    broad = importlib.util.module_from_spec(spec); spec.loader.exec_module(broad)
    base = static_field(protocol); field = SimpleNamespace(**base.__dict__)
    broad.install_time_gate(field, state, 'predictive', protocol['known_circles'], protocol['known_rectangles'])
    times = np.arange(1, len(poses)+1)*.01
    if state['center'] is None:
        return field.causal_values_at_times(poses, times)
    return np.maximum(field.causal_values_at_times(poses, times), np.minimum(pose_values(base, poses), radial_lower(base, poses, state, times)))


def check_successor(c, protocol, limits, rate):
    from self_geometry import containment_margin
    q = np.asarray(c['qpos']); yaw = np.arctan2(2*(q[:, 3]*q[:, 6]+q[:, 4]*q[:, 5]), 1-2*(q[:, 5]**2+q[:, 6]**2))
    base = np.vstack((c['prefix_poses'], np.c_[q[:, :2], yaw]))
    extra = c['one_cycle_continuation']
    assert extra['no_future_observations_assumed'] is True
    assert abs(extra['absolute_end_time']-c['created_time']-3.36) <= 1e-8
    eq = np.asarray(extra['extra_qpos']); ev = np.asarray(extra['extra_qvel'])
    eyaw = np.arctan2(2*(eq[:, 3]*eq[:, 6]+eq[:, 4]*eq[:, 5]), 1-2*(eq[:, 5]**2+eq[:, 6]**2))
    assert len(eq) == len(ev) == len(extra['extra_controls']) == 8
    ep = np.c_[eq[:, :2], eyaw]
    assert np.max(abs(ep-extra['extra_poses'])) <= 1e-12
    complete = np.vstack((base, ep)); values = independent_values(complete, c['forecast_state'], protocol)
    assert len(base) == 328 and len(values) == 336
    assert values.min() >= .155-1e-10 and abs(values.min()-extra['minimum_clearance_m']) <= 1e-8
    assert abs(values[:328].min()-c['minimum_causal_predicted_clearance_m']) <= 1e-8
    assert extra['minimum_self_margin_m'] >= .002
    assert containment_margin(np.asarray(extra['extra_self_bounds']), np.asarray(protocol['footprint_bounds'])).min() >= .002
    assert np.linalg.norm(ev[-1, :2]) <= .025 and abs(np.linalg.norm(ev[-1, :2])-extra['terminal_speed_m_s']) <= 1e-10
    controls = np.vstack((c['prefix_command'], c['controls'], extra['extra_controls']))
    assert np.all(controls >= limits[:, 0]-1e-12) and np.all(controls <= limits[:, 1]+1e-12)
    assert np.all(abs(np.diff(controls[::8], axis=0)) <= rate+1e-12)
    if 'reference_following' in c:
        expected_follow(c, limits, rate)
    else:
        last = np.asarray(c['prefix_command'], float); expected = []
        for tick in range(0, 328, 8):
            target = np.asarray(c['target'], float).copy()
            if tick >= c['brake_after_native_ticks']:
                target[2:] = 0.
            last = np.clip(np.clip(target, limits[:, 0], limits[:, 1]), last-rate, last+rate)
            expected.extend([last.copy() for _ in range(8)])
        assert np.max(abs(np.asarray(expected)-np.vstack((c['controls'], extra['extra_controls'])))) <= 1e-12
    return dict(kind=c['recovery_kind'], minimum_original328_m=float(values[:328].min()), minimum_successor336_m=float(values.min()))
