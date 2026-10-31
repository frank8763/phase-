#!/usr/bin/env python3
"""Foreground Frozen-SAC counterfactual pilot; writes only its fresh run directory."""
from __future__ import annotations
import argparse
import ast
import copy
import dataclasses
import fcntl
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import pickle
import random
import signal
import sys
import time
import traceback
from types import MethodType

PROJECT = Path('/home/linghu/catkin_ws/src/mk-mini')
G11B = Path('/home/linghu/mkmini_g11b_budget162_confirmatory_v1_1/g11b_budget162_confirmatory_v1.py')
MODEL = PROJECT / 'training/phase20_unknown_obstacle_adaptation/checkpoints/stage_b_randomized/phase20_stage_b_325000_steps.zip'
EXPECTED_MODEL = '4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f'
OUT = None
NP = TORCH = MJ = None


class BudgetExceeded(Exception):
    pass


class ReplayMismatch(Exception):
    pass


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def json_value(v):
    if NP is not None and isinstance(v, NP.ndarray):
        return json_value(v.tolist())
    if NP is not None and isinstance(v, NP.generic):
        return json_value(v.item())
    if isinstance(v, float) and not math.isfinite(v):
        return None
    if isinstance(v, dict):
        return {str(k):json_value(x) for k,x in v.items()}
    if isinstance(v, (list,tuple)):
        return [json_value(x) for x in v]
    if isinstance(v, Path):
        return str(v)
    return v


def write(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(json_value(value), ensure_ascii=False, indent=2)+'\n')
    os.replace(temporary,path)


def event(kind, **fields):
    value={'wall_time':time.strftime('%F %T'), 'event':kind, **fields}
    with (OUT/'events.jsonl').open('a') as f:
        f.write(json.dumps(json_value(value),ensure_ascii=False)+'\n')
    print(json.dumps(json_value(value),ensure_ascii=False),flush=True)


def write_guard(event_name, args):
    if event_name == 'open':
        path, mode, flags = args
        if isinstance(path, int):
            return
        p=Path(os.fsdecode(path)).resolve()
        forbidden = ('/training/e2e_', '/experiments/e2e_', '/notes2/')
        if any(x in str(p) for x in forbidden):
            raise PermissionError('Stage source excluded: '+str(p))
        writable=bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if writable and not p.is_relative_to(OUT):
            raise PermissionError('Write outside isolated experiment: '+str(p))
    if event_name in {'os.mkdir','os.remove','os.rmdir'}:
        p=Path(os.fsdecode(args[0])).resolve()
        if event_name=='os.mkdir' and p.is_dir():
            return
        if not p.is_relative_to(OUT):
            raise PermissionError('Filesystem mutation outside isolated experiment: '+str(p))
    if event_name in {'os.rename','os.link','os.symlink'}:
        # Renames require both endpoints inside OUT; symlinks may read immutable assets.
        paths=args[:2] if event_name=='os.rename' else args[1:2]
        for item in paths:
            p=Path(os.fsdecode(item)).absolute()
            if not p.is_relative_to(OUT):
                raise PermissionError('Filesystem mutation outside isolated experiment: '+str(p))


def objects(env):
    result=[]
    queue=[env]
    seen=set()
    while queue:
        obj=queue.pop(0)
        if id(obj) in seen:
            continue
        seen.add(id(obj)); result.append(obj)
        local=vars(obj)
        for key in ('inner','env','base_env'):
            if key in local and local[key] is not obj and hasattr(local[key],'__dict__'):
                queue.append(local[key])
    return result


def canonical(value, seen=None):
    if seen is None:
        seen={}
    if isinstance(value, NP.ndarray):
        return ('array',str(value.dtype),tuple(value.shape),hashlib.sha256(value.tobytes()).hexdigest())
    if isinstance(value, NP.generic):
        return canonical(value.item(),seen)
    if isinstance(value, NP.dtype):
        return ('numpy_dtype',value.str)
    if isinstance(value,(TORCH.dtype,TORCH.device)):
        return ('torch_type',str(value))
    if isinstance(value,type):
        return ('class',value.__module__,value.__qualname__)
    if isinstance(value,(str,bytes,int,bool,type(None))):
        return value
    if isinstance(value,float):
        return ('float',value.hex())
    if isinstance(value,Path):
        return ('path',str(value))
    if isinstance(value,NP.random.Generator):
        return ('generator',canonical(value.bit_generator.state,seen))
    if isinstance(value,NP.random.RandomState):
        return ('randomstate',canonical(value.get_state(),seen))
    if callable(value):
        return ('callable',getattr(value,'__module__',None),getattr(value,'__qualname__',type(value).__name__))
    identity=id(value)
    if identity in seen:
        return ('reference',seen[identity])
    seen[identity]=len(seen)
    if isinstance(value,dict):
        return tuple((str(k),canonical(value[k],seen)) for k in sorted(value,key=str))
    if isinstance(value,(list,tuple)):
        return (type(value).__name__,tuple(canonical(x,seen) for x in value))
    if isinstance(value,(set,frozenset)):
        return (type(value).__name__,tuple(sorted((canonical(x,seen) for x in value),key=repr)))
    if dataclasses.is_dataclass(value):
        return (type(value).__module__,type(value).__qualname__,
                tuple((field.name,canonical(getattr(value,field.name),seen)) for field in dataclasses.fields(value)))
    if hasattr(value,'__dict__'):
        return (type(value).__module__,type(value).__qualname__,canonical(vars(value),seen))
    raise TypeError('Unaccounted mutable state type: '+str(type(value)))


def fingerprint(value):
    return hashlib.sha256(pickle.dumps(canonical(value),protocol=5)).hexdigest()


def model_arrays(model):
    return {name:getattr(model,name) for name in dir(model)
            if not name.startswith('_') and isinstance(getattr(model,name), NP.ndarray)}


def model_sections(model):
    sections={'opt':model.opt,'stat':model.stat}
    for name in ('global_','quality','headlight','map','scale','rgba'):
        sections['vis.'+name]=getattr(model.vis,name)
    values={}
    for prefix,obj in sections.items():
        values[prefix]={}
        for key in dir(obj):
            if key.startswith('_'):
                continue
            v=getattr(obj,key)
            if isinstance(v,(int,float,bool,NP.ndarray)):
                values[prefix][key]=v.copy() if isinstance(v,NP.ndarray) else v
    return values


class Snapshot:
    def __init__(self,env,shift):
        self.env=env
        self.owners=objects(env)
        self.immutable={}
        memo={id(obj):obj for obj in self.owners}
        for obj in self.owners:
            for k,v in vars(obj).items():
                if k in ('inner','env','base_env','model','data','renderer','base_model') or callable(v):
                    self.immutable[(id(obj),k)]=v
                    memo[id(v)]=v
        self.python=copy.deepcopy([{k:v for k,v in vars(obj).items()
                                   if (id(obj),k) not in self.immutable} for obj in self.owners],memo)
        self.model=copy.copy(env.model)
        self.data=copy.copy(env.data)
        self.sections=model_sections(env.model)
        self.shift=copy.deepcopy(shift)
        self.random=random.getstate()
        self.numpy=NP.random.get_state()
        self.torch=TORCH.get_rng_state().clone()
        self.renderers=[]
        for obj in self.owners:
            renderer=vars(obj).get('renderer')
            if renderer is not None:
                self.renderers.append((renderer,{k:copy.deepcopy(getattr(renderer,k)) for k in ('_depth_rendering','_segmentation_rendering') if hasattr(renderer,k)}))

    def restore(self,shift):
        live=self.env.model
        for name,saved in model_arrays(self.model).items():
            target=getattr(live,name)
            if target.shape!=saved.shape:
                raise ReplayMismatch('Model topology changed: '+name)
            if target.flags.writeable:
                target[...] = saved
            elif not NP.array_equal(target,saved,equal_nan=True):
                raise ReplayMismatch('Readonly model array changed: '+name)
        for prefix,values in self.sections.items():
            obj=live
            for component in prefix.split('.'):
                obj=getattr(obj,component)
            for key,v in values.items():
                target=getattr(obj,key)
                if isinstance(v,NP.ndarray):
                    target[...] = v
                elif target!=v:
                    setattr(obj,key,v)
        MJ.mj_copyData(self.env.data,live,self.data)
        memo={id(obj):obj for obj in self.owners}
        for value in self.immutable.values():
            memo[id(value)]=value
        restored=copy.deepcopy(self.python,memo)
        for obj,fields in zip(self.owners,restored):
            local=vars(obj)
            local.clear(); local.update(fields)
            local.update({k:v for (identity,k),v in self.immutable.items() if identity==id(obj)})
        for renderer,flags in self.renderers:
            for key,value in flags.items():
                setattr(renderer,key,value)
        shift.clear(); shift.update(copy.deepcopy(self.shift))
        random.setstate(self.random); NP.random.set_state(self.numpy); TORCH.set_rng_state(self.torch)

    def save(self,name):
        payload={'model':self.model,'data':self.data,'python':self.python,'sections':self.sections,
                 'shift':self.shift,'python_rng':self.random,'numpy_rng':self.numpy,'torch_rng':self.torch,
                 'owner_types':[type(x).__module__+'.'+type(x).__name__ for x in self.owners],
                 'preserved_handles':[{ 'owner':i,'key':k,'type':type(v).__name__}
                                      for i,obj in enumerate(self.owners) for (identity,k),v in self.immutable.items() if identity==id(obj)]}
        with (OUT/name).open('wb') as f:
            pickle.dump(payload,f,protocol=5)


def data_state(env):
    values={}
    for name in ('time','qpos','qvel','act','ctrl','qacc','qacc_warmstart','sensordata','xpos','xmat','geom_xpos','geom_xmat','actuator_force','qfrc_applied','xfrc_applied','userdata','mocap_pos','mocap_quat','eq_active'):
        value=getattr(env.data,name)
        values[name]=value.copy() if isinstance(value,NP.ndarray) else value
    values['contacts']=[(int(c.geom1),int(c.geom2),float(c.dist),c.pos.copy(),c.frame.copy()) for c in env.data.contact]
    return values


def state_hash(env,shift,include_model=True,components=False):
    saved=Snapshot(env,shift)
    values={'python':saved.python,'data':data_state(env),'shift':saved.shift,
            'random':saved.random,'numpy':saved.numpy,'torch':saved.torch.numpy(),
            'renderer_flags':[flags for _,flags in saved.renderers]}
    if include_model:
        values.update(model=model_arrays(env.model),sections=saved.sections)
    parts={}
    for index,(owner,fields) in enumerate(zip(saved.owners,saved.python)):
        prefix=str(index)+'.'+type(owner).__module__+'.'+type(owner).__name__
        for key,value in fields.items():
            parts[prefix+'.'+key]=fingerprint(value)
    for key,value in values['data'].items():
        parts['mujoco_data.'+key]=fingerprint(value)
    for key in ('shift','random','numpy','torch','renderer_flags'):
        parts['runtime.'+key]=fingerprint(values[key])
    if include_model:
        for key,value in values['model'].items():
            parts['mujoco_model.'+key]=fingerprint(value)
        for key,value in values['sections'].items():
            parts['mujoco_model.'+key]=fingerprint(value)
    # A deepcopy can preserve equal field contents while changing incidental
    # cross-field Python object aliasing. Hash semantic values field by field.
    digest=fingerprint(parts)
    if not components:
        return digest
    return digest,parts


def load_shift(seed):
    tree=ast.parse(G11B.read_text())
    names={'FUSION_MOD','LIDAR_SIGMA_M','LIDAR_CLIP_M','LIDAR_DROPOUT','DEPTH_SIGMA_M','DEPTH_CLIP_M','DEPTH_DROPOUT'}
    scope={'np':NP,'hashlib':hashlib,'inspect':inspect,'importlib':__import__('importlib')}
    functions=[]
    for n in tree.body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id in names:
                    scope[t.id]=ast.literal_eval(n.value)
        if isinstance(n,ast.FunctionDef) and n.name in {'stable_seed','arrhash','install_shift_patch'}:
            functions.append(n)
    if len(functions)!=3 or not names<=scope.keys():
        raise RuntimeError('SHIFT source contract changed')
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(G11B),'exec'),scope)
    return scope['install_shift_patch'](seed)


def isolate_assets():
    from training.envs.mkmini_real_indoor_astar_sac_env import MkMiniRealIndoorAStarSACEnv
    from training.phase7_residual_camera_aux.envs.mkmini_phase7_residual_camera_aux_env import MkMiniPhase7ResidualCameraAuxEnv
    old_xml=MkMiniRealIndoorAStarSACEnv._make_real_indoor_xml
    def xml(self):
        self.real_robot_xml=PROJECT/'training/assets/mkmini_real/mkmini_mobile_manipulator_v1.xml'
        self.real_indoor_xml=OUT/'assets/isolated_indoor.xml'
        return old_xml(self)
    MkMiniRealIndoorAStarSACEnv._make_real_indoor_xml=xml
    old_init=MkMiniPhase7ResidualCameraAuxEnv.__init__
    def init(self,*args,**kwargs):
        if args:
            args=(str(PROJECT/args[0]) if not Path(args[0]).is_absolute() else args[0],*args[1:])
        else:
            p=Path(kwargs.get('base_model_path','training/phase6_clean/confirmed/phase6_v1_lidar_main_camera_goal_55k_confirmed.zip'))
            kwargs['base_model_path']=str(PROJECT/p) if not p.is_absolute() else str(p)
        return old_init(self,*args,**kwargs)
    MkMiniPhase7ResidualCameraAuxEnv.__init__=init


def clean_map(self):
    rectangles=[]; circles=[]
    for gid in range(self.model.ngeom):
        name=MJ.mj_id2name(self.model,MJ.mjtObj.mjOBJ_GEOM,gid) or ''
        if name in self.HIDDEN_GEOM_NAMES:
            continue
        if 'real_rect_obs' not in name.lower() and 'real_circle_obs' not in name.lower():
            continue
        m=self.model
        if (int(m.geom_contype[gid])==0 and int(m.geom_conaffinity[gid])==0) or float(m.geom_rgba[gid,3])<=0.01 or float(m.geom_pos[gid,2]) < -1:
            continue
        x,y=map(float,m.geom_pos[gid,:2])
        if 'real_rect_obs' in name.lower():
            rectangles.append([x,y,float(m.geom_size[gid,0]),float(m.geom_size[gid,1])])
        else:
            circles.append([x,y,float(m.geom_size[gid,0])])
    return NP.asarray(rectangles,dtype=NP.float32).reshape(-1,4),NP.asarray(circles,dtype=NP.float32).reshape(-1,3)


def audit_known_map(env):
    _,circles=env._phase21_v4_known_map_obstacles()
    hits=[]
    for gid in env.phase19_unknown_geom_ids:
        truth=NP.r_[env.model.geom_pos[gid,:2],env.model.geom_size[gid,0]].astype(NP.float32)
        if any(NP.array_equal(row,truth) for row in circles):
            hits.append(MJ.mj_id2name(env.model,MJ.mjtObj.mjOBJ_GEOM,gid))
    return {'unknown_geoms_in_known_map':hits,'known_map_source_gate_pass':not hits,
            'truth_access_role':'audit/evaluation only; not risk-model features'}


class SearchHook:
    def __init__(self,env,shift,planner,module):
        self.env=env; self.shift=shift; self.planner=planner; self.module=module
        self.original_search=module.search_continuous_corridor
        self.original_evaluate=planner._evaluate_candidate
        self.context={}; self.selected=None; self.candidates=[]; self.expected=None; self.mode='discover'
        self.triggered=False; self.last_input=None; self.snapshot=None; self.request=None; self.audit=None
        planner._evaluate_candidate=self.evaluate
        module.search_continuous_corridor=self.search

    def evaluate(self,*args,**kwargs):
        candidate=self.original_evaluate(*args,**kwargs)
        self.current.append(copy.deepcopy(candidate))
        return candidate

    def search(self,*args,**kwargs):
        request={k:v.copy() if isinstance(v,NP.ndarray) else v for k,v in kwargs.items() if k!='env'}
        capture=not self.triggered
        if capture:
            h,parts=state_hash(self.env,self.shift,components=True)
            if self.mode!='discover' and h!=self.expected:
                prior=self.expected_parts
                changed=[key for key in prior if prior[key]!=parts.get(key)]
                added=sorted(set(parts)-set(prior))
                write('decision_replay_diff.json',{'expected_hash':self.expected,'actual_hash':h,
                                                   'changed_components':changed,'added_components':added,
                                                   'expected_component_hashes':{key:prior[key] for key in changed},
                                                   'actual_component_hashes':{key:parts.get(key) for key in changed}})
                raise ReplayMismatch('Decision state differs before candidate selection: '+repr(changed[:12]))
            self.last_input=h
            self.last_parts=parts
            self.snapshot=Snapshot(self.env,self.shift)
            self.request=copy.deepcopy(request)
            self.audit=audit_known_map(self.env)
        self.current=[]
        selected,count=self.original_search(*args,**kwargs)
        if capture:
            self.triggered=True
            signature=fingerprint(self.current)
            if self.mode!='discover' and signature!=self.candidate_signature:
                raise ReplayMismatch('Real candidate set/order differs on replay')
            if self.mode=='discover':
                self.candidates=self.current
                self.selected=copy.deepcopy(selected)
                self.candidate_signature=signature
                self.expected_parts=parts
                self.context_at_event=copy.deepcopy(self.context)
                self.count=count
                event('REAL_CANDIDATE_POOL',api=self.context,attempted=count,non_null=sum(x is not None for x in self.current),feasible=sum(x is not None and x.feasible for x in self.current),source_audit=self.audit)
            elif self.forced is not None:
                selected=copy.deepcopy(self.forced)
        return selected,count

    def replay(self,forced):
        self.mode='replay'; self.triggered=False; self.forced=forced


def candidate_record(c,index):
    return {'attempt_index':index, **{k:v for k,v in vars(c).items() if k not in ('active_path','local_curve')},
            'path_hash':fingerprint(c.active_path)}


def finish_api(out):
    if len(out)==5:
        obs,reward,terminated,truncated,info=out
    else:
        obs,reward,done,info=out; terminated=done; truncated=False
    return obs,float(reward),bool(terminated),bool(truncated),dict(info or {})


def trajectory(env,model,shift,obs,initial=None,horizon=150):
    from training.phase18_ablation.scripts.eval_phase18_A_full_fixed_seed import robot_obstacle_contact,check_map_penetration
    samples=[]; distance0=float(NP.linalg.norm(env.goal_xy-env.robot_xy)); minimum=float('inf')
    total=0.; collided=False; success=False; recovery_steps=0
    for step in range(horizon):
        if step==0 and initial is not None:
            action,output=initial
        else:
            action,_=model.predict(obs,deterministic=True)
            output=env.step(action)
        obs,reward,terminated,truncated,info=finish_api(output)
        contact=bool(robot_obstacle_contact(env))
        penetration=bool(check_map_penetration(env,margin=0.02))
        collision=bool(info.get('collision',False) or contact or penetration or info.get('phase20_unknown_penetration',False) or info.get('phase20_known_penetration',False))
        arrived=bool(info.get('reach_goal',False) or info.get('success',False) or info.get('is_success',False))
        clear=info.get('phase20_unknown_clearance')
        if isinstance(clear,(float,int)) and math.isfinite(clear):
            minimum=min(minimum,float(clear))
        inner=env.inner
        recovery=vars(inner).get('recovery_stage','UNKNOWN')
        recovery_steps+=int(recovery!='NORMAL')
        full_hash,parts=state_hash(env,shift,False,components=True)
        record={'step':step+1,'observation':NP.asarray(obs).copy(),'policy_action':NP.asarray(action).copy(),
                'qpos':env.data.qpos.copy(),'qvel':env.data.qvel.copy(),'ctrl':env.data.ctrl.copy(),
                'reward':reward,'terminated':terminated,'truncated':truncated,'collision':collision,
                'success':arrived,'recovery_stage':recovery,'state_components':parts,'state_hash':full_hash}
        samples.append(record); total+=reward; collided|=collision; success|=arrived
        if terminated or truncated or collision:
            break
    return samples,{'steps':len(samples),'collision':collided,'safe_success':success and not collided,
                    'horizon_censored':not(terminated or truncated or collided),'minimum_unknown_clearance_evaluation':minimum,
                    'goal_progress_m':distance0-float(NP.linalg.norm(env.goal_xy-env.robot_xy)),
                    'final_recovery_stage':vars(env.inner).get('recovery_stage'),'recovery_steps':recovery_steps,
                    'total_reward':total}


def same_trace(a,b):
    if len(a)!=len(b):
        return {'equal':False,'reason':'different trajectory lengths','a_steps':len(a),'b_steps':len(b)}
    for i,(x,y) in enumerate(zip(a,b),1):
        for key in x:
            if canonical(x[key])!=canonical(y[key]):
                if key=='state_components':
                    changed=[part for part in x[key] if x[key][part]!=y[key].get(part)]
                    return {'equal':False,'first_step':i,'field':key,'changed_components':changed[:30],
                            'changed_count':len(changed)}
                return {'equal':False,'first_step':i,'field':key,'a':json_value(x[key]) if key not in ('observation',) else fingerprint(x[key]),'b':json_value(y[key]) if key not in ('observation',) else fingerprint(y[key])}
    return {'equal':True,'compared_steps':len(a),'criterion':'bitwise arrays and exact scalar/controller-state hashes'}


def source_manifest():
    paths={Path(__file__).resolve(),MODEL,G11B,PROJECT/'training/phase6_clean/confirmed/phase6_v1_lidar_main_camera_goal_55k_confirmed.zip',PROJECT/'training/assets/mkmini_real/mkmini_mobile_manipulator_indoor_v1.xml'}
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename and Path(filename).is_relative_to(PROJECT) and Path(filename).suffix=='.py':
            paths.add(Path(filename))
    return {str(p):sha(p) for p in sorted(paths) if p.is_file()}


def execute(args):
    global NP,TORCH,MJ
    import numpy as np
    import torch
    import mujoco
    NP,TORCH,MJ=np,torch,mujoco
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
    sys.path.insert(0,str(PROJECT))
    isolate_assets()
    from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import MkMiniPhase22V1ContinuousCorridorEnv
    import envs.phase22.mkmini_phase22_v1_continuous_corridor_env as env_module
    import navigation.phase22.continuous_corridor_planner as planner
    from training.phase21_risk_switch_fusion_sac.tests import eval_phase21_v3_exact_pair_5ep as E
    from stable_baselines3 import SAC
    if sha(MODEL)!=EXPECTED_MODEL:
        raise RuntimeError('Frozen model hash mismatch')
    shift=load_shift(args.seed)
    E.seed_all(args.seed)
    env=MkMiniPhase22V1ContinuousCorridorEnv()
    if args.variant=='clean':
        env._phase21_v4_known_map_obstacles=MethodType(clean_map,env)
    model=SAC.load(str(MODEL),device='cpu')
    hashes=source_manifest(); write('frozen_sources_before.json',hashes)
    write('runtime_inventory.json',{'owners':[{ 'type':type(obj).__module__+'.'+type(obj).__name__,'attributes':{k:type(v).__name__ for k,v in vars(obj).items()}} for obj in objects(env)],
                                    'mro':[cls.__module__+'.'+cls.__name__ for cls in type(env).mro()], 'mujoco':mujoco.__version__,'torch':torch.__version__,
                                    'source_variant':args.variant,'shift_noise_source':str(G11B)+':275','sac_device':'cpu','renderer':'original EGL depth rendering'})
    try:
        if args.probe:
            obs,_=E.reset_env(env,args.seed)
            before=Snapshot(env,shift); h=state_hash(env,shift)
            before.save('probe_snapshot.pkl')
            action,_=model.predict(obs,deterministic=True); env.step(action)
            before.restore(shift)
            restored=state_hash(env,shift)
            result={'gate':'SNAPSHOT_ROUNDTRIP_PASS' if h==restored else 'SNAPSHOT_ROUNDTRIP_FAIL','before_hash':h,'restored_hash':restored,'candidate_trajectory_replay_proven':False,'source_audit':audit_known_map(env)}
            write('probe_result.json',result); event('SNAPSHOT_PROBE',**result)
            return result
        hook=SearchHook(env,shift,planner,env_module)
        hook.context={'api':'reset','public_step':0}
        boundary=Snapshot(env,shift)
        obs,reset_info=E.reset_env(env,args.seed)
        api='reset'; pending_action=None; pending_obs=None; pending_output=None
        for step in range(1,601):
            if hook.triggered:
                break
            boundary=Snapshot(env,shift)
            pending_obs=np.asarray(obs).copy()
            pending_action,_=model.predict(obs,deterministic=True)
            # Policy inference is deterministic; snapshot immediately before public env.step.
            boundary=Snapshot(env,shift)
            hook.context={'api':'step','public_step':step}
            pending_output=env.step(pending_action)
            api='step'
            obs,_,terminated,truncated,info=finish_api(pending_output)
            if terminated or truncated:
                break
        if not hook.triggered or hook.selected is None:
            result={'gate':'NO_EXECUTABLE_CONTINUOUS_EVENT','seed':args.seed,'variant':args.variant,'counterfactual_executed':False}
            write('result.json',result); return result
        # Freeze the pool and branch choice before evaluating any continuation outcomes.
        selected=copy.deepcopy(hook.selected)
        pool=[]; seen=set()
        for i,c in enumerate(hook.candidates):
            if c is not None and c.feasible:
                key=fingerprint(c.active_path)
                if key not in seen:
                    seen.add(key); pool.append((i,copy.deepcopy(c)))
        original_key=fingerprint(selected.active_path)
        alternatives=sorted([(i,c) for i,c in pool if fingerprint(c.active_path)!=original_key],key=lambda x:(-x[1].score,x[0]))[:2]
        write('candidate_manifest.json',{'api':hook.context_at_event,'decision_state_hash':hook.last_input,'candidate_set_hash':hook.candidate_signature,'attempted':hook.count,
                                         'valid_candidates':[candidate_record(c,i) for i,c in enumerate(hook.candidates) if c is not None],
                                         'selected':candidate_record(selected,-1),'alternative_attempt_indices':[i for i,c in alternatives],
                                         'choice_rule':'original candidate plus next two highest pre-decision-score unique feasible paths',
                                         'source_audit':hook.audit,'features_frozen_before_outcomes':True})
        write('decision_inputs.json',hook.request)
        boundary.save('api_boundary_snapshot.pkl'); hook.snapshot.save('decision_snapshot.pkl')
        expected=hook.last_input; audit=hook.audit.copy()
        hook.expected=expected
        initial=None if api=='reset' else (pending_action,pending_output)
        original_trace,original_result=trajectory(env,model,shift,obs,initial,args.horizon)
        write('branches/original_trace.json',original_trace); write('branches/original_result.json',original_result)
        results=[{'candidate':'original','repetition':0,**original_result}]
        def branch(candidate,name):
            boundary.restore(shift)
            hook.replay(candidate)
            if api=='reset':
                branch_obs,_=E.reset_env(env,args.seed)
                initial=None
            else:
                output=env.step(pending_action)
                branch_obs=finish_api(output)[0]
                initial=(pending_action,output)
            if not hook.triggered:
                raise ReplayMismatch('Replay did not reach the original decision event')
            trace,result=trajectory(env,model,shift,branch_obs,initial,args.horizon)
            write('branches/'+name+'_trace.json',trace); write('branches/'+name+'_result.json',result)
            event('BRANCH_FINISHED',branch=name,**result)
            return trace,result
        repeat_checks=[]
        for repetition in (1,2):
            trace,result=branch(selected,f'original_repeat_{repetition}')
            comparison=same_trace(original_trace,trace); repeat_checks.append(comparison)
            write('same_candidate_checks.json',repeat_checks)
            if not comparison['equal']:
                raise ReplayMismatch('Same-candidate trajectory diverged: '+repr(comparison))
            results.append({'candidate':'original','repetition':repetition,**result})
        event('SAME_CANDIDATE_GATE_PASS',checks=repeat_checks)
        cf_checks=[]
        if args.variant=='technical' and not audit['known_map_source_gate_pass']:
            gate='DETERMINISM_PASS_SOURCE_LEAK_CONFIRMED'
            event('COUNTERFACTUAL_SCIENCE_GATE_STOP',reason='unknown geometry enters known_margin; separate clean baseline required')
        elif len(alternatives)<2:
            gate='DETERMINISM_PASS_INSUFFICIENT_DISTINCT_CANDIDATES'
        else:
            if not audit['known_map_source_gate_pass']:
                raise RuntimeError('Clean-map source gate failed')
            for i,c in alternatives:
                first=None
                for repetition in (1,2):
                    trace,result=branch(c,f'candidate_{i}_repeat_{repetition}')
                    results.append({'candidate_attempt':i,'repetition':repetition,**result})
                    if first is None:
                        first=trace
                    else:
                        comparison=same_trace(first,trace); cf_checks.append({'candidate_attempt':i,**comparison})
                        if not comparison['equal']:
                            raise ReplayMismatch('Alternative candidate repeat diverged: '+repr(comparison))
            gate='COUNTERFACTUAL_PILOT_PASS'
        result={'gate':gate,'seed':args.seed,'variant':args.variant,'decision_hash':expected,
                'same_candidate_checks':repeat_checks,'counterfactual_repeat_checks':cf_checks,
                'source_audit':audit,'branches':results,'horizon':args.horizon,
                'innovation_effectiveness_proven':False,'risk_model_trained':False,
                'notes':'mechanism pilot; outcome-selected development seed; no independent generalization claim'}
        write('result.json',result); event('PILOT_FINISHED',gate=gate,seed=args.seed,variant=args.variant)
        return result
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        env.close()
        after=source_manifest(); write('frozen_sources_after.json',after)
        changed=[p for p,h in hashes.items() if after.get(p)!=h]
        write('integrity.json',{'frozen_input_changes':changed,'frozen_model_sha256':sha(MODEL),'original_sources_unchanged':not changed})
        if changed:
            raise RuntimeError('Frozen source changed: '+repr(changed))


def main():
    global OUT
    p=argparse.ArgumentParser()
    p.add_argument('--out',required=True); p.add_argument('--seed',type=int,default=306517)
    p.add_argument('--variant',choices=('technical','clean'),default='technical')
    p.add_argument('--horizon',type=int,default=150); p.add_argument('--budget-seconds',type=int,default=600)
    p.add_argument('--probe',action='store_true')
    args=p.parse_args()
    OUT=Path(args.out).resolve(); OUT.mkdir(parents=True,exist_ok=False)
    lock=(OUT.parent/'pilot.lock').open('a'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    os.chdir(OUT)
    (OUT/'assets').mkdir(); (OUT/'assets/meshes_fixed').symlink_to(PROJECT/'training/assets/mkmini_real/meshes_fixed',target_is_directory=True)
    for key in ('XDG_CACHE_HOME','MESA_SHADER_CACHE_DIR','__GL_SHADER_DISK_CACHE_PATH'):
        os.environ[key]=str(OUT/'cache')
    os.environ['PYTHONDONTWRITEBYTECODE']='1'; os.environ['MUJOCO_GL']='egl'; os.environ['CUDA_VISIBLE_DEVICES']=''
    os.environ['OMP_NUM_THREADS']='1'; os.environ['OPENBLAS_NUM_THREADS']='1'
    # matplotlib can try to create a per-user cache on import.
    os.environ['MPLCONFIGDIR']=str(OUT/'cache/matplotlib')
    sys.addaudithook(write_guard)
    write('preregistration.json',{'experiment':'RP-P0B3','created_at':time.strftime('%F %T'),**vars(args),
                                 'frozen_sac':True,'training':False,'same_candidate_repetitions':3,
                                 'counterfactual_alternatives':2,'alternative_repetitions':2,
                                 'source_gate':'unknown geometry excluded before clean-map selection',
                                 'failure_policy':'stop counterfactual acquisition immediately on any replay mismatch',
                                 'files_policy':'only fresh isolated output; unchanged original code/models/XML',
                                 'same_state_strategy':'restore full API boundary and verify pre-selection decision-state identity'})
    def alarm(*_):
        raise BudgetExceeded('Foreground wall-clock budget exceeded; not a navigation outcome')
    signal.signal(signal.SIGALRM,alarm); signal.setitimer(signal.ITIMER_REAL,args.budget_seconds)
    started=time.monotonic()
    try:
        result=execute(args)
        write('completion.json',{'status':'FINISHED','elapsed_seconds':time.monotonic()-started,'gate':result['gate']})
    except ReplayMismatch as exc:
        write('failure.json',{'status':'REPLAY_GATE_FAIL','reason':str(exc),'counterfactual_acquisition_stopped':True,'traceback':traceback.format_exc()})
        event('REPLAY_GATE_FAIL',reason=str(exc))
        return 2
    except BudgetExceeded as exc:
        write('failure.json',{'status':'COMPUTE_CENSORED','reason':str(exc),'elapsed_seconds':time.monotonic()-started})
        event('COMPUTE_CENSORED',reason=str(exc)); return 124
    except Exception as exc:
        write('failure.json',{'status':'IMPLEMENTATION_ERROR','reason':repr(exc),'traceback':traceback.format_exc()})
        event('IMPLEMENTATION_ERROR',reason=repr(exc)); traceback.print_exc(); return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
    return 0


if __name__=='__main__':
    sys.exit(main())
