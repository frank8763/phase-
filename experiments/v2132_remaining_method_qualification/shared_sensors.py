"""Explicit software-only sensor producer; consumer packets never expose geometry."""
import math,hashlib,json,copy
from types import SimpleNamespace
from pure_sources import original_sensors
METHODS=['RP-CCR','DWA','TEB','RPP','MPPI','SVG-MPPI','SCCR','PRIEST','PSF','PCBF']
def digest(z):return hashlib.sha256(json.dumps(z,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def capture_fixture(np,world,body,goal,native,sim_time,producer):
 assert type(native)is int and native>=0 and abs(sim_time-.01*native)<=1e-8
 assert len(body)==3 and len(goal)==2 and all(math.isfinite(x)for x in body+goal)
 assert set(world)=={'rectangles','circles','bounds'}and world['bounds']==[-5.,5.]
 env=SimpleNamespace(map_min=-5.,map_max=5.,robot_xy=np.array(body[:2],dtype=np.float32),robot_yaw=body[2],goal_xy=np.array(goal,dtype=np.float32),rect_obstacles=np.array(world['rectangles'],dtype=np.float32).reshape(-1,4),circle_obstacles=np.array(world['circles'],dtype=np.float32).reshape(-1,3),phase17c_depth_num_rays=15,phase17c_depth_max_range=3.)
 s=original_sensors(np)
 camera=np.clip(s.p6.get_camera_goal_features(env,90.,6.),-1.,1.)
 depth7=s.p7.get_front_depth_camera_features(env,15,90.,3.5);summary7=s.p7.get_front_depth_summary(depth7)
 depth17=s.p17._phase17c_get_depth(env);summary17=s.p17._phase17c_depth_summary(env,depth17)
 assert np.array_equal(s.p6.get_lidar_features(env,32,3.),s.p14.get_lidar_features(env,32,3.))
 assert np.array_equal(s.p6.get_camera_goal_features(env,90.,6.),s.p14.get_camera_goal_features(env,90.,6.))
 blocks=dict(phase6_camera_goal=camera.tolist(),phase7_depth_summary=np.r_[depth7,summary7].tolist(),phase17_camera_goal=camera.tolist(),phase17_depth_summary=np.r_[depth17,summary17].tolist())
 assert sum(len(v)for v in blocks.values())==50
 value=dict(schema='EQUAL_SIMULATED_CAMERA_DEPTH_SOFTWARE_FIXTURE_V1',software_fixture=True,actual_sensor_acquisition=False,native_tick=native,sim_time=sim_time,producer_source_sha256=producer,camera_semantics='PUBLIC_GOAL_DIRECTION_RANGE_FEATURE_NOT_RGB',depth_semantics='ORIGINAL_DISCRETE_RAYCAST_NOT_RENDERED_DEPTH_IMAGE',camera_depth_features=blocks,physical_authority=False)
 value['packet_sha256']=digest(value);return value
class Consumer:
 def __init__(self,method,producer):assert method in METHODS;self.method=method;self.producer=producer;self.last=-1
 def receive(self,packet,expected_native):
  assert packet['software_fixture']and not packet['physical_authority']and not packet['actual_sensor_acquisition']
  assert set(packet)=={'schema','software_fixture','actual_sensor_acquisition','native_tick','sim_time','producer_source_sha256','camera_semantics','depth_semantics','camera_depth_features','physical_authority','packet_sha256'}
  assert packet['producer_source_sha256']==self.producer and packet['native_tick']==expected_native>self.last and abs(packet['sim_time']-.01*expected_native)<=1e-8
  clean=dict(packet);h=clean.pop('packet_sha256');assert digest(clean)==h
  blocks=packet['camera_depth_features'];assert {k:len(v)for k,v in blocks.items()}==dict(phase6_camera_goal=5,phase7_depth_summary=20,phase17_camera_goal=5,phase17_depth_summary=20)
  assert all(math.isfinite(v)for b in blocks.values()for v in b)
  self.last=expected_native;return copy.deepcopy(blocks)
