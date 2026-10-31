#!/usr/bin/env python3
"""B68 observed-map Hybrid-A* and same-state real-controller development test."""
from __future__ import annotations
import argparse
import dataclasses
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
import traceback
from types import MethodType

ROOT = Path('/home/linghu/catkin_ws/src/mk-mini')
HERE = Path(__file__).resolve().parent
os.environ.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
                  OPENBLAS_NUM_THREADS='1', MUJOCO_GL='egl', CUDA_VISIBLE_DEVICES='')
sys.path.insert(0, str(ROOT/'experiments/phase_rpccr_p0b64_v1'))
import action_snapshot_worker as X
A, W, B, P, G, C = X.A, X.W, X.B, X.P, X.G, X.C
from semantic_sync import refresh
sys.path.insert(0, str(HERE))
from hybrid_planner import ObservedMap, plan

ROLLOUT_SEEDS = (73102366, 73102370, 73102379, 73102384)


def world_input(env, sensor_points):
    np = B.NP
    rectangles, circles = env._phase21_v4_known_map_obstacles()
    q = np.asarray(env.data.qpos)
    yaw = math.atan2(2*(q[3]*q[6]+q[4]*q[5]), 1-2*(q[5]**2+q[6]**2))
    return {'rectangles': np.asarray(rectangles).tolist(),
            'circles': np.asarray(circles).tolist(),
            'sensor_points': np.asarray(sensor_points).tolist(),
            'start': [float(q[0]), float(q[1]), yaw],
            'goal': np.asarray(env.goal_xy).tolist(),
            'robot_radius': float(getattr(env, 'robot_radius', 0.28)),
            'sensor_radius': float(env.phase21_corridor_radius),
            'wheel_base': float(env.inner.wheel_base),
            'max_steer': float(env.inner.max_steer)}


def search(inputs):
    observed = ObservedMap(inputs['rectangles'], inputs['circles'], inputs['sensor_points'],
                           inputs['robot_radius'], inputs['sensor_radius'])
    path, stats = plan(observed, inputs['start'], inputs['goal'],
                       inputs['wheel_base'], inputs['max_steer'])
    return observed, path, stats


def candidate_for(path, selected, observed):
    np = B.NP
    xy = np.asarray(path[:, :2], dtype=np.float32)
    lengths = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    curvatures = np.abs(np.diff(path[:, 2]))/np.maximum(lengths, 1e-9)
    original = np.asarray(selected.active_path)
    length0 = float(np.linalg.norm(np.diff(original, axis=0), axis=1).sum())
    heading = np.asarray([math.cos(path[0, 2]), math.sin(path[0, 2])])
    relative = xy[min(20, len(xy)-1)]-xy[0]
    side = 1.0 if heading[0]*relative[1]-heading[1]*relative[0] >= 0 else -1.0
    sensor_margin = float('inf')
    if len(observed.sensor_points):
        sensor_margin = float(np.min(np.linalg.norm(xy[:, None, :]
                        -observed.sensor_points[None, :, :], axis=2))-observed.sensor_radius)
    # Telemetry only. The new search is checked using its own frozen map criterion.
    return dataclasses.replace(selected, active_path=xy, local_curve=xy,
        approach_index=0, rejoin_index=len(original)-1, side_sign=side,
        offset=float(np.min(np.linalg.norm(xy[:, None, :]-original[None, :, :], axis=2), axis=1).max()),
        approach_distance=0.0, rejoin_distance=float(lengths.sum()), shoulder=0.0,
        sensor_margin=sensor_margin,
        p95_curvature=float(np.percentile(curvatures, 95)),
        max_heading_delta=float(np.abs(np.diff(path[:, 2])).max()),
        length_ratio=float(lengths.sum()/max(length0, 1e-9)),
        reverse_count=0, objective=0.0, score=0.0, feasible=True)


def apply(env, obs, shift, path, observed, pool, module, parent):
    candidate = candidate_for(path, pool['selected'], observed)
    C.apply_candidate(env, module, parent, candidate, pool['count'], pool['request_hash'])
    obs, sync = refresh(env, obs, shift, B)
    if not (sync['complete_other_state_equal'] and sync['all_non_path_observation_equal']
            and sync['no_sensor_queries']):
        raise B.ReplayMismatch('New path changed unrelated observation/state')
    dense = B.NP.asarray(env.inner.dense_path)
    return obs, {'sync': sync, 'new_path_hash': B.fingerprint(candidate.active_path),
                 'consumer_dense_path_hash': B.fingerprint(dense),
                 'consumer_dense_min_observed_clearance_m':
                    float(observed.exact_clearance(dense).min())}


def dump_trace(name, rows):
    with gzip.open(B.OUT/f'branches/{name}_trace.json.gz', 'wt', encoding='utf-8',
                   compresslevel=5) as stream:
        json.dump(rows, stream, separators=(',', ':'))


def physical_hash(rows):
    # Pickle-based state hashes also encode object-sharing/memoization, which can
    # differ between in-memory and JSON-loaded equal values. Compare physical
    # records through a deterministic value serialization instead.
    physical = [{key: value for key, value in row.items()
                 if key != 'state_hash_without_model'} for row in rows]
    payload = json.dumps(B.json_value(physical), sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload.encode()).hexdigest()


def rolling_rollout(env, model, shift, obs, gate_step, pool, module, parent):
    """Use the unchanged real step; request new paths using causal sensor points."""
    np = B.NP
    events, rows = [], []
    searches = 0
    collided = arrived = terminal = False
    for step in range(gate_step, 601):
        if (step > gate_step and (step-gate_step) % 10 == 0 and searches < 6
                and str(env.inner.recovery_stage) == 'NORMAL'):
            margin = env._phase21_v8_future_sensor_margin()
            if margin is not None and math.isfinite(float(margin)) and margin < 0.05:
                snapshot = B.Snapshot(env, shift)
                before = A.state_digest(env, shift)
                sensor_world, _ = env._phase21_sensor_points()
                inputs = world_input(env, sensor_world)
                snapshot.restore(shift)
                if A.state_digest(env, shift) != before:
                    raise B.ReplayMismatch('Rolling sensor query not restored')
                observed, path, stats = search(inputs)
                searches += 1
                event = {'public_step': step, 'input_hash': B.fingerprint(inputs),
                         'margin_m': float(margin), 'search': stats}
                if path is not None:
                    # A fresh request is needed only for the existing injection boundary.
                    # Generate no new candidate pool; reproduce the live Phase22 request.
                    requests = []
                    def capture(*args, **kwargs):
                        requests.append({k: v for k, v in kwargs.items() if k != 'env'})
                        return None, 0
                    boundary = B.Snapshot(env, shift)
                    try:
                        C.forced_call(env, parent, module, capture)
                    finally:
                        boundary.restore(shift)
                    if len(requests) == 1:
                        live = dict(pool)
                        live['request_hash'] = B.fingerprint(requests[0])
                        obs, applied = apply(env, obs, shift, path, observed, live, module, parent)
                        event['applied'] = applied
                    else:
                        event['not_applied_reason'] = 'existing_phase22_boundary_not_reached'
                events.append(event)
                A.write(B.OUT/'rolling_progress.json', events)
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = B.finish_api(env.step(action))
        audit = G.label_step(env, info)
        collision = bool(audit['primary_collision'])
        success = bool(info.get('reach_goal', False) or info.get('success', False)
                       or info.get('is_success', False))
        collided |= collision
        arrived |= success
        rows.append({'public_step': step, 'action': np.asarray(action).tolist(),
            'observation': np.asarray(obs).tolist(), 'qpos': env.data.qpos.copy().tolist(),
            'qvel': env.data.qvel.copy().tolist(), 'ctrl': env.data.ctrl.copy().tolist(),
            'robot_xy': np.asarray(env.robot_xy).tolist(), 'reward': float(reward),
            'collision': collision, 'success': success, 'terminated': bool(terminated),
            'truncated': bool(truncated),
            'unknown_penetration': bool(audit['environment_flags']['phase20_unknown_penetration']),
            'known_penetration': bool(audit['environment_flags']['phase20_known_penetration']),
            'native_contact': bool(audit['native_obstacle_contact']),
            'state_hash_without_model': B.state_hash(env, shift, include_model=False),
            'recovery_stage': str(env.inner.recovery_stage), 'active_path_hash': W.path_hash(env),
            'unknown_clearance_evaluation_only': info.get('phase20_unknown_clearance')})
        if terminated or truncated or collision:
            terminal = True
            break
    result = {'trace_hash': B.fingerprint(rows), 'steps_from_gate': len(rows),
        'terminal_public_step': gate_step-1+len(rows), 'safe_success': arrived and not collided,
        'collision': collided, 'horizon_censored': not terminal,
        'unknown_penetration_ever': any(row['unknown_penetration'] for row in rows),
        'known_penetration_ever': any(row['known_penetration'] for row in rows),
        'native_contact_ever': any(row['native_contact'] for row in rows),
        'goal_distance_final_m': float(np.linalg.norm(env.goal_xy-env.robot_xy)),
        'final_robot_xy': np.asarray(env.robot_xy).tolist(), 'rolling_searches': events}
    return rows, result


def execute(args):
    import numpy as np
    import torch
    import mujoco
    B.NP, B.TORCH, B.MJ = np, torch, mujoco
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    P.install()
    import navigation.phase22.continuous_corridor_planner as planner
    import envs.phase22.mkmini_phase22_v1_continuous_corridor_env as module
    from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import MkMiniPhase22V1ContinuousCorridorEnv as Env
    from envs.phase21.mkmini_phase21_v11_candidate_recovery_env import MkMiniPhase21V11CandidateRecoveryEnv as Parent
    from training.phase21_risk_switch_fusion_sac.tests import eval_phase21_v3_exact_pair_5ep as E
    from stable_baselines3 import SAC
    if B.sha(B.MODEL) != B.EXPECTED_MODEL:
        raise RuntimeError('Frozen SAC model differs')
    source = X.SOURCE_RUN/f'seed_{args.seed}'/'data'
    manifest = json.loads((source/'decision_manifest.json').read_text())
    frozen = W.sources()
    for path in (HERE/'PROTOCOL_2026-10-17.md', HERE/'hybrid_planner.py', Path(__file__),
                 Path(X.__file__), source/'decision_snapshot.pkl',
                 source/'decision_observation.json', source/'decision_manifest.json'):
        frozen[str(path.resolve())] = B.sha(path)
    A.write(B.OUT/'frozen_sources_before.json', frozen)
    E.seed_all(args.seed)
    shift = B.load_shift(args.seed)
    env = Env()
    env._phase21_v4_known_map_obstacles = MethodType(B.clean_map, env)
    started = time.monotonic()
    try:
        E.reset_env(env, args.seed)
        if B.sha(B.OUT/'assets/isolated_indoor.xml') != B.sha(source/'assets/isolated_indoor.xml'):
            raise B.ReplayMismatch('Reset XML mismatch')
        checkpoint = X.restore_checkpoint(env, shift, source/'decision_snapshot.pkl')
        state = A.state_digest(env, shift)
        if state != manifest['decision_state_hash']:
            raise B.ReplayMismatch('Decision state mismatch')
        audit = B.audit_known_map(env)
        if not audit['known_map_source_gate_pass']:
            raise RuntimeError('Hidden geometry entered known map')
        pool = C.collect(env, shift, planner, module, Parent)
        if (pool['pool_hash'] != manifest['pool_hash']
                or pool['request_hash'] != manifest['request_hash']):
            raise B.ReplayMismatch('Frozen Phase22 pool/request differs')
        inputs = world_input(env, pool['request']['sensor_points'])
        A.write(B.OUT/'planner_input.json', inputs)
        observed, path, stats = search(inputs)
        _, repeated_path, repeated_stats = search(inputs)
        if B.fingerprint(path) != B.fingerprint(repeated_path) or stats['status'] != repeated_stats['status']:
            raise B.ReplayMismatch('Identical search input produced different path')
        if A.state_digest(env, shift) != state:
            raise B.ReplayMismatch('Pure planning changed simulator state')
        A.write(B.OUT/'planner_result.json', {'search': stats,
            'repeat_status': repeated_stats['status'], 'path_equal': True,
            'path_hash': B.fingerprint(path), 'path_xy_yaw': None if path is None else path.tolist()})
        result = {'seed': args.seed, 'gate_public_step': manifest['public_step'],
            'decision_state_hash': state, 'known_map_audit': audit,
            'planner_input_hash': B.fingerprint(inputs), 'search': stats,
            'same_input_path_deterministic': True, 'branches': [],
            'training': False, 'development_only': True, 'independent_validation': False}
        if args.rollout:
            model = SAC.load(str(B.MODEL), device='cpu')
            obs0 = np.asarray(json.loads((source/'decision_observation.json').read_text()), dtype=np.float32)
            names = ('phase22_anchor', 'hybrid_once', 'hybrid_rolling') if path is not None else ('phase22_anchor',)
            repeat_hash = {}
            for name in names:
                for repeat in range(1, args.repeats+1):
                    checkpoint.restore(shift)
                    if A.state_digest(env, shift) != state:
                        raise B.ReplayMismatch('Branch start state differs')
                    obs = obs0.copy()
                    applied = None
                    if name == 'phase22_anchor':
                        C.apply_candidate(env, module, Parent, pool['selected'], pool['count'], pool['request_hash'])
                        obs, _ = refresh(env, obs, shift, B)
                    else:
                        obs, applied = apply(env, obs, shift, path, observed, pool, module, Parent)
                    begin = time.monotonic()
                    if name == 'hybrid_rolling':
                        rows, outcome = rolling_rollout(env, model, shift, obs, manifest['public_step'], pool, module, Parent)
                    else:
                        rows, outcome = C.rollout(env, model, shift, obs, manifest['public_step'])
                    phash = physical_hash(rows)
                    dump_trace(f'{name}_repeat_{repeat}', rows)
                    if repeat == 1:
                        repeat_hash[name] = phash
                    elif phash != repeat_hash[name]:
                        raise B.ReplayMismatch('Repeated physical trace differs')
                    if name == 'phase22_anchor':
                        with gzip.open(source/'branches/phase22_original_recovery_repeat_1_trace.json.gz', 'rt') as stream:
                            old = json.load(stream)
                        if phash != physical_hash(old):
                            raise B.ReplayMismatch('Phase22 anchor differs physically from B57')
                    record = {'condition': name, 'repeat': repeat, 'physical_trace_hash': phash,
                              'applied': applied, 'wall_seconds': time.monotonic()-begin, **outcome}
                    result['branches'].append(record)
                    A.write(B.OUT/'branch_progress.json', result['branches'])
                    print(json.dumps({'event': 'BRANCH_DONE', 'seed': args.seed,
                         'condition': name, 'repeat': repeat, 'safe': outcome['safe_success'],
                         'step': outcome['terminal_public_step']}), flush=True)
        result['wall_seconds'] = time.monotonic()-started
        A.write(B.OUT/'result.json', result)
        print(json.dumps({'event': 'DONE', 'seed': args.seed, 'search': stats['status']}), flush=True)
    finally:
        env.close()
        changes = [p for p, digest in frozen.items() if B.sha(Path(p)) != digest]
        A.write(B.OUT/'integrity.json', {'frozen_source_changes': changes,
                                      'frozen_model_sha256': B.sha(B.MODEL)})
        if changes:
            raise RuntimeError('Frozen source changed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, choices=X.SEEDS, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--rollout', action='store_true')
    parser.add_argument('--repeats', type=int, choices=(1, 2), default=1)
    parser.add_argument('--budget-seconds', type=int, default=900)
    args = parser.parse_args()
    if args.rollout and args.seed not in ROLLOUT_SEEDS:
        parser.error('Rollout seeds fixed in protocol')
    B.OUT = args.out.resolve()
    B.OUT.mkdir(parents=True, exist_ok=False)
    os.chdir(B.OUT)
    (B.OUT/'assets').mkdir()
    (B.OUT/'branches').mkdir()
    (B.OUT/'assets/meshes_fixed').symlink_to(ROOT/'training/assets/mkmini_real/meshes_fixed', target_is_directory=True)
    for key in ('XDG_CACHE_HOME', 'MESA_SHADER_CACHE_DIR', '__GL_SHADER_DISK_CACHE_PATH'):
        os.environ[key] = str(B.OUT/'cache')
    os.environ['MPLCONFIGDIR'] = str(B.OUT/'cache/matplotlib')
    sys.addaudithook(B.write_guard)
    A.write(B.OUT/'preregistration.json', {'experiment': 'B68', 'seed': args.seed,
        'rollout': args.rollout, 'repeats': args.repeats, 'budget_seconds': args.budget_seconds,
        'model_sha256': B.EXPECTED_MODEL, 'development_only': True, 'training': False})
    def alarm(*_):
        raise P.HardBudgetExceeded('B68 per-state wall budget')
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, args.budget_seconds)
    code = 0
    try:
        execute(args)
        A.write(B.OUT/'completion.json', {'status': 'FINISHED'})
    except P.HardBudgetExceeded as exc:
        code = 124
        A.write(B.OUT/'failure.json', {'status': 'COMPUTE_CENSORED', 'reason': str(exc)})
    except Exception as exc:
        code = 1
        A.write(B.OUT/'failure.json', {'status': 'IMPLEMENTATION_ERROR', 'reason': repr(exc),
                                    'traceback': traceback.format_exc()})
        traceback.print_exc()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    return code


if __name__ == '__main__':
    sys.exit(main())
