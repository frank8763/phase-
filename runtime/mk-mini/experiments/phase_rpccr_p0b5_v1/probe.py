#!/usr/bin/env python3
"""B5 long-horizon runtime entry probe and frozen-SAC counterfactual gate."""
from __future__ import annotations
import argparse
import copy
import fcntl
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

PROJECT=Path('/home/linghu/catkin_ws/src/mk-mini')
GATE_PATH=PROJECT/'experiments/phase_rpccr_p0b4_v1/runtime_gate.py'
spec=importlib.util.spec_from_file_location('p0b4_gate_support',GATE_PATH)
G=importlib.util.module_from_spec(spec); sys.modules[spec.name]=G; spec.loader.exec_module(G)
B=G.B


class HardBudgetExceeded(BaseException):
    """Must bypass the environment's broad except Exception recovery clauses."""
    pass
B.BudgetExceeded=HardBudgetExceeded


def predecision_control(env):
    fields=('phase14_last_yaw_sync_v','phase14_last_yaw_sync_yaw_rate',
            'phase14_last_yaw_sync_steer','phase14_last_yaw_sync_wheel',
            '_h2_last_steer_cmd','last_lf_steer','last_rf_steer','last_lr_wheel','last_rr_wheel',
            'phase21_v8_unsafe_streak','phase21_v8_replan_count','phase21_v8_replan_failure_count',
            'phase21_v8_last_replan_step','phase21_v8_step','recovery_stage')
    values={}; sources={}
    for key in fields:
        for index,obj in enumerate(B.objects(env)):
            if key in vars(obj):
                values[key]=copy.deepcopy(vars(obj)[key]); sources[key]=f'owner[{index}].{key}'; break
        else:
            values[key]=None; sources[key]='missing; not silently zero-filled'
    values['robot_xy']=B.NP.asarray(env.robot_xy).copy(); sources['robot_xy']='own robot pose, same source as planner request'
    values['robot_yaw']=float(getattr(env,'robot_yaw',0.0)); sources['robot_yaw']='own robot heading, same source as planner request'
    return {'values':values,'sources':sources,
            'role':'decision-time own-controller cache; no obstacle truth, RNG, SHIFT counts or future outputs'}


OriginalRuntimeHook=G.RuntimeHook
class FeatureHook(OriginalRuntimeHook):
    def search(self,*args,**kwargs):
        capture=self.context.get('api')=='step' and not self.triggered
        if capture and self.mode=='discover' and getattr(self,'checkpoint_expected',None) is not None:
            live=B.state_hash(self.env,self.shift)
            if live!=self.checkpoint_expected:
                raise B.ReplayMismatch('Portable checkpoint does not reproduce the historical decision state')
        if capture:
            self.control_features=predecision_control(self.env)
        result=super().search(*args,**kwargs)
        if capture and self.mode=='discover' and self.triggered:
            B.write('decision_control_features.json',self.control_features)
        return result


def load_snapshot(path,env,shift):
    # Only checkpoints written by this experiment are accepted.
    path=Path(path).resolve()
    if not path.is_relative_to(PROJECT/'experiments/phase_rpccr_p0b5_v1/runs'):
        raise ValueError('Checkpoint outside this experiment is not supported')
    with path.open('rb') as f: payload=pickle.load(f)
    snapshot=B.Snapshot(env,shift)
    expected=[type(owner).__module__+'.'+type(owner).__name__ for owner in snapshot.owners]
    if payload['owner_types']!=expected: raise B.ReplayMismatch('Checkpoint owner schema differs')
    for name in ('model','data','python','sections','shift'):
        setattr(snapshot,name,payload[name])
    snapshot.random=payload['python_rng']; snapshot.numpy=payload['numpy_rng']; snapshot.torch=payload['torch_rng']
    return snapshot


OriginalMonitor=G.ContactMonitor
class ProgressMonitor(OriginalMonitor):
    def begin(self,env):
        super().begin(env)
        self.goal_distance_start=float(B.NP.linalg.norm(env.goal_xy-env.robot_xy))
    def finish(self,env):
        super().finish(env)
        self.last['pre_api_goal_distance_m']=self.goal_distance_start


def install():
    G.ContactMonitor=ProgressMonitor
    G.install_instrumentation()
    from navigation.phase21.local_planners.phase21_v8_adaptive_runtime_safe import Phase21V8AdaptiveRuntimeSafePlanner
    original=Phase21V8AdaptiveRuntimeSafePlanner.plan
    def observe(planner,request):
        return G.record_runtime_plan(original,planner,request)
    Phase21V8AdaptiveRuntimeSafePlanner.plan=observe


def trajectory(env,model,shift,obs,initial=None,horizon=150):
    distance0=(float(G.MONITOR.last['pre_api_goal_distance_m']) if initial is not None
               else float(B.NP.linalg.norm(env.goal_xy-env.robot_xy)))
    trace,result=G.trajectory(env,model,shift,obs,initial,horizon)
    result['goal_progress_m']=distance0-float(B.NP.linalg.norm(env.goal_xy-env.robot_xy))
    result['goal_progress_reference']='same public-step boundary, including the decision-containing first step'
    return trace,result


def shape(path):
    np=B.NP; path=np.asarray(path,dtype=np.float64)
    lengths=np.linalg.norm(np.diff(path,axis=0),axis=1)
    cumulative=np.r_[0.,np.cumsum(lengths)]
    if cumulative[-1]<=1e-9: return np.repeat(path[:1],64,axis=0)
    samples=np.linspace(0.,cumulative[-1],64)
    return np.column_stack([np.interp(samples,cumulative,path[:,axis]) for axis in (0,1)])


def choose(candidates,selected,seed):
    np=B.NP; pool=[]; hashes=set(); original_hash=B.fingerprint(selected.active_path)
    selected_shapes=[shape(selected.active_path)]
    for index,candidate in enumerate(candidates):
        if candidate is None or not candidate.feasible: continue
        digest=B.fingerprint(candidate.active_path)
        if digest==original_hash or digest in hashes: continue
        hashes.add(digest); pool.append((index,copy.deepcopy(candidate),shape(candidate.active_path)))
    selected_items=[]; selection=[]
    def add(order,rule):
        for index,candidate,points in order:
            if any(index==x[0] for x in selected_items): continue
            if min(float(np.mean(np.linalg.norm(points-other,axis=1))) for other in selected_shapes)<0.02:
                continue
            selected_items.append((index,candidate)); selected_shapes.append(points)
            selection.append({'attempt_index':index,'rule':rule}); return
    add(sorted(pool,key=lambda x:(-x[1].sensor_margin,x[0])),'maximum_sensor_margin')
    add(sorted(pool,key=lambda x:(x[1].p95_curvature,x[0])),'minimum_p95_curvature')
    add(sorted(pool,key=lambda x:(x[1].length_ratio,x[0])),'minimum_length_ratio')
    add(sorted(pool,key=lambda x:(-min(float(np.mean(np.linalg.norm(x[2]-other,axis=1)))
                                     for other in selected_shapes),x[0])),'farthest_predecision_path_shape')
    rng=np.random.default_rng(seed+731000000)
    add([pool[int(i)] for i in rng.permutation(len(pool))],'fixed_seed_random_feasible')
    return selected_items,selection


def geometry_features(candidate,index,control):
    np=B.NP; row=B.candidate_record(candidate,index)
    path=np.asarray(candidate.active_path,dtype=np.float64)
    nearest=int(np.argmin(np.linalg.norm(path-np.asarray(control['robot_xy']),axis=1)))
    end=min(len(path)-1,nearest+2)
    tangent=path[end]-path[max(0,nearest-1)]
    heading=math.atan2(float(tangent[1]),float(tangent[0]))
    difference=heading-float(control['robot_yaw'])
    row['initial_heading_error_rad']=math.atan2(math.sin(difference),math.cos(difference))
    speed=control.get('phase14_last_yaw_sync_v')
    row['incoming_speed_times_p95_curvature']=None if speed is None else abs(float(speed))*candidate.p95_curvature
    return row


def sources():
    result=B.source_manifest()
    for path in (GATE_PATH,Path(__file__).resolve()): result[str(path)]=B.sha(path)
    return result


def reset_geometry(env):
    """Match the historical G2B long-horizon rule using only reset-time data."""
    np=B.NP
    path_source=None; route=None
    for name in ('phase19_planned_path','phase21_v3_original_path','raw_astar_path'):
        value=getattr(env,name,None)
        if value is None: continue
        points=np.asarray(value,dtype=np.float64)
        if points.ndim==2 and points.shape[0]>=2 and points.shape[1]>=2:
            route=points[:,:2]; path_source=name; break
    length=None if route is None else float(np.linalg.norm(np.diff(route,axis=0),axis=1).sum())
    euclid=float(np.linalg.norm(np.asarray(env.goal_xy)-np.asarray(env.robot_xy)))
    return {'robot_xy':np.asarray(env.robot_xy).tolist(),'goal_xy':np.asarray(env.goal_xy).tolist(),
            'astar_path_length_m':length,'euclidean_start_goal_m':euclid,'path_source':path_source,
            'long_horizon_eligible':bool(length is not None and length>=3.0 and euclid>=2.5),
            'rule':'G2B-LH40: reset A* path >=3.0 m and Euclidean start-goal >=2.5 m; outcome blind'}


def execute(args):
    import numpy as np
    import torch
    import mujoco
    B.NP,B.TORCH,B.MJ=np,torch,mujoco
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
    sys.path.insert(0,str(PROJECT)); install()
    from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import MkMiniPhase22V1ContinuousCorridorEnv
    import envs.phase22.mkmini_phase22_v1_continuous_corridor_env as env_module
    import navigation.phase22.continuous_corridor_planner as planner
    from training.phase21_risk_switch_fusion_sac.tests import eval_phase21_v3_exact_pair_5ep as E
    from stable_baselines3 import SAC
    if B.sha(B.MODEL)!=B.EXPECTED_MODEL: raise RuntimeError('Frozen SAC model hash mismatch')
    shift=B.load_shift(args.seed); E.seed_all(args.seed)
    env=MkMiniPhase22V1ContinuousCorridorEnv()
    env._phase21_v4_known_map_obstacles=MethodType(B.clean_map,env)
    model=SAC.load(str(B.MODEL),device='cpu')
    before=sources(); B.write('frozen_sources_before.json',before)
    B.write('runtime_inventory.json',{'planner_instance':type(env._phase21_v7_planner).__module__+'.'+type(env._phase21_v7_planner).__name__,
                                     'observer_matches_actual_runtime_class':True,'mujoco':mujoco.__version__,
                                     'sac_device':'cpu','control_feature_whitelist':list(predecision_control(env)['values'])})
    try:
        hook=FeatureHook(env,shift,planner,env_module); hook.context={'api':'reset','public_step':0}
        pending_action=pending_output=None; acquisition_trace=[]
        if args.checkpoint_source:
            source=Path(args.checkpoint_source).resolve()
            old_protocol=json.loads((source/'preregistration.json').read_text())
            if old_protocol['seed']!=args.seed: raise ValueError('Checkpoint seed differs')
            B.write('reset_geometry.json',json.loads((source/'reset_geometry.json').read_text()))
            old_manifest=json.loads((source/'candidate_manifest.json').read_text())
            decision=load_snapshot(source/'decision_snapshot.pkl',env,shift); decision.restore(shift)
            restored=B.state_hash(env,shift)
            probe={'historical_decision_hash':old_manifest['decision_state_hash'],'restored_decision_hash':restored,
                   'equal':restored==old_manifest['decision_state_hash'],'source':str(source)}
            B.write('portable_checkpoint_probe.json',probe)
            if not probe['equal']: raise B.ReplayMismatch('Portable decision checkpoint content differs')
            boundary=load_snapshot(source/'api_boundary_snapshot.pkl',env,shift); boundary.restore(shift)
            pending_action=np.asarray(json.loads((source/'pending_action.json').read_text()),dtype=np.float32)
            hook.context=copy.deepcopy(old_manifest['api']); hook.checkpoint_expected=old_manifest['decision_state_hash']
            pending_output=env.step(pending_action)
            obs=B.finish_api(pending_output)[0]
            if B.fingerprint(hook.candidates)!=old_manifest['candidate_set_hash']:
                raise B.ReplayMismatch('Historical candidate pool/order differs after portable restoration')
            B.event('PORTABLE_CHECKPOINT_GATE_PASS',api=hook.context,decision_hash=restored)
        else:
            obs,_=E.reset_env(env,args.seed)
            B.write('reset_geometry.json',reset_geometry(env))
            for step in range(1,601):
                pending_action,_=model.predict(obs,deterministic=True)
                boundary=B.Snapshot(env,shift)
                hook.context={'api':'step','public_step':step}
                pending_output=env.step(pending_action)
                obs,reward,terminated,truncated,info=B.finish_api(pending_output)
                audit=G.label_step(env,info)
                acquisition_trace.append({'public_step':step,'reward':reward,'terminated':terminated,'truncated':truncated,
                                          'primary_collision':audit['primary_collision'],'sim_time':float(env.data.time)})
                if hook.triggered or terminated or truncated or audit['primary_collision']: break
        B.write('acquisition_trace.json',acquisition_trace)
        if not hook.triggered or hook.selected is None:
            result={'gate':'NO_EXECUTABLE_RUNTIME_SCCR_EVENT','seed':args.seed,'counterfactual_executed':False,
                    'runtime_coverage':G.COUNTS.copy()}
            B.write('result.json',result); return result
        selected=copy.deepcopy(hook.selected)
        alternatives,selection=choose(hook.candidates,selected,args.seed)
        expected=hook.last_input; source_audit=hook.audit.copy()
        if not source_audit['known_map_source_gate_pass']: raise RuntimeError('Known-map source gate failed')
        B.write('candidate_manifest.json',{'api':hook.context_at_event,'decision_state_hash':expected,
                                          'candidate_set_hash':hook.candidate_signature,'attempted':hook.count,
                                          'feasible_count':sum(c is not None and c.feasible for c in hook.candidates),
                                          'selected':B.candidate_record(selected,-1),
                                          'valid_candidates':[B.candidate_record(c,i) for i,c in enumerate(hook.candidates) if c is not None],
                                          'alternative_selection':selection,'near_duplicate_mean_path_distance_m':0.02,
                                          'source_audit':source_audit,'choice_frozen_before_outcomes':True,
                                          'interpretation':'sampled feasible subset; not exhaustive oracle over all candidates'})
        feature_rows=[{'candidate':'original','geometry':geometry_features(selected,-1,hook.control_features['values']),
                       'control':hook.control_features['values']}]
        feature_rows += [{'candidate_attempt':index,'geometry':geometry_features(c,index,hook.control_features['values']),
                          'control':hook.control_features['values']} for index,c in alternatives]
        B.write('predecision_features.json',feature_rows); B.write('decision_inputs.json',hook.request)
        boundary.save('api_boundary_snapshot.pkl'); hook.snapshot.save('decision_snapshot.pkl')
        B.write('pending_action.json',pending_action)
        if args.entry_only:
            result={'experiment':'RP-P0B5-ENTRY','gate':'ENTRY_CAPTURED','seed':args.seed,
                    'decision_hash':expected,'decision_api':hook.context_at_event,
                    'decision_control_stage':hook.control_features['values'].get('recovery_stage'),
                    'distinct_alternatives':len(alternatives),'counterfactual_executed':False,
                    'runtime_coverage':G.COUNTS.copy(),'source_audit':source_audit}
            B.write('result.json',result); B.event('ENTRY_CAPTURED',seed=args.seed,stage=result['decision_control_stage'])
            return result
        hook.expected=expected
        original_trace,original_result=trajectory(env,model,shift,obs,(pending_action,pending_output),args.horizon)
        B.write('branches/original_trace.json',original_trace); B.write('branches/original_result.json',original_result)
        results=[{'candidate':'original','repetition':0,**original_result}]
        def branch(candidate,name):
            boundary.restore(shift); hook.replay(candidate)
            output=env.step(pending_action); branch_obs=B.finish_api(output)[0]
            if not hook.triggered: raise B.ReplayMismatch('Original runtime decision event not reached on replay')
            trace,result=trajectory(env,model,shift,branch_obs,(pending_action,output),args.horizon)
            B.write('branches/'+name+'_trace.json',trace); B.write('branches/'+name+'_result.json',result)
            B.event('BRANCH_FINISHED',branch=name,**result); return trace,result
        repeated,result=branch(selected,'original_repeat_1')
        same=B.same_trace(original_trace,repeated); B.write('same_candidate_checks.json',[same])
        if not same['equal']: raise B.ReplayMismatch('Original candidate replay diverged: '+repr(same))
        results.append({'candidate':'original','repetition':1,**result})
        B.event('SAME_CANDIDATE_GATE_PASS',check=same)
        cf_checks=[]
        for position,(index,candidate) in enumerate(alternatives):
            first=None
            for repetition in ((1,2) if position==0 else (1,)):
                trace,result=branch(candidate,f'candidate_{index}_repeat_{repetition}')
                results.append({'candidate_attempt':index,'repetition':repetition,**result})
                if first is None: first=trace
                else:
                    comparison=B.same_trace(first,trace); cf_checks.append({'candidate_attempt':index,**comparison})
                    if not comparison['equal']: raise B.ReplayMismatch('Alternative replay diverged: '+repr(comparison))
        gate='RUNTIME_DIVERSE_CANDIDATE_SCREEN_PASS' if alternatives else 'REPLAY_PASS_INSUFFICIENT_DISTINCT_CANDIDATES'
        result={'experiment':'RP-P0B5-COUNTERFACTUAL','gate':gate,'seed':args.seed,'decision_hash':expected,
                'same_candidate_checks':[same],'counterfactual_repeat_checks':cf_checks,'source_audit':source_audit,
                'branches':results,'runtime_coverage':G.COUNTS.copy(),'horizon_steps':args.horizon,
                'unique_executed_candidates':1+len(alternatives),'risk_model_trained':False,'independent_confirmatory_test':False,
                'innovation_effectiveness_proven':False,'label_version':'B4-native-and-environment-attribution-v1'}
        B.write('result.json',result); B.event('SCREEN_FINISHED',gate=gate,seed=args.seed)
        return result
    finally:
        signal.setitimer(signal.ITIMER_REAL,0); env.close()
        after=sources(); B.write('frozen_sources_after.json',after)
        changed=[path for path,digest in before.items() if after.get(path)!=digest]
        B.write('integrity.json',{'frozen_input_changes':changed,'original_sources_unchanged':not changed,
                                 'frozen_model_sha256':B.sha(B.MODEL)})
        if changed: raise RuntimeError('Frozen source changed during run: '+repr(changed))


def main():
    p=argparse.ArgumentParser(); p.add_argument('--out',required=True); p.add_argument('--seed',type=int,required=True)
    p.add_argument('--horizon',type=int,default=150); p.add_argument('--budget-seconds',type=int,default=900)
    p.add_argument('--checkpoint-source'); p.add_argument('--entry-only',action='store_true')
    args=p.parse_args(); B.OUT=Path(args.out).resolve(); B.OUT.mkdir(parents=True,exist_ok=False)
    lock=(B.OUT.parent/'runtime_gate.lock').open('a'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    os.chdir(B.OUT); (B.OUT/'assets').mkdir()
    (B.OUT/'assets/meshes_fixed').symlink_to(PROJECT/'training/assets/mkmini_real/meshes_fixed',target_is_directory=True)
    for key in ('XDG_CACHE_HOME','MESA_SHADER_CACHE_DIR','__GL_SHADER_DISK_CACHE_PATH'): os.environ[key]=str(B.OUT/'cache')
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',MUJOCO_GL='egl',CUDA_VISIBLE_DEVICES='',
                      OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MPLCONFIGDIR=str(B.OUT/'cache/matplotlib'))
    sys.addaudithook(B.write_guard)
    B.write('preregistration.json',{'experiment':'RP-P0B5-LONG-HORIZON-GATE','created_at':time.strftime('%F %T'),**vars(args),
                                  'frozen_sac':True,'training':False,'required_api':'step','maximum_unique_candidates':6,
                                  'candidate_selection':['original','sensor_margin','curvature','length_ratio','shape_diversity','fixed_seed_random'],
                                  'deduplication_mean_path_distance_m':0.02,'original_repetitions':2,'first_alternative_repetitions':2,
                                  'remaining_alternative_repetitions':1,'actual_runtime_v8_class_observed':True,
                                  'feature_policy':'predecision geometry and own-controller whitelist only',
                                  'failure_policy':'stop immediately on replay/state/pool mismatch; compute censoring is not collision',
                                  'development_only':True,'progress_reference':'public-step boundary before candidate intervention',
                                  'reset_long_horizon_rule':{'astar_path_length_m_min':3.0,'euclidean_start_goal_m_min':2.5}})
    def alarm(*_): raise B.BudgetExceeded('Foreground wall-clock budget exceeded; not a navigation outcome')
    signal.signal(signal.SIGALRM,alarm); signal.setitimer(signal.ITIMER_REAL,args.budget_seconds)
    started=time.monotonic(); code=0; status='STARTED'
    try:
        result=execute(args); status='FINISHED'
        B.write('completion.json',{'status':status,'elapsed_seconds':time.monotonic()-started,'gate':result['gate']})
    except B.ReplayMismatch as exc:
        status='REPLAY_GATE_FAIL'; code=2
        B.write('failure.json',{'status':status,'reason':str(exc),'traceback':traceback.format_exc()}); B.event(status,reason=str(exc))
    except B.BudgetExceeded as exc:
        status='COMPUTE_CENSORED'; code=124
        B.write('failure.json',{'status':status,'reason':str(exc),'elapsed_seconds':time.monotonic()-started}); B.event(status,reason=str(exc))
    except Exception as exc:
        status='IMPLEMENTATION_ERROR'; code=1
        B.write('failure.json',{'status':status,'reason':repr(exc),'traceback':traceback.format_exc()})
        B.event(status,reason=repr(exc)); traceback.print_exc()
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        B.write('runtime_coverage.json',{'status':status,'counts':G.COUNTS,'elapsed_seconds':time.monotonic()-started})
    return code


if __name__=='__main__': sys.exit(main())
