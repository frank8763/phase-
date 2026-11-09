"""Actual installed ROS message/publisher/planner construction, no vehicle or goal."""
import gzip,importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v911_periodic_causal_navigation'
class BlockModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','factory'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN')
sys.meta_path.insert(0,BlockModel())
import ros_worker
import rclpy
from rclpy.node import Node
sys.path.insert(0,str(C));from motion_publisher import MotionPublisher
sys.path.insert(0,str(C));from dynamic_proxy import DynamicPlannerProxy
rclpy.init();node=Node('phase_v911_zero_vehicle_probe');publisher=MotionPublisher(node,O)
try:
    scan=json.loads(gzip.decompress((O/'saved/SENSORS.json.gz').read_bytes()))[0];now=time.monotonic()
    packet=dict(scan=scan,phase='WAITING',native_tick=0,body=[*scan['xy'],scan['yaw'],0.,0.],scan_measured_at=now,sent_at=now,body_measured_at=now)
    publisher.observe(packet);publisher.publish();config=json.loads((C/'A_motion.yaml').read_text())
    proxy=DynamicPlannerProxy(node,lambda:packet,O,time.time()+120,publisher.planning_snapshot,json.loads(config['global_costmap']['global_costmap']['ros__parameters']['footprint']))
    _,source,body=proxy.forecast();assert source['source_native_tick']==body['native_tick']==0
    result=dict(passed=True,actual_ros_node_publisher_and_planner_constructed=True,planning_snapshot_same_transaction=True,vehicle_models=0,navigation_goals_sent=0,integrations=0)
    (O/'ROS_SOFTWARE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
finally:node.destroy_node();rclpy.shutdown()
