"""Pure controller-only shared-route software prototype; never a plant driver."""
from __future__ import annotations
import ast,copy,hashlib,json,math,os
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2];OUT=R/'runs/v2173_sccr_inner_control_readout'
D=R/'runtime/mk-mini/training';sources={};seams=[]
W=D/'envs/mkmini_real_indoor_phase5_wheel_astar_sac_env.py'
S=D/'envs/mkmini_real_indoor_phase5_wheel_safe_astar_sac_env.py'
P=D/'envs/mkmini_real_indoor_phase5_wheel_residual_safe_astar_sac_env.py'
C=D/'envs/mkmini_real_indoor_phase5_wheel_corner_residual_safe_env.py'
F=D/'final_envs/mkmini_real_indoor_phase5_wheel_fast_corner_env_final_diff.py'
P9=D/'phase9_static_no_dynamic/envs/mkmini_phase9_static_no_dynamic_env.py'
P14=D/'phase14_lidar_depth_nav/envs/mkmini_phase14_phase9_yawsync_fast_nav_env.py'
I=D/'envs/mkmini_indoor_room_astar_sac_env.py'

def method(p,name):
 sources[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 ns=[n for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.FunctionDef)and n.name==name]
 assert len(ns)==1,(p,name)
 n=copy.deepcopy(ns[0]);seams.append({'source':str(p.relative_to(R)),'method':name,'line':n.lineno,'end_line':n.end_lineno,'AST_SHA256':hashlib.sha256(ast.dump(n).encode()).hexdigest()});return n

def stop_before_parent(p):
 n=method(p,'step')
 for i,x in enumerate(n.body):
  if isinstance(x,ast.Assign)and isinstance(x.value,ast.Call)and isinstance(x.value.func,ast.Attribute)and x.value.func.attr=='step':
   assert isinstance(x.value.func.value,ast.Call)and ast.unparse(x.value.func.value)=='super()'
   n.body=n.body[:i]+[ast.Return(value=x.value)];seams[-1]['split_before_parent_call_line']=x.lineno;return n
 raise AssertionError('NO_PARENT_STEP_SEAM')

class SnapshotBoundary:
 def _update_pose_from_mujoco(self):
  # Explicit read-only measured-state seam; no simulator or cached environment pose.
  assert self.snapshot_bound
 def _goal_distance(self):return float(np.linalg.norm(self.goal_xy-self.robot_xy))
 def _waypoint_distance(self):return self._goal_distance()
 def _simulate_lidar(self):return self.lidar36.copy()

def classes():
 nodes=[]
 def add(name,base,fns):nodes.append(ast.ClassDef(name=name,bases=[ast.Name(id=base,ctx=ast.Load())],keywords=[],body=fns,decorator_list=[]))
 wheel=[method(W,n)for n in ['_rate_limit','_ackermann_from_steer_speed','_apply_wheel_ctrl','_nearest_path_error']]
 n=method(W,'step');i=next(i for i,x in enumerate(n.body)if isinstance(x,ast.For));n.body=n.body[:i]+ast.parse("return {'virtual_steer_rad':steer_cmd,'virtual_wheel_rad_s':wheel_speed,'requested_motor_targets':[lf,rf,lr,rr],'rate_limited_motor_targets':self.data.ctrl.tolist()}").body;seams[-1]['split_before_physics_line']=method(W,'step').body[i].lineno;wheel.append(n)
 add('Wheel','SnapshotBoundary',wheel)
 add('Safe','Wheel',[method(S,n)for n in ['_sector_min','_lidar_clearance','_front_is_safe','_start_recovery','_is_danger_close','_recovery_action']]+[stop_before_parent(S)])
 add('Residual','Safe',[method(P,n)for n in ['_wrap_angle_local','_select_lookahead_point','_base_pursuit_action']]+[stop_before_parent(P)])
 add('Corner','Residual',[method(C,'_base_pursuit_action')])
 add('Fast','Corner',[method(F,n)for n in ['_base_pursuit_action','_is_danger_close','_recovery_action']])
 # Exact Phase9 prefix, return inner result instead of executing observation/reward tails.
 n=method(P9,'step');j=next(i for i,x in enumerate(n.body)if isinstance(x,ast.Assign)and isinstance(x.value,ast.Call)and ast.unparse(x.value.func)=='self.inner.step');seams[-1]['split_at_inner_step_line']=n.body[j].lineno;n.body=n.body[:j]+[ast.Return(value=n.body[j].value)]
 add('Outer','object',[method(P9,'_apply_turn35_params'),method(P14,'_phase14_set_if_exists'),method(P14,'_phase14_apply_p10p11_params'),n])
 g={'SnapshotBoundary':SnapshotBoundary,'np':np,'math':math}
 exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<original_controller_AST_prefixes>','exec'),g)
 return g['Fast'],g['Outer']
Fast,Outer=classes()

def literal_attributes(obj,p):
 n=method(p,'__init__')
 for x in n.body:
  if isinstance(x,ast.Assign)and len(x.targets)==1 and isinstance(x.targets[0],ast.Attribute)and isinstance(x.targets[0].value,ast.Name)and x.targets[0].value.id=='self':
   try:value=ast.literal_eval(x.value)
   except (ValueError,TypeError):continue
   if value is None or type(value)in(bool,str,int,float):setattr(obj,x.targets[0].attr,value)

def bind(packet,base):
 assert set(packet['producer_proof']) and packet['producer_proof']['no_hidden_actor_truth']
 for key,dim in [('body',5),('core_lidar36_raw_m',36),('goal_xy',2)]:
  a=np.asarray(packet[key],dtype=float);assert a.shape==(dim,)and np.isfinite(a).all(),'BAD_SNAPSHOT:'+key
 assert np.asarray(packet['path_world']).ndim==2 and len(packet['path_world'])>=2
 b=np.asarray(base,dtype=np.float32);assert b.shape==(2,)and np.isfinite(b).all()
 z=Fast() # This class has NO historical __init__, model, policy, renderer or engine.
 for p in [I,W,S,P,C,F]:literal_attributes(z,p)
 z.robot_xy=np.asarray(packet['body'][:2],dtype=np.float32);z.robot_yaw=float(packet['body'][2]);z.goal_xy=np.asarray(packet['goal_xy'],dtype=np.float32)
 z.path_world=np.asarray(packet['path_world'],dtype=np.float32);z.dense_path=z.path_world.copy();z.snapshot_bound=True
 z.lidar36=np.asarray(packet['core_lidar36_raw_m'],dtype=np.float32)
 z.data=SimpleNamespace(ctrl=np.zeros(4));z.model=SimpleNamespace(nu=4) # Explicit software arrays, NEVER MuJoCo objects.
 z.id_lf_steer,z.id_rf_steer,z.id_lr_wheel,z.id_rr_wheel=range(4)
 o=Outer();literal_attributes(o,P14)
 # Only two nonliteral Phase14 constructor assignments needed by its original setter.
 o.phase14_p10_straight_wheel=6.2*o.phase14_p10_speed_boost;o.phase14_p10_curve_wheel=4.2*o.phase14_p10_speed_boost
 o.inner=z;o.residual_scale=.06;o.max_steer_rad=math.radians(35);o.turn_after_body_ratio=.5;o.speed_boost=1.15
 o.last_raw_obs=None;o._base_action=lambda _:b.copy()
 o._apply_smooth_ref_path=lambda:None # Declared common validated route substitution, not original smoothing.
 o._phase14_targets=lambda:[o,z]
 o._phase14_apply_p10p11_params()
 return o,z

def evaluate(packet,base,residual):
 o,z=bind(packet,base);a=np.asarray(residual,dtype=np.float32);assert a.shape==(2,)and np.isfinite(a).all()
 # Exact original Phase14 action scaling before Phase9.step; no poststep state sync.
 scaled=np.clip(a,-1.,1.)*float(o.phase14_assist_scale)
 result=o.step(scaled)
 steer=result['virtual_steer_rad'];wheel=result['virtual_wheel_rad_s'];v=wheel*z.wheel_radius;w=v*math.tan(steer)/z.wheel_base
 result.update(source_default_effective_parameters={k:getattr(z,k)for k in ['max_steer','max_wheel_speed','max_steer_delta','max_wheel_delta','wheel_base','wheel_radius','track_width','diff_gain','lookahead']},
               conditional_virtual_bicycle_twist=[v,w],common_raw_domain_passed=(abs(v)<=.100001 and abs(w)<=abs(v)/1.32+1e-6 and not(abs(v)<.005 and abs(w)>1e-6)),
               recovery_stage=z.recovery_stage,rate_memory=[z.last_lf_steer,z.last_rf_steer,z.last_lr_wheel,z.last_rr_wheel],
               outer_mixed_inner_input=o.last_final_action.tolist(),not_issued_to_physics=True,
               computed_virtual_bicycle_twist_not_actual_body_velocity=True)
 return result,z

def main():
 assert os.sched_getaffinity(0)=={0} and not(OUT/'RESULT.json').exists()
 rows=[];inputs={}
 prior=R/'runs/v2170_sccr_live_source_scope/components/SCCR/actual'
 for tick in [0,5,10]:
  f=prior/f'SCCR_UNION_{tick:06d}.json';inputs[str(f.relative_to(R))]=hashlib.sha256(f.read_bytes()).hexdigest();a=json.loads(f.read_text())
  y,z=evaluate(a['sensor_packet'],a['assembly']['base_action_2'],a['residual_action']);rows.append({'native':tick,'result':y})
  assert np.max(np.abs(z.data.ctrl[:2]))<=z.max_steer_delta+1e-12 and np.max(np.abs(z.data.ctrl[2:]))<=z.max_wheel_delta+1e-12
 # Independent nonzero Ackermann/rate-limit identities, preserving native diff_gain.
 p=json.loads((prior/'SCCR_UNION_000000.json').read_text())['sensor_packet'];o,z=bind(p,[0.,0.])
 tests=[]
 for steer,wheel in [(0.,2.),(.2,2.),(-.2,2.),(.2,-2.)]:
  lf,rf,lr,rr=z._ackermann_from_steer_speed(steer,wheel)
  if steer==0:assert [lf,rf,lr,rr]==[0.,0.,wheel,wheel]
  else:
   v=wheel*z.wheel_radius;omega=v*math.tan(steer)/z.wheel_base
   assert abs((rr-lr)*z.wheel_radius/z.track_width-z.diff_gain*omega)<1e-12
   assert lf*steer>0 and rf*steer>0
  tests.append({'steer_rad':steer,'wheel_rad_s':wheel,'motor_targets':[lf,rf,lr,rr]})
 # Front blockage must invoke original Fast recovery, rather than treating positive residual as permission.
 blocked=copy.deepcopy(p);blocked['core_lidar36_raw_m']=[3.]*36;blocked['core_lidar36_raw_m'][0]=.1
 b,z=evaluate(blocked,[.9,.94],[.7,1.]);assert b['recovery_stage']=='BACKUP' and b['virtual_wheel_rad_s']<0
 rejects=[]
 for label in ['short','nonfinite']:
  bad=copy.deepcopy(p)
  if label=='short':bad['core_lidar36_raw_m']=bad['core_lidar36_raw_m'][:-1]
  else:bad['body'][0]=float('nan')
  try:evaluate(bad,[.9,.94],[.7,1.])
  except AssertionError:rejects.append(label)
  else:raise AssertionError('INVALID_SNAPSHOT_ACCEPTED')
 r=dict(passed=True,closed=True,scope='PURE_INNER_CONTROL_SHARED_ROUTE_SOFTWARE_PROTOTYPE',saved_frames=rows,ackermann_equation_cases=tests,
        blocked_recovery_negative=b,rejected_inputs=rejects,source_sha256=sources,input_sha256=inputs,source_prefixes=seams,
        read_only_snapshot_and_shared_route_adapters_explicit=True,historical_runtime_configuration_equivalence=False,
        omitted=['upstream V3 detour/path selection','domain randomization/action noise','historical path smoothing','all environment/model constructors','poststep vehicle state corrections','actual engine and sensor observations after control'],
        source_default_virtual_twist_exceeds_common_domain=any(not q['result']['common_raw_domain_passed']for q in rows),
        learned_policy_inference_models_renderers_physics_replay_audit_source_claims_formal_samples=0,
        common_plant_controller_adaptation_qualified=False,native_full_SCCR_qualified=False,
        not_actual_body_or_plant_commands=True)
 raw=json.dumps(r,indent=2,allow_nan=False)+'\n';assert len(raw.encode())<128*1024;(OUT/'RESULT.json').write_text(raw)
 print(json.dumps({'passed':True,'saved_frames':3,'nonzero_Ackermann_cases':len(tests),'recovery_negative':True,'new_models_or_physics':0,'raw_domain_mismatch':r['source_default_virtual_twist_exceeds_common_domain']}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  (OUT/'FAILED_ATTEMPT.json').write_text(json.dumps({'type':type(e).__name__,'first_error':str(e),'new_NN_or_physics':0})+'\n');raise
