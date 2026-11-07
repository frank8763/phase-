"""Real Nav2 lifecycle exercise. Stationary synthetic ROS messages; no vehicle model."""
import json,math,os,sys,time,traceback
from pathlib import Path
import rclpy
from rclpy.node import Node
from lifecycle_msgs.srv import GetState
from nav2_msgs.srv import ManageLifecycleNodes
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from tf2_ros import TransformBroadcaster,StaticTransformBroadcaster
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v861_startup_gate'
sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'))
from ros_stack import Stack
NAMES=['map_server','planner_server','controller_server','behavior_server','velocity_smoother','collision_monitor','bt_navigator']
class Stationary(Node):
 def __init__(self):
  super().__init__('phase_startup_qualification');self.tf=TransformBroadcaster(self);self.static=StaticTransformBroadcaster(self);self.odom=self.create_publisher(Odometry,'odom',10);self.scan=self.create_publisher(LaserScan,'scan',10);self.count=0
  transforms=[]
  for parent,child in [('map','odom'),('base_link','base_scan')]:
   t=TransformStamped();t.header.stamp=self.get_clock().now().to_msg();t.header.frame_id=parent;t.child_frame_id=child;t.transform.rotation.w=1.;transforms.append(t)
  self.static.sendTransform(transforms);self.create_timer(.02,self.publish)
  self.states={name:self.create_client(GetState,name+'/get_state')for name in NAMES};self.manager=self.create_client(ManageLifecycleNodes,'lifecycle_manager_navigation/manage_nodes')
 def publish(self):
  stamp=self.get_clock().now().to_msg();t=TransformStamped();t.header.stamp=stamp;t.header.frame_id='odom';t.child_frame_id='base_link';t.transform.translation.x=-4.;t.transform.translation.y=-2.;t.transform.rotation.w=1.;self.tf.sendTransform(t);od=Odometry();od.header.stamp=stamp;od.header.frame_id='odom';od.child_frame_id='base_link';od.pose.pose.position.x=-4.;od.pose.pose.position.y=-2.;od.pose.pose.orientation.w=1.;self.odom.publish(od)
  if self.count%2==0:
   s=LaserScan();s.header.stamp=stamp;s.header.frame_id='base_scan';s.angle_min=0.;s.angle_max=2*math.pi*31/32;s.angle_increment=2*math.pi/32;s.range_min=.05;s.range_max=3.;s.scan_time=.04;s.ranges=[float('inf')]*32;self.scan.publish(s)
  self.count+=1
def spin_until(node,predicate,seconds):
 until=time.monotonic()+seconds
 while time.monotonic()<until:
  rclpy.spin_once(node,timeout_sec=.01)
  if predicate():return True
 return False
def state(node,name,timeout=3.):
 client=node.states[name];assert spin_until(node,client.service_is_ready,timeout),'SERVICE_NOT_DISCOVERED '+name
 start=time.monotonic();future=client.call_async(GetState.Request());assert spin_until(node,future.done,timeout),'STATE_RESPONSE_TIMEOUT '+name
 return dict(state=future.result().current_state.id,response_s=time.monotonic()-start)
def main():
 mode,slot=sys.argv[1:3];out=O/(mode+slot);out.mkdir(exist_ok=False);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:3]));rclpy.init();node=Stationary();stack=Stack(out,C/(mode+'.yaml'));start=time.monotonic();result=dict(passed=False,physical_vehicle_models=0,native_integrations=0,navigation_actions=0,synthetic_stationary_messages_only=True,mode=mode,slot=slot);rows=[]
 try:
  stack.start()
  if mode=='gated':
   for round_index in range(2):
    for name in NAMES:
     row=state(node,name);assert row['state']==1,'NODE_NOT_UNCONFIGURED '+name;rows.append(dict(name=name,round=round_index,**row))
   assert spin_until(node,node.manager.service_is_ready,3.),'MANAGER_NOT_READY';req=ManageLifecycleNodes.Request();req.command=0;future=node.manager.call_async(req);assert spin_until(node,future.done,20.),'MANAGER_STARTUP_TIMEOUT';assert future.result().success,'MANAGER_STARTUP_REJECTED'
  else:
   assert spin_until(node,lambda:node.states['bt_navigator'].service_is_ready(),8.),'NAVIGATOR_SERVICE_ABSENT'
   until=time.monotonic()+28
   while time.monotonic()<until:
    if state(node,'bt_navigator')['state']==3:break
    spin_until(node,lambda:False,.1)
   else:raise TimeoutError('ORIGINAL_AUTOSTART_NOT_ACTIVE_35S')
  final={name:state(node,name)for name in NAMES};assert all(v['state']==3 for v in final.values()),'NOT_ALL_SEVEN_ACTIVE';result.update(passed=True,all_managed_nodes=final,readiness_probes=rows,wall_s=time.monotonic()-start)
  # Negative gate: an unready state must not authorize a vehicle start.
  values=[v['state']for v in final.values()];assert all(v==3 for v in values);assert not all(v==3 for v in values[:-1]+[2]);result['inactive_node_negative_gate_rejected']=True
 except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc(),wall_s=time.monotonic()-start)
 finally:
  stack.close();node.destroy_node();rclpy.shutdown();(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
