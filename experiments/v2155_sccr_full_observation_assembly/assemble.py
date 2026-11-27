"""Original observation concatenation methods, explicit sensor-only providers.

No policy, renderer, simulator, map/actor geometry or inference is constructed.
All original blocks are supplied with provenance; missing blocks are refused.
"""
from pathlib import Path
import ast,copy,hashlib,math,types
R=Path(__file__).resolve().parents[2]
BASE=R/'runtime/mk-mini/training/envs/mkmini_indoor_room_astar_sac_env.py'
DEPTH=R/'runtime/mk-mini/training/envs/mkmini_real_indoor_phase3_depth_astar_sac_env.py'
PHASE6=R/'runtime/mk-mini/training/phase6_clean/envs/mkmini_phase6_lidar_camera_astar_sac_env.py'
PHASE7=R/'runtime/mk-mini/training/phase7_camera_depth/envs/mkmini_phase7_depth_camera_aux_env.py'
RESIDUAL=R/'runtime/mk-mini/training/phase7_residual_camera_aux/envs/mkmini_phase7_residual_camera_aux_env.py'
PHASE17=R/'runtime/mk-mini/training/phase17_fusion_safety_sac_nav/envs/mkmini_phase17c_lidar_camera_fusion_env.py'
SENSOR6=R/'runtime/mk-mini/training/phase6_clean/envs/sensor_utils.py'
SENSOR14=R/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs/phase14_sensor_utils.py'
SUMMARY7=R/'runtime/mk-mini/training/phase7_camera_depth/envs/camera_depth_utils.py'
FIELDS={'native','sim_time','body','goal_xy','path_world','wp_index','previous_body_command','core_lidar36_raw_m','rendered_depth24','phase6_lidar32','phase7_depth15','phase17_lidar32','phase17_depth15','producer_proof'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def method(path,name):return copy.deepcopy(next(x for x in ast.walk(ast.parse(path.read_text()))if isinstance(x,ast.FunctionDef)and x.name==name))
def function(path,name,space):
 node=method(path,name);scope=dict(space);exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),scope);return scope[name]
def builders(np):
 scope=dict(np=np,math=math)
 room_names=['_get_obs','_goal_distance','_goal_angle','_waypoint_xy','_waypoint_distance','_waypoint_angle','_update_waypoint','_wrap_angle']
 cls=ast.ClassDef(name='MkMiniIndoorRoomAStarSACEnv',bases=[ast.Name(id='object',ctx=ast.Load())],keywords=[],body=[method(BASE,n)for n in room_names],decorator_list=[])
 exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),str(BASE),'exec'),scope);room=scope[cls.name]
 cls=ast.ClassDef(name='MkMiniRealIndoorPhase3DepthAStarSACEnv',bases=[ast.Name(id=room.__name__,ctx=ast.Load())],keywords=[],body=[method(DEPTH,'_get_obs')],decorator_list=[])
 exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),str(DEPTH),'exec'),scope)
 wrap6=function(SENSOR6,'wrap_angle',scope);wrap14=function(SENSOR14,'wrap_angle',scope)
 cam6=function(SENSOR6,'get_camera_goal_features',dict(scope,wrap_angle=wrap6));cam14=function(SENSOR14,'get_camera_goal_features',dict(scope,wrap_angle=wrap14));summary7=function(SUMMARY7,'get_front_depth_summary',scope)
 return dict(room=room,depth=scope[cls.name],phase6=function(PHASE6,'_build_phase6_obs',scope),safety6=function(PHASE6,'_get_safety_feat',scope),phase7=function(PHASE7,'_build_phase7_obs',dict(scope,get_front_depth_summary=summary7)),make=function(RESIDUAL,'_make_obs',scope),phase17=function(PHASE17,'_phase17c_build_obs',scope),summary17=function(PHASE17,'_phase17c_depth_summary',scope),cam6=cam6,cam14=cam14)
def build(np,packet,base_action_provider,*,developer_fixture=False):
 assert set(packet)==FIELDS,'SCCR_MISSING_OR_PRIVATE_FEATURE_FIELD'
 k=packet['native'];assert type(k)is int and k>=0 and abs(packet['sim_time']-.01*k)<=1e-8
 proof=packet['producer_proof']
 if developer_fixture:assert proof['explicit_synthetic_fixture']and not proof['actual_fresh_sensor']
 else:assert proof['actual_fresh_sensor']and proof['all_sensor_sources_qualified']and proof['no_hidden_actor_truth']and proof['native']==k and proof['equal_availability_all_ten_methods']
 sizes={'body':5,'goal_xy':2,'previous_body_command':2,'core_lidar36_raw_m':36,'rendered_depth24':24,'phase6_lidar32':32,'phase7_depth15':15,'phase17_lidar32':32,'phase17_depth15':15}
 a={}
 for name,n in sizes.items():
  x=np.asarray(packet[name],np.float32);assert x.shape==(n,)and np.isfinite(x).all(),name;a[name]=x
 for name in ['rendered_depth24','phase6_lidar32','phase7_depth15','phase17_lidar32','phase17_depth15']:assert ((0<=a[name])&(a[name]<=1)).all(),name
 assert ((0<=a['core_lidar36_raw_m'])&(a['core_lidar36_raw_m']<=5)).all()
 path=np.asarray(packet['path_world'],np.float32);assert path.ndim==2 and path.shape[1]==2 and np.isfinite(path).all()and type(packet['wp_index'])is int
 f=builders(np);v=f['depth']();v.robot_xy=a['body'][:2];v.robot_yaw=float(a['body'][2]);v.goal_xy=a['goal_xy'];v.path_world=path;v.wp_index=packet['wp_index'];v.prev_action=a['previous_body_command'];v.lidar_range=5.
 v._simulate_lidar=lambda:a['core_lidar36_raw_m'].copy();v._get_depth_features=lambda:a['rendered_depth24'].copy()
 core=f['depth']._get_obs(v);assert core.shape==(66,)
 v._get_lidar=lambda:a['phase6_lidar32'].copy();v._get_camera_goal=lambda:f['cam6'](v,fov_deg=90.,max_range=6.);v._get_safety_feat=types.MethodType(f['safety6'],v)
 p6=f['phase6'](v,core);assert p6.shape==(107,)
 v._get_depth=lambda:a['phase7_depth15'].copy();p7=f['phase7'](v,p6);assert p7.shape==(127,)
 calls=[]
 def action(raw):
  assert raw.shape==(127,);value=np.asarray(base_action_provider(raw[:107].copy()),np.float32);assert value.shape==(2,)and np.isfinite(value).all()and (abs(value)<=1).all();calls.append(value.copy());return value
 v._base_action=action;base=f['make'](v,p7);assert base.shape==(129,)and len(calls)==1
 v._phase17c_get_lidar=lambda:a['phase17_lidar32'].copy();v._phase17c_get_camera_goal=lambda:f['cam14'](v,fov_deg=90.,max_range=6.);v._phase17c_get_depth=lambda:a['phase17_depth15'].copy();v._phase17c_depth_summary=types.MethodType(f['summary17'],v)
 obs=f['phase17'](v,base);assert obs.shape==(186,)and obs.dtype==np.float32 and np.isfinite(obs).all()
 return obs,dict(core66=core.tolist(),phase6_107=p6.tolist(),raw127=p7.tolist(),base_action_2=calls[0].tolist(),base129=base.tolist(),complete186=obs.tolist(),original_concatenation_methods_executed=True,original_raw_ray_and_renderer_producers_not_executed=True,Phase21_risk_fusion_and_actual_policy_not_qualified=True,physical_authority=False,explicit_base_provider_calls=1,developer_fixture=developer_fixture)
