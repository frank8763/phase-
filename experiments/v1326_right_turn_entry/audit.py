"""Independent recorded physical trace and control-contract audit, zero new models."""
import gzip
import json
import numpy as np
from pathlib import Path


def audit(task):
    out = Path(task['output']); r = json.loads((out / 'RESULT.json').read_text())
    setup = json.loads((out / 'physics/SETUP.json').read_text())
    initial = json.loads((out / 'INITIAL_PACKET.json').read_text())
    with np.load(out / 'physics/NATIVE_TRACE.npz') as z:
        trace = {k: z[k].copy() for k in z.files}
    journal = json.loads((out / 'APPLIED_JOURNAL.json').read_text()); n = len(trace['time'])
    ctrl = trace['ctrl'][:, setup['actuator_ids']]; limits = np.asarray(setup['limits']); rate = np.asarray(setup['slew_per_second']) * .01
    with gzip.open(out / 'physics/CONTACTS.json.gz', 'rt') as f:
        contacts = json.load(f)
    checks = dict(fully_recorded=n == r['new_actual_native'] == r['own_replay_native'] == len(journal),
                  finite_all_states=all(np.isfinite(trace[k]).all() for k in ['qpos', 'qvel', 'ctrl', 'mocap_pos', 'mocap_quat']),
                  time_monotonic=bool(abs(trace['time'] - .01 * np.arange(1, n + 1)).max() <= 1e-8),
                  actual_clearance=bool(trace['clearance'].min() >= .15 - 1e-8),
                  full_self=bool(trace['self_margin'].min() >= -1e-10),
                  actual_control_limits=bool((ctrl >= limits[:, 0] - 1e-10).all() and (ctrl <= limits[:, 1] + 1e-10).all()),
                  actual_control_rates=bool((abs(np.diff(np.vstack([initial['controller_memory']['last_ctrl'], ctrl]), axis=0)) <= rate + 1e-10).all()),
                  bad_contacts_zero=len(contacts) == n + 1 and all(c[2] not in ['robot_obstacle_contact', 'robot_obstacle_penetration', 'unknown_contact', 'robot_self_contact'] for row in contacts for c in row),
                  own_full_replay=r.get('replay', {}).get('passed') is True and r['replay']['maximum_qpos_qvel_ctrl_mocap_error'] <= 1e-8,
                  independent_allocation=r.get('independent_allocation', {}).get('passed') is True,
                  complete_stop=len(journal) >= 200 and all(x['phase'] == 'COMPLETE_STOP_TAIL' and x['request'] == [0., 0., False] for x in journal[-200:]),
                  component_functional=r['passed'] is True,
                  sources_unchanged=r['source_unchanged'] is True)
    q = trace['qpos']; yaw = np.arctan2(2 * (q[:, 3] * q[:, 6] + q[:, 4] * q[:, 5]), 1 - 2 * (q[:, 5]**2 + q[:, 6]**2))
    rear = q[:,:2] - .30*np.c_[np.cos(yaw),np.sin(yaw)]
    radial_error = float(abs(np.linalg.norm(rear - np.asarray(task['arc_center']), axis=1) - task['arc_radius_m']).max())
    final_error = abs(float(np.arctan2(np.sin(yaw[-1] - task['component_goal_yaw']), np.cos(yaw[-1] - task['component_goal_yaw']))))
    checks.update(independent_arc_tracking=radial_error <= .04, independent_terminal_heading=final_error <= .12, independent_actual_turn=float(np.arctan2(np.sin(yaw[-1]-task['start_yaw']),np.cos(yaw[-1]-task['start_yaw']))) * task['turn_sign'] >= .15, independent_component_goal=float(np.linalg.norm(q[-1, :2] - task['component_goal_xy'])) <= .15)
    return dict(passed=all(checks.values()), checks=checks, actual_reviewed=n,
                minimum_actual_clearance_m=float(trace['clearance'].min()), models=0, new_physical_native=0)
