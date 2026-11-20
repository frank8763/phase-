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
from transport import send_latest
from gear_handoff import GearHandoff
from stamped_contract import validate_delivery, before_step, assess_delivery
from evidence_io import Journal
from prefix_restore import restore
from frames import SampleCache,wire_packet,validate_binding


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
    finishing = False
    v = None; in_step = False; creating = False; sock = None; journal = []; inflight = False
    result = dict(passed=False, canonical_vehicle_initializations=0, internal_factory_model_constructions=None,
                  new_actual_native=0, own_replay_native=0, private_mujoco_native=0, analytical_vehicle_native=0,
                  training_updates=0, original_goal_navigation=False, historical_controls_used=0, historical_prefix_replay_native=0, new_component_native=0)
    start = time.monotonic(); end = min(time.time() + 1500, window['absolute_deadline_unix'] - 10)
    result['adapter_source'] = str(Path(Adapter.compute.__code__.co_filename).resolve().relative_to(R))
    try:
        import mujoco as mj
        signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('PHYSICAL_COMPONENT_ROOT_STOP')))
        signal.signal(signal.SIGTERM, lambda *_: None if finishing else (_ for _ in ()).throw(InterruptedError('SUPERVISOR_STOP_PRESERVE_EVIDENCE')))
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
        last_ros_sequence=-1;delivery=None;freshness_rejections=[];freshness_start=None;active_rejection=None
        received_journal=Journal(out/'RECEIVED_COMMANDS.jsonl')
        original_step = v.step; gear_handoff = GearHandoff();sampler=SampleCache();sent_observations={}
        observation_journal=Journal(out/'OBSERVATIONS_SENT.jsonl')

        def step(vr, wr, phase):
            nonlocal in_step
            assert time.time() < end - 60 and remaining(window) > 70, 'REPLAY_TIME_RESERVE'
            assert v.count < 60000, 'COMPONENT_NATIVE_LIMIT'
            feedback_body = list(v.body()); feedback_encoders = v.steering_sample().copy()
            raw_upstream=[vr,wr,False];expiry=None
            if phase.endswith('_ACTUAL_FEEDBACK'):
                vr,wr,expiry=before_step(vr,wr,delivery,time.monotonic())
            requested = [vr, wr, False]
            vr, wr, gear_proof = gear_handoff.select(vr, wr, native_tick=v.count, body=feedback_body,
                                                     last_ctrl=v.adapter.last, encoders=feedback_encoders)
            row = dict(before_native=v.count, phase=phase, request=[vr, wr, False], upstream_request=requested,
                       gear_handoff=gear_proof, last_ctrl=v.adapter.last.copy(), integral=v.adapter.integral,
                       encoders=feedback_encoders, body=feedback_body, applied=False,
                       raw_upstream_request=raw_upstream,expiry_gate=expiry,
                       delivery=delivery if expiry is not None else None,command_sequence=accepted if expiry is not None else None,
                       freshness_rejection_index=active_rejection if phase=='FRESHNESS_BRAKE_HOLD' else None)
            journal.append(row); v.adapter.parked_target = None; in_step = True; original_step(vr, wr, False); in_step = False; row['applied'] = True
            p = old.packet(v); old.previous.body_gate(p)
            if v.count % 500 == 0:
                dump(out / 'PARTIAL.json', dict(native=v.count, body=p['body'], phase=phase))

        # Prefix reconstruction uses the same actual Adapter and gear gate.
        proof=restore(v,task,step,end)
        result['historical_prefix_replay_native']=proof['historical_prefix_replay_native']
        result['historical_controls_used']=task['origin_native_tick']
        dump(out/'PREFIX_RESTORE.json',proof);dump(out/'COMPONENT_INITIAL_PACKET.json',old.packet(v))
        until = min(time.monotonic() + 120, window['hard_stop_monotonic'] - 100)
        while not stopped:
            if freshness_start is not None and time.monotonic()-freshness_start>=2.:
                result['functional_navigation_stop']='NO_FRESH_INPUT_FOR_2S';stopped=True;break
            if (out/'STOP_AFTER_CURRENT_PREFIX.json').exists():
                result['supervisor_stop_receipt']=read(out/'STOP_AFTER_CURRENT_PREFIX.json');receipt=read(out/'ROS_RESULT.json') if (out/'ROS_RESULT.json').exists() else {};ros_pass=receipt.get('passed') is True and not receipt.get('error');stopped=True;break
            if v.count-task['origin_native_tick'] >= task['component_native_limit']:
                result['functional_component_stop'] = 'COMPONENT_LIVE_NATIVE_LIMIT_30'
                stopped = True
                break
            assert time.monotonic() < until, 'COMPONENT_NAVIGATION_WALL_STOP'
            wire=wire_packet(sampler,v,task['run_id'],sequence)
            core={k:wire[k] for k in ['schema','run_id','sequence','sampled_at','body','ranges_m']}
            observation(core,run_id=task['run_id'],now=time.monotonic(),previous_sequence=sequence-1)
            sent_observations[sequence]=wire;observation_journal.append(wire);sequence+=1
            sent=send_latest(sock,json.dumps(wire).encode(),peer)
            if not sent:result['observation_transport_drops']=result.get('observation_transport_drops',0)+1
            try:
                received = json.loads(sock.recv(65536))
            except socket.timeout:
                if freshness_start is not None and time.monotonic()-freshness_start>=2.:
                    result['functional_navigation_stop']='NO_FRESH_INPUT_FOR_2S';stopped=True;break
                continue
            assert received['run_id'] == task['run_id'], 'FOREIGN_ROS_PACKET'
            if received['kind'] == 'stop':
                assert 0 <= time.monotonic() - received['issued_at'] <= .2, 'STALE_STOP'
                ros_pass = received['passed']; stopped = True; break
            if received['kind'] == 'arm':
                assert not armed and v.count == task['origin_native_tick'] and 0 <= time.monotonic() - received['issued_at'] <= .2, 'ARM_ORDER'
                armed = True
                continue
            assert armed, 'COMMAND_BEFORE_ARM'
            assert received['kind'] == 'command', 'UNKNOWN_COMMAND_KIND'
            checked=time.monotonic();validate_binding(received,sent_observations);decision=assess_delivery(received,checked,run_id=task['run_id'],previous_sequence=accepted)
            received_journal.append(dict(before_native=v.count,packet=received,decision=decision))
            if not decision['accepted']:
                accepted=received['sequence'];active_rejection=len(freshness_rejections)
                event=dict(before_native=v.count,packet=received,decision=decision,brake_native=5,applied_native=0)
                freshness_rejections.append(event)
                for _ in range(5):step(0.,0.,'FRESHNESS_BRAKE_HOLD');event['applied_native']+=1
                active_rejection=None
                if freshness_start is None:freshness_start=checked
                if time.monotonic()-freshness_start>=2.:
                    result['functional_navigation_stop']='NO_FRESH_INPUT_FOR_2S';stopped=True;break
                continue
            freshness_start=None;delivery=validate_delivery(received,checked)
            p = {k: received[k] for k in ['run_id', 'sequence', 'issued_at', 'v', 'w']}
            vr, wr = command(p, run_id=task['run_id'], now=checked, previous_sequence=accepted); accepted = p['sequence']
            for _ in range(5):
                step(vr, wr, task['algorithm'].upper()+'_ACTUAL_FEEDBACK')
        for _ in range(200):
            step(0., 0., 'COMPLETE_STOP_TAIL')
            if v.count % 5 == 0:
                v.scan()
        final = old.packet(v); dump(out / 'FINAL_PACKET.json', final)
        result['functional_checks']=dict(peer_passed=ros_pass,
            exact_native_count=v.count==task['origin_native_tick']+task['expected_new_native'],
            four_observation_expiry_refusals=len(freshness_rejections)==4 and all(e['decision']['reason']=='OBSERVATION_EXPIRED' and e['applied_native']==5 for e in freshness_rejections),
            body_stopped=abs(np.asarray(final['body'][3:])).max()<=.003,
            steering_settled=abs(np.asarray(final['steering']['velocity'])).max()<=.03,
            drive_command_zero=abs(v.adapter.last[2:]).max()<=1e-10)
        result.update(passed=all(result['functional_checks'].values()),component_scope='sampling fault injection only, no navigation')
    except BaseException as exc:
        result.update(passed=False, error=repr(exc), traceback=traceback.format_exc())
        if v is not None and not in_step and v.count<59800 and remaining(window)>100:
            try:
                for _ in range(200):
                    step(0.,0.,'COMPLETE_STOP_TAIL')
                    if v.count%5==0:v.scan()
                dump(out/'FINAL_PACKET.json',old.packet(v));result['error_stop_tail_completed']=True
            except BaseException as stopping_error:result['error_stop_tail_error']=repr(stopping_error)
        print(json.dumps(dict(primary_error=repr(exc), traceback=traceback.format_exc())), flush=True)
    finally:
        finishing=True
        result.update(new_actual_native=None if in_step else (v.count if v is not None else 0),model_native_inflight_unknown=in_step,own_replay_native=0)
        if 'received_journal' in locals():received_journal.close()
        if 'observation_journal' in locals():observation_journal.close()
        dump(out/'FRESHNESS_REJECTIONS.json',freshness_rejections if 'freshness_rejections' in locals() else [])
        dump(out/'RESULT_PROGRESS.json',dict(result,phase='BEFORE_EVIDENCE_SAVE',closed=False))
        dump(out / 'APPLIED_JOURNAL.json', journal)
        result['canonical_vehicle_initializations'] = None if creating else result['canonical_vehicle_initializations']
        if v is not None:
            result.update(new_actual_native=None if in_step else v.count, model_native_inflight_unknown=in_step)
            try:
                result['physical'] = v.finish(); result['evidence_saved'] = True
                dump(out/'RESULT_PROGRESS.json',dict(result,phase='PHYSICAL_EVIDENCE_SAVED',closed=False))
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
                    inflight = True; dump(out/'REPLAY_ATTEMPT.json',dict(at=time.time(),maximum_replay_native=len(v.rows)));proof = replay(v, end, out / 'physics'); inflight = False
                    result.update(replay=proof, own_replay_native=proof['replay_native'], passed=result['passed'] and proof['passed'])
                except BaseException as exc:
                    result.update(passed=False, replay_error=repr(exc), own_replay_native=None if inflight else 0)
        if sock is not None:
            sock.close(); Path(address).unlink(missing_ok=True)
        origin=task['origin_native_tick']
        result.update(historical_prefix_replay_native=None if in_step and v is not None and v.count<origin else min(origin,v.count) if v is not None else 0,
            new_component_native=None if in_step else max(0,v.count-origin) if v is not None else 0,
            actual_total_native=None if in_step else v.count if v is not None else 0)
        signal.alarm(0); result.update(closed=True, wall_s=time.monotonic() - start, closed_unix=time.time(), source_unchanged=sources())
        dump(out / 'RESULT.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('task'); parser.add_argument('--entry-check', action='store_true'); args = parser.parse_args()
    task = read(args.task); task_check(task)
    if args.entry_check:
        class NoPhysical(importlib.abc.MetaPathFinder):
            def find_spec(self, name, *extra):
                if name.split('.')[0] in {'mujoco', 'vehicle', 'torch'}:
                    raise AssertionError('ENTRY_MODELS_FORBIDDEN ' + name)
        sys.meta_path.insert(0, NoPhysical()); old, Adapter, _, _ = binding()
        assert Path(Adapter.compute.__code__.co_filename).resolve() == R / 'experiments/v1114_coupled_steering_mode/coupled_control.py'
        print(json.dumps(dict(passed=True, models=0, physical_native=0, actual_current_adapter_imported=True))); return 0
    window=read(O/'ROUND_WINDOW.json');authorize(task,window)
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
