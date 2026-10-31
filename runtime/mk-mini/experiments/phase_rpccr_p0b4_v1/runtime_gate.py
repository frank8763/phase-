#!/usr/bin/env python3
"""RP-P0B4-A: natural runtime SCCR coverage, replay gate and contact attribution."""
from __future__ import annotations
import argparse
import copy
import dataclasses
import fcntl
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
import traceback

PROJECT=Path('/home/linghu/catkin_ws/src/mk-mini')
BASE_PATH=PROJECT/'experiments/phase_rpccr_p0b3_v1/pilot.py'
spec=importlib.util.spec_from_file_location('p0b3_frozen_support',BASE_PATH)
B=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=B
spec.loader.exec_module(B)
original_json_value=B.json_value
def structured_json(value):
    if dataclasses.is_dataclass(value):
        value={field.name:getattr(value,field.name) for field in dataclasses.fields(value)}
    return original_json_value(value)
B.json_value=structured_json
HOOK=None
MONITOR=None
COUNTS={'reset_sccr_searches':0,'runtime_sccr_searches':0,'runtime_v7_plans':0,
        'observed_api_steps':0,'native_physics_steps':0,'native_obstacle_contact_steps':0,
        'native_obstacle_penetration_steps':0}


def contacts(env):
    hits=[]
    for contact in env.data.contact:
        a=B.MJ.mj_id2name(env.model,B.MJ.mjtObj.mjOBJ_GEOM,int(contact.geom1)) or ''
        b=B.MJ.mj_id2name(env.model,B.MJ.mjtObj.mjOBJ_GEOM,int(contact.geom2)) or ''
        pair=(a+' '+b).lower()
        robot=any(token in pair for token in ('chassis_collision','wheel','lidar_body','fr3','d435i'))
        obstacle='real_rect_obs' in pair or 'real_circle_obs' in pair
        if robot and obstacle:
            hits.append({'geom1':a,'geom2':b,'distance_m':float(contact.dist),
                         'position':contact.pos.copy(),'sim_time':float(env.data.time)})
    return hits


class ContactMonitor:
    def __init__(self):
        self.env=None; self.active=False; self.last={}

    def begin(self,env):
        self.env=env; self.active=True; self.native=[]; self.native_steps=0
        self.sim_start=float(env.data.time)

    def after_native_step(self,model,data):
        if not self.active or model is not self.env.model or data is not self.env.data:
            return
        self.native_steps+=1; COUNTS['native_physics_steps']+=1
        hits=contacts(self.env)
        if hits:
            COUNTS['native_obstacle_contact_steps']+=1
            COUNTS['native_obstacle_penetration_steps']+=int(any(x['distance_m']<=0 for x in hits))
            self.native.append({'native_step':self.native_steps,'contacts':hits})

    def finish(self,env):
        self.active=False
        self.last={'sim_start':self.sim_start,'sim_end':float(env.data.time),
                   'native_steps':self.native_steps,'native_contact_events':self.native,
                   'end_of_api_contacts':contacts(env),
                   'sample_timing':'immediately after every mj_step, before later wrapper pose correction'}


OriginalHook=B.SearchHook


class RuntimeHook(OriginalHook):
    def __init__(self,*args,**kwargs):
        global HOOK
        super().__init__(*args,**kwargs); HOOK=self
        self.first_runtime_request=False

    def search(self,*args,**kwargs):
        api=self.context.get('api')
        if api!='step':
            COUNTS['reset_sccr_searches']+=1
            self.current=[]
            return self.original_search(*args,**kwargs)
        COUNTS['runtime_sccr_searches']+=1
        selected,count=super().search(*args,**kwargs)
        if self.mode=='discover' and self.triggered and selected is None:
            # An empty pool is evidence, not an executable counterfactual state.
            self.triggered=False
            B.event('RUNTIME_SCCR_EMPTY',public_step=self.context.get('public_step'),attempted=count)
        return selected,count


def record_runtime_plan(original,planner,request):
    if HOOK is None or HOOK.context.get('api')!='step':
        return original(planner,request)
    COUNTS['runtime_v7_plans']+=1
    first=not HOOK.first_runtime_request
    if first:
        HOOK.first_runtime_request=True
        B.write('first_runtime_v7_request.json',
                {field.name:getattr(request,field.name) for field in dataclasses.fields(request)})
        B.Snapshot(HOOK.env,HOOK.shift).save('first_runtime_v7_snapshot.pkl')
        B.write('first_runtime_v7_state.json',{'api':HOOK.context,'decision_hash':B.state_hash(HOOK.env,HOOK.shift),
                                             'source_audit':B.audit_known_map(HOOK.env)})
    result=original(planner,request)
    record={'api':copy.deepcopy(HOOK.context),'success':bool(result.success),
            'family':str(result.candidate_family),'attempted':int(result.candidate_count),
            'feasible':int(result.feasible_count),'reason':str(result.failure_reason),
            'known_margin':float(result.known_margin),'sensor_margin':float(result.sensor_margin)}
    with (B.OUT/'runtime_v7_events.jsonl').open('a') as f:
        f.write(json.dumps(B.json_value(record),ensure_ascii=False)+'\n')
    B.event('NATURAL_RUNTIME_V7_PLAN',**record)
    return result


original_isolate=B.isolate_assets


def install_instrumentation():
    global MONITOR
    original_isolate()
    from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import MkMiniPhase22V1ContinuousCorridorEnv as Env
    from navigation.phase21.local_planners.phase21_v7_adaptive_planner import Phase21V7AdaptivePlanner
    MONITOR=ContactMonitor()
    native_step=B.MJ.mj_step
    def observed_native_step(model,data,*args,**kwargs):
        value=native_step(model,data,*args,**kwargs)
        MONITOR.after_native_step(model,data)
        return value
    B.MJ.mj_step=observed_native_step
    env_step=Env.step
    def observed_api_step(env,action):
        MONITOR.begin(env)
        try:
            value=env_step(env,action)
            MONITOR.finish(env)
        finally:
            MONITOR.active=False
        COUNTS['observed_api_steps']+=1
        obs,reward,terminated,truncated,info=B.finish_api(value)
        if terminated or truncated:
            B.write('acquisition_or_branch_terminal.json',
                    {'api':copy.deepcopy(HOOK.context) if HOOK else {},
                     'mode':HOOK.mode if HOOK else 'initialization',
                     'terminated':terminated,'truncated':truncated,'reward':reward,
                     'info':info,'collision_attribution':label_step(env,info)})
        if HOOK is not None and HOOK.mode=='discover' and COUNTS['observed_api_steps']%25==0:
            B.event('ACQUISITION_PROGRESS',public_step=HOOK.context.get('public_step'),
                    runtime_sccr=COUNTS['runtime_sccr_searches'],runtime_v7=COUNTS['runtime_v7_plans'],
                    sim_time=float(env.data.time))
        return value
    Env.step=observed_api_step
    original_plan=Phase21V7AdaptivePlanner.plan
    def observed_plan(planner,request):
        return record_runtime_plan(original_plan,planner,request)
    Phase21V7AdaptivePlanner.plan=observed_plan


def label_step(env,info):
    from training.phase18_ablation.scripts.eval_phase18_A_full_fixed_seed import check_map_penetration
    audit=copy.deepcopy(MONITOR.last)
    native_contact=bool(audit['native_contact_events'])
    native_penetration=any(c['distance_m']<=0 for event in audit['native_contact_events'] for c in event['contacts'])
    end_contact=bool(audit['end_of_api_contacts'])
    map_proxy=check_map_penetration(env,margin=0.02)
    flags={key:bool(info.get(key,False)) for key in
           ('collision','phase20_unknown_penetration','phase20_known_penetration')}
    primary=bool(native_penetration or any(flags.values()))
    legacy=bool(primary or end_contact or map_proxy)
    return {'primary_collision':primary,'legacy_strict_collision_proxy':legacy,
            'native_obstacle_contact':native_contact,'native_obstacle_penetration':native_penetration,
            'end_of_api_obstacle_contact':end_contact,'map_penetration_margin_0p02':map_proxy,
            'environment_flags':flags,'physics_audit':audit}


def trajectory(env,model,shift,obs,initial=None,horizon=150):
    np=B.NP
    samples=[]; distance0=float(np.linalg.norm(env.goal_xy-env.robot_xy)); minimum=float('inf')
    start_time=float(env.data.time); total=0.; collided=False; success=False; recovery_steps=0
    for step in range(horizon):
        if step==0 and initial is not None:
            action,output=initial
            start_time=float(MONITOR.last['sim_start'])
        else:
            action,_=model.predict(obs,deterministic=True); output=env.step(action)
        obs,reward,terminated,truncated,info=B.finish_api(output)
        audit=label_step(env,info)
        collision=audit['primary_collision']
        arrived=bool(info.get('reach_goal',False) or info.get('success',False) or info.get('is_success',False))
        clear=info.get('phase20_unknown_clearance')
        if isinstance(clear,(float,int)) and math.isfinite(clear): minimum=min(minimum,float(clear))
        recovery=vars(env.inner).get('recovery_stage','UNKNOWN')
        recovery_steps+=int(recovery!='NORMAL')
        full_hash,parts=B.state_hash(env,shift,False,components=True)
        samples.append({'step':step+1,'observation':np.asarray(obs).copy(),'policy_action':np.asarray(action).copy(),
                        'qpos':env.data.qpos.copy(),'qvel':env.data.qvel.copy(),'ctrl':env.data.ctrl.copy(),
                        'reward':reward,'terminated':terminated,'truncated':truncated,'collision':collision,
                        'success':arrived,'recovery_stage':recovery,'state_components':parts,'state_hash':full_hash,
                        'collision_attribution':audit,
                        'environment_timeouts':{key:bool(info.get(key,False)) for key in ('timeout','env_timeout')},
                        'sim_time':float(env.data.time)})
        total+=reward; collided|=collision; success|=arrived
        if terminated or truncated or collision: break
    return samples,{'steps':len(samples),'collision':collided,'safe_success':success and not collided,
                    'horizon_censored':not(terminated or truncated or collided),
                    'minimum_unknown_clearance_evaluation':minimum,
                    'goal_progress_m':distance0-float(np.linalg.norm(env.goal_xy-env.robot_xy)),
                    'final_recovery_stage':vars(env.inner).get('recovery_stage'),
                    'recovery_steps':recovery_steps,'total_reward':total,
                    'simulated_seconds':float(env.data.time)-start_time,
                    'legacy_proxy_ever':any(x['collision_attribution']['legacy_strict_collision_proxy'] for x in samples),
                    'primary_label_definition':'environment collision/penetration flags OR native robot-obstacle contact distance <= 0'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',required=True); p.add_argument('--seed',type=int,required=True)
    p.add_argument('--horizon',type=int,default=150); p.add_argument('--budget-seconds',type=int,default=600)
    args=p.parse_args(); args.variant='clean'; args.probe=False
    B.OUT=Path(args.out).resolve(); B.OUT.mkdir(parents=True,exist_ok=False)
    lock=(B.OUT.parent/'runtime_gate.lock').open('a'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    os.chdir(B.OUT); (B.OUT/'assets').mkdir()
    (B.OUT/'assets/meshes_fixed').symlink_to(PROJECT/'training/assets/mkmini_real/meshes_fixed',target_is_directory=True)
    for key in ('XDG_CACHE_HOME','MESA_SHADER_CACHE_DIR','__GL_SHADER_DISK_CACHE_PATH'):
        os.environ[key]=str(B.OUT/'cache')
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',MUJOCO_GL='egl',CUDA_VISIBLE_DEVICES='',
                      OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MPLCONFIGDIR=str(B.OUT/'cache/matplotlib'))
    sys.addaudithook(B.write_guard)
    B.write('preregistration.json',{'experiment':'RP-P0B4-A','created_at':time.strftime('%F %T'),**vars(args),
                                  'frozen_sac':True,'training':False,'required_target_api':'step',
                                  'native_contact_timing':'after each mj_step before later wrapper corrections',
                                  'primary_collision':'environment collision/penetration OR native contact distance <= 0',
                                  'legacy_map_proxy_kept_separately':True,'reset_event_never_counted_as_runtime':True,
                                  'v7_observer_changes_result':False,'max_acquisition_steps':600,
                                  'same_candidate_repetitions':3,'alternative_candidates':2,'alternative_repetitions':2,
                                  'failure_policy':'stop counterfactual sampling on state/pool/trajectory mismatch'})
    B.SearchHook=RuntimeHook; B.isolate_assets=install_instrumentation; B.trajectory=trajectory
    original_manifest=B.source_manifest
    def manifest():
        result=original_manifest(); result[str(Path(__file__).resolve())]=B.sha(__file__); return result
    B.source_manifest=manifest
    def alarm(*_): raise B.BudgetExceeded('Foreground wall-clock budget exceeded; not a navigation outcome')
    signal.signal(signal.SIGALRM,alarm); signal.setitimer(signal.ITIMER_REAL,args.budget_seconds)
    started=time.monotonic(); status='STARTED'; exit_code=0
    try:
        result=B.execute(args)
        if result['gate']=='NO_EXECUTABLE_CONTINUOUS_EVENT':
            result.update(gate='NO_EXECUTABLE_RUNTIME_SCCR_EVENT',runtime_v7_plans=COUNTS['runtime_v7_plans'])
        result.update(experiment='RP-P0B4-A',runtime_coverage=COUNTS.copy(),
                      native_collision_attribution_enabled=True,independent_test=False)
        B.write('result.json',result)
        status='FINISHED'; B.write('completion.json',{'status':status,'elapsed_seconds':time.monotonic()-started,'gate':result['gate']})
        B.event('RUNTIME_GATE_FINISHED',gate=result['gate'],counts=COUNTS)
    except B.ReplayMismatch as exc:
        status='REPLAY_GATE_FAIL'; exit_code=2
        B.write('failure.json',{'status':status,'reason':str(exc),'traceback':traceback.format_exc()})
        B.event(status,reason=str(exc))
    except B.BudgetExceeded as exc:
        status='COMPUTE_CENSORED'; exit_code=124
        B.write('failure.json',{'status':status,'reason':str(exc),'elapsed_seconds':time.monotonic()-started})
        B.event(status,reason=str(exc))
    except Exception as exc:
        status='IMPLEMENTATION_ERROR'; exit_code=1
        B.write('failure.json',{'status':status,'reason':repr(exc),'traceback':traceback.format_exc()})
        B.event(status,reason=repr(exc)); traceback.print_exc()
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        B.write('runtime_coverage.json',{'status':status,'counts':COUNTS,'elapsed_seconds':time.monotonic()-started})
    return exit_code


if __name__=='__main__': sys.exit(main())
