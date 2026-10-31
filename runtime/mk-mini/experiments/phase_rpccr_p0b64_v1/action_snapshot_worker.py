#!/usr/bin/env python3
"""Audit causal candidate actions at every opened B57 first gate without stepping."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import pickle
import signal
import sys
import time
import traceback
from types import MethodType

ROOT = Path('/home/linghu/catkin_ws/src/mk-mini')
HERE = Path(__file__).resolve().parent
SOURCE_RUN = ROOT/'experiments/phase_rpccr_p0b57_v1/runs/bounded32_20261017_01'
SEEDS = (73102366,73102367,73102370,73102374,73102376,73102379,
         73102381,73102382,73102384,73102386,73102395,73102396)
os.environ.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
                  OPENBLAS_NUM_THREADS='1', MUJOCO_GL='egl', CUDA_VISIBLE_DEVICES='')
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'experiments/phase_rpccr_p0b37_v1'))
sys.path.insert(0,str(ROOT/'experiments/phase_rpccr_p0b57_v1'))
spec=importlib.util.spec_from_file_location('b64_b8_support',
    ROOT/'experiments/phase_rpccr_p0b8_v1/candidate_worker.py')
C=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=C
spec.loader.exec_module(C)
A,W,B,P,G=C.A,C.W,C.B,C.P,C.G
from semantic_sync import refresh
from admission import decide


def restore_checkpoint(env, shift, path):
    with path.open('rb') as stream:
        payload=pickle.load(stream)
    checkpoint=B.Snapshot(env,shift)
    owners=[type(owner).__module__+'.'+type(owner).__name__ for owner in checkpoint.owners]
    if payload['owner_types']!=owners:
        raise B.ReplayMismatch('Snapshot owner schema differs')
    handles=[{'owner':i,'key':key,'type':type(value).__name__}
             for i,obj in enumerate(checkpoint.owners)
             for (identity,key),value in checkpoint.immutable.items() if identity==id(obj)]
    if payload['preserved_handles']!=handles:
        raise B.ReplayMismatch('Snapshot preserved handles differ')
    for key in ('model','data','python','sections','shift'):
        setattr(checkpoint,key,payload[key])
    checkpoint.random=payload['python_rng']
    checkpoint.numpy=payload['numpy_rng']
    checkpoint.torch=payload['torch_rng']
    checkpoint.restore(shift)
    return checkpoint


def execute(args):
    import numpy as np
    import torch
    import mujoco
    B.NP,B.TORCH,B.MJ=np,torch,mujoco
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    P.install()
    import navigation.phase22.continuous_corridor_planner as planner
    import envs.phase22.mkmini_phase22_v1_continuous_corridor_env as module
    from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import MkMiniPhase22V1ContinuousCorridorEnv as Env
    from envs.phase21.mkmini_phase21_v11_candidate_recovery_env import MkMiniPhase21V11CandidateRecoveryEnv as Parent
    from training.phase21_risk_switch_fusion_sac.tests import eval_phase21_v3_exact_pair_5ep as E
    from stable_baselines3 import SAC
    if B.sha(B.MODEL)!=B.EXPECTED_MODEL:
        raise RuntimeError('Frozen SAC SHA256 differs')
    source=SOURCE_RUN/f'seed_{args.seed}'/'data'
    manifest=json.loads((source/'decision_manifest.json').read_text())
    source_result=json.loads((source/'result.json').read_text())
    if not source_result['gate']:
        raise RuntimeError('Frozen seed has no gate')
    frozen=W.sources()
    for path in (HERE/'PROTOCOL_2026-10-17.md',Path(__file__).resolve(),
                 ROOT/'experiments/phase_rpccr_p0b57_v1/paired_worker.py',
                 ROOT/'experiments/phase_rpccr_p0b57_v1/admission.py',
                 ROOT/'experiments/phase_rpccr_p0b62_v1/action_pool_worker.py',
                 source/'decision_snapshot.pkl',source/'decision_observation.json',
                 source/'decision_manifest.json'):
        frozen[str(path.resolve())]=B.sha(path)
    A.write(B.OUT/'frozen_sources_before.json',frozen)
    shift=B.load_shift(args.seed)
    E.seed_all(args.seed)
    env=Env()
    env._phase21_v4_known_map_obstacles=MethodType(B.clean_map,env)
    model=SAC.load(str(B.MODEL),device='cpu')
    began=time.monotonic()
    try:
        E.reset_env(env,args.seed)
        if B.sha(B.OUT/'assets/isolated_indoor.xml')!=B.sha(source/'assets/isolated_indoor.xml'):
            raise B.ReplayMismatch('Reset XML differs from B57')
        checkpoint=restore_checkpoint(env,shift,source/'decision_snapshot.pkl')
        state=A.state_digest(env,shift)
        if state!=manifest['decision_state_hash']:
            raise B.ReplayMismatch('Decision snapshot state differs from B57')
        obs=np.asarray(json.loads((source/'decision_observation.json').read_text()),dtype=np.float32)
        audit=B.audit_known_map(env)
        if not audit['known_map_source_gate_pass']:
            raise RuntimeError('Hidden geometry in known-map input')
        pool=C.collect(env,shift,planner,module,Parent)
        again=C.collect(env,shift,planner,module,Parent)
        if pool['pool_hash']!=again['pool_hash'] or pool['request_hash']!=again['request_hash']:
            raise B.ReplayMismatch('Same-state candidate pool is nondeterministic')
        if pool['pool_hash']!=manifest['pool_hash'] or pool['request_hash']!=manifest['request_hash']:
            raise B.ReplayMismatch('Candidate pool/request differs from B57')
        rows=[]
        for index,candidate in enumerate(pool['candidates']):
            if candidate is None or not bool(candidate.feasible) or not math.isfinite(float(candidate.score)):
                continue
            checkpoint.restore(shift)
            if A.state_digest(env,shift)!=state:
                raise B.ReplayMismatch('Per-candidate state drift')
            C.apply_candidate(env,module,Parent,candidate,pool['count'],pool['request_hash'])
            candidate_obs,sync=refresh(env,obs.copy(),shift,B)
            if not (sync['complete_other_state_equal'] and sync['all_non_path_observation_equal']
                    and sync['no_sensor_queries']):
                raise B.ReplayMismatch('Path observation sync changed unrelated state')
            sac_action,_=model.predict(candidate_obs,deterministic=True)
            nominal=env.inner._base_pursuit_action()
            rows.append({'index':index,'path_hash':B.fingerprint(candidate.active_path),
                'score':float(candidate.score),'offset_m':float(candidate.offset),
                'length_ratio':float(candidate.length_ratio),
                'known_margin_m':float(candidate.known_margin),
                'sensor_margin_m':float(candidate.sensor_margin),
                'guarded_admission':bool(decide(candidate)['accept']),
                'nominal_steer_norm':float(nominal[0]),
                'nominal_wheel_norm':float(nominal[1]),
                'nominal_steer_radians':float(nominal[2]),
                'lookahead_target':np.asarray(nominal[3]).tolist(),
                'heading_error_rad':float(nominal[4]),
                'sac_action':np.asarray(sac_action).tolist(),
                'changed_observation_components':sync['changed_observation_components']})
        checkpoint.restore(shift)
        if A.state_digest(env,shift)!=state:
            raise B.ReplayMismatch('Final candidate scan state not restored')
        best_hash=B.fingerprint(pool['selected'].active_path)
        best=next((row for row in rows if row['path_hash']==best_hash),None)
        if best is None:
            raise B.ReplayMismatch('B57 best candidate absent in feasible scan')
        result={'seed':args.seed,'decision_state_hash':state,
            'gate_public_step':manifest['public_step'],'pool_hash':pool['pool_hash'],
            'request_hash':pool['request_hash'],'candidate_count':pool['count'],
            'feasible_count':len(rows),'guarded_count':sum(row['guarded_admission'] for row in rows),
            'best':best,'known_map_audit':audit,'rows':rows,
            'training':False,'calibration_only':True,'wall_seconds':time.monotonic()-began}
        A.write(B.OUT/'result.json',result)
        print(json.dumps({'event':'DONE','seed':args.seed,'feasible':len(rows),
                          'guarded':result['guarded_count']}),flush=True)
    finally:
        env.close()
        changes=[path for path,old in frozen.items() if B.sha(Path(path))!=old]
        A.write(B.OUT/'integrity.json',{'frozen_source_changes':changes,
                'frozen_model_sha256':B.sha(B.MODEL)})
        if changes:
            raise RuntimeError('Frozen input changed')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,choices=SEEDS,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--budget-seconds',type=int,default=900)
    args=parser.parse_args()
    B.OUT=args.out.resolve()
    B.OUT.mkdir(parents=True,exist_ok=False)
    os.chdir(B.OUT)
    (B.OUT/'assets').mkdir()
    (B.OUT/'assets/meshes_fixed').symlink_to(ROOT/'training/assets/mkmini_real/meshes_fixed',target_is_directory=True)
    for name in ('XDG_CACHE_HOME','MESA_SHADER_CACHE_DIR','__GL_SHADER_DISK_CACHE_PATH'):
        os.environ[name]=str(B.OUT/'cache')
    os.environ['MPLCONFIGDIR']=str(B.OUT/'cache/matplotlib')
    sys.addaudithook(B.write_guard)
    A.write(B.OUT/'preregistration.json',{'experiment':'B64','seed':args.seed,
        'calibration_only':True,'training':False,'physical_rollout_steps':0,
        'max_wall_seconds':args.budget_seconds,'frozen_sac_sha256':B.EXPECTED_MODEL})
    def alarm(*_):
        raise P.HardBudgetExceeded('B64 per-seed wall budget')
    signal.signal(signal.SIGALRM,alarm)
    signal.setitimer(signal.ITIMER_REAL,args.budget_seconds)
    code=0
    try:
        execute(args)
        A.write(B.OUT/'completion.json',{'status':'FINISHED'})
    except P.HardBudgetExceeded as exc:
        code=124
        A.write(B.OUT/'failure.json',{'status':'COMPUTE_CENSORED','reason':str(exc)})
    except Exception as exc:
        code=1
        A.write(B.OUT/'failure.json',{'status':'IMPLEMENTATION_ERROR',
                'reason':repr(exc),'traceback':traceback.format_exc()})
        traceback.print_exc()
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
    return code


if __name__=='__main__':
    sys.exit(main())
