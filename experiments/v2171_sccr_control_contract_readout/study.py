"""Bounded saved-input/source arithmetic only; no simulator or policy imports."""
from __future__ import annotations
import ast
import copy
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
from types import SimpleNamespace
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'runs/v2171_sccr_control_contract_readout'
V2 = ROOT/'runtime/mk-mini/training/phase21_risk_switch_fusion_sac/envs/mkmini_phase21_v2_corridor_detect_control_failed.py'
P14 = ROOT/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs/mkmini_phase14_phase9_yawsync_fast_nav_env.py'
P9 = ROOT/'runtime/mk-mini/training/phase9_static_no_dynamic/envs/mkmini_phase9_static_no_dynamic_env.py'
SHIELD = ROOT/'runtime/mk-mini/training/phase17_fusion_safety_sac_nav/envs/mkmini_phase17b_safety_shield_env.py'
PRIOR = ROOT/'runs/v2170_sccr_live_source_scope/components/SCCR/actual'
SOURCES = {}
EXTRACTED = []

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def method(path, name):
    SOURCES[str(path.relative_to(ROOT))] = sha(path)
    tree = ast.parse(path.read_text())
    nodes = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(nodes) == 1, (path, name)
    n = copy.deepcopy(nodes[0])
    EXTRACTED.append({'source':str(path.relative_to(ROOT)), 'method':name, 'line':n.lineno, 'end_line':n.end_lineno,
                      'AST_sha256':hashlib.sha256(ast.dump(n, include_attributes=False).encode()).hexdigest()})
    return n

def defaults(path):
    n = method(path, '__init__')
    r = {}
    for a,d in zip(n.args.args[-len(n.args.defaults):],n.args.defaults):
        try: r[a.arg] = ast.literal_eval(d)
        except (ValueError, TypeError): pass
    for a,d in zip(n.args.kwonlyargs, n.args.kw_defaults):
        if d is not None:
            try: r[a.arg] = ast.literal_eval(d)
            except (ValueError, TypeError): pass
    return r

def make_class(name, nodes):
    c = ast.ClassDef(name=name,bases=[],keywords=[],body=nodes,decorator_list=[])
    m = ast.fix_missing_locations(ast.Module(body=[c],type_ignores=[]))
    g = {'np':np,'math':math,'Any':object}
    exec(compile(m, '<extracted_original_source>', 'exec'),g)
    return g[name]

def validate_packet(p):
    allowed = {'native','sim_time','body','goal_xy','path_world','wp_index','previous_body_command','rendered_depth24',
               'core_lidar36_raw_m','phase6_lidar32','phase7_depth15','phase17_lidar32','phase17_depth15','producer_proof'}
    assert set(p) == allowed, 'UNREGISTERED_PACKET_FIELD'
    for k,n in [('body',5),('phase17_lidar32',32),('phase17_depth15',15)]:
        x = np.asarray(p[k],dtype=np.float64)
        assert x.shape == (n,) and np.isfinite(x).all(), 'INVALID_SENSOR_DIMENSION_OR_FINITE'
        if k != 'body': assert ((x >= 0)&(x <= 1)).all(), 'INVALID_NORMALIZED_SENSOR'
    path = np.asarray(p['path_world'],dtype=np.float64)
    assert path.ndim == 2 and path.shape[1] == 2 and len(path)>=2 and np.isfinite(path).all()

NAMES=['_phase17_try_get_lidar','_phase17_lidar_sectors','_phase17_apply_safety_shield',
       '_phase21_get_future_path','_phase21_sensor_points','_phase21_point_segment_distances',
       '_phase21_compute_corridor_state']
Risk = make_class('OriginalRiskReadout',[method(V2,n) for n in NAMES])
v2_defaults=defaults(V2); shield_defaults=defaults(SHIELD); p9_defaults=defaults(P9)
p14_init=method(P14,'__init__')
p14_defaults={}
for n in p14_init.body:
    if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Attribute):
        try:p14_defaults[n.targets[0].attr]=ast.literal_eval(n.value)
        except (ValueError,TypeError):pass

def shell(p):
    validate_packet(p)
    s=Risk()
    for k,v in v2_defaults.items():setattr(s,k,v)
    for k,v in shield_defaults.items():setattr(s,k,v)
    s.phase21_corridor_radius=.28+s.phase21_corridor_margin
    s.phase21_last_steer_direction=0.
    s.robot_xy=np.array(p['body'][:2],dtype=np.float32)
    s.robot_yaw=float(p['body'][2])
    s.phase17c_last_lidar=np.array(p['phase17_lidar32'],dtype=np.float32)
    s.phase17c_last_depth=np.array(p['phase17_depth15'],dtype=np.float32)
    s.phase17c_lidar_max_range=3.;s.phase17c_depth_max_range=3.
    s.get_phase14_smooth_path=lambda:np.array(p['path_world'],dtype=np.float32)
    return s

# Source-exact action scaling and contiguous additive-mix prefix only.
p14_step=method(P14,'step')
scale_nodes=p14_step.body[1:3]
assert [n.targets[0].id for n in scale_nodes]==['raw_action','safe_action']
p9_step=method(P9,'step')
start=next(i for i,n in enumerate(p9_step.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='action')
end=next(i for i,n in enumerate(p9_step.body) if isinstance(n,ast.Try))
mix_nodes=p9_step.body[start:end]
assert 'base_action = self._base_action(self.last_raw_obs)' in ast.unparse(ast.Module(body=mix_nodes,type_ignores=[]))
clip_forward=next(n for n in p9_step.body if isinstance(n,ast.Assign) and ast.unparse(n)=='final_action[1] = np.clip(final_action[1], 0.0, 1.0)')

def conditional_mix(base, residual):
    s=SimpleNamespace(phase14_assist_scale=p14_defaults['phase14_assist_scale'],
                      residual_scale=p9_defaults['residual_scale'],speed_boost=p9_defaults['speed_boost'],
                      last_raw_obs=None,_base_action=lambda _:np.array(base,dtype=np.float32))
    g={'np':np,'self':s,'action':np.array(residual,dtype=np.float32)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(scale_nodes),type_ignores=[])),'<phase14_scale_prefix>','exec'),g)
    g['action']=g['safe_action']
    exec(compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(mix_nodes+[clip_forward]),type_ignores=[])),'<phase9_mix_prefix>','exec'),g)
    return g['final_action'].tolist()


def clean(x):
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    if isinstance(x,np.generic):return clean(x.item())
    if isinstance(x,float) and not math.isfinite(x):return None
    return x


def main():
    assert os.sched_getaffinity(0)=={0}
    assert not (OUT/'RESULT.json').exists(), 'READOUT_ALREADY_CLOSED_NO_RERUN'
    inputs={}; rows=[]
    for tick in [0,5,10]:
        f=PRIOR/f'SCCR_UNION_{tick:06d}.json';inputs[str(f.relative_to(ROOT))]=sha(f)
        a=json.loads(f.read_text());p=a['sensor_packet'];s=shell(p)
        s._phase21_compute_corridor_state()
        r=a['residual_action']; b=a['assembly']['base_action_2']
        shield=s._phase17_apply_safety_shield(r)
        rows.append({'native':tick,'original_risk':s.phase21_last_risk,'conflicts':s.phase21_last_conflict_count,
                     'min_path_clearance_m':s.phase21_last_min_path_clearance,'nearest_forward_m':s.phase21_last_nearest_forward,
                     'side':s.phase21_last_obstacle_side,'normalized_sectors':s._phase17_lidar_sectors(s.phase17c_last_lidar),
                     'recorded_phase6_action':b,'recorded_186_residual':r,'shielded_residual':shield.tolist(),
                     'shield_reason':s.phase17_shield_reason,'conditional_unshielded_inner_input':conditional_mix(b,r),
                     'conditional_shielded_inner_input':conditional_mix(b,shield),
                     'not_body_v_omega_or_motor_command':True,'V3_detour_and_inner_pursuit_not_executed':True})
    p=json.loads((PRIOR/'SCCR_UNION_000000.json').read_text())['sensor_packet']
    synthetic=[]
    for label,obstruction in [('front_stop',0),('rear_does_not_trigger_front',16),('left_escape',0),('right_escape',0),('clear',None)]:
        s=shell(p);s.phase17c_last_lidar=np.ones(32,dtype=np.float32)
        if obstruction is not None:s.phase17c_last_lidar[obstruction]=.1
        if label=='left_escape':s.phase17c_last_lidar[3]=.2
        if label=='right_escape':s.phase17c_last_lidar[27]=.2
        out=s._phase17_apply_safety_shield([.2,.8])
        if label in ['front_stop','left_escape','right_escape']:assert out[1]==np.float32(-.15) and s.phase17_shield_active
        if label=='left_escape':assert out[0]<0
        if label=='right_escape':assert out[0]>0
        if label in ['clear','rear_does_not_trigger_front']:assert np.array_equal(out,np.array([.2,.8],dtype=np.float32)) and not s.phase17_shield_active
        synthetic.append({'case':label,'action':out.tolist(),'reason':s.phase17_shield_reason})
    rejected=[]
    for label in ['short','nonfinite','hidden_truth','out_of_range']:
        q=copy.deepcopy(p)
        if label=='short':q['phase17_lidar32']=q['phase17_lidar32'][:-1]
        if label=='nonfinite':q['phase17_depth15'][0]=float('nan')
        if label=='hidden_truth':q['actor_truth']=[0.,0.]
        if label=='out_of_range':q['phase17_lidar32'][0]=1.01
        try:validate_packet(q)
        except AssertionError as e:rejected.append({'case':label,'rejected':True,'reason':str(e)})
        else:raise AssertionError('NEGATIVE_ACCEPTED:'+label)
    # A residual-only shield does not, by itself, certify the downstream command.
    counterexample=conditional_mix([.9,.94],[-.35,-.15])
    assert counterexample[1]==1.0
    Sync=make_class('OriginalSyntheticStateSync',[method(P14,'_phase14_wrap_angle'),method(P14,'_phase14_apply_bicycle_yaw_sync')])
    w=Sync()
    for k,v in p14_defaults.items():setattr(w,k,v)
    qpos=np.array([0.,0.,0.,1.,0.,0.,0.]);qvel=np.zeros(6)
    target=SimpleNamespace(data=SimpleNamespace(qpos=qpos,qvel=qvel),model=object(),dt=.02)
    w._phase14_targets=lambda:[target];w._phase14_get_ctrl_steer_wheel=lambda:(.2,6.)
    before=(qpos.copy(),qvel.copy());w._phase14_apply_bicycle_yaw_sync()
    assert np.linalg.norm(qpos[:2]-before[0][:2])>0 and qvel[5]!=0
    witness={'explicit_synthetic_arrays_not_plant':True,'new_physics_steps':0,'qpos_before':before[0].tolist(),
             'qpos_after':qpos.tolist(),'qvel_after':qvel.tolist(),'displacement_m':float(np.linalg.norm(qpos[:2]-before[0][:2])),
             'original_step_calls_post_parent_sync':any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='_phase14_apply_bicycle_yaw_sync' for n in ast.walk(p14_step))}
    assert witness['original_step_calls_post_parent_sync']
    result={'passed':True,'scope':'SAVED_SENSOR_RISK_SHIELD_AND_CONDITIONAL_ACTION_CONTRACT_ONLY',
            'created_at':datetime.datetime.now().astimezone().isoformat(),'source_sha256':SOURCES,'input_sha256':inputs,'extracted_methods':EXTRACTED,
            'source_defaults_only':{'v2':v2_defaults,'shield':shield_defaults,'phase9':p9_defaults,'phase14':p14_defaults,
                                   'corridor_robot_radius_fallback':.28,'registered_sensor_ranges_m':[3.,3.]},
            'saved_frames':rows,'synthetic_shield_cases':synthetic,'input_negative_cases':rejected,
            'residual_only_stop_counterexample':{'phase6_base':[.9,.94],'shielded_residual':[-.35,-.15],
                 'conditional_inner_input':counterexample,'not_full_controller_or_motor_command':True},
            'synthetic_original_state_mutation_witness':witness,
            'native_full_environment_compatible_with_common_no_state_injection_plant':False,
            'prospective_controller_only_adaptation_requires_new_identity_and_complete_control_qualification':True,
            'omissions':['original upstream action noise/control domain randomization and runtime configuration',
                         'V3 path trigger/detour generation','inner pure-pursuit/recovery/steering limits/rate limits',
                         'final wheel and Ackermann mapping','common physical/predicted/actuator feasibility gates'],
            'new_calls':{'policy_inference':0,'learned_model_load':0,'renderer':0,'physical_model':0,'NLP':0,'physics':0,'replay':0,'physical_audit':0,'source_claim':0,'formal_samples':0},
            'formal_120_unchanged':{'closed':72,'whole':7,'unexecuted':48},'full_SCCR_navigation_qualified':False}
    payload=json.dumps(clean(result),indent=2,allow_nan=False)+'\n'
    assert len(payload.encode())<512*1024
    (OUT/'RESULT.json').write_text(payload)
    print(json.dumps({'passed':True,'saved_frames':len(rows),'shield_cases':len(synthetic),'rejected_inputs':len(rejected),
                      'native_environment_common_plant_compatible':False,'new_policy_or_physics':0}))

if __name__=='__main__':
    try:main()
    except BaseException as e:
        (OUT/'FAILED_ATTEMPT.json').write_text(json.dumps({'type':type(e).__name__,'error':str(e),'new_NN_or_physics':0})+'\n')
        raise
