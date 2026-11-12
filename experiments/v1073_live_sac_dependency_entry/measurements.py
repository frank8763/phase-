"""Sensor-only reconstruction of the frozen SAC observation modalities.

Only this backend sees physical obstacle geometry. Policies get ranges/depth
and public goal/reference data, never actor labels, anchor/axis/phase/future.
"""
import math,importlib.util
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
sensor=load('v1071_original_feature_sensor',R/'runtime/mk-mini/training/phase6_clean/envs/sensor_utils.py')
depth=load('v1071_original_depth_features',R/'runtime/mk-mini/training/phase7_camera_depth/envs/camera_depth_utils.py')
def depth24(image):
 image=np.asarray(image,float);assert image.shape==(64,64)and np.isfinite(image).all(),'REAL_FINITE_64_DEPTH_REQUIRED';image=np.clip(image,0,5);edges=np.linspace(0,64,9).astype(int);return np.asarray([image[max(0,r-3):min(64,r+4),edges[j]:edges[j+1]].mean()/5 for r in [int(64*.30),int(64*.50),int(64*.70)]for j in range(8)],np.float32)
def lidar36(s):
 distances=np.full(36,5.,np.float32)
 for i in range(36):
  angle=s.robot_yaw+2*math.pi*i/36
  for j in range(1,121):
   d=5*j/120;x=s.robot_xy[0]+d*math.cos(angle);y=s.robot_xy[1]+d*math.sin(angle)
   if sensor.point_in_obstacle(s,[x,y]):distances[i]=d;break
 return distances/5

def build_blocks(proxy,depth_image,waypoint_xy,previous_normalized_action,primary32=None):
 xy=np.asarray(proxy.robot_xy,float);goal=np.asarray(proxy.goal_xy,float);wp=np.asarray(waypoint_xy,float);previous=np.asarray(previous_normalized_action,np.float32);assert xy.shape==goal.shape==wp.shape==previous.shape==(2,)
 def relative(target):
  delta=target-xy;angle=sensor.wrap_angle(math.atan2(delta[1],delta[0])-proxy.robot_yaw);return [np.linalg.norm(delta)/10,angle/math.pi]
 base42=np.r_[lidar36(proxy),relative(goal),relative(wp),previous].astype(np.float32);assert base42.shape==(42,);base66=np.r_[base42,depth24(depth_image)].astype(np.float32);lidar=sensor.get_lidar_features(proxy,32,3.);camera=np.clip(sensor.get_camera_goal_features(proxy,90.,6.),-1.,1.);lidar=np.asarray(primary32 if primary32 is not None else lidar,np.float32);assert lidar.shape==(32,)and np.isfinite(lidar).all()and (lidar>=0).all()and(lidar<=1).all(),'PRIMARY_LIDAR_CONTRACT';safe=np.asarray([min(lidar),lidar[0],lidar[8],lidar[24]],np.float32);d7=depth.get_front_depth_camera_features(proxy,15,90.,3.5);d7sum=depth.get_front_depth_summary(d7)
 outer=np.asarray([sensor.ray_cast_distance(proxy,proxy.robot_yaw+math.radians(70)*(-.5+i/14),3.,.08)/3 for i in range(15)],np.float32);left,mid,right=outer[:5],outer[5:10],outer[10:];outer_summary=np.asarray([min(outer),np.mean(outer),min(left),min(mid),min(right)],np.float32)
 return dict(phase5_base=base66,lidar=lidar,camera_goal=camera,safety=safe,phase7_depth=d7,phase7_depth_summary=d7sum,outer_lidar=lidar.copy(),outer_camera_goal=camera.copy(),outer_depth=outer,outer_depth_summary=outer_summary)

class NativeMeasurements:
 def __init__(self,model,data,known,goal_xy,waypoint_xy,previous_normalized_action=(0.,0.),primary32_reader=None):
  import mujoco
  self.mj=mujoco;self.m=model;self.d=data;self.goal=np.asarray(goal_xy,float);self.waypoint=np.asarray(waypoint_xy,float);self.previous=np.asarray(previous_normalized_action,np.float32);self.renderer=mujoco.Renderer(model,height=64,width=64);self.primary32_reader=primary32_reader;self.camera='d435i_depth_camera';assert mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_CAMERA,self.camera)>=0,'REQUIRED_DEPTH_CAMERA_MISSING'
 def close(self):self.renderer.close()
 def read(self,vehicle):
  assert vehicle.m is self.m and vehicle.d is self.d,'SENSOR_MODEL_BINDING';before={k:np.asarray(getattr(self.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};stamp=float(self.d.time);tick=vehicle.count;rect=[];circles=[]
  for gid in range(self.m.ngeom):
   name=self.mj.mj_id2name(self.m,self.mj.mjtObj.mjOBJ_GEOM,gid)or''
   if not name.startswith(('real_rect_obs','real_circle_obs'))or(not self.m.geom_contype[gid]and not self.m.geom_conaffinity[gid]):continue
   xy=self.d.geom_xpos[gid,:2]
   if name.startswith('real_circle_obs'):circles.append([*xy,float(self.m.geom_size[gid,0])])
   else:
    rotation=self.d.geom_xmat[gid].reshape(3,3);assert abs(rotation[0,1])+abs(rotation[1,0])<1e-6,'NON_AXIS_ALIGNED_SENSOR_BOX_UNSUPPORTED';rect.append([*xy,*self.m.geom_size[gid,:2]])
  body=vehicle.body();proxy=SimpleNamespace(robot_xy=np.asarray(body[:2],np.float32),robot_yaw=float(body[2]),goal_xy=self.goal,map_min=-5.,map_max=5.,rect_obstacles=np.asarray(rect,np.float32).reshape(-1,4),circle_obstacles=np.asarray(circles,np.float32).reshape(-1,3))
  self.renderer.update_scene(self.d,camera=self.camera);self.renderer.enable_depth_rendering()
  try:image=np.asarray(self.renderer.render()).copy()
  finally:self.renderer.disable_depth_rendering()
  primary32=None if self.primary32_reader is None else self.primary32_reader(proxy,tick);blocks=build_blocks(proxy,image,self.waypoint,self.previous,primary32);assert vehicle.count==tick and float(self.d.time)==stamp and all(np.array_equal(v,np.asarray(getattr(self.d,k)))for k,v in before.items()),'OBSERVATION_MUTATED_STATE'
  return dict(native_tick=tick,sim_time=stamp,blocks=blocks,depth_image=image,scope='Real sensor-backend data; richer than the previous32-ray contract',policy_receives_no_obstacle_geometry=True)
