#!/usr/bin/env python3
"""B69 current self-envelope / wheel-target-limit paired development experiment."""
from __future__ import annotations
import argparse
import functools
import gzip
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
os.environ.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                  MUJOCO_GL='egl', CUDA_VISIBLE_DEVICES='')
sys.path.insert(0, str(ROOT/'experiments/phase_rpccr_p0b68_v1'))
import search_worker as H
X, A, W, B, P, G, C = H.X, H.A, H.W, H.B, H.P, H.G, H.C
sys.path.insert(0, str(HERE))
import footprint_map as F

ROLLOUT = (73102366, 73102370, 73102384)
CAP = {'enabled': False, 'calls': 0, 'clamped': 0}
CONTACT = {'active': False, 'events': []}


def install_observers(env, footprint, mj):
    owner = next(cls for cls in type(env.inner).__mro__ if '_apply_wheel_ctrl' in cls.__dict__)
    original = owner.__dict__['_apply_wheel_ctrl']
    @functools.wraps(original)
    def wheel(self, lf, rf, lr, rr):
        if CAP['enabled']:
            CAP['calls'] += 1
            bound = .20*float(self.max_wheel_speed)
            left, right = max(-bound, min(bound, lr)), max(-bound, min(bound, rr))
            CAP['clamped'] += int(left != lr or right != rr)
            lr, rr = left, right
        return original(self, lf, rf, lr, rr)
    owner._apply_wheel_ctrl = wheel
    ids = {e['geom_id'] for e in footprint['active_robot_geoms']}
    step = mj.mj_step
    @functools.wraps(step)
    def observed_step(model, data, *args, **kwargs):
        value = step(model, data, *args, **kwargs)
        if CONTACT['active']:
            for contact in data.contact:
                ga, gb = int(contact.geom1), int(contact.geom2)
                if (ga in ids) == (gb in ids):
                    continue
                robot, other = (ga, gb) if ga in ids else (gb, ga)
                name = mj.mj_id2name(model, mj.mjtObj.mjOBJ_GEOM, other) or ''
                if 'real_rect_obs' in name or 'real_circle_obs' in name:
                    CONTACT['events'].append({'sim_time': float(data.time),
                        'robot_geom_id': robot,
                        'robot_geom_name': mj.mj_id2name(model, mj.mjtObj.mjOBJ_GEOM, robot),
                        'obstacle_name_evaluation_only': name, 'distance_m': float(contact.dist)})
        return value
    mj.mj_step = observed_step
    return {'wheel_owner': owner.__module__+'.'+owner.__name__,
            'cap_normalized_target': .20, 'rate_limiter_retained': True,
            'all_self_contact_scope': 'every physical mj_step, evaluation only'}


def b68_data(seed):
    status = json.loads((ROOT/'experiments/phase_rpccr_p0b68_v1/runs/panel12_20261017_01/status.json').read_text())
    return Path(next(j['data'] for j in status['jobs'] if j['seed'] == seed))


def footprint_input(env, sensors, bounds):
    inputs = H.world_input(env, sensors)
    inputs['footprint_bounds'] = bounds
    return inputs


def footprint_future_margin(env, sensors, bounds):
    np = B.NP
    path = np.asarray(env.phase21_v3_active_path, dtype=float)
    position = np.asarray(env.robot_xy, dtype=float)
    nearest = int(np.argmin(np.linalg.norm(path-position, axis=1)))
    future = path[nearest:]
    if len(future) < 2:
        return None
    cumulative = np.r_[0, np.cumsum(np.linalg.norm(np.diff(future, axis=0), axis=1))]
    end = min(len(future), max(2, int(np.searchsorted(cumulative, 1.5))+1))
    future = future[:end]
    angles = np.arctan2(np.diff(future[:, 1]), np.diff(future[:, 0]))
    poses = np.column_stack((future, np.r_[angles, angles[-1]]))
    inputs = footprint_input(env, sensors, bounds)
    observed = F.FootprintMap(inputs)
    current = observed.pose_values([inputs['start']])[0]
    ahead = observed.pose_values(poses).min()
    return float(min(current, ahead)), {'current_m': float(current), 'reference_ahead_m': float(ahead)}


def full_rollout(env, model, shift, obs, gate, pool, module, parent, bounds):
    np = B.NP
    rows, events = [], []
    searches = 0
    collided = arrived = terminal = False
    for step in range(gate, 601):
        if step > gate and (step-gate) % 10 == 0:
            event = {'public_step': step, 'stage': str(env.inner.recovery_stage)}
            if event['stage'] != 'NORMAL':
                event['reason'] = 'recovery_stage'
            elif searches >= 6:
                event['reason'] = 'search_limit'
            else:
                snapshot = B.Snapshot(env, shift)
                state = A.state_digest(env, shift)
                sensors, _ = env._phase21_sensor_points()
                inputs = footprint_input(env, sensors, bounds)
                assessed = footprint_future_margin(env, sensors, bounds)
                snapshot.restore(shift)
                if A.state_digest(env, shift) != state:
                    raise B.ReplayMismatch('Footprint sensor query state drift')
                if assessed is None:
                    event['reason'] = 'short_reference'
                else:
                    margin, detailed = assessed
                    event.update(footprint_margin_m=margin, margin_parts=detailed)
                    if margin >= .05:
                        event['reason'] = 'margin_sufficient'
                    else:
                        observed, path, stats = F.search(inputs)
                        searches += 1
                        event.update(reason='searched', search=stats, input_hash=B.fingerprint(inputs))
                        if path is not None:
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
                                live = dict(pool, request_hash=B.fingerprint(requests[0]))
                                obs, applied = H.apply(env, obs, shift, path, observed, live, module, parent)
                                event['applied'] = applied
                            else:
                                event['not_applied_reason'] = 'existing_phase22_boundary_not_reached'
            events.append(event)
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = B.finish_api(env.step(action))
        audit = G.label_step(env, info)
        collision = bool(audit['primary_collision'])
        success = bool(info.get('reach_goal', False) or info.get('success', False) or info.get('is_success', False))
        collided |= collision
        arrived |= success
        rows.append({'public_step': step, 'action': np.asarray(action).tolist(),
            'observation': np.asarray(obs).tolist(), 'qpos': env.data.qpos.copy().tolist(),
            'qvel': env.data.qvel.copy().tolist(), 'ctrl': env.data.ctrl.copy().tolist(),
            'robot_xy': np.asarray(env.robot_xy).tolist(), 'reward': float(reward),
            'collision': collision, 'success': success, 'terminated': bool(terminated), 'truncated': bool(truncated),
            'unknown_penetration': bool(audit['environment_flags']['phase20_unknown_penetration']),
            'known_penetration': bool(audit['environment_flags']['phase20_known_penetration']),
            'native_contact': bool(audit['native_obstacle_contact']),
            'state_hash_without_model': B.state_hash(env, shift, include_model=False),
            'recovery_stage': str(env.inner.recovery_stage), 'active_path_hash': W.path_hash(env),
            'unknown_clearance_evaluation_only': info.get('phase20_unknown_clearance')})
        if terminated or truncated or collision:
            terminal = True
            break
    return rows, {'trace_hash': B.fingerprint(rows), 'safe_success': arrived and not collided,
        'collision': collided, 'horizon_censored': not terminal, 'terminal_public_step': step,
        'native_contact_ever': any(r['native_contact'] for r in rows),
        'known_penetration_ever': any(r['known_penetration'] for r in rows),
        'unknown_penetration_ever': any(r['unknown_penetration'] for r in rows),
        'goal_distance_final_m': float(np.linalg.norm(env.goal_xy-env.robot_xy)),
        'rolling_checks': events}


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
    source = X.SOURCE_RUN/f'seed_{args.seed}'/'data'
    prior = b68_data(args.seed)
    manifest = json.loads((source/'decision_manifest.json').read_text())
    frozen = W.sources()
    for path in (Path(__file__), HERE/'footprint_map.py', HERE/'PROTOCOL_2026-10-17.md',
                 Path(H.__file__), Path(F.base.__file__), Path(X.__file__),
                 source/'decision_snapshot.pkl', source/'decision_manifest.json',
                 source/'decision_observation.json', prior/'planner_input.json'):
        frozen[str(path.resolve())] = B.sha(path)
    A.write(B.OUT/'frozen_sources_before.json', frozen)
    if B.sha(B.MODEL) != B.EXPECTED_MODEL:
        raise RuntimeError('Frozen SAC differs')
    E.seed_all(args.seed)
    shift = B.load_shift(args.seed)
    env = Env()
    env._phase21_v4_known_map_obstacles = MethodType(B.clean_map, env)
    began = time.monotonic()
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
            raise RuntimeError('Known map leakage')
        footprint = F.extract_self_envelope(env, mujoco)
        A.write(B.OUT/'self_geometry_audit.json', footprint)
        pool = C.collect(env, shift, planner, module, Parent)
        if pool['pool_hash'] != manifest['pool_hash'] or pool['request_hash'] != manifest['request_hash']:
            raise B.ReplayMismatch('Frozen candidate pool/request mismatch')
        original_inputs = H.world_input(env, pool['request']['sensor_points'])
        if original_inputs != json.loads((prior/'planner_input.json').read_text()):
            raise B.ReplayMismatch('B68 input values mismatch')
        inputs = dict(original_inputs, footprint_bounds=footprint['bounds_xy'])
        A.write(B.OUT/'planner_input.json', inputs)
        observed, path, stats = F.search(inputs)
        _, again, repeated = F.search(inputs)
        if B.fingerprint(path) != B.fingerprint(again) or stats['status'] != repeated['status']:
            raise B.ReplayMismatch('Footprint search nondeterministic')
        if A.state_digest(env, shift) != state:
            raise B.ReplayMismatch('Self audit/search mutated state')
        A.write(B.OUT/'planner_result.json', {'search': stats,
            'path_xy_yaw': None if path is None else path.tolist(), 'repeat_path_equal': True})
        result = {'seed': args.seed, 'search': stats, 'footprint_bounds': footprint['bounds_xy'],
            'known_map_audit': audit, 'same_input_path_deterministic': True, 'branches': [],
            'development_only': True, 'independent_validation': False, 'training': False}
        if args.rollout:
            model = SAC.load(str(B.MODEL), device='cpu')
            obs0 = np.asarray(json.loads((source/'decision_observation.json').read_text()), dtype=np.float32)
            circle_field, circle_path, _ = H.search(original_inputs)
            if circle_path is None:
                raise B.ReplayMismatch('Frozen B68 rollout path disappeared')
            observer = install_observers(env, footprint, mujoco)
            result['observer_contract'] = observer
            choices = [('circle_rolling_anchor', False, circle_field, circle_path),
                       ('circle_rolling_speedcap', True, circle_field, circle_path)]
            if path is not None:
                choices += [('footprint_rolling', False, observed, path),
                            ('footprint_rolling_speedcap', True, observed, path)]
            repeated_hash = {}
            for name, capped, field, chosen in choices:
                for repeat in range(1, args.repeats+1):
                    checkpoint.restore(shift)
                    if A.state_digest(env, shift) != state:
                        raise B.ReplayMismatch('Paired initial state mismatch')
                    CAP.update(enabled=capped, calls=0, clamped=0)
                    CONTACT.update(active=True, events=[])
                    obs, applied = H.apply(env, obs0.copy(), shift, chosen, field, pool, module, Parent)
                    start = time.monotonic()
                    if name.startswith('circle'):
                        rows, outcome = H.rolling_rollout(env, model, shift, obs, manifest['public_step'], pool, module, Parent)
                    else:
                        rows, outcome = full_rollout(env, model, shift, obs, manifest['public_step'], pool, module, Parent, footprint['bounds_xy'])
                    CONTACT['active'] = False
                    phash = H.physical_hash(rows)
                    if repeat == 1:
                        repeated_hash[name] = phash
                    elif repeated_hash[name] != phash:
                        raise B.ReplayMismatch('Repeat physical trajectory mismatch')
                    if name == 'circle_rolling_anchor':
                        with gzip.open(prior/'branches/hybrid_rolling_repeat_1_trace.json.gz', 'rt') as stream:
                            old = json.load(stream)
                        if H.physical_hash(old) != phash:
                            raise B.ReplayMismatch('B68 rolling anchor changed')
                    with gzip.open(B.OUT/f'branches/{name}_repeat_{repeat}_trace.json.gz', 'wt') as stream:
                        json.dump(rows, stream, separators=(',', ':'))
                    A.write(B.OUT/f'branches/{name}_repeat_{repeat}_contacts_evaluation_only.json', CONTACT['events'])
                    record = {'condition': name, 'repeat': repeat, 'physical_trace_hash': phash,
                        'cap_calls': CAP['calls'], 'cap_clamped_calls': CAP['clamped'],
                        'all_robot_contact_ever': bool(CONTACT['events']),
                        'all_robot_penetration_ever': any(e['distance_m'] <= 0 for e in CONTACT['events']),
                        'applied': applied, 'wall_seconds': time.monotonic()-start, **outcome}
                    result['branches'].append(record)
                    A.write(B.OUT/'branch_progress.json', result['branches'])
                    print(json.dumps({'event': 'BRANCH_DONE', 'seed': args.seed, 'condition': name,
                        'repeat': repeat, 'safe': outcome['safe_success'], 'step': outcome['terminal_public_step'],
                        'all_robot_contact': record['all_robot_contact_ever']}), flush=True)
            CAP['enabled'] = False
        result['wall_seconds'] = time.monotonic()-began
        A.write(B.OUT/'result.json', result)
        print(json.dumps({'event': 'DONE', 'seed': args.seed, 'search': stats['status']}), flush=True)
    finally:
        env.close()
        changes = [path for path, old in frozen.items() if B.sha(Path(path)) != old]
        A.write(B.OUT/'integrity.json', {'frozen_source_changes': changes,
                                       'frozen_model_sha256': B.sha(B.MODEL)})
        if changes:
            raise RuntimeError('Frozen source/model changed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=int, choices=X.SEEDS, required=True)
    parser.add_argument('--rollout', action='store_true')
    parser.add_argument('--repeats', type=int, choices=(1, 2), default=1)
    parser.add_argument('--budget-seconds', type=int, default=900)
    args = parser.parse_args()
    if args.rollout and args.seed not in ROLLOUT:
        parser.error('Rollout seeds fixed')
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
    A.write(B.OUT/'preregistration.json', {'experiment': 'B69', 'seed': args.seed,
        'rollout': args.rollout, 'repeats': args.repeats, 'budget_seconds': args.budget_seconds,
        'development_only': True, 'cap_normalized_target': .20, 'model_sha256': B.EXPECTED_MODEL})
    def alarm(*_):
        raise P.HardBudgetExceeded('B69 state budget')
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
        A.write(B.OUT/'failure.json', {'status': 'IMPLEMENTATION_ERROR', 'reason': repr(exc), 'traceback': traceback.format_exc()})
        traceback.print_exc()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    return code


if __name__ == '__main__':
    sys.exit(main())
