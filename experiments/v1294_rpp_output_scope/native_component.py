"""Canonical V1281 plant and current Adapter; physical boundary is disabled by default."""
import argparse
import fcntl
import importlib.abc
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import socket
import sys
import time
import traceback
from component_context import *


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module


def binding():
    # Identical module preparation and Adapter lookup to V1281's worker.
    sys.path.insert(0, str(R / 'experiments/v1180_fresh_recovery_chain'))
    import chain_tools as old
    sys.path.insert(0, str(R / 'experiments/v1114_coupled_steering_mode'))
    from bindings import Adapter
    f = load('v1290_scene_binding', R / 'experiments/v1067_causal_replan_brake_reserve/scene_binding.py')
    f.O = O
    replay = load('v1290_exact_replay', R / 'experiments/v882_runtime_evidence_repair/physical.py').replay
    return old, Adapter, f, replay


def run(task, window):
    os.chdir(R)
    out = Path(task['output']); old, Adapter, factory, replay = binding(); np = old.np
    contract = load('v1290_common_interface', R / 'experiments/v1288_baseline_interface/contract.py')
    command, observation = contract.command, contract.observation
    v = None; in_step = False; creating = False; sock = None; journal = []; inflight = False
    result = dict(passed=False, canonical_vehicle_initializations=0, internal_factory_model_constructions=None,
                  new_actual_native=0, own_replay_native=0, private_mujoco_native=0, analytical_vehicle_native=0,
                  training_updates=0, original_goal_navigation=False, historical_controls_used=0)
    start = time.monotonic(); end = min(time.time() + 300, window['absolute_deadline_unix'] - 10)
    result['adapter_source'] = str(Path(Adapter.compute.__code__.co_filename).resolve().relative_to(R))
    try:
        import mujoco as mj
        signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('PHYSICAL_COMPONENT_ROOT_STOP')))
        signal.alarm(max(1, int(end - time.time())))
        creating = True; dump(out / 'INITIALIZATION_ATTEMPT.json', dict(at=time.time(), native=0))
        v = factory.create_vehicle(out / 'physics', task); creating = False; result['canonical_vehicle_initializations'] = 1; old.pin()
        assert v.count == 0 and v.d.time == 0., 'NONZERO_INITIAL_STATE'
        before = {k: np.array(getattr(v.d, k)).copy() for k in ['qpos', 'qvel', 'ctrl', 'mocap_pos', 'mocap_quat']}
        previous = v.adapter; v.adapter = Adapter(v.m, mj, v.dt, encoders=previous.encoders); v.adapter.virtual_rate = .6; v.adapter.last = previous.last.copy(); v.adapter.integral = previous.integral
        assert all(np.array_equal(before[k], getattr(v.d, k)) for k in before), 'ADAPTER_REBIND_CHANGED_STATE'
        dump(out / 'INITIAL_PACKET.json', old.packet(v))
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM); address = str(out.relative_to(R) / 'native.sock'); sock.bind(address); sock.settimeout(.02)
        peer = str(out.relative_to(R) / 'ros.sock'); sequence = 0; accepted = -1; ros_pass = False; stopped = False; armed = False
        scan = None; scan_at = 0.; original_step = v.step

        def step(vr, wr, phase):
            nonlocal in_step
            assert time.time() < end - 60 and remaining(window) > 70, 'REPLAY_TIME_RESERVE'
            assert v.count < 6000, 'COMPONENT_NATIVE_LIMIT'
            row = dict(before_native=v.count, phase=phase, request=[vr, wr, False], last_ctrl=v.adapter.last.copy(), integral=v.adapter.integral, encoders=v.steering_sample().copy(), body=list(v.body()), applied=False)
            journal.append(row); v.adapter.parked_target = None; in_step = True; original_step(vr, wr, False); in_step = False; row['applied'] = True
            p = old.packet(v); old.previous.body_gate(p)
            if v.count % 500 == 0:
                dump(out / 'PARTIAL.json', dict(native=v.count, body=p['body'], phase=phase))

        until = min(time.monotonic() + 220, window['hard_stop_monotonic'] - 100)
        while not stopped:
            assert time.monotonic() < until, 'COMPONENT_NAVIGATION_WALL_STOP'
            now = time.monotonic()
            if scan is None or now - scan_at >= .04:
                scan = v.scan(); scan_at = now
            packet = dict(schema=1, run_id=task['run_id'], sequence=sequence, sampled_at=time.monotonic(), body=list(v.body()), ranges_m=scan['ranges'])
            observation(packet, run_id=task['run_id'], now=time.monotonic(), previous_sequence=sequence - 1); sequence += 1
            try:
                sock.sendto(json.dumps(packet).encode(), peer)
            except (FileNotFoundError, BlockingIOError, ConnectionRefusedError):
                pass
            try:
                received = json.loads(sock.recv(65536))
            except socket.timeout:
                continue
            assert received['run_id'] == task['run_id'], 'FOREIGN_ROS_PACKET'
            if received['kind'] == 'stop':
                assert 0 <= time.monotonic() - received['issued_at'] <= .2, 'STALE_STOP'
                ros_pass = received['passed']; stopped = True; break
            if received['kind'] == 'arm':
                assert not armed and v.count == 0 and 0 <= time.monotonic() - received['issued_at'] <= .2, 'ARM_ORDER'
                armed = True
                continue
            assert armed, 'COMMAND_BEFORE_ARM'
            assert received['kind'] == 'command', 'UNKNOWN_COMMAND_KIND'
            p = {k: received[k] for k in ['run_id', 'sequence', 'issued_at', 'v', 'w']}
            vr, wr = command(p, run_id=task['run_id'], now=time.monotonic(), previous_sequence=accepted); accepted = p['sequence']
            for _ in range(5):
                step(vr, wr, 'RPP_ACTUAL_FEEDBACK')
            scan = v.scan(); scan_at = time.monotonic()
        for _ in range(200):
            step(0., 0., 'COMPLETE_STOP_TAIL')
            if v.count % 5 == 0:
                v.scan()
        final = old.packet(v); dump(out / 'FINAL_PACKET.json', final)
        distance = float(np.linalg.norm(np.asarray(final['body'][:2]) - task['component_goal_xy']))
        forward = final['body'][0] - task['start_xy'][0]
        result['functional_checks'] = dict(upstream_action_succeeded=ros_pass, component_distance=distance <= .15,
                                           actual_forward_m=forward >= 1., body_stopped=abs(np.asarray(final['body'][3:])).max() <= .03,
                                           steering_settled=abs(np.asarray(final['steering']['velocity'])).max() <= .03,
                                           drive_command_zero=abs(v.adapter.last[2:]).max() <= 1e-8)
        result.update(passed=all(result['functional_checks'].values()), component_goal_distance_m=distance, forward_displacement_m=forward)
    except BaseException as exc:
        result.update(passed=False, error=repr(exc), traceback=traceback.format_exc())
        print(json.dumps(dict(primary_error=repr(exc), traceback=traceback.format_exc())), flush=True)
    finally:
        dump(out / 'APPLIED_JOURNAL.json', journal)
        result['canonical_vehicle_initializations'] = None if creating else result['canonical_vehicle_initializations']
        if v is not None:
            result.update(new_actual_native=None if in_step else v.count, model_native_inflight_unknown=in_step)
            try:
                result['physical'] = v.finish(); result['evidence_saved'] = True
            except BaseException as exc:
                result.update(passed=False, save_error=repr(exc))
            if result.get('evidence_saved') and not in_step:
                try:
                    initial = read(out / 'INITIAL_PACKET.json'); cursor = [None]
                    owner = Adapter(v.m, mj, v.dt, encoders=lambda: np.asarray(cursor[0]['encoders']))
                    owner.virtual_rate = .6; owner.last = np.asarray(initial['controller_memory']['last_ctrl']); owner.integral = initial['controller_memory']['integral']
                    maximum = 0.; memory_error = 0.
                    for i, row in enumerate(journal):
                        cursor[0] = row
                        assert row['applied'] and row['before_native'] == i
                        memory_error = max(memory_error, float(abs(owner.last - row['last_ctrl']).max()), abs(owner.integral - row['integral']))
                        u = owner.compute(*row['request'][:2], *row['body'][3:], False)
                        maximum = max(maximum, float(abs(u - v.rows[i]['ctrl'][v.adapter.commands.ids]).max()))
                    result['independent_allocation'] = dict(passed=max(maximum, memory_error) <= 1e-8, control_error=maximum, memory_error=memory_error, recorded_rows=len(journal))
                    result['passed'] = bool(result['passed'] and result['independent_allocation']['passed'])
                except BaseException as exc:
                    result.update(passed=False, allocation_audit_error=repr(exc))
            if not in_step and result.get('evidence_saved') and time.time() < end - 20:
                try:
                    inflight = True; proof = replay(v, end, out / 'physics'); inflight = False
                    result.update(replay=proof, own_replay_native=proof['replay_native'], passed=result['passed'] and proof['passed'])
                except BaseException as exc:
                    result.update(passed=False, replay_error=repr(exc), own_replay_native=None if inflight else 0)
        if sock is not None:
            sock.close(); Path(address).unlink(missing_ok=True)
        signal.alarm(0); result.update(closed=True, wall_s=time.monotonic() - start, closed_unix=time.time(), source_unchanged=sources())
        dump(out / 'RESULT.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('task'); parser.add_argument('--entry-check', action='store_true'); args = parser.parse_args()
    task = read(args.task); window = read(O / 'ROUND_WINDOW.json'); authorize(task, window)
    if args.entry_check:
        class NoPhysical(importlib.abc.MetaPathFinder):
            def find_spec(self, name, *extra):
                if name.split('.')[0] in {'mujoco', 'vehicle', 'torch'}:
                    raise AssertionError('ENTRY_MODELS_FORBIDDEN ' + name)
        sys.meta_path.insert(0, NoPhysical()); old, Adapter, _, _ = binding()
        assert Path(Adapter.compute.__code__.co_filename).resolve() == R / 'experiments/v1114_coupled_steering_mode/coupled_control.py'
        print(json.dumps(dict(passed=True, models=0, physical_native=0, actual_current_adapter_imported=True))); return 0
    assert not (R / 'REVIEW_PENDING').exists(), 'REVIEW_HOLD'
    lock = (R / 'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        proof = run(task, window)
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
    return 0 if proof['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
