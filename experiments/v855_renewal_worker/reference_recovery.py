"""Causal reference-following native backup and one-public-cycle continuation.

Only the public path and predicted robot states guide controls. No future sensor
packet, actor truth, or scene phase is available to this module.
"""
import math
import os
import time
import numpy as np
from self_geometry import containment_margin, quaternion_matrices

LOOKAHEADS = (.35, .55)
WHEELS = (4., 8., 12.)
DRIVE_TICKS = (160, 208, 240)
MAX_STEER = .42722137342572125


def pose(q):
    return np.array([q[0], q[1], math.atan2(2*(q[3]*q[6]+q[4]*q[5]), 1-2*(q[5]**2+q[6]**2))])


def reference_target(current, path, index, lookahead, wheel, wheel_base=.60):
    path = np.asarray(path, float)
    assert path.ndim == 2 and path.shape[1] == 4 and len(path) >= 2
    assert np.isfinite(path).all() and int(path[min(index+1, len(path)-1), 3]) == 1
    end = index+1
    while end < len(path)-1 and int(path[end+1, 3]) == 1:
        end += 1
    start = index
    while start > 0 and int(path[start-1, 3]) == 1:
        start -= 1
    lo, hi = max(start, index-12), min(end, index+40)
    index = lo+int(np.argmin(np.linalg.norm(path[lo:hi+1, :2]-current[:2], axis=1)))
    index = min(index, end-1)
    target_index = index+1
    arc = 0.
    while target_index < end and arc < lookahead:
        arc += float(np.linalg.norm(path[target_index+1, :2]-path[target_index, :2]))
        target_index += 1
    relative = path[target_index, :2]-current[:2]
    lateral = -math.sin(current[2])*relative[0]+math.cos(current[2])*relative[1]
    steer = float(np.clip(math.atan2(2*wheel_base*lateral, max(float(relative@relative), .02)), -MAX_STEER, MAX_STEER))
    if abs(steer) < 1e-9:
        target = np.array([0., 0., wheel, wheel])
    else:
        radius = wheel_base/math.tan(abs(steer))
        inner = math.atan2(wheel_base, radius-.27)
        outer = math.atan2(wheel_base, radius+.27)
        target = np.array([inner, outer, wheel, wheel] if steer > 0 else [-outer, -inner, wheel, wheel])
    delta=8.0*wheel*math.tan(steer)*.54/(2*wheel_base)
    target[2:]=[wheel-delta,wheel+delta]
    return target, index


def budget(predictor, ticks):
    deadline = float(os.environ.get('PHASE_MODEL_ABSOLUTE_DEADLINE', 'inf'))
    cap = int(os.environ.get('PHASE_PRIVATE_NATIVE_CAP', '30000000'))
    assert time.time() < deadline, 'REFERENCE_PREDICTION_ABSOLUTE_DEADLINE'
    assert predictor.prediction_steps+ticks <= cap, 'REFERENCE_PRIVATE_NATIVE_CAP'


def finish(predictor, qpos, qvel, packet, commands, targets, reported=320):
    qpos, qvel, packet = map(np.asarray, [qpos, qvel, packet])
    horizon = len(qpos)
    geoms = packet[:, 7:].reshape(horizon, -1, 7)
    bounds = predictor.self_geometry.bounds(geoms[:, :, :3], quaternion_matrices(geoms[:, :, 3:]), packet[:, :3], packet[:, 3:7])
    d, m = predictor.data, predictor.model
    d.qpos[:] = qpos[-1]; d.qvel[:] = qvel[-1]
    predictor.mj.mj_kinematics(m, d)
    terminal = predictor.self_geometry.actual(m, d)
    all_bounds = np.vstack((bounds, terminal))
    yaw = np.arctan2(2*(qpos[:, 3]*qpos[:, 6]+qpos[:, 4]*qpos[:, 5]), 1-2*(qpos[:, 5]**2+qpos[:, 6]**2))
    all_poses = np.c_[qpos[:, :2], yaw]
    predictor.last_forecast_qpos = qpos[:reported].copy()
    predictor.last_forecast_qvel = qvel[:reported].copy()
    predictor.last_self_bounds = all_bounds[:reported+1].copy()
    predictor.prediction_self_margin = float(containment_margin(predictor.last_self_bounds, predictor.domain).min())
    predictor.prediction_self_contained = predictor.prediction_self_margin >= .002
    predictor.terminal_speed = float(np.linalg.norm(qvel[reported-1, :2]))
    predictor.last_root_sensors = packet[:reported, :7].copy()
    predictor.first_geom_sensors = geoms[0].copy()
    predictor.reference_prediction = dict(qpos=qpos.copy(), qvel=qvel.copy(), poses=all_poses.copy(),
        controls=np.asarray(commands).copy(), targets=np.asarray(targets).copy(),
        self_bounds=all_bounds.copy(), self_margin=float(containment_margin(all_bounds, predictor.domain).min()),
        terminal_speed=float(np.linalg.norm(qvel[-1, :2])))
    return all_poses[:reported].copy()


def predict_schedule(predictor, real, target, ids, last, brake_after):
    """Original constant target, same first320 states, plus8 stopped continuation."""
    import mujoco.rollout
    horizon = 448
    budget(predictor, horizon)
    m, d, mj = predictor.model, predictor.data, predictor.mj
    mj.mj_resetData(m, d)
    for name in ['qpos', 'qvel', 'act', 'qacc_warmstart']:
        getattr(d, name)[:] = getattr(real, name)
    d.time = float(real.time); d.ctrl[:] = 0.; mj.mj_forward(m, d)
    spec = mj.mjtState.mjSTATE_FULLPHYSICS
    initial = np.empty(mj.mj_stateSize(m, spec)); mj.mj_getState(m, d, initial, spec)
    commands = predictor.command_map.sequence(target, last, horizon, brake_after)
    controls = np.zeros((1, horizon, m.nu)); controls[0][:, ids] = commands
    states, sensors = mujoco.rollout.rollout(m, d, initial, controls, initial_warmstart=real.qacc_warmstart.copy(), persistent_pool=True)
    predictor.prediction_steps += horizon
    targets = np.repeat([np.asarray(target, float)], horizon, axis=0)
    targets[brake_after:, 2:] = 0.
    return finish(predictor, states[0, :, 1:1+m.nq], states[0, :, 1+m.nq:1+m.nq+m.nv], sensors[0], commands, targets)


def predict_follow(predictor, real, ids, last, reference, lookahead, wheel, brake_after):
    """Feedback in the robot-only forecast; persist the resulting open-loop tail."""
    horizon = 448
    budget(predictor, horizon)
    m, d, mj = predictor.model, predictor.data, predictor.mj
    mj.mj_resetData(m, d)
    for name in ['qpos', 'qvel', 'act', 'qacc_warmstart']:
        getattr(d, name)[:] = getattr(real, name)
    d.time = float(real.time); d.ctrl[:] = 0.; mj.mj_forward(m, d)
    d.qacc_warmstart[:] = real.qacc_warmstart
    path = np.asarray(reference['path'], float)
    index = int(reference['index'])
    command = np.asarray(last, float).copy()
    target = np.r_[command[:2], 0., 0.]
    qpos, qvel, sensors, controls, targets = [], [], [], [], []
    for tick in range(horizon):
        if tick % 8 == 0:
            budget(predictor, 1)
            if tick < brake_after:
                target, index = reference_target(pose(d.qpos), path, index, lookahead, wheel, reference['wheel_base'])
            else:
                target = target.copy(); target[2:] = 0.
            command = predictor.command_map.step(target, command)
            d.ctrl[:] = 0.; d.ctrl[ids] = command
        predictor.native(m, d); predictor.prediction_steps += 1
        qpos.append(d.qpos.copy()); qvel.append(d.qvel.copy()); sensors.append(d.sensordata.copy())
        controls.append(command.copy()); targets.append(target.copy())
    return finish(predictor, qpos, qvel, sensors, controls, targets)
