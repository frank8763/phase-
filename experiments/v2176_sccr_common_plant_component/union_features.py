"""Pure registered ray/noise profile; private world stays inside the producer."""
from pathlib import Path
from types import SimpleNamespace
import ast,hashlib,importlib.util,sys,math,copy
R=Path(__file__).resolve().parents[2]
PURE=R/'experiments/v2164_sccr_measured_union_sensor/union.py'
NOISE=R/'experiments/v733_early_low_translation_scan/sensor_model.py'
CONSTANTS=R/'runtime/home/mkmini_g11b_budget162_confirmatory_v1_1/g11b_budget162_confirmatory_v1.py'
def load(n,p):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def corruption(np):
 names={'LIDAR_SIGMA_M','LIDAR_CLIP_M','LIDAR_DROPOUT','DEPTH_SIGMA_M','DEPTH_CLIP_M','DEPTH_DROPOUT'};values={}
 for node in ast.parse(CONSTANTS.read_text()).body:
  if isinstance(node,ast.Assign):
   for target in node.targets:
    if isinstance(target,ast.Name)and target.id in names:values[target.id]=ast.literal_eval(node.value)
 assert set(values)==names
 fn=next(x for x in ast.parse(NOISE.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='corrupt');space=dict(np=np,hashlib=hashlib,constants=values);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(NOISE),'exec'),space);return space['corrupt']
def blocks(np,measured,world,scan,seed,noise_base):
 assert set(measured)=={'native','sim_time','body'}and set(world)=={'native','sim_time','bounds','rectangles','circles'}
 k=measured['native'];assert type(k)is int and k>=0 and k%5==0 and world['native']==scan['native_tick']==k and world['sim_time']==measured['sim_time']==scan['time']and abs(measured['sim_time']-.01*k)<=1e-8
 assert world['bounds']==[-5.,5.]and len(measured['body'])==5 and len(scan['ranges'])==32
 assert all(math.isfinite(x)for x in measured['body']+scan['ranges'])and all(0<=x<=3 for x in scan['ranges'])
 kwargs=dict(map_min=-5.,map_max=5.,rect_obstacles=np.asarray(world['rectangles'],np.float32).reshape(-1,4),circle_obstacles=np.asarray(world['circles'],np.float32).reshape(-1,3),lidar_num=36,lidar_range=5.,phase17c_depth_num_rays=15,phase17c_depth_max_range=3.)
 view=SimpleNamespace(**kwargs,robot_xy=np.asarray(measured['body'][:2],np.float32),robot_yaw=float(measured['body'][2]))
 sensor=SimpleNamespace(**kwargs,robot_xy=np.asarray(scan['xy'],np.float32),robot_yaw=float(scan['yaw']))
 pure=load('source_exact_registered_union_rays',PURE);corrupt=corruption(np)
 with pure.sensors(np)as source:
  import types
  view._point_hits_obstacle=types.MethodType(source.core._point_hits_obstacle,view)
  core=source.core._simulate_lidar(view);p6=source.p6.get_lidar_features(view,32,3.);d7=source.p7.get_front_depth_camera_features(view,15,90.,3.5)
  raw32=source.p14.get_lidar_features(sensor,32,3.);p17=corrupt(raw32,seed,noise_base['lidar_call']+k//5,'lidar',3.)
  raw15=source.p17._phase17c_get_depth(sensor);d17=corrupt(raw15,seed,noise_base['depth_call']+k//5,'depth',3.)
 assert np.array_equal(p17*3.,np.asarray(scan['ranges'],np.float32)),'FULL_UNION_PRIMARY_SCAN_NOISE_OR_WORLD_MISMATCH'
 result=dict(core_lidar36_raw_m=core.tolist(),phase6_lidar32=p6.tolist(),phase7_depth15=d7.tolist(),phase17_lidar32=p17.tolist(),phase17_depth15=d17.tolist())
 for name,n in [('core_lidar36_raw_m',36),('phase6_lidar32',32),('phase7_depth15',15),('phase17_lidar32',32),('phase17_depth15',15)]:assert len(result[name])==n and np.isfinite(np.asarray(result[name])).all()
 return result,dict(primary32_measured_meters_byte_exact=True,lidar_noise_index=noise_base['lidar_call']+k//5,depth_noise_index=noise_base['depth_call']+k//5,registered_phase17_cadence='original_initial_counter_plus_native_div5',original_noise_corruption_source=True,full_historical_wrapper_call_cadence_identity_not_claimed=True)
