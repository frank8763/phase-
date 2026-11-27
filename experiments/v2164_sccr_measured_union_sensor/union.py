"""Current measured state owns sensor origins; private geometry never crosses packet boundary."""
from pathlib import Path
from contextlib import contextmanager
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,math,sys,types
R=Path(__file__).resolve().parents[2]
P6=R/'runtime/mk-mini/training/phase6_clean/envs/sensor_utils.py'
P14=R/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs/phase14_sensor_utils.py'
P7=R/'runtime/mk-mini/training/phase7_camera_depth/envs/camera_depth_utils.py'
P17=R/'runtime/mk-mini/training/phase17_fusion_safety_sac_nav/envs/mkmini_phase17c_lidar_camera_fusion_env.py'
BASE=R/'runtime/mk-mini/training/envs/mkmini_indoor_room_astar_sac_env.py'
METHODS=['RP-CCR','DWA','TEB','RPP','MPPI','SVG-MPPI','SCCR','PRIEST','PSF','PCBF']
SHIM='training.phase14_lidar_depth_nav.envs.phase14_sensor_utils'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def functions(path,names,np):
 nodes=[];tree=ast.parse(path.read_text())
 for n in names:
  found=[v for v in ast.walk(tree)if isinstance(v,ast.FunctionDef)and v.name==n];assert len(found)==1;nodes.append(copy.deepcopy(found[0]))
 space=dict(np=np,math=math);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),space)
 return SimpleNamespace(**{n:space[n]for n in names})
@contextmanager
def sensors(np):
 prior=sys.modules.get(SHIM);names=['wrap_angle','point_in_obstacle','ray_cast_distance','get_lidar_features','get_camera_goal_features']
 p6=functions(P6,names,np);p14=functions(P14,names,np);p7=functions(P7,['get_front_depth_camera_features','get_front_depth_summary'],np)
 p7.get_front_depth_camera_features.__globals__['ray_cast_distance']=p6.ray_cast_distance
 p17=functions(P17,['_phase17c_get_depth','_phase17c_depth_summary'],np);core=functions(BASE,['_point_hits_obstacle','_simulate_lidar'],np)
 m=types.ModuleType(SHIM)
 for n in names:setattr(m,n,getattr(p14,n))
 try:
  sys.modules[SHIM]=m;yield SimpleNamespace(p6=p6,p14=p14,p7=p7,p17=p17,core=core)
 finally:
  if prior is None:sys.modules.pop(SHIM,None)
  else:sys.modules[SHIM]=prior

def collect_saved_fixture(np,current,private_world,rendered24,route,previous,*,proof,actual_mode=False):
 assert not actual_mode,'SCCR_LIVE_UNION_NOT_QUALIFIED'
 assert set(current)=={'native','sim_time','body'}and type(current['native'])is int and current['native']>=0
 k=current['native'];assert abs(current['sim_time']-.01*k)<=1e-8
 assert set(private_world)=={'native','sim_time','bounds','rectangles','circles'}and private_world['native']==k and private_world['sim_time']==current['sim_time'],'PRIVATE_SENSOR_WORLD_STALE'
 assert private_world['bounds']==[-5.,5.]and set(route)=={'goal_xy','path_world','wp_index'}
 assert len(current['body'])==5 and all(math.isfinite(x)for x in current['body'])
 assert len(previous)==2 and all(math.isfinite(x)for x in previous)
 depth=np.asarray(rendered24,np.float32);assert depth.shape==(24,)and np.isfinite(depth).all()and((depth>=0)&(depth<=1)).all()
 xy=np.asarray(current['body'][:2],np.float32).copy();xy.setflags(write=False)
 rect=np.asarray(private_world['rectangles'],np.float32).reshape(-1,4).copy();circles=np.asarray(private_world['circles'],np.float32).reshape(-1,3).copy();assert np.isfinite(rect).all()and np.isfinite(circles).all()
 assert (rect[:,2:]>0).all()and(circles[:,2]>0).all();rect.setflags(write=False);circles.setflags(write=False)
 v=SimpleNamespace(map_min=-5.,map_max=5.,robot_xy=xy,robot_yaw=current['body'][2],goal_xy=np.asarray(route['goal_xy'],np.float32),rect_obstacles=rect,circle_obstacles=circles,lidar_num=36,lidar_range=5.,phase17c_depth_num_rays=15,phase17c_depth_max_range=3.)
 with sensors(np)as s:
  v._point_hits_obstacle=types.MethodType(s.core._point_hits_obstacle,v)
  core=s.core._simulate_lidar(v);lidar6=np.clip(s.p6.get_lidar_features(v,32,3.),0.,1.)
  lidar17=s.p14.get_lidar_features(v,32,3.);assert np.array_equal(lidar6,lidar17)
  d7=s.p7.get_front_depth_camera_features(v,15,90.,3.5);d17=s.p17._phase17c_get_depth(v)
 packet=dict(native=k,sim_time=current['sim_time'],body=list(current['body']),goal_xy=list(route['goal_xy']),path_world=copy.deepcopy(route['path_world']),wp_index=route['wp_index'],previous_body_command=list(previous),core_lidar36_raw_m=core.tolist(),rendered_depth24=depth.tolist(),phase6_lidar32=lidar6.tolist(),phase7_depth15=d7.tolist(),phase17_lidar32=lidar17.tolist(),phase17_depth15=d17.tolist(),producer_proof=dict(explicit_synthetic_fixture=True,saved_measured_input_fixture=True,actual_fresh_sensor=False,all_sensor_sources_qualified=False,no_hidden_actor_truth=True,equal_availability_all_ten_methods=True,native=k,measured_state_bound=True,input_provenance=copy.deepcopy(proof)))
 # Geometry/motion/state not whitelisted above must stay strictly producer-private.
 assert not any(x in packet for x in ['actor','actor_pose','actor_phase','rectangles','circles','private_world'])
 return packet

def consume_fixture(packet,method):
 assert method in METHODS
 allowed={'native','sim_time','body','goal_xy','path_world','wp_index','previous_body_command','core_lidar36_raw_m','rendered_depth24','phase6_lidar32','phase7_depth15','phase17_lidar32','phase17_depth15','producer_proof'}
 assert set(packet)==allowed and packet['producer_proof']['saved_measured_input_fixture']and not packet['producer_proof']['actual_fresh_sensor']
 return copy.deepcopy(packet)
