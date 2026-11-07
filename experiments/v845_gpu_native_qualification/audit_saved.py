"""Independent saved-value/candidate-control audit; forbids physical model imports."""
import sys


class NoModels:
    def find_spec(self, name, *args):
        if name == 'mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('NATIVE_SAVED_AUDIT_FORBIDS_MODELS')


sys.meta_path.insert(0, NoModels())
from common import *
from independent_norm import radial_lower
from exact_footprint import pose_values
from self_geometry import containment_margin


def main():
    root = ROOT / 'native01'
    unchanged()
    result = read(root / 'RESULT.json')
    protocol, states = read(PAIR / 'STATIC_PROTOCOL.json'), read(ROOT / 'FIXED_STATES.json')
    contract = read(CELL / 'ACTUATOR_COMMAND_CONTRACT.json')
    limits, rate = np.asarray(contract['limits']), np.asarray(contract['rate'])
    ids = contract['ids']
    records = []
    for entry in result['records']:
        step = entry['step']
        state = states[str(step)]
        base, broad = fields(protocol, state, refined=False)
        proposal = np.load(GPU / f'proposal_step{step:04d}.npz')
        audited = []
        for row in entry['candidates']:
            rank = row['rank']
            z = np.load(root / f'step{step:04d}_rank{rank}.npz')
            qpos, qvel, controls = z['qpos'], z['qvel'], z['controls']
            assert qpos.shape[0] == qvel.shape[0] == controls.shape[0] == 336
            assert np.array_equal(controls, np.repeat(proposal['controls'][rank], 8, axis=0))
            assert np.all(controls >= limits[:, 0] - 1e-12) and np.all(controls <= limits[:, 1] + 1e-12)
            public = controls[::8]
            delta = np.diff(np.vstack((z['initial_ctrl'][ids], public)), axis=0)
            assert np.all(abs(delta) <= rate + 1e-12)
            p = poses(qpos)
            dense = dense_poses(z['initial_pose'], p)
            assert np.max(abs(p - z['poses'])) <= 1e-12
            assert np.max(abs(dense - z['dense_poses'])) <= 1e-12
            clock = np.arange(673)*.005
            expected = np.maximum(broad.causal_values_at_times(dense, clock),
                                  np.minimum(pose_values(base, dense), radial_lower(base, dense, state, clock)))
            error = float(np.max(abs(expected - z['causal_values'])))
            assert error <= 1e-8, 'INDEPENDENT_CAUSAL_GEOMETRY_MISMATCH'
            margin = float(containment_margin(z['self_boxes'], protocol['footprint_bounds']).min())
            goal = np.asarray(protocol['goal_xy'])
            initial_distance = float(np.linalg.norm(z['initial_pose'][:2] - goal))
            first_gain = initial_distance - float(np.linalg.norm(p[7, :2] - goal))
            full_gain = initial_distance - float(np.linalg.norm(p[-1, :2] - goal))
            checks = dict(causal_clearance=bool(np.min(expected) >= .155), full_self=bool(margin >= .002),
                          terminal328=bool(np.linalg.norm(qvel[327, :2]) <= .025),
                          terminal336=bool(np.linalg.norm(qvel[-1, :2]) <= .025),
                          positive_first_public=bool(first_gain >= .001), positive_complete=bool(full_gain >= .02),
                          amplitude_slew=True)
            assert checks == row['checks'] and all(checks.values()) == row['qualified']
            assert abs(margin - row['minimum_self_margin_m']) <= 1e-12
            audited.append(dict(rank=rank, qualified=row['qualified'], checks=checks,
                                independent_geometry_error=error, dense_samples=673))
        selected = next((row['rank'] for row in audited if row['qualified']), None)
        assert selected == entry['selected_rank']
        records.append(dict(step=step, selected_rank=selected, candidates=audited))
    assert result['counts']['old_replay_native'] == 9584 and result['counts']['private_native'] == 5376
    assert result['counts']['actual_branch_native'] == result['counts']['repeat_branch_native'] == 0
    passed = all(row['selected_rank'] is not None for row in records)
    save(root / 'INDEPENDENT_AUDIT.json', dict(status='SAVED_NATIVE_CERTIFICATES_INDEPENDENTLY_CHECKED',
                evidence_passed=True, all_four_states_have_candidate=passed, records=records,
                counts=result['counts'], models_in_audit=0, integrations_in_audit=0,
                full_closed_loop_realtime_passed=False, navigation_or_confirmation_passed=False))
    print('NATIVE_SAVED_INDEPENDENT_AUDIT_PASS', passed, flush=True)


if __name__ == '__main__':
    main()
