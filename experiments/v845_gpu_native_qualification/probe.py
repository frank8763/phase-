"""One bounded original-model replay plus 16 fixed private certificates, no new control."""
import fcntl
import gzip
import signal
import time
import traceback

from common import *
import mujoco
import mujoco.rollout
from dynamic_scene import Motion
from geometry_predictor import RobotPredictor
from self_geometry import containment_margin, quaternion_matrices


def main():
    unchanged()
    start = time.time()
    deadline = float(os.environ['PHASE_MODEL_ABSOLUTE_DEADLINE'])
    assert deadline <= 1794009600. and start < deadline
    root = ROOT / 'native01'
    root.mkdir(exist_ok=False)
    lock = (REPO / 'runs/v648_static_unknown/execution.lock').open('rb')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('NATIVE_ABSOLUTE_DEADLINE')))
    signal.setitimer(signal.ITIMER_REAL, deadline - time.time())
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    counts = dict(old_replay_native=0, private_native=0, actual_branch_native=0,
                  repeat_branch_native=0, new_navigation=0, new24=0)
    rows, status, maximum = [], 'RUNNING', 0.
    save(root / 'ROUND_WINDOW.json', dict(started_unix=start, absolute_deadline_unix=deadline,
                                         round_closed=False, pid=os.getpid()))
    try:
        protocol = read(PAIR / 'STATIC_PROTOCOL.json')
        motion = Motion(read(PAIR / 'DYNAMIC_PROTOCOL.json'))  # Old physics replay only.
        model = mujoco.MjModel.from_binary_path(str(PAIR / 'scene_model.mjb'))
        data = mujoco.MjData(model)
        data.qpos[:] = protocol['start_qpos']
        motion.apply(model, data)
        mujoco.mj_forward(model, data)
        snapshots = {}
        with gzip.open(CELL / 'dynamic_native.jsonl.gz', 'rt') as stream:
            for i, line in enumerate(stream):
                if i >= max(STEPS) * 8:
                    break
                assert time.time() < deadline
                recorded = json.loads(line)
                data.ctrl[:] = recorded['actual_ctrl']
                mujoco.mj_step(model, data)
                counts['old_replay_native'] += 1
                motion.apply(model, data)
                mujoco.mj_kinematics(model, data)
                mujoco.mj_collision(model, data)
                error = max(float(np.max(abs(data.qpos - recorded['qpos_full']))),
                            float(np.max(abs(data.qvel - recorded['qvel_full']))),
                            float(np.max(abs(data.ctrl - recorded['actual_ctrl']))),
                            float(np.max(abs(data.mocap_pos - recorded['mocap_pos']))))
                maximum = max(maximum, error)
                assert maximum <= 1e-8, 'ORIGINAL_NATIVE_REPLAY_STATE_MISMATCH'
                if (i+1) % 8 == 0 and (i+1)//8 in STEPS:
                    step = (i+1)//8
                    snapshot = mujoco.MjData(model)
                    mujoco.mj_copyData(snapshot, model, data)
                    snapshots[step] = snapshot
        assert counts['old_replay_native'] == max(STEPS)*8
        save(root / 'REPLAY.json', dict(status='OLD_CONTROL_REPLAY_EXACT', native=counts['old_replay_native'],
                                        maximum_qpos_qvel_ctrl_mocap_error=maximum))
        predictor = RobotPredictor(SimpleNamespace(model=model, data=data), REPO / 'runtime/mk-mini',
                                   mujoco, mujoco.mj_step)
        m, d, ids = predictor.model, predictor.data, predictor.command_map.ids
        states = read(ROOT / 'FIXED_STATES.json')
        for step in STEPS:
            assert time.time() < deadline
            unchanged()
            real = snapshots[step]
            state = states[str(step)]
            assert abs(float(real.time) - state['time']) <= 1e-8
            proposal = np.load(GPU / f'proposal_step{step:04d}.npz')
            commands = np.repeat(proposal['controls'], 8, axis=1)
            assert commands.shape == (4, 336, 4)
            assert np.max(abs(proposal['previous_control'] - real.ctrl[ids])) <= 1e-12
            pose0 = poses(real.qpos[None])[0]
            assert np.max(abs(pose0 - proposal['pose'])) <= 1e-8
            for command in commands:
                previous = real.ctrl[ids].copy()
                for tick in range(0, 336, 8):
                    predictor.command_map.assert_first(command[tick], previous)
                    previous = command[tick]
            before = time.perf_counter()
            _, field = fields(protocol, state)
            field_setup_ms = 1000.*(time.perf_counter()-before)
            mujoco.mj_resetData(m, d)
            for name in ['qpos', 'qvel', 'act', 'qacc_warmstart']:
                getattr(d, name)[:] = getattr(real, name)
            d.time = float(real.time)
            d.ctrl[:] = 0.
            mujoco.mj_forward(m, d)
            spec = mujoco.mjtState.mjSTATE_FULLPHYSICS
            initial = np.empty(mujoco.mj_stateSize(m, spec))
            mujoco.mj_getState(m, d, initial, spec)
            control = np.zeros((4, 336, m.nu))
            control[:, :, ids] = commands
            before = time.perf_counter()
            states_out, sensors = mujoco.rollout.rollout(m, d, np.tile(initial, (4, 1)), control,
                    initial_warmstart=np.tile(real.qacc_warmstart, (4, 1)), persistent_pool=True)
            native_ms = 1000.*(time.perf_counter()-before)
            counts['private_native'] += 4*336
            qpos, qvel = states_out[:, :, 1:1+m.nq], states_out[:, :, 1+m.nq:1+m.nq+m.nv]
            candidate_rows = []
            geom_total_ms = 0.
            for rank in range(4):
                before = time.perf_counter()
                packet = sensors[rank]
                geoms = packet[:, 7:].reshape(336, -1, 7)
                boxes = predictor.self_geometry.bounds(geoms[:, :, :3], quaternion_matrices(geoms[:, :, 3:]),
                                                        packet[:, :3], packet[:, 3:7])
                d.qpos[:] = qpos[rank, -1]
                d.qvel[:] = qvel[rank, -1]
                mujoco.mj_kinematics(m, d)
                terminal = predictor.self_geometry.actual(m, d)
                self_margin = float(min(containment_margin(boxes, predictor.domain).min(),
                                        containment_margin(terminal, predictor.domain)))
                p = poses(qpos[rank])
                dense = dense_poses(pose0, p)
                clock = np.arange(673)*.005
                values = field.causal_values_at_times(dense, clock)
                end328 = float(np.linalg.norm(qvel[rank, 327, :2]))
                end336 = float(np.linalg.norm(qvel[rank, -1, :2]))
                goal = np.asarray(protocol['goal_xy'])
                before_goal = float(np.linalg.norm(pose0[:2] - goal))
                first_gain = before_goal - float(np.linalg.norm(p[7, :2] - goal))
                full_gain = before_goal - float(np.linalg.norm(p[-1, :2] - goal))
                checks = dict(causal_clearance=bool(np.min(values) >= .155),
                              full_self=bool(self_margin >= .002),
                              terminal328=bool(end328 <= .025), terminal336=bool(end336 <= .025),
                              positive_first_public=bool(first_gain >= .001),
                              positive_complete=bool(full_gain >= .02), amplitude_slew=True)
                geometry_ms = 1000.*(time.perf_counter()-before)
                geom_total_ms += geometry_ms
                approximate_error = float(np.max(np.linalg.norm(p[7::8, :2] - proposal['approximate_poses'][rank, :, :2], axis=1)))
                row = dict(rank=rank, candidate_index=int(proposal['candidate_indices'][rank]),
                           qualified=bool(all(checks.values())), checks=checks,
                           minimum_causal_clearance_m=float(np.min(values)),
                           minimum_self_margin_m=self_margin, terminal328_speed_m_s=end328,
                           terminal336_speed_m_s=end336, first_public_goal_gain_m=first_gain,
                           complete_goal_gain_m=full_gain, maximum_ideal_native_xy_error_m=approximate_error,
                           self_and_risk_ms=geometry_ms)
                candidate_rows.append(row)
                file = root / f'step{step:04d}_rank{rank}.npz'
                np.savez_compressed(file, qpos=qpos[rank], qvel=qvel[rank], poses=p, controls=commands[rank],
                                    self_boxes=np.vstack((boxes, terminal)), dense_poses=dense,
                                    causal_values=values, initial_pose=pose0, initial_qpos=real.qpos,
                                    initial_qvel=real.qvel, initial_ctrl=real.ctrl, initial_warmstart=real.qacc_warmstart)
            selected = next((row['rank'] for row in candidate_rows if row['qualified']), None)
            row = dict(step=step, selected_rank=selected, all_rejected=selected is None,
                       field_setup_ms=field_setup_ms, four_candidate_native_rollout_ms=native_ms,
                       full_self_and_risk_ms=geom_total_ms,
                       native_computation_ms=field_setup_ms+native_ms+geom_total_ms,
                       input_state_not_changed=True, candidates=candidate_rows)
            rows.append(row)
            save(root / 'PARTIAL.json', dict(records=rows, counts=counts))
            print(json.dumps(row), flush=True)
        unchanged()
        status = 'FIXED_NATIVE_CANDIDATES_EVALUATED'
        save(root / 'RESULT.json', dict(status=status, all_four_states_have_candidate=all(not row['all_rejected'] for row in rows),
                                        records=rows, counts=counts, maximum_old_replay_error=maximum,
                                        model_initializations=None, new_navigation=0, no_execution_authorized=True,
                                        full_closed_loop_realtime_passed=False))
    except BaseException as error:
        status = 'STOPPED_EXCEPTION'
        save(root / 'ERROR.json', dict(type=type(error).__name__, message=str(error),
                                       traceback=traceback.format_exc(), completed_counts=counts,
                                       in_flight_private_count_unknown=True))
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        save(root / 'COMPLETION.json', dict(status=status, records_completed=len(rows), counts=counts,
                                            elapsed_s=time.time()-start, round_closed=True))
        save(root / 'ROUND_WINDOW.json', dict(started_unix=start, absolute_deadline_unix=deadline,
                                              round_closed=True, status=status, pid=os.getpid()))


if __name__ == '__main__':
    main()
