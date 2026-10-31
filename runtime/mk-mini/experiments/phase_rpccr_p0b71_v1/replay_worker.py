#!/usr/bin/env python3
"""Only B71 snapshot replays; no training and no previous experiment entrypoints."""
from __future__ import annotations
import argparse
import functools
import gzip
import hashlib
import inspect
import json
import os
from pathlib import Path
import random
import signal
import struct
import sys
import time
import traceback
from types import MethodType

ROOT = Path('/home/linghu/catkin_ws/src/mk-mini')
HERE = Path(__file__).resolve().parent
os.environ.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                  MKL_NUM_THREADS='1', MUJOCO_GL='egl', CUDA_VISIBLE_DEVICES='')
sys.path.insert(0, str(ROOT/'experiments/phase_rpccr_p0b68_v1'))
import search_worker as H
X, A, W, B, P, G, C = H.X, H.A, H.W, H.B, H.P, H.G, H.C
from contact_contract import GeometryCatalog, ContactRecorder, canonical


def read(path):
    return json.loads(path.read_text())


def physical_state_hash(model, data):
    digest = hashlib.sha256(struct.pack('<d', float(data.time)))
    for name in ('qpos','qvel','act','ctrl','qacc','qacc_warmstart','sensordata','xpos','xmat',
                 'geom_xpos','geom_xmat','actuator_force','qfrc_applied','xfrc_applied',
                 'userdata','mocap_pos','mocap_quat','eq_active'):
        value = getattr(data, name)
        digest.update(name.encode()); digest.update(str(value.shape).encode())
        digest.update(str(value.dtype).encode()); digest.update(value.tobytes())
    for contact in data.contact:
        digest.update(struct.pack('<iid', int(contact.geom1), int(contact.geom2), float(contact.dist)))
        digest.update(contact.pos.tobytes()); digest.update(contact.frame.tobytes())
    return digest.hexdigest()


def rng_hash(np, torch):
    return B.fingerprint((random.getstate(), np.random.get_state(), torch.get_rng_state().numpy()))


def branch_paths(seed):
    status = read(ROOT/'experiments/phase_rpccr_p0b68_v1/runs/panel12_20261017_01/status.json')
    b68 = Path(next(j['data'] for j in status['jobs'] if j['seed'] == seed))
    b69base = ROOT/'experiments/phase_rpccr_p0b69_v1/runs'
    b69 = b69base/'pilot_73102366_01' if seed == 73102366 else b69base/f'panel12_20261017_01/seed_{seed}/data'
    name = 'circle_rolling_speedcap' if seed == 73102384 else 'circle_rolling_anchor'
    return b68, b69, name


def execute(args):
    import numpy as np
    import torch
    import mujoco
    B.NP, B.TORCH, B.MJ = np, torch, mujoco
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    frozen = read(HERE/'preflight.json')['original_hashes']
    frozen.update(read(HERE/'b71_implementation_hashes.json'))
    def integrity():
        changes = [path for path, digest in frozen.items() if B.sha(Path(path)) != digest]
        if changes:
            raise B.ReplayMismatch('Frozen input hashes changed: '+repr(changes))
    integrity()
    P.install()
    import navigation.phase22.continuous_corridor_planner as planner
    import envs.phase22.mkmini_phase22_v1_continuous_corridor_env as module
    from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import MkMiniPhase22V1ContinuousCorridorEnv as Env
    from envs.phase21.mkmini_phase21_v11_candidate_recovery_env import MkMiniPhase21V11CandidateRecoveryEnv as Parent
    from training.phase21_risk_switch_fusion_sac.tests import eval_phase21_v3_exact_pair_5ep as E
    from stable_baselines3 import SAC
    source = X.SOURCE_RUN/f'seed_{args.seed}'/'data'
    manifest = read(source/'decision_manifest.json')
    prior, b69, branch_name = branch_paths(args.seed)
    oldpath = b69/f'branches/{branch_name}_repeat_1_trace.json.gz'
    with gzip.open(oldpath, 'rt') as stream:
        oldrows = json.load(stream)
    oldhash = H.physical_hash(oldrows)
    if args.seed != 73102384:
        with gzip.open(prior/'branches/hybrid_rolling_repeat_1_trace.json.gz', 'rt') as stream:
            if H.physical_hash(json.load(stream)) != oldhash:
                raise B.ReplayMismatch('B68/B69 anchor evidence disagrees')
    E.seed_all(args.seed)
    shift = B.load_shift(args.seed)
    env = Env()
    env._phase21_v4_known_map_obstacles = MethodType(B.clean_map, env)
    result = {'seed': args.seed, 'historical_branch': branch_name, 'historical_trace': str(oldpath),
              'historical_physical_hash': oldhash, 'snapshot': str(source/'decision_snapshot.pkl'),
              'snapshot_sha256': B.sha(source/'decision_snapshot.pkl'), 'runs': [],
              'status': 'RUNNING', 'training': False}
    began = time.monotonic()
    recorder = None
    try:
        E.reset_env(env, args.seed)
        if B.sha(B.OUT/'assets/isolated_indoor.xml') != B.sha(source/'assets/isolated_indoor.xml'):
            raise B.ReplayMismatch('Initial XML hash mismatch')
        checkpoint = X.restore_checkpoint(env, shift, source/'decision_snapshot.pkl')
        state = A.state_digest(env, shift)
        if state != manifest['decision_state_hash']:
            raise B.ReplayMismatch('Snapshot restore state mismatch')
        result['decision_state_hash'] = state
        result['gate_public_step'] = manifest['public_step']
        result['isolated_xml_sha256'] = B.sha(B.OUT/'assets/isolated_indoor.xml')
        audit = B.audit_known_map(env)
        if not audit['known_map_source_gate_pass']:
            raise B.ReplayMismatch('Known-map isolation failed')
        pool = C.collect(env, shift, planner, module, Parent)
        if (pool['pool_hash'], pool['request_hash']) != (manifest['pool_hash'], manifest['request_hash']):
            raise B.ReplayMismatch('Frozen candidate pool/request mismatch')
        inputs = H.world_input(env, pool['request']['sensor_points'])
        if inputs != read(prior/'planner_input.json'):
            raise B.ReplayMismatch('Frozen B68 planner input mismatch')
        saved_path = read(prior/'planner_result.json')['path_xy_yaw']
        if saved_path is None:
            raise B.ReplayMismatch('No unambiguous saved branch path')
        chosen = np.asarray(saved_path, dtype=float)
        field = H.ObservedMap(inputs['rectangles'], inputs['circles'], inputs['sensor_points'],
                              inputs['robot_radius'], inputs['sensor_radius'])
        catalog = GeometryCatalog(env.model, mujoco, B.OUT/'assets/isolated_indoor.xml')
        if A.state_digest(env, shift) != state:
            raise B.ReplayMismatch('Pre-rollout audits mutated restored state')
        A.write(B.OUT/'geometry_catalog.json', catalog.audit())
        A.write(B.OUT/'branch_configuration.json', {'seed': args.seed, 'branch': branch_name,
            'pool_hash': pool['pool_hash'], 'request_hash': pool['request_hash'],
            'initial_path_source': str(prior/'planner_result.json'), 'initial_path_sha256': B.sha(prior/'planner_result.json'),
            'path_value_hash': B.fingerprint(chosen), 'known_map_audit': audit,
            'speed_cap': .20 if args.seed == 73102384 else None,
            'preserved_rate_limiter': True, 'original_rolling_function': str(Path(H.__file__))+'::rolling_rollout'})
        model = SAC.load(str(B.MODEL), device='cpu')
        obs0 = np.asarray(read(source/'decision_observation.json'), dtype=np.float32)
        cap = {'enabled': args.seed == 73102384, 'calls': 0, 'clamped': 0}
        owner = next(cls for cls in type(env.inner).__mro__ if '_apply_wheel_ctrl' in cls.__dict__)
        wheel_original = owner.__dict__['_apply_wheel_ctrl']
        @functools.wraps(wheel_original)
        def wheel(self, lf, rf, lr, rr):
            if cap['enabled']:
                cap['calls'] += 1
                bound = .20*float(self.max_wheel_speed)
                left, right = max(-bound,min(bound,lr)), max(-bound,min(bound,rr))
                cap['clamped'] += int(left != lr or right != rr)
                lr, rr = left, right
            return wheel_original(self, lf, rf, lr, rr)
        owner._apply_wheel_ctrl = wheel
        native_original, api_original = mujoco.mj_step, Env.step
        context = {'active': False}
        call_chain = []
        @functools.wraps(native_original)
        def native(model_arg, data, *args_native, **kwargs):
            if context['active']:
                nstep = kwargs.get('nstep', args_native[0] if args_native else 1)
                if nstep != 1:
                    raise B.ReplayMismatch('Batched mj_step cannot be individually observed')
                if model_arg is not env.model or data is not env.data:
                    raise B.ReplayMismatch('Unexpected simulation model/data during replay')
                if not call_chain:
                    call_chain.extend({'file': f.filename, 'line': f.lineno, 'function': f.function}
                                      for f in inspect.stack()[1:22])
            value = native_original(model_arg, data, *args_native, **kwargs)
            if context['active']:
                context['physics_step'] += 1
                before = physical_state_hash(model_arg, data)
                if context['recorder'] is not None:
                    rng_before = rng_hash(np, torch)
                    context['recorder'].record(data, context['physics_step'], context['public_step'])
                    if physical_state_hash(model_arg, data) != before or rng_hash(np, torch) != rng_before:
                        raise B.ReplayMismatch('Evaluator mutated physics/RNG state')
                    context['per_step_nonmutation_checks'] += 1
                encoded = canonical({'physics_step': context['physics_step'],
                    'public_step': context['public_step'], 'sim_time': float(data.time), 'state_sha256': before})+'\n'
                context['physics_hasher'].update(encoded.encode())
                context['physics_stream'].write(encoded)
            return value
        @functools.wraps(api_original)
        def api(self, action):
            value = api_original(self, action)
            if context['active']:
                context['public_step'] += 1
            return value
        mujoco.mj_step, Env.step = native, api
        result['runtime_chain'] = {'owners': [type(o).__module__+'.'+type(o).__name__ for o in B.objects(env)],
            'mro': {type(o).__name__: [c.__module__+'.'+c.__name__ for c in type(o).__mro__] for o in B.objects(env)},
            'wheel_owner': owner.__module__+'.'+owner.__name__}
        controls = None
        for name, enabled in [('evaluator_off',False), ('evaluator_on_repeat_1',True), ('evaluator_on_repeat_2',True)]:
            integrity()
            checkpoint.restore(shift)
            if A.state_digest(env, shift) != state:
                raise B.ReplayMismatch('Per-run snapshot restoration mismatch')
            cell = B.OUT/name
            cell.mkdir(exist_ok=False)
            cap.update(calls=0, clamped=0)
            observation, applied = H.apply(env, obs0.copy(), shift, chosen, field, pool, module, Parent)
            applied_hash = A.state_digest(env, shift)
            # Full state diagnostic: includes all environment/controller/cache fields,
            # model arrays/sections, MjData, RNG and renderer flags (no state writes).
            if enabled:
                for contact in env.data.contact:
                    catalog.classify(contact, 0, manifest['public_step']-1, float(env.data.time))
                if A.state_digest(env, shift) != applied_hash:
                    raise B.ReplayMismatch('Pure classification mutated complete state')
            recorder = ContactRecorder(catalog, cell) if enabled else None
            with gzip.open(cell/'physical_trajectory.jsonl.gz', 'xt', encoding='utf-8') as stream:
                context.update(active=True, physics_step=0, public_step=manifest['public_step'],
                    recorder=recorder, physics_hasher=hashlib.sha256(), physics_stream=stream,
                    per_step_nonmutation_checks=0)
                start = time.monotonic()
                try:
                    rows, outcome = H.rolling_rollout(env, model, shift, observation,
                        manifest['public_step'], pool, module, Parent)
                finally:
                    context['active'] = False
                    if recorder is not None:
                        recorder.close()
            summary = recorder.summary() if recorder is not None else None
            recorder = None
            with gzip.open(cell/'public_trace.json.gz', 'xt') as stream:
                json.dump(rows, stream, separators=(',', ':'))
            physical = H.physical_hash(rows)
            controller_hash = hashlib.sha256(canonical([row['state_hash_without_model'] for row in rows]).encode()).hexdigest()
            record = {'name': name, 'evaluator_enabled': enabled, 'restored_start_state_equal': True,
                'after_path_application_state_hash': applied_hash, 'physical_trace_hash': physical,
                'per_physics_trace_hash': context['physics_hasher'].hexdigest(),
                'controller_cache_rng_trace_hash': controller_hash, 'physics_steps': context['physics_step'],
                'per_physics_nonmutation_checks': context['per_step_nonmutation_checks'],
                'public_steps': len(rows), 'matches_historical_trace': physical == oldhash,
                'original_environment_success': any(row['success'] for row in rows),
                'goal_reached': any(row['success'] for row in rows),
                'original_goal_threshold_m': float(env.inner.goal_threshold),
                'goal_xy': np.asarray(env.goal_xy).tolist(), 'cap_calls': cap['calls'],
                'cap_clamped_calls': cap['clamped'], 'outcome': outcome, 'contact_evaluation': summary,
                'wall_seconds': time.monotonic()-start}
            if controls is None:
                controls = record
            record['matches_evaluator_off'] = all(record[k] == controls[k] for k in
                ('physical_trace_hash','per_physics_trace_hash','controller_cache_rng_trace_hash',
                 'after_path_application_state_hash','physics_steps','public_steps'))
            if summary is not None:
                record['strict_safe_arrival'] = record['goal_reached'] and summary['robot_obstacle_contact_records'] == 0 and summary['robot_obstacle_penetration_records'] == 0 and summary['unknown_contact_records'] == 0
                record['penetration_only_safe_arrival'] = record['goal_reached'] and summary['robot_obstacle_penetration_records'] == 0 and summary['unknown_contact_records'] == 0
            A.write(cell/'result.json', record)
            result['runs'].append(record)
            A.write(B.OUT/'result.json', result)
            A.write(B.OUT/'runtime_call_chain.json', call_chain)
            print(json.dumps({'event':'REPLAY_DONE','seed':args.seed,'name':name,
                'public_steps':len(rows),'matches_historical':physical == oldhash,
                'matches_off':record['matches_evaluator_off'],'contact':summary}), flush=True)
            if physical != oldhash or not record['matches_evaluator_off']:
                # Preserve first value-level mismatch, then halt this anchor.
                differences = []
                for index,(new,old) in enumerate(zip(rows,oldrows)):
                    fields = [k for k in new if k != 'state_hash_without_model' and new[k] != old.get(k)]
                    if fields:
                        differences.append({'index':index,'public_step':new['public_step'], 'fields':fields})
                        break
                A.write(cell/'mismatch.json', {'new_length':len(rows),'old_length':len(oldrows), 'first_differences':differences})
                raise B.ReplayMismatch('Evaluator-off/on or historical trajectory mismatch; replay stopped')
        on = [r for r in result['runs'] if r['evaluator_enabled']]
        result['contact_repeats_identical'] = on[0]['contact_evaluation'] == on[1]['contact_evaluation']
        if not result['contact_repeats_identical']:
            raise B.ReplayMismatch('Contact logs differ across repeated execution')
        integrity()
        result.update(status='PASS', wall_seconds=time.monotonic()-began,
            frozen_source_changes=[], frozen_model_sha256=B.sha(B.MODEL))
        A.write(B.OUT/'result.json', result)
    finally:
        context_active = locals().get('context')
        if context_active is not None:
            context_active['active'] = False
        if recorder is not None:
            recorder.close()
        env.close()
        changes = [path for path,digest in frozen.items() if B.sha(Path(path)) != digest]
        A.write(B.OUT/'integrity.json', {'frozen_source_changes':changes, 'frozen_model_sha256':B.sha(B.MODEL)})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, choices=(73102384,73102366,73102370), required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    B.OUT = args.out.resolve()
    B.OUT.mkdir(parents=True, exist_ok=False)
    os.chdir(B.OUT)
    (B.OUT/'assets').mkdir()
    (B.OUT/'assets/meshes_fixed').symlink_to(ROOT/'training/assets/mkmini_real/meshes_fixed', target_is_directory=True)
    for key in ('XDG_CACHE_HOME','MESA_SHADER_CACHE_DIR','__GL_SHADER_DISK_CACHE_PATH'):
        os.environ[key] = str(B.OUT/'cache')
    os.environ['MPLCONFIGDIR'] = str(B.OUT/'cache/matplotlib')
    sys.addaudithook(B.write_guard)
    def timeout(*_):
        raise RuntimeError('B71 anchor exceeded 900-second bound')
    signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, 900)
    try:
        execute(args)
        A.write(B.OUT/'completion.json', {'status':'PASS'})
        return 0
    except Exception as exc:
        A.write(B.OUT/'failure.json', {'status':'BLOCKED','reason':repr(exc),'traceback':traceback.format_exc()})
        A.write(B.OUT/'completion.json', {'status':'BLOCKED'})
        traceback.print_exc()
        return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    sys.exit(main())
