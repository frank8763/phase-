#!/usr/bin/env python3
"""Repeat same-state baseline and forced-Phase22 candidate branches at audited B7 gate."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback
from types import MethodType

ROOT=Path('/home/linghu/catkin_ws/src/mk-mini')
AUDIT=ROOT/'experiments/phase_rpccr_p0b7_v1/audit_worker.py'
spec=importlib.util.spec_from_file_location('rpccr_b7_audit_support',AUDIT)
A=importlib.util.module_from_spec(spec);sys.modules[spec.name]=A;spec.loader.exec_module(A)
W=A.W;B=A.B;P=A.P;G=A.G
AUDIT_RUN=ROOT/'experiments/phase_rpccr_p0b7_v1/runs/audit_20261014_01'
B6_RUN=ROOT/'experiments/phase_rpccr_p0b6_v1/runs/paired_20261014_02'
GATES={73101502:55,73101509:49,73101512:82,73101515:13,73101522:33}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def force_phase22(env,parent_class,env_module):
    original_parent=parent_class._phase21_v3_build_detour
    original_search=env_module.search_continuous_corridor
    selected=[];counts=[]
    def stub(self):
        self.phase21_v3_failure_reason='no_feasible_candidate'
        return False
    def observe(*args,**kwargs):
        candidate,count=original_search(*args,**kwargs)
        selected.append(None if candidate is None else B.fingerprint(candidate.active_path))
        counts.append(int(count))
        return candidate,count
    parent_class._phase21_v3_build_detour=stub
    env_module.search_continuous_corridor=observe
    try:success=bool(env._phase21_v3_build_detour())
    finally:
        parent_class._phase21_v3_build_detour=original_parent
        env_module.search_continuous_corridor=original_search
    return {'success':success,'selected_path_hash':selected[-1] if selected else None,
            'search_attempts':counts,'failure_reason':str(getattr(env,'phase22_v1_failure_reason','none'))}


def execute(args):
    import numpy as np
    import torch
    import mujoco
    B.NP,B.TORCH,B.MJ=np,torch,mujoco
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    sys.path.insert(0,str(ROOT));P.install()
    import navigation.phase22.continuous_corridor_planner as planner
    import envs.phase22.mkmini_phase22_v1_continuous_corridor_env as env_module
    from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import MkMiniPhase22V1ContinuousCorridorEnv as Env
    from envs.phase21.mkmini_phase21_v11_candidate_recovery_env import MkMiniPhase21V11CandidateRecoveryEnv as Parent
    from training.phase21_risk_switch_fusion_sac.tests import eval_phase21_v3_exact_pair_5ep as E
    from stable_baselines3 import SAC
    if B.sha(B.MODEL)!=B.EXPECTED_MODEL:raise RuntimeError('Frozen SAC model hash mismatch')
    frozen=W.sources();frozen[str(AUDIT)]=sha(AUDIT);frozen[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
    A.write(B.OUT/'frozen_sources_before.json',frozen)
    cell=AUDIT_RUN/f'seed_{args.seed}'
    audited=json.loads((cell/'queries.json').read_text())
    expected=next((x for x in audited if x['public_step']==args.gate_step),None)
    if expected is None or expected['selected_path_hash'] is None:raise RuntimeError('No predeclared selected gate')
    old=json.loads((B6_RUN/f'seed_{args.seed}_baseline'/'result.json').read_text())
    shift=B.load_shift(args.seed);E.seed_all(args.seed)
    env=Env();env._phase21_v4_known_map_obstacles=MethodType(B.clean_map,env)
    model=SAC.load(str(B.MODEL),device='cpu')
    try:
        obs,_=E.reset_env(env,args.seed)
        if A.state_digest(env,shift)!=old['semantic_reset_state_hash']:
            raise B.ReplayMismatch('Reset state differs from B6')
        for step in range(1,args.gate_step):
            # Match the query-only baseline's read sequence before every public action.
            env._phase21_v8_future_sensor_margin();env._phase21_sensor_points()
            action,_=model.predict(obs,deterministic=True)
            obs,reward,terminated,truncated,info=B.finish_api(env.step(action))
            if terminated or truncated or G.label_step(env,info)['primary_collision']:
                raise B.ReplayMismatch('Baseline terminated before audited decision gate')
        margin=env._phase21_v8_future_sensor_margin();env._phase21_sensor_points()
        stage=str(getattr(env.inner,'recovery_stage','unknown'))
        state=A.state_digest(env,shift)
        if state!=expected['decision_state_hash']:
            raise B.ReplayMismatch('Decision state differs from complete B7 audit')
        if stage!='NORMAL' or margin is None or float(margin)>min(expected['trigger_thresholds_m']):
            raise B.ReplayMismatch('Pre-action trigger condition differs')
        snapshot=B.Snapshot(env,shift)
        query=A.query(env,shift,args.gate_step,expected['trigger_thresholds_m'],planner,env_module,Parent)
        if query['selected_path_hash']!=expected['selected_path_hash']:
            raise B.ReplayMismatch('Candidate selected at audited gate differs')
        A.write(B.OUT/'decision_gate.json',{'seed':args.seed,'public_step':args.gate_step,
            'decision_state_hash':state,'audited_selected_path_hash':expected['selected_path_hash'],
            'repeat_query_selected_path_hash':query['selected_path_hash'],
            'query_state_restored_equal':query['state_restored_equal'],
            'pre_action_stage':stage,'pre_action_margin_m':float(margin),
            'audited_query_path':str(cell/'queries.json'),'query':query})
        branches=[];started=time.monotonic()
        for method in ('original','early_phase22'):
            for repetition in (1,2):
                snapshot.restore(shift)
                if A.state_digest(env,shift)!=state:raise B.ReplayMismatch('Branch reset state differs')
                applied=None
                if method=='early_phase22':
                    applied=force_phase22(env,Parent,env_module)
                    if not applied['success'] or applied['selected_path_hash']!=expected['selected_path_hash']:
                        raise B.ReplayMismatch('Early Phase22 failed to apply audited selected candidate')
                branch_obs=np.asarray(obs).copy();rows=[];collided=False;arrived=False;terminal=False
                for public_step in range(args.gate_step,601):
                    action,_=model.predict(branch_obs,deterministic=True)
                    branch_obs,reward,terminated,truncated,info=B.finish_api(env.step(action))
                    audit=G.label_step(env,info)
                    collision=bool(audit['primary_collision'])
                    success=bool(info.get('reach_goal',False) or info.get('success',False) or info.get('is_success',False))
                    collided|=collision;arrived|=success
                    rows.append({'public_step':public_step,'action':np.asarray(action).tolist(),
                                 'observation':np.asarray(branch_obs).tolist(),
                                 'qpos':env.data.qpos.copy().tolist(),'qvel':env.data.qvel.copy().tolist(),
                                 'robot_xy':np.asarray(env.robot_xy).tolist(),'reward':float(reward),
                                 'collision':collision,'success':success,'terminated':bool(terminated),
                                 'truncated':bool(truncated),
                                 'unknown_penetration':bool(audit['environment_flags']['phase20_unknown_penetration']),
                                 'known_penetration':bool(audit['environment_flags']['phase20_known_penetration']),
                                 'native_contact':bool(audit['native_obstacle_contact'])})
                    if terminated or truncated or collision:terminal=True;break
                A.write(B.OUT/f'branches/{method}_repeat_{repetition}_trace.json',rows)
                row={'method':method,'repetition':repetition,'intervention':applied,
                     'decision_state_hash':state,'trace_hash':B.fingerprint(rows),
                     'steps_from_gate':len(rows),'terminal_public_step':args.gate_step-1+len(rows),
                     'safe_success':arrived and not collided,'collision':collided,
                     'unknown_penetration_ever':any(x['unknown_penetration'] for x in rows),
                     'known_penetration_ever':any(x['known_penetration'] for x in rows),
                     'native_contact_ever':any(x['native_contact'] for x in rows),
                     'horizon_censored':not terminal,
                     'final_robot_xy':rows[-1]['robot_xy'] if rows else None}
                branches.append(row)
                A.write(B.OUT/'branch_progress.json',branches)
                print(json.dumps({'event':'BRANCH_DONE','seed':args.seed,'method':method,
                                  'repeat':repetition,'step':row['terminal_public_step'],
                                  'success':row['safe_success'],'collision':row['collision']}),flush=True)
        for method in ('original','early_phase22'):
            first,second=[r for r in branches if r['method']==method]
            if first['trace_hash']!=second['trace_hash']:
                raise B.ReplayMismatch(f'{method} same-candidate repetitions differ')
        original=branches[0];intervention=branches[2]
        if not all(original[k]==old[k] for k in ('safe_success','collision',
                  'unknown_penetration_ever','known_penetration_ever')) or (
                  original['native_contact_ever']!=old['native_obstacle_contact_ever']):
            raise B.ReplayMismatch('Original branch differs from B6 terminal outcome')
        if original['terminal_public_step']!=old['steps']:
            raise B.ReplayMismatch('Original branch terminal step differs from B6')
        result={'experiment':'RP-P0B7-SAME-STATE-EARLY-PHASE22-BRANCH-DEVELOPMENT',
                'seed':args.seed,'decision_public_step':args.gate_step,'decision_state_hash':state,
                'selected_path_hash':expected['selected_path_hash'],
                'original_repeat_equal':True,'candidate_repeat_equal':True,
                'original_B6_reproduced':True,'branches':branches,
                'rescued':not original['safe_success'] and intervention['safe_success'],
                'method_wall_seconds':time.monotonic()-started,
                'training':False,'development_only':True}
        A.write(B.OUT/'result.json',result)
        return result
    finally:
        env.close()
        after=W.sources();after[str(AUDIT)]=sha(AUDIT);after[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
        changes=[path for path,h in frozen.items() if after.get(path)!=h]
        A.write(B.OUT/'integrity.json',{'frozen_source_changes':changes,'frozen_model_sha256':B.sha(B.MODEL)})
        if changes:raise RuntimeError('Frozen source changed during branch')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True);parser.add_argument('--seed',type=int,choices=sorted(GATES),required=True)
    parser.add_argument('--budget-seconds',type=int,default=360)
    args=parser.parse_args();args.gate_step=GATES[args.seed]
    B.OUT=Path(args.out).resolve();B.OUT.mkdir(parents=True,exist_ok=False)
    os.chdir(B.OUT);(B.OUT/'assets').mkdir();(B.OUT/'branches').mkdir()
    (B.OUT/'assets/meshes_fixed').symlink_to(ROOT/'training/assets/mkmini_real/meshes_fixed',target_is_directory=True)
    for key in ('XDG_CACHE_HOME','MESA_SHADER_CACHE_DIR','__GL_SHADER_DISK_CACHE_PATH'):
        os.environ[key]=str(B.OUT/'cache')
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',MUJOCO_GL='egl',CUDA_VISIBLE_DEVICES='',
                      OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MPLCONFIGDIR=str(B.OUT/'cache/matplotlib'))
    sys.addaudithook(B.write_guard)
    A.write(B.OUT/'preregistration.json',{'experiment':'RP-P0B7-SAME-STATE-EARLY-PHASE22-BRANCH',
         'seed':args.seed,'public_step':args.gate_step,'methods':['original','early_phase22'],
         'repetitions_per_method':2,'gate_source':'complete B7 query-only audit',
         'candidate_rule':'existing Phase22 highest-score feasible candidate, frozen before branch outcomes',
         'max_public_step':600,'budget_seconds':args.budget_seconds,
         'frozen_sac':True,'training':False,'development_only':True})
    def alarm(*_):raise P.HardBudgetExceeded('B7 branch worker wall budget exceeded')
    signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,args.budget_seconds)
    code=0
    try:execute(args);A.write(B.OUT/'completion.json',{'status':'FINISHED'})
    except P.HardBudgetExceeded as exc:
        code=124;A.write(B.OUT/'failure.json',{'status':'COMPUTE_CENSORED','reason':str(exc)})
    except Exception as exc:
        code=1;A.write(B.OUT/'failure.json',{'status':'IMPLEMENTATION_ERROR','reason':repr(exc),'traceback':traceback.format_exc()})
        traceback.print_exc()
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    return code


if __name__=='__main__':sys.exit(main())
