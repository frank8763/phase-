"""Observe closed V987 controls and responses; no plant prediction or model import."""
import gzip
import hashlib
import importlib.abc
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parents[2]
O = R / 'runs/v989_actuation_reference_diagnosis'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'torch', 'vehicle', 'physical', 'factory', 'rclpy'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN ' + name)


sys.meta_path.insert(0, NoModel())
sys.path.insert(0, str(R / 'experiments/v987_bounded_startup_components'))
from tracking import dense_reference


def read(name):
    p = O / name
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x) ** 2)))


def span(ticks):
    return dict(samples=len(ticks), first_native_tick=int(ticks[0]) if len(ticks) else None,
                last_native_tick=int(ticks[-1]) if len(ticks) else None)


def main():
    for row in read('RESTORE_RECEIPT.json')['files']:
        assert sha(R / row['path']) == row['sha256']
    xml = R / 'runtime/mk-mini/training/assets/mkmini_real/mkmini_mobile_manipulator_indoor_v1.xml'
    addresses = {}; nq = nv = 0
    for node in ET.parse(xml).getroot().find('worldbody').iter():
        if node.tag not in {'joint', 'freejoint'}:
            continue
        kind = 'free' if node.tag == 'freejoint' else node.get('type', 'hinge')
        addresses[node.get('name')] = dict(qpos=nq, qvel=nv)
        a, b = {'free': (7, 6), 'ball': (4, 3), 'hinge': (1, 1), 'slide': (1, 1)}[kind]
        nq += a; nv += b
    setup = read('physics/SETUP.json')
    si = [addresses[n]['qpos'] for n in ['left_front_steer_joint', 'right_front_steer_joint']]
    ri = [addresses[n]['qvel'] for n in ['left_rear_wheel_joint', 'right_rear_wheel_joint']]
    assert si == setup['steering_qpos_addresses'] and ri == [10, 11]
    with np.load(O / 'physics/NATIVE_TRACE.npz') as z:
        q = z['qpos']; vel = z['qvel']; ctrl = z['ctrl'][:, setup['actuator_ids']]
        assert q.shape[1] == nq and vel.shape[1] == nv
    origin = read('RESULT.json')['historical_prefix_replay_native']
    fault = read('ONLINE_TRACKING_FAULT.json')['packet']['native_tick']
    yaw = np.arctan2(2 * (q[:, 3] * q[:, 6] + q[:, 4] * q[:, 5]),
                     1 - 2 * (q[:, 5] ** 2 + q[:, 6] ** 2))
    speed = vel[:, 0] * np.cos(yaw) + vel[:, 1] * np.sin(yaw)
    actual_w = vel[:, 5]
    plan = read('COMPONENT_REFERENCE.json')['proposal']
    ref = dense_reference(plan)
    poses = np.c_[q[origin:, :2], yaw[origin:]]
    closest = np.array([np.argmin(np.sum((ref[:, :2] - p[:2]) ** 2, axis=1)) for p in poses])
    reference_yaw = ref[closest, 2]
    error = np.arctan2(np.sin(poses[:, 2] - reference_yaw), np.cos(poses[:, 2] - reference_yaw))
    rows = read('physics/YAW_FEEDBACK.json.gz')
    tubes = read('COMMAND_TUBES.json.gz')
    assert len(rows) == len(poses) == 348
    ticks = np.arange(origin + 1, len(q) + 1)
    assert [r['native_tick'] for r in rows] == ticks.tolist()
    driving = np.array([r['proof']['applied'] for r in rows])
    active = [r for r in rows if r['proof']['applied']]
    first = active[0]['native_tick']
    stop = next(r['native_tick'] for r in rows if r['native_tick'] > first and r['stale'])
    moving = (ticks >= first) & (ticks < stop)
    pre_stop_index = stop - origin - 2
    peak_index = int(np.argmax(abs(error)))
    cmd = np.array([[r['v'], r['w']] for r in rows])
    u = ctrl[origin:]
    assert np.max(abs(u - np.array([r['actual_ctrl'] for r in rows]))) <= 1e-8
    tangent = np.tan(u[:, :2])
    front_k = np.mean(tangent / (.6 + tangent * np.array([.27, -.27])), axis=1)
    measured_tangent = np.tan(q[origin:, si])
    measured_k = np.mean(measured_tangent / (.6 + measured_tangent * np.array([.27, -.27])), axis=1)
    common = u[:, 2:].mean(axis=1)
    differential = (u[:, 3] - u[:, 2]) / 2
    # Pure rolling rear-wheel velocity compatibility. These are actuator targets,
    # not a claimed physical no-slip law for the actual chassis/contact state.
    required_d = common * .54 * front_k / 2
    rear_k = np.divide(2 * differential, .54 * common, out=np.zeros_like(common), where=abs(common) > 1e-10)
    opposite = moving & (front_k * rear_k < -1e-10)
    actual_opposite = moving & (measured_k > .01) & (actual_w[origin:] < -.005)
    limited = [r for r in active if r['proof']['projection_limited']]
    zero = [r for r in active if abs(r['proof']['selected_differential']) < 1e-12
            and abs(r['proof']['requested_differential']) > 1e-6]
    # Causal first-step allocation witness: same rate/positivity constraints, but
    # release the post-slew common equality. This is algebra, NOT a new response.
    d = active[0]['proof']; wanted_d = d['requested_differential']
    max_rear_step = setup['slew_per_second'][2] * setup['dt']
    first_nominal = np.array(d['nominal'][2:])
    alternative_d = -min(abs(wanted_d), max_rear_step / 2)
    alternative_common = abs(alternative_d)
    witness_targets = np.array([alternative_common - alternative_d, alternative_common + alternative_d])
    assert np.all(witness_targets >= 0) and np.all(witness_targets <= max_rear_step + 1e-12)
    assert d['feasible_differential'] == [0., 0.] and np.max(abs(first_nominal - max_rear_step)) < 1e-12
    assert abs(error[peak_index]) > .035
    fault_index = fault - origin - 1
    keys = [first, 6124, 6144, 6164, 6184, 6204, fault, stop, ticks[peak_index], int(ticks[-1])]
    witnesses = []
    for tick in keys:
        i = int(tick - origin - 1)
        witnesses.append(dict(native_tick=int(tick), seconds_from_first_drive=(int(tick) - first) * .01,
            requested_v_w=cmd[i].tolist(), actual_v_w=[float(speed[tick-1]), float(actual_w[tick-1])],
            reference_yaw_rad=float(reference_yaw[i]), actual_yaw_rad=float(poses[i, 2]), signed_heading_error_rad=float(error[i]),
            front_target_rad=u[i, :2].tolist(), measured_steering_rad=q[tick-1, si].tolist(),
            rear_velocity_target_rad_s=u[i, 2:].tolist(), measured_rear_velocity_rad_s=vel[tick-1, ri].tolist(),
            front_target_rolling_curvature_m_inv=float(front_k[i]), rear_target_rolling_curvature_m_inv=float(rear_k[i])))
    summary = dict(models=0, integrations=0, physical_revision=None, physics_authorized=False,
        original_outcome='V987_NOT_PASSED', input_archive_sha256=read('RESTORE_RECEIPT.json')['archive_sha256'],
        xml_address_source=dict(path=str(xml.relative_to(R)), sha256=sha(xml), purpose='Only joint-address decoding; no XML model loaded'),
        counts=dict(new_actual=348, feedback_applied=117, first_drive_native_tick=first, first_stop_native_tick=stop,
                    online_fault_native_tick=fault, full_tail_included=True),
        allocation=dict(projection_limited=span([r['native_tick'] for r in limited]),
            nonzero_requested_zero_allocated=span([r['native_tick'] for r in zero]),
            first_step_witness=dict(original_targets=first_nominal.tolist(), original_common_rad_s=float(first_nominal.mean()),
                original_requested_differential_rad_s=wanted_d, original_feasible_differential=d['feasible_differential'],
                alternate_targets_same_rate_and_sign_bounds=witness_targets.tolist(),
                alternate_common_rad_s=alternative_common, alternate_differential_rad_s=alternative_d,
                original_common_equality_intentionally_released=True, physical_improvement_inferred=False),
            conclusion='The fixed post-slew common equality removes all differential authority in six startup ticks; 110/117 feedback ticks are not projection-limited. This alone does not establish the full tracking cause.'),
        coordination=dict(opposite_front_rear_target_rolling_curvatures=span(ticks[opposite]),
            maximum_abs_rear_target_rolling_curvature_m_inv=float(abs(rear_k[moving]).max()),
            original_body_curvature_cap_m_inv=.758770385,
            rms_target_differential_minus_front_rolling_compatible_differential_rad_s=rms((differential-required_d)[moving]),
            actual_front_positive_body_yaw_negative=span(ticks[actual_opposite]),
            interpretation='Nominal body curvature legality and motor bounds do not establish common rolling compatibility of the final four actuator targets. Contact slip/inertia can also cause transient mismatch; unique cause not identified.'),
        error_budget=dict(at_online_fault_rad=float(abs(error[fault_index])),
            immediately_before_first_stop_rad=float(abs(error[pre_stop_index])),
            complete_tail_max_rad=float(abs(error[peak_index])), peak_native_tick=int(ticks[peak_index]),
            stop_tail_peak_increase_rad=float(abs(error[peak_index])-abs(error[pre_stop_index])),
            limit_rad=.035, quantization_reserve_rad=.758770385*.00025+1e-5,
            interpretation='The driving phase nearly exhausts the heading budget; the complete stop tail adds error. Removing the tail or raising the gate would hide this failure.'),
        exclusions=dict(actuator_map_mismatch=False, alternate_controller_takeovers=0,
            old_state_replay_error=0., startup_blocked_this_response=False, evidence_of_compute_or_observation_deadline_failure=False,
            source='Original independently verified V987/V988 counts and ingress audits'),
        witnesses=witnesses,
        scope='All metrics observe the original closed trace. No fitted trajectory, counterfactual rollout, stability proof, new model or successful component is asserted.')
    (O / 'ANALYSIS.json').write_text(json.dumps(summary, indent=2) + '\n')
    # Persistent scientific artifact, using only the original measured trajectory.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    t = (ticks - first) * .01
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    ax = axes[0, 0]
    ax.plot(t, reference_yaw, label='Committed reference heading')
    ax.plot(t, poses[:, 2], label='Actual body heading')
    ax.fill_between(t, reference_yaw-.035, reference_yaw+.035, alpha=.14, color='tab:green', label='Original +/-0.035 rad gate')
    ax.set(ylabel='Heading (rad)', title='Small position error still permits heading failure')
    ax = axes[0, 1]
    ax.plot(t, cmd[:, 1], label='Dispatched yaw-rate request')
    ax.plot(t, actual_w[origin:], label='Actual body yaw rate')
    ax.plot(t, speed[origin:]*measured_k, label='Measured steering no-slip kinematics', alpha=.75)
    ax.axhline(0, color='gray', lw=.6); ax.set(ylabel='Yaw rate (rad/s)', title='Corrective command precedes actual yaw response')
    ax = axes[1, 0]
    ax.plot(t, front_k, label='Front-target rolling curvature')
    ax.plot(t, rear_k, label='Rear-target rolling curvature')
    ax.set(ylabel='Target-implied curvature (1/m)', title='Four targets do not share one rolling curvature')
    ax.axhline(0, color='gray', lw=.6)
    ax = axes[1, 1]
    desired = np.array([r['proof'].get('requested_differential', np.nan) for r in rows])
    ax.plot(t, desired, label='Yaw feedback requested differential')
    ax.plot(t, differential, label='Actually dispatched differential')
    ax.plot(t, required_d, label='Front-compatible differential at same mean', alpha=.75)
    ax.set(ylabel='Rear half-difference (rad/s)', title='Rate projection blocks only the earliest correction')
    for ax in axes.flat:
        ax.axvline((fault-first)*.01, color='tab:red', ls='--', lw=1, label='Online fault')
        ax.axvline((stop-first)*.01, color='black', ls=':', lw=1, label='First stop input')
        ax.set_xlabel('Simulation seconds from first drive command')
        ax.grid(alpha=.2); ax.legend(fontsize=7, loc='best')
    fig.suptitle('V989: saved V987 response diagnosis (zero new physics)', fontsize=14)
    fig.savefig(O / 'RESPONSE_DIAGNOSIS.png', dpi=150)
    plt.close(fig)
    print(json.dumps({k: summary[k] for k in ['counts', 'allocation', 'coordination', 'error_budget']}))


if __name__ == '__main__':
    main()
