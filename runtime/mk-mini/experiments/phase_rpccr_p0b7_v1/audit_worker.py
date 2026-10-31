#!/usr/bin/env python3
"""B7 decision-time opportunity audit on frozen long-horizon Phase22 rollouts."""
from __future__ import annotations
import argparse
import copy
import hashlib
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

ROOT=Path('/home/linghu/catkin_ws/src/mk-mini')
SUPPORT=ROOT/'experiments/phase_rpccr_p0b6_v1/worker.py'
spec=importlib.util.spec_from_file_location('rpccr_b6_support',SUPPORT)
W=importlib.util.module_from_spec(spec);sys.modules[spec.name]=W;spec.loader.exec_module(W)
B=W.B;P=W.P;G=W.G
THRESHOLDS=(0.05,0.025)
MAX_STEPS=600


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(B.json_value(value),ensure_ascii=False,indent=2)+'\n')
    os.replace(temporary,path)


def state_digest(env,shift):
    _,parts=B.state_hash(env,shift,components=True)
    fields={k:v for k,v in parts.items() if not k.endswith('.real_indoor_xml')}
    if len(fields)!=len(parts)-1:
        raise B.ReplayMismatch('Expected exactly one output-specific XML path field')
    return B.fingerprint(fields)


def query(env,shift,step,thresholds,planner_module,env_module,parent_class):
    """Force only the Phase22 search entry on a restorable decision-state clone."""
    snapshot=B.Snapshot(env,shift)
    before=state_digest(env,shift)
    original_parent=parent_class._phase21_v3_build_detour
    original_evaluate=planner_module._evaluate_candidate
    original_search=env_module.search_continuous_corridor
    evaluated=[];searches=[];selected=[]
    def ancestor_gate(self):
        self.phase21_v3_failure_reason='no_feasible_candidate'
        return False
    def observe_candidate(*args,**kwargs):
        value=original_evaluate(*args,**kwargs)
        if value is not None:
            evaluated.append({'feasible':bool(value.feasible),
                              'path_hash':B.fingerprint(value.active_path) if value.feasible else None})
        return value
    def observe_search(*args,**kwargs):
        candidate,count=original_search(*args,**kwargs)
        searches.append({'attempted':int(count),'selected':candidate is not None})
        if candidate is not None:selected.append(copy.deepcopy(candidate))
        return candidate,count
    parent_class._phase21_v3_build_detour=ancestor_gate
    planner_module._evaluate_candidate=observe_candidate
    env_module.search_continuous_corridor=observe_search
    began=time.monotonic()
    error=None;applied=False;failure_reason=None
    try:
        applied=bool(env._phase21_v3_build_detour())
        failure_reason=str(getattr(env,'phase22_v1_failure_reason','none'))
    except Exception as exc:
        error=repr(exc)
    finally:
        parent_class._phase21_v3_build_detour=original_parent
        planner_module._evaluate_candidate=original_evaluate
        env_module.search_continuous_corridor=original_search
        snapshot.restore(shift)
    after=state_digest(env,shift)
    if before!=after:raise B.ReplayMismatch(f'Query changed decision state at public step {step}')
    if error is not None:raise RuntimeError('Phase22 query error: '+error)
    feasible=[x['path_hash'] for x in evaluated if x['feasible']]
    selected_hash=B.fingerprint(selected[0].active_path) if selected else None
    checkpoint=None;candidate_file=None
    if selected:
        checkpoint=f'checkpoints/step_{step:03d}.pkl'
        candidate_file=f'checkpoints/step_{step:03d}_selected.pkl'
        (B.OUT/'checkpoints').mkdir(exist_ok=True)
        snapshot.save(checkpoint)
        with (B.OUT/candidate_file).open('wb') as f:pickle.dump(selected[0],f,protocol=5)
    return {'public_step':step,'trigger_thresholds_m':list(thresholds),
            'decision_state_hash':before,'state_restored_equal':True,
            'ancestor_reason_gate_bypassed_for_query':True,
            'phase22_applied_in_discarded_clone':applied,'phase22_failure_reason':failure_reason,
            'searches':searches,'evaluated_non_null_count':len(evaluated),
            'feasible_attempts':len(feasible),'distinct_feasible_path_hashes':len(set(feasible)),
            'selected_path_hash':selected_hash,'checkpoint':checkpoint,'selected_candidate_file':candidate_file,
            'query_wall_seconds':time.monotonic()-began}


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
    if B.sha(B.MODEL)!=B.EXPECTED_MODEL:raise RuntimeError('Frozen SAC model SHA256 mismatch')
    frozen=W.sources();frozen[str(Path(__file__).resolve())]=W.digest(Path(__file__).resolve())
    write(B.OUT/'frozen_sources_before.json',frozen)
    shift=B.load_shift(args.seed);E.seed_all(args.seed)
    env=Env();env._phase21_v4_known_map_obstacles=MethodType(B.clean_map,env)
    model=SAC.load(str(B.MODEL),device='cpu')
    try:
        obs,_=E.reset_env(env,args.seed)
        geometry=P.reset_geometry(env)
        if not geometry['long_horizon_eligible']:raise RuntimeError('B5 long-horizon eligibility changed')
        write(B.OUT/'reset_geometry.json',geometry)
        reset_hash=state_digest(env,shift)
        xml_paths=[Path(vars(x)['real_indoor_xml']).resolve() for x in B.objects(env) if 'real_indoor_xml' in vars(x)]
        if len(xml_paths)!=1 or not xml_paths[0].is_relative_to(B.OUT):raise RuntimeError('Isolated XML source mismatch')
        xml_sha=W.digest(xml_paths[0])
        write(B.OUT/'reset_state.json',{'semantic_state_hash':reset_hash,'isolated_xml_sha256':xml_sha})
        samples=[];queries=[];triggered=set();collided=False;arrived=False;terminal=False
        began=time.monotonic()
        for step in range(1,MAX_STEPS+1):
            stage=str(getattr(env.inner,'recovery_stage','unknown'))
            margin=env._phase21_v8_future_sensor_margin()
            margin_value=None if margin is None or not math.isfinite(float(margin)) else float(margin)
            sensor_world,sensor_local=env._phase21_sensor_points()
            pre_path_hash=W.path_hash(env)
            pre_streak=int(getattr(env,'phase21_v8_unsafe_streak',0))
            pre_last_replan=int(getattr(env,'phase21_v8_last_replan_step',0))
            to_query=[x for x in THRESHOLDS if x not in triggered and margin_value is not None
                      and margin_value<=x and stage=='NORMAL']
            if to_query:
                triggered.update(to_query)
                q=query(env,shift,step,to_query,planner,env_module,Parent)
                queries.append(q)
                write(B.OUT/'queries.json',queries)
                print(json.dumps({'event':'QUERY','seed':args.seed,'step':step,
                                  'thresholds':to_query,'selected':q['selected_path_hash'] is not None,
                                  'feasible':q['feasible_attempts']}),flush=True)
            action,_=model.predict(obs,deterministic=True)
            output=env.step(action)
            obs,reward,terminated,truncated,info=B.finish_api(output)
            audit=G.label_step(env,info)
            collision=bool(audit['primary_collision'])
            success=bool(info.get('reach_goal',False) or info.get('success',False) or info.get('is_success',False))
            collided|=collision;arrived|=success
            samples.append({'public_step':step,'pre_action_margin_m':margin_value,'pre_action_stage':stage,
                            'pre_action_path_hash':pre_path_hash,'pre_action_v81_unsafe_streak':pre_streak,
                            'pre_action_v81_last_replan_step':pre_last_replan,
                            'pre_action_sensor_world':np.asarray(sensor_world).tolist(),
                            'pre_action_sensor_local':np.asarray(sensor_local).tolist(),
                            'sim_time_after':float(env.data.time),'robot_xy_after':np.asarray(env.robot_xy).tolist(),
                            'collision':collision,'safe_success':success and not collided,
                            'native_obstacle_contact':bool(audit['native_obstacle_contact']),
                            'unknown_penetration':bool(audit['environment_flags']['phase20_unknown_penetration']),
                            'known_penetration':bool(audit['environment_flags']['phase20_known_penetration']),
                            'terminated':bool(terminated),'truncated':bool(truncated)})
            if terminated or truncated or collision:
                terminal=True;break
        write(B.OUT/'trajectory.json',samples);write(B.OUT/'queries.json',queries)
        result={'experiment':'RP-P0B7-DECISION-TIME-OPPORTUNITY-AUDIT-DEVELOPMENT',
                'seed':args.seed,'reset_geometry':geometry,'semantic_reset_state_hash':reset_hash,
                'isolated_xml_sha256':xml_sha,'steps':len(samples),'safe_success':arrived and not collided,
                'collision':collided,'horizon_censored':not terminal,
                'unknown_penetration_ever':any(x['unknown_penetration'] for x in samples),
                'known_penetration_ever':any(x['known_penetration'] for x in samples),
                'native_obstacle_contact_ever':any(x['native_obstacle_contact'] for x in samples),
                'query_count':len(queries),'thresholds_triggered_m':sorted(triggered),
                'selected_query_count':sum(x['selected_path_hash'] is not None for x in queries),
                'wall_seconds':time.monotonic()-began,'training':False,'development_only':True}
        write(B.OUT/'result.json',result)
        return result
    finally:
        env.close()
        after=W.sources();after[str(Path(__file__).resolve())]=W.digest(Path(__file__).resolve())
        changes=[path for path,digest in frozen.items() if after.get(path)!=digest]
        write(B.OUT/'integrity.json',{'frozen_source_changes':changes,'frozen_model_sha256':B.sha(B.MODEL)})
        if changes:raise RuntimeError('Frozen source changed during B7 audit')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True);parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--budget-seconds',type=int,default=240)
    args=parser.parse_args()
    B.OUT=Path(args.out).resolve();B.OUT.mkdir(parents=True,exist_ok=False)
    os.chdir(B.OUT);(B.OUT/'assets').mkdir()
    (B.OUT/'assets/meshes_fixed').symlink_to(ROOT/'training/assets/mkmini_real/meshes_fixed',target_is_directory=True)
    for key in ('XDG_CACHE_HOME','MESA_SHADER_CACHE_DIR','__GL_SHADER_DISK_CACHE_PATH'):
        os.environ[key]=str(B.OUT/'cache')
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',MUJOCO_GL='egl',CUDA_VISIBLE_DEVICES='',
                      OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MPLCONFIGDIR=str(B.OUT/'cache/matplotlib'))
    sys.addaudithook(B.write_guard)
    write(B.OUT/'preregistration.json',{'experiment':'RP-P0B7-OPPORTUNITY-AUDIT','seed':args.seed,
                                      'thresholds_m':THRESHOLDS,'first_finite_value_at_or_below_threshold_in_NORMAL':True,
                                      'max_public_steps':MAX_STEPS,'budget_seconds':args.budget_seconds,
                                      'query_on_restorable_clone':True,'ancestor_gate_bypassed_for_query_only':True,
                                      'baseline_path_unchanged':True,'frozen_sac':True,'training':False})
    def alarm(*_):raise P.HardBudgetExceeded('B7 worker compute budget exceeded')
    signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,args.budget_seconds)
    code=0
    try:
        execute(args);write(B.OUT/'completion.json',{'status':'FINISHED'})
    except P.HardBudgetExceeded as exc:
        code=124;write(B.OUT/'failure.json',{'status':'COMPUTE_CENSORED','reason':str(exc)})
    except Exception as exc:
        code=1;write(B.OUT/'failure.json',{'status':'IMPLEMENTATION_ERROR','reason':repr(exc),'traceback':traceback.format_exc()})
        traceback.print_exc()
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    return code


if __name__=='__main__':sys.exit(main())
