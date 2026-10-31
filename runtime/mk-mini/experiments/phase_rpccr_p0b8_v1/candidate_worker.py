#!/usr/bin/env python3
"""Fixed decision-time diverse candidates, full closed-loop frozen-SAC executions."""
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import pickle
import signal
import sys
import time
import traceback
from types import MethodType

ROOT=Path('/home/linghu/catkin_ws/src/mk-mini')
SUPPORT=ROOT/'experiments/phase_rpccr_p0b7_v1/branch_worker.py'
spec=importlib.util.spec_from_file_location('b7_branch_support',SUPPORT)
Q=importlib.util.module_from_spec(spec);sys.modules[spec.name]=Q;spec.loader.exec_module(Q)
A=Q.A;W=Q.W;B=Q.B;P=Q.P;G=Q.G
GATES=Q.GATES.copy()


def forced_call(env,parent,module,search):
    old_parent=parent._phase21_v3_build_detour
    old_search=module.search_continuous_corridor
    def stub(self):
        self.phase21_v3_failure_reason='no_feasible_candidate'
        return False
    parent._phase21_v3_build_detour=stub;module.search_continuous_corridor=search
    try:return bool(env._phase21_v3_build_detour())
    finally:
        parent._phase21_v3_build_detour=old_parent;module.search_continuous_corridor=old_search


def collect(env,shift,planner,module,parent):
    snapshot=B.Snapshot(env,shift);before=A.state_digest(env,shift)
    old_evaluate=planner._evaluate_candidate;old_search=module.search_continuous_corridor
    candidates=[];selected=[];requests=[];counts=[]
    def evaluate(*args,**kwargs):
        value=old_evaluate(*args,**kwargs);candidates.append(copy.deepcopy(value));return value
    def search(*args,**kwargs):
        if args:raise RuntimeError('Unexpected positional Phase22 search request')
        requests.append(copy.deepcopy({k:v for k,v in kwargs.items() if k!='env'}))
        candidate,count=old_search(*args,**kwargs)
        selected.append(copy.deepcopy(candidate));counts.append(int(count));return candidate,count
    planner._evaluate_candidate=evaluate
    try:success=forced_call(env,parent,module,search)
    finally:
        planner._evaluate_candidate=old_evaluate;snapshot.restore(shift)
    if A.state_digest(env,shift)!=before:raise B.ReplayMismatch('Candidate collection changed decision state')
    if not success or len(selected)!=1 or selected[0] is None or counts[0]!=len(candidates):
        raise B.ReplayMismatch('Expected one executable Phase22 search at audited gate')
    return {'candidates':candidates,'selected':selected[0],'count':counts[0],
            'request':requests[0],'request_hash':B.fingerprint(requests[0]),
            'pool_hash':B.fingerprint(candidates)}


def apply_candidate(env,module,parent,candidate,count,expected_request):
    invoked=[]
    def inject(*args,**kwargs):
        if args:raise B.ReplayMismatch('Unexpected positional request on candidate injection')
        request={k:v for k,v in kwargs.items() if k!='env'}
        if B.fingerprint(request)!=expected_request:raise B.ReplayMismatch('Candidate injection request differs')
        invoked.append(True);return copy.deepcopy(candidate),count
    if not forced_call(env,parent,module,inject) or len(invoked)!=1:
        raise B.ReplayMismatch('Candidate application failed')
    if W.path_hash(env)!=B.fingerprint(candidate.active_path):
        raise B.ReplayMismatch('Applied path differs from frozen candidate')


def rollout(env,model,shift,obs,gate_step):
    np=B.NP;rows=[];collided=False;arrived=False;terminal=False
    for step in range(gate_step,601):
        action,_=model.predict(obs,deterministic=True)
        obs,reward,terminated,truncated,info=B.finish_api(env.step(action))
        audit=G.label_step(env,info);collision=bool(audit['primary_collision'])
        success=bool(info.get('reach_goal',False) or info.get('success',False) or info.get('is_success',False))
        collided|=collision;arrived|=success
        rows.append({'public_step':step,'action':np.asarray(action).tolist(),'observation':np.asarray(obs).tolist(),
            'qpos':env.data.qpos.copy().tolist(),'qvel':env.data.qvel.copy().tolist(),
            'ctrl':env.data.ctrl.copy().tolist(),'robot_xy':np.asarray(env.robot_xy).tolist(),'reward':float(reward),
            'collision':collision,'success':success,'terminated':bool(terminated),'truncated':bool(truncated),
            'unknown_penetration':bool(audit['environment_flags']['phase20_unknown_penetration']),
            'known_penetration':bool(audit['environment_flags']['phase20_known_penetration']),
            'native_contact':bool(audit['native_obstacle_contact']),
            'state_hash_without_model':B.state_hash(env,shift,include_model=False),
            'recovery_stage':str(getattr(env.inner,'recovery_stage','unknown')),
            'active_path_hash':W.path_hash(env),
            'unknown_clearance_evaluation_only':info.get('phase20_unknown_clearance')})
        if terminated or truncated or collision:terminal=True;break
    result={'trace_hash':B.fingerprint(rows),'steps_from_gate':len(rows),
        'terminal_public_step':gate_step-1+len(rows),'safe_success':arrived and not collided,
        'collision':collided,'horizon_censored':not terminal,
        'unknown_penetration_ever':any(x['unknown_penetration'] for x in rows),
        'known_penetration_ever':any(x['known_penetration'] for x in rows),
        'native_contact_ever':any(x['native_contact'] for x in rows),
        'goal_distance_final_m':float(np.linalg.norm(env.goal_xy-env.robot_xy)),
        'final_robot_xy':np.asarray(env.robot_xy).tolist()}
    return rows,result


def matches_b7_trace(rows,previous):
    if len(rows)!=len(previous):return False
    return all(B.fingerprint({k:row[k] for k in old})==B.fingerprint(old)
               for row,old in zip(rows,previous))


def execute(args):
    import numpy as np
    import torch
    import mujoco
    B.NP,B.TORCH,B.MJ=np,torch,mujoco
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    sys.path.insert(0,str(ROOT));P.install()
    import navigation.phase22.continuous_corridor_planner as planner
    import envs.phase22.mkmini_phase22_v1_continuous_corridor_env as module
    from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import MkMiniPhase22V1ContinuousCorridorEnv as Env
    from envs.phase21.mkmini_phase21_v11_candidate_recovery_env import MkMiniPhase21V11CandidateRecoveryEnv as Parent
    from training.phase21_risk_switch_fusion_sac.tests import eval_phase21_v3_exact_pair_5ep as E
    from stable_baselines3 import SAC
    if B.sha(B.MODEL)!=B.EXPECTED_MODEL:raise RuntimeError('Frozen SAC hash mismatch')
    frozen=W.sources()
    for p in (SUPPORT,Q.AUDIT,Path(__file__).resolve()):frozen[str(p)]=B.sha(p)
    A.write(B.OUT/'frozen_sources_before.json',frozen)
    expected=next(x for x in json.loads((Q.AUDIT_RUN/f'seed_{args.seed}'/'queries.json').read_text())
                  if x['public_step']==args.gate_step)
    shift=B.load_shift(args.seed);E.seed_all(args.seed)
    env=Env();env._phase21_v4_known_map_obstacles=MethodType(B.clean_map,env)
    model=SAC.load(str(B.MODEL),device='cpu')
    try:
        obs,_=E.reset_env(env,args.seed)
        old=json.loads((Q.B6_RUN/f'seed_{args.seed}_baseline'/'result.json').read_text())
        if A.state_digest(env,shift)!=old['semantic_reset_state_hash']:raise B.ReplayMismatch('Reset differs from B6')
        for step in range(1,args.gate_step):
            env._phase21_v8_future_sensor_margin();env._phase21_sensor_points()
            action,_=model.predict(obs,deterministic=True)
            obs,_,terminated,truncated,info=B.finish_api(env.step(action))
            if terminated or truncated or G.label_step(env,info)['primary_collision']:
                raise B.ReplayMismatch('Baseline ended before gate')
        env._phase21_v8_future_sensor_margin();env._phase21_sensor_points()
        state=A.state_digest(env,shift)
        if state!=expected['decision_state_hash']:raise B.ReplayMismatch('Decision differs from B7')
        snapshot=B.Snapshot(env,shift)
        pool=collect(env,shift,planner,module,Parent)
        repeated=collect(env,shift,planner,module,Parent)
        if pool['pool_hash']!=repeated['pool_hash'] or pool['request_hash']!=repeated['request_hash']:
            raise B.ReplayMismatch('Candidate pool/order is nondeterministic')
        if B.fingerprint(pool['selected'].active_path)!=expected['selected_path_hash']:
            raise B.ReplayMismatch('Best candidate differs from B7')
        del repeated
        alternatives,rules=P.choose(pool['candidates'],pool['selected'],args.seed)
        choices=[('keep_original',None,'no_intervention'),('phase22_best',pool['selected'],'original_phase22_score')]
        choices += [(f'candidate_{index}',candidate,rule['rule'])
                    for (index,candidate),rule in zip(alternatives,rules)]
        control=P.predecision_control(env)
        records=[]
        for name,candidate,rule in choices:
            records.append({'name':name,'rule':rule,'candidate':None if candidate is None else
                            P.geometry_features(candidate,-1,control['values'])})
        source_audit=B.audit_known_map(env)
        if not source_audit['known_map_source_gate_pass']:raise RuntimeError('Unknown geometry leaked into known map')
        A.write(B.OUT/'candidate_manifest.json',{'seed':args.seed,'public_step':args.gate_step,
             'decision_state_hash':state,'pool_hash':pool['pool_hash'],'request_hash':pool['request_hash'],
             'attempted':pool['count'],'feasible_attempts':sum(c is not None and c.feasible for c in pool['candidates']),
             'distinct_feasible_hashes':len({B.fingerprint(c.active_path) for c in pool['candidates'] if c is not None and c.feasible}),
             'choices':records,'selection_frozen_before_outcomes':True,'source_audit':source_audit,
             'pool_repetition_equal':True,'selection_is_sampled_not_exhaustive':True})
        A.write(B.OUT/'decision_inputs.json',pool['request']);A.write(B.OUT/'control_features.json',control)
        A.write(B.OUT/'decision_observation.json',obs)
        snapshot.save('decision_snapshot.pkl')
        with (B.OUT/'frozen_choices.pkl').open('wb') as f:pickle.dump(choices,f,protocol=5)
        branches=[];traces={};checks=[];started=time.monotonic()
        b7=ROOT/'experiments/phase_rpccr_p0b7_v1/runs/branches_20261014_02'/f'seed_{args.seed}'/'branches'
        for position,(name,candidate,rule) in enumerate(choices):
            for repetition in ((1,2) if position<=2 else (1,)):
                snapshot.restore(shift)
                if A.state_digest(env,shift)!=state:raise B.ReplayMismatch('Branch restore differs')
                if candidate is not None:
                    apply_candidate(env,module,Parent,candidate,pool['count'],pool['request_hash'])
                rows,result=rollout(env,model,shift,np.asarray(obs).copy(),args.gate_step)
                A.write(B.OUT/f'branches/{name}_repeat_{repetition}_trace.json',rows)
                record={'name':name,'rule':rule,'repetition':repetition,
                        'path_hash':None if candidate is None else B.fingerprint(candidate.active_path),**result}
                branches.append(record);A.write(B.OUT/'branch_progress.json',branches)
                if repetition==1:
                    traces[name]=result['trace_hash']
                    if name in ('keep_original','phase22_best'):
                        old_name='original' if name=='keep_original' else 'early_phase22'
                        previous=json.loads((b7/f'{old_name}_repeat_1_trace.json').read_text())
                        if not matches_b7_trace(rows,previous):raise B.ReplayMismatch(f'{name} differs from B7 trajectory')
                else:
                    equal=traces[name]==result['trace_hash'];checks.append({'name':name,'equal':equal})
                    if not equal:raise B.ReplayMismatch('Same candidate full-state replay differs')
                print(json.dumps({'event':'BRANCH_DONE','seed':args.seed,'name':name,'repeat':repetition,
                                  'success':result['safe_success'],'collision':result['collision'],
                                  'step':result['terminal_public_step']}),flush=True)
        unique=[r for r in branches if r['repetition']==1]
        result={'experiment':'RP-P0B8-DIVERSE-CANDIDATE-EXISTENCE-DEVELOPMENT','seed':args.seed,
            'public_step':args.gate_step,'decision_state_hash':state,'branches':branches,
            'same_candidate_checks':checks,'unique_candidates_executed':len(unique)-1,
            'baseline_B7_reproduced':True,'best_B7_reproduced':True,
            'baseline_safe_success':unique[0]['safe_success'],
            'safe_candidate_count':sum(r['safe_success'] for r in unique[1:]),
            'safe_candidate_names':[r['name'] for r in unique[1:] if r['safe_success']],
            'rescue_opportunity':not unique[0]['safe_success'] and any(r['safe_success'] for r in unique[1:]),
            'method_wall_seconds':time.monotonic()-started,'training':False,'development_only':True,
            'sampled_subset_only':True}
        A.write(B.OUT/'result.json',result);return result
    finally:
        env.close();after=W.sources()
        for p in (SUPPORT,Q.AUDIT,Path(__file__).resolve()):after[str(p)]=B.sha(p)
        changes=[p for p,h in frozen.items() if after.get(p)!=h]
        A.write(B.OUT/'integrity.json',{'frozen_source_changes':changes,'frozen_model_sha256':B.sha(B.MODEL)})
        if changes:raise RuntimeError('Frozen source changed')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True);parser.add_argument('--seed',type=int,choices=sorted(GATES),required=True)
    parser.add_argument('--budget-seconds',type=int,default=900)
    args=parser.parse_args();args.gate_step=GATES[args.seed]
    B.OUT=Path(args.out).resolve();B.OUT.mkdir(parents=True,exist_ok=False)
    os.chdir(B.OUT);(B.OUT/'assets').mkdir();(B.OUT/'branches').mkdir()
    (B.OUT/'assets/meshes_fixed').symlink_to(ROOT/'training/assets/mkmini_real/meshes_fixed',target_is_directory=True)
    for key in ('XDG_CACHE_HOME','MESA_SHADER_CACHE_DIR','__GL_SHADER_DISK_CACHE_PATH'):os.environ[key]=str(B.OUT/'cache')
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',MUJOCO_GL='egl',CUDA_VISIBLE_DEVICES='',
                      OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MPLCONFIGDIR=str(B.OUT/'cache/matplotlib'))
    sys.addaudithook(B.write_guard)
    A.write(B.OUT/'preregistration.json',{'experiment':'RP-P0B8-CANDIDATE-EXISTENCE',**vars(args),
        'candidate_rules':['keep_original','phase22_best','maximum_sensor_margin','minimum_p95_curvature',
                           'minimum_length_ratio','farthest_path_shape','fixed_seed_random'],
        'dedup_mean_path_m':0.02,'same_candidate_repeats':'baseline, best, first alternate each twice',
        'max_public_step':600,'frozen_sac':True,'training':False,'development_only':True,
        'first_action_observation':'same gate observation as B7; only candidate changes',
        'future_truth':'evaluation labels only, never candidate selection or online features'})
    def alarm(*_):raise P.HardBudgetExceeded('B8 worker wall budget exceeded')
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
