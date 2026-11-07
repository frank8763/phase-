"""Nonphysical analytic ROS interface smoke. Never evidence of vehicle safety/arrival."""
import json,math,os,sys,time,traceback
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist,TransformStamped
from nav_msgs.msg import Odometry,Path as NavPath
from sensor_msgs.msg import LaserScan
from nav2_msgs.action import NavigateToPose
from lifecycle_msgs.srv import GetState
from tf2_ros import TransformBroadcaster,StaticTransformBroadcaster
from ros_stack import Stack
C=Path(__file__).parent;R=C.parents[1];OUT=R/'runs/v856_nav2_foundation'
class Bridge(Node):
    def __init__(self,out):
        super().__init__('phase_nonphysical_smoke');self.out=out;self.x=-3.;self.y=0.;self.yaw=0.;self.v=0.;self.w=0.;self.cmd_at=-1.;self.last=time.monotonic();self.commands=[];self.nav_commands=[];self.plans=0;self.trace=[]
        self.tf=TransformBroadcaster(self);self.static=StaticTransformBroadcaster(self)
        for parent,child in [('map','odom'),('base_link','base_scan')]:
            t=TransformStamped();t.header.stamp=self.get_clock().now().to_msg();t.header.frame_id=parent;t.child_frame_id=child;t.transform.rotation.w=1.;self.static.sendTransform(t)
        self.odom=self.create_publisher(Odometry,'odom',10);self.scan=self.create_publisher(LaserScan,'scan',qos_profile_sensor_data)
        self.create_subscription(Twist,'cmd_vel',self.command,10);self.create_subscription(Twist,'cmd_vel_nav',lambda m:self.nav_commands.append([time.monotonic(),m.linear.x,m.angular.z]),10)
        self.create_subscription(NavPath,'plan',lambda m:setattr(self,'plans',self.plans+1),10)
        self.create_timer(.01,self.tick);self.action=ActionClient(self,NavigateToPose,'navigate_to_pose');self.lifecycle=self.create_client(GetState,'bt_navigator/get_state');self.state_future=None;self.active=False
    def command(self,m):self.v=m.linear.x;self.w=m.angular.z;self.cmd_at=time.monotonic();self.commands.append([self.cmd_at,self.v,self.w])
    def tick(self):
        now=time.monotonic();dt=min(now-self.last,.05);self.last=now
        v,w=(self.v,self.w)if now-self.cmd_at<.2 else(0.,0.)
        self.x+=v*math.cos(self.yaw)*dt;self.y+=v*math.sin(self.yaw)*dt;self.yaw+=w*dt
        stamp=self.get_clock().now().to_msg();t=TransformStamped();t.header.stamp=stamp;t.header.frame_id='odom';t.child_frame_id='base_link';t.transform.translation.x=self.x;t.transform.translation.y=self.y;t.transform.rotation.z=math.sin(self.yaw/2);t.transform.rotation.w=math.cos(self.yaw/2);self.tf.sendTransform(t)
        od=Odometry();od.header.stamp=stamp;od.header.frame_id='odom';od.child_frame_id='base_link';od.pose.pose.position.x=self.x;od.pose.pose.position.y=self.y;od.pose.pose.orientation=t.transform.rotation;od.twist.twist.linear.x=v;od.twist.twist.angular.z=w;self.odom.publish(od)
        if len(self.trace)%5==0:
            s=LaserScan();s.header.stamp=stamp;s.header.frame_id='base_scan';s.angle_min=-math.pi;s.angle_max=math.pi-2*math.pi/32;s.angle_increment=2*math.pi/32;s.range_min=.05;s.range_max=3.;s.scan_time=.05;s.ranges=[float('inf')]*32;self.scan.publish(s)
        self.trace.append([now,self.x,self.y,self.yaw,v,w])
        if len(self.trace)%100==0:
            p=self.out/'PARTIAL.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(dict(wall_monotonic=now,pose=[self.x,self.y,self.yaw],goal_distance_m=math.hypot(self.x-3,self.y),commands=len(self.commands),plans=self.plans)));tmp.replace(p)
def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
    start=time.monotonic();result={'test_type':'NONPHYSICAL_GENUINE_NAV2_INTERFACE_SMOKE','model_initializations':0,'physics_integrations':0,'dynamic_acceptance':False};(out/'START.json').write_text(json.dumps(dict(pid=os.getpid(),started_unix=time.time(),wall_limit_s=180,model_initializations=0)));stack=Stack(out,C/'phase_nav2_params.yaml');node=None;rclpy.init()
    try:
        node=Bridge(out);stack.start();future=None;accepted=False;goal_sent=False
        while time.monotonic()-start<180 and time.time()<1794052800:
            rclpy.spin_once(node,timeout_sec=.01)
            if stack.failed():raise RuntimeError('NAV2_SERVER_EXIT '+str(stack.failed()))
            if not goal_sent and time.monotonic()-start>30:raise RuntimeError('NAV2_ACTIVATION_30S_TIMEOUT')
            if node.state_future is not None and node.state_future.done():
                node.active=node.state_future.result().current_state.id==3;node.state_future=None
            if not node.active and node.state_future is None and node.lifecycle.service_is_ready():node.state_future=node.lifecycle.call_async(GetState.Request())
            if not goal_sent and node.active and node.action.server_is_ready():
                g=NavigateToPose.Goal();g.pose.header.frame_id='map';g.pose.header.stamp=node.get_clock().now().to_msg();g.pose.pose.position.x=3.;g.pose.pose.orientation.w=1.;future=node.action.send_goal_async(g);goal_sent=True
            if future is not None and future.done():
                if not accepted:
                    handle=future.result();assert handle.accepted,'NAV2_GOAL_REJECTED';accepted=True;future=handle.get_result_async()
                else:
                    response=future.result();result.update(action_status=response.status,action_error_code=response.result.error_code,final_pose=[node.x,node.y,node.yaw],goal_distance_m=math.hypot(node.x-3,node.y),plan_messages=node.plans,command_count=len(node.commands));result['passed']=response.status==4 and result['goal_distance_m']<=.45;break
        else:result.update(passed=False,reason='BOUNDED_WALL_STOP')
    except BaseException as e:result.update(passed=False,error=repr(e),traceback=traceback.format_exc())
    finally:
        stack.close();result['wall_s']=time.monotonic()-start
        if node:
            (out/'TRACE.json').write_text(json.dumps(node.trace));(out/'COMMANDS.json').write_text(json.dumps({'cmd_vel':node.commands,'cmd_vel_nav':node.nav_commands}));node.destroy_node()
        rclpy.shutdown();(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result.get('passed')else 1
if __name__=='__main__':sys.exit(main())
