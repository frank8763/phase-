"""Evaluator-only original ray backend/noise, no belief or planner truth input."""
import ast,hashlib,math
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from phase14_sensor_utils import get_lidar_features,ray_cast_distance
repo=Path(__file__).resolve().parents[2]
source=repo/'runtime/home/mkmini_g11b_budget162_confirmatory_v1_1/g11b_budget162_confirmatory_v1.py'
names={'LIDAR_SIGMA_M','LIDAR_CLIP_M','LIDAR_DROPOUT','DEPTH_SIGMA_M','DEPTH_CLIP_M','DEPTH_DROPOUT'}
constants={}
for node in ast.parse(source.read_text()).body:
 if isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name)and target.id in names:constants[target.id]=ast.literal_eval(node.value)
assert set(constants)==names
def corrupt(raw,seed,idx,tag,maximum):
 raw=np.asarray(raw,np.float32);token=f'{seed}|{idx}|{tag}|{tuple(raw.shape)}'.encode();key=int.from_bytes(hashlib.sha256(token).digest()[:8],'little')&0x7fffffff;rng=np.random.default_rng(key);prefix=tag.upper()
 noise=np.clip(rng.normal(0.,constants[prefix+'_SIGMA_M'],raw.shape),-constants[prefix+'_CLIP_M'],constants[prefix+'_CLIP_M']).astype(np.float32);drop=rng.random(raw.shape)<constants[prefix+'_DROPOUT'];value=np.clip(np.clip(raw,0,1)*maximum+noise,0.,maximum);value[drop]=maximum
 return (value/maximum).astype(np.float32)
def packet(xy,yaw,when,step,protocol,motion,initial_noise_calls):
 env=SimpleNamespace(robot_xy=np.asarray(xy,np.float32),robot_yaw=float(yaw),map_min=-5.,map_max=5.,rect_obstacles=np.asarray(protocol['known_rectangles'],np.float32),circle_obstacles=np.asarray([*protocol['known_circles'],[*motion.xy(when),.10]],np.float32))
 raw_lidar=get_lidar_features(env,num_rays=32,max_range=3.);half=math.radians(70.)*.5;raw_depth=np.asarray([ray_cast_distance(env,yaw-half+2*half*i/14,3.,.08)/3. for i in range(15)],np.float32)
 return dict(step=int(step),time=float(when),xy=np.asarray(xy).tolist(),yaw=float(yaw),lidar=corrupt(raw_lidar,protocol['seed'],initial_noise_calls['lidar_call']+step,'lidar',3.).tolist(),depth=corrupt(raw_depth,protocol['seed'],initial_noise_calls['depth_call']+step,'depth',3.).tolist(),lidar_max_range=3.,depth_max_range=3.)
