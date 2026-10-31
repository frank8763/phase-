#!/usr/bin/env python3
"""Paired long-horizon development test of an isolated runtime-failure bridge."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
import traceback
from types import MethodType

ROOT=Path('/home/linghu/catkin_ws/src/mk-mini')
B5_PATH=ROOT/'experiments/phase_rpccr_p0b5_v1/probe.py'
spec=importlib.util.spec_from_file_location('rpccr_b5_frozen_support',B5_PATH)
P=importlib.util.module_from_spec(spec); sys.modules[spec.name]=P; spec.loader.exec_module(P)
B=P.B
G=P.G
ALLOWED_FAILURES=('cluster_bspline_no_feasible_candidate','no_corridor_sensor_cluster')
MAX_STEPS=600


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(B.json_value(value),ensure_ascii=False,indent=2)+'\n')
    os.replace(temporary,path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    manifest=P.sources()
    manifest[str(Path(__file__).resolve())]=digest(Path(__file__).resolve())
    return manifest


def path_hash(env):
    value=getattr(env,'phase21_v3_active_path',None)
    return None if value is None else B.fingerprint(value)


def execute(args,events):
    import numpy as np
    import torch
    import mujoco
    B.NP,B.TORCH,B.MJ=np,torch,mujoco
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    sys.path.insert(0,str(ROOT))
    P.install()
    import envs.phase22.mkmini_phase22_v1_continuous_corridor_env as env_module
    from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import MkMiniPhase22V1ContinuousCorridorEnv as Env
    from envs.phase21.mkmini_phase21_v8_1_runtime_safe_revalidate_env import MkMiniPhase21V81RuntimeSafeRevalidateEnv as V81
    from training.phase21_risk_switch_fusion_sac.tests import eval_phase21_v3_exact_pair_5ep as E
    from stable_baselines3 import SAC

    if B.sha(B.MODEL)!=B.EXPECTED_MODEL:
        raise RuntimeError('Frozen SAC model hash mismatch')
    before=sources(); write(B.OUT/'frozen_sources_before.json',before)
    context={'api':'reset','public_step':0}
    original_search=env_module.search_continuous_corridor
    def traced_search(*search_args,**search_kwargs):
        candidate,count=original_search(*search_args,**search_kwargs)
        events.append({'kind':'phase22_search','api':copy.deepcopy(context),
                       'attempted':int(count),'selected':candidate is not None,
                       'selected_path_hash':None if candidate is None else B.fingerprint(candidate.active_path)})
        return candidate,count
    env_module.search_continuous_corridor=traced_search

    original_build=Env._phase21_v3_build_detour
    def traced_build(self):
        before_path=path_hash(self)
        result=bool(original_build(self))
        events.append({'kind':'phase22_build','api':copy.deepcopy(context),'result':result,
                       'phase21_v3_failure_reason':str(getattr(self,'phase21_v3_failure_reason','none')),
                       'phase22_failure_reason':str(getattr(self,'phase22_v1_failure_reason','none')),
                       'path_changed':before_path!=path_hash(self)})
        return result
    Env._phase21_v3_build_detour=traced_build

    original_replan=V81._phase21_v8_replan
    def traced_replan(self,margin_before):
        before_path=path_hash(self)
        original_success=bool(original_replan(self,margin_before))
        reason=str(getattr(self,'phase21_v8_last_replan_reason','none'))
        bridge_attempted=False; bridge_success=False
        if args.method=='bridge' and not original_success and reason in ALLOWED_FAILURES:
            bridge_attempted=True
            bridge_success=bool(self._phase21_v3_build_detour())
        events.append({'kind':'v81_runtime_replan','api':copy.deepcopy(context),
                       'margin_before_m':float(margin_before),
                       'original_success':original_success,'original_failure_reason':reason,
                       'bridge_attempted':bridge_attempted,'bridge_success':bridge_success,
                       'path_changed':before_path!=path_hash(self),
                       'recovery_stage':str(getattr(self.inner,'recovery_stage','unknown'))})
        return original_success or bridge_success
    V81._phase21_v8_replan=traced_replan

    shift=B.load_shift(args.seed); E.seed_all(args.seed)
    env=Env()
    env._phase21_v4_known_map_obstacles=MethodType(B.clean_map,env)
    model=SAC.load(str(B.MODEL),device='cpu')
    write(B.OUT/'runtime_inventory.json',{'environment_class':type(env).__module__+'.'+type(env).__name__,
                                         'runtime_planner_class':type(env._phase21_v7_planner).__module__+'.'+type(env._phase21_v7_planner).__name__,
                                         'mujoco':mujoco.__version__,'model_device':'cpu'})
    try:
        obs,_=E.reset_env(env,args.seed)
        geometry=P.reset_geometry(env)
        write(B.OUT/'reset_geometry.json',geometry)
        if not geometry['long_horizon_eligible']:
            raise RuntimeError('B5-selected long-horizon seed became ineligible')
        reset_state_hash,reset_components=B.state_hash(env,shift,components=True)
        xml_fields=[vars(owner)['real_indoor_xml'] for owner in B.objects(env)
                    if 'real_indoor_xml' in vars(owner)]
        if len(xml_fields)!=1:
            raise RuntimeError('Expected exactly one isolated XML path in environment owners')
        xml_path=Path(xml_fields[0]).resolve()
        if not xml_path.is_relative_to(B.OUT) or not xml_path.is_file():
            raise RuntimeError('Isolated XML is missing or outside this worker')
        xml_sha256=digest(xml_path)
        normalized_components={key:value for key,value in reset_components.items()
                               if not key.endswith('.real_indoor_xml')}
        if len(normalized_components)!=len(reset_components)-1:
            raise RuntimeError('Exactly one output-directory XML path must be normalized')
        semantic_reset_hash=B.fingerprint(normalized_components)
        write(B.OUT/'reset_state.json',{'state_hash':reset_state_hash,
                                       'semantic_state_hash':semantic_reset_hash,
                                       'components':reset_components,
                                       'isolated_xml_path':str(xml_path),
                                       'isolated_xml_sha256':xml_sha256,
                                       'normalization':'drop only owner.real_indoor_xml absolute output path; compare XML bytes separately',
                                       'robot_xy':np.asarray(env.robot_xy).tolist(),
                                       'goal_xy':np.asarray(env.goal_xy).tolist()})
        rows=[]; collided=False; arrived=False; terminal=False; start=time.monotonic()
        for step in range(1,MAX_STEPS+1):
            action,_=model.predict(obs,deterministic=True)
            context.update(api='step',public_step=step)
            output=env.step(action)
            obs,reward,terminated,truncated,info=B.finish_api(output)
            audit=G.label_step(env,info)
            collision=bool(audit['primary_collision'])
            success=bool(info.get('reach_goal',False) or info.get('success',False) or info.get('is_success',False))
            collided|=collision; arrived|=success
            row={'step':step,'sim_time':float(env.data.time),'robot_xy':np.asarray(env.robot_xy).tolist(),
                 'goal_distance_m':float(np.linalg.norm(env.goal_xy-env.robot_xy)),
                 'reward':float(reward),'terminated':bool(terminated),'truncated':bool(truncated),
                 'collision':collision,'safe_success':success and not collided,
                 'collision_attribution':audit,
                 'recovery_stage':str(getattr(env.inner,'recovery_stage','unknown')),
                 'v81_replan_count':int(getattr(env,'phase21_v8_replan_count',0)),
                 'v81_replan_failures':int(getattr(env,'phase21_v8_replan_failure_count',0)),
                 'phase22_attempted':bool(getattr(env,'phase22_v1_attempted',False)),
                 'phase22_success':bool(getattr(env,'phase22_v1_success',False)),
                 'active_path_hash':path_hash(env)}
            rows.append(row)
            if terminated or truncated or collision:
                terminal=True
                break
        write(B.OUT/'trajectory.json',rows)
        write(B.OUT/'events.json',events)
        result={'experiment':'RP-P0B6-RUNTIME-BRIDGE-DEVELOPMENT','seed':args.seed,'method':args.method,
                'reset_state_hash':reset_state_hash,
                'semantic_reset_state_hash':semantic_reset_hash,
                'isolated_xml_sha256':xml_sha256,'reset_geometry':geometry,
                'steps':len(rows),'safe_success':arrived and not collided,
                'collision':collided,'horizon_censored':not terminal,
                'goal_distance_final_m':rows[-1]['goal_distance_m'] if rows else None,
                'native_obstacle_contact_ever':any(r['collision_attribution']['native_obstacle_contact'] for r in rows),
                'unknown_penetration_ever':any(r['collision_attribution']['environment_flags']['phase20_unknown_penetration'] for r in rows),
                'known_penetration_ever':any(r['collision_attribution']['environment_flags']['phase20_known_penetration'] for r in rows),
                'runtime_replan_events':sum(x['kind']=='v81_runtime_replan' and x['api']['api']=='step' for x in events),
                'runtime_replan_failures':sum(x['kind']=='v81_runtime_replan' and not x['original_success'] and x['api']['api']=='step' for x in events),
                'bridge_attempts':sum(x['kind']=='v81_runtime_replan' and x['bridge_attempted'] for x in events),
                'bridge_successes':sum(x['kind']=='v81_runtime_replan' and x['bridge_success'] for x in events),
                'phase22_runtime_searches':sum(x['kind']=='phase22_search' and x['api']['api']=='step' for x in events),
                'phase22_runtime_selections':sum(x['kind']=='phase22_search' and x['api']['api']=='step' and x['selected'] for x in events),
                'wall_seconds':time.monotonic()-start,'training':False,
                'causal_scope':'isolated development intervention; not a validated RP-CCR long-horizon gain'}
        write(B.OUT/'result.json',result)
        return result
    finally:
        env.close()
        write(B.OUT/'events.json',events)
        after=sources();write(B.OUT/'frozen_sources_after.json',after)
        changed=[path for path,sha in before.items() if after.get(path)!=sha]
        write(B.OUT/'integrity.json',{'frozen_source_changes':changed,
                                       'frozen_model_sha256':B.sha(B.MODEL),
                                       'unchanged':not changed})
        if changed: raise RuntimeError('Frozen input changed during worker')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--method',choices=('baseline','bridge'),required=True)
    parser.add_argument('--budget-seconds',type=int,default=180)
    args=parser.parse_args()
    B.OUT=Path(args.out).resolve();B.OUT.mkdir(parents=True,exist_ok=False)
    os.chdir(B.OUT)
    (B.OUT/'assets').mkdir()
    (B.OUT/'assets/meshes_fixed').symlink_to(ROOT/'training/assets/mkmini_real/meshes_fixed',target_is_directory=True)
    for key in ('XDG_CACHE_HOME','MESA_SHADER_CACHE_DIR','__GL_SHADER_DISK_CACHE_PATH'):
        os.environ[key]=str(B.OUT/'cache')
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',MUJOCO_GL='egl',CUDA_VISIBLE_DEVICES='',
                      OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MPLCONFIGDIR=str(B.OUT/'cache/matplotlib'))
    sys.addaudithook(B.write_guard)
    write(B.OUT/'preregistration.json',{'experiment':'RP-P0B6-RUNTIME-BRIDGE-DEVELOPMENT',
                                      'created_at':time.strftime('%F %T'),**vars(args),
                                      'allowed_failure_reasons':ALLOWED_FAILURES,
                                      'bridge_action':'on V8.1 runtime planner failure, call the existing Phase22 detour chain once',
                                      'frozen_sac':True,'training':False,'max_public_steps':MAX_STEPS,
                                      'primary_endpoint':'collision-free goal arrival within 600 public steps',
                                      'collision_label':'environment collision/penetration OR native contact penetration'})
    def alarm(*_): raise P.HardBudgetExceeded('Worker wall-clock budget exceeded')
    signal.signal(signal.SIGALRM,alarm)
    signal.setitimer(signal.ITIMER_REAL,args.budget_seconds)
    events=[]; code=0
    try:
        execute(args,events)
        write(B.OUT/'completion.json',{'status':'FINISHED'})
    except P.HardBudgetExceeded as exc:
        code=124
        write(B.OUT/'failure.json',{'status':'COMPUTE_CENSORED','reason':str(exc)})
    except Exception as exc:
        code=1
        write(B.OUT/'failure.json',{'status':'IMPLEMENTATION_ERROR','reason':repr(exc),'traceback':traceback.format_exc()})
        traceback.print_exc()
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        write(B.OUT/'events.json',events)
    return code


if __name__=='__main__':
    sys.exit(main())
