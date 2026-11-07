"""Genuine Nav2 action client and causal sensor/actuator IPC adapter. No scene truth."""
import json,math,os,socket,sys,time,traceback
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist,TransformStamped
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry,Path as NavPath
from lifecycle_msgs.srv import GetState
from nav2_msgs.action import NavigateToPose
from tf2_ros import TransformBroadcaster,StaticTransformBroadcaster
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiments/v856_nav2_foundation'))
from ros_stack import Stack
C=Path(__file__).parent;R=C.parents[1];OUT=R/'runs/v858_nav2_verified';END=1794052800.
class Bridge(Node):
    def __init__(self,out):
        super().__init__('phase_native_nav2_bridge');self.out=out;self.latest=None;self.messages=0;self.command_times=[];self.nav_times=[];self.plans=[];self.lastscan=-1;self.goal_started=None;self.observation_ages=[];self.scan_ages=[]
        self.s=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);assert not Path('runs/v858_nav2_verified/r.sock').exists();self.s.bind('runs/v858_nav2_verified/r.sock');self.s.setblocking(False)
        self.tf=TransformBroadcaster(self);self.static=StaticTransformBroadcaster(self);self.last_command=None
        for parent,child in [('map','odom'),('base_link','base_scan')]:
            t=TransformStamped();t.header.stamp=self.get_clock().now().to_msg();t.header.frame_id=parent;t.child_frame_id=child;t.transform.rotation.w=1.;self.static.sendTransform(t)
        self.odom=self.create_publisher(Odometry,'odom',10);self.scan=self.create_publisher(LaserScan,'scan',qos_profile_sensor_data)
        self.create_subscription(Twist,'cmd_vel',self.command,10);self.create_subscription(Twist,'cmd_vel_nav',lambda m:self.nav_times.append([time.monotonic(),m.linear.x,m.angular.z]),10);self.create_subscription(NavPath,'plan',self.plan,10)
        self.action=ActionClient(self,NavigateToPose,'navigate_to_pose');self.lifecycle=self.create_client(GetState,'bt_navigator/get_state');self.state_future=None;self.active=False;self.create_timer(.005,self.read)
    def plan(self,m):
        self.plans.append(dict(wall_monotonic=time.monotonic(),path=[[p.pose.position.x,p.pose.position.y,2*math.atan2(p.pose.orientation.z,p.pose.orientation.w)]for p in m.poses]))
    def send(self,value):
        try:self.s.sendto(json.dumps(value).encode(),'runs/v858_nav2_verified/p.sock')
        except (FileNotFoundError,ConnectionRefusedError,BlockingIOError):pass
    def command(self,m):
        now=time.monotonic();self.command_times.append([now,m.linear.x,m.angular.z]);self.send(dict(v=m.linear.x,w=m.angular.z,wall_monotonic=now))
    def read(self):
        value=None
        while True:
            try:value=json.loads(self.s.recv(65536))
            except BlockingIOError:break
        if value is None:return
        self.latest=value;self.messages+=1;age=time.monotonic()-value['wall_monotonic'];self.observation_ages.append(age);assert age<=.2,'NATIVE_ODOMETRY_TOO_OLD'
        x,y,yaw,v,w=value['body'];stamp=self.get_clock().now().to_msg();t=TransformStamped();t.header.stamp=stamp;t.header.frame_id='odom';t.child_frame_id='base_link';t.transform.translation.x=x;t.transform.translation.y=y;t.transform.rotation.z=math.sin(yaw/2);t.transform.rotation.w=math.cos(yaw/2);self.tf.sendTransform(t)
        od=Odometry();od.header.stamp=stamp;od.header.frame_id='odom';od.child_frame_id='base_link';od.pose.pose.position.x=x;od.pose.pose.position.y=y;od.pose.pose.orientation=t.transform.rotation;od.twist.twist.linear.x=v;od.twist.twist.angular.z=w;self.odom.publish(od)
        scan=value.get('scan')
        if scan is not None and scan['native_tick']!=self.lastscan:
            self.scan_ages.append(age+max(0.,value['sim_time']-scan['time']))
            self.lastscan=scan['native_tick'];s=LaserScan();s.header.stamp=stamp;s.header.frame_id='base_scan';s.angle_min=0.;s.angle_max=2*math.pi*31/32;s.angle_increment=2*math.pi/32;s.range_min=.05;s.range_max=3.;s.scan_time=.05;s.ranges=[max(.05,float(r))if r<2.999 else float('inf')for r in scan['ranges']];self.scan.publish(s)
def main():
    task=json.loads(Path(sys.argv[1]).read_text());out=Path(task['output']);out.mkdir(parents=True,exist_ok=True);rosout=out/'ros';rosout.mkdir(exist_ok=False);os.chdir(R);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:3]));rclpy.init();node=None;stack=Stack(rosout,task['nav2_params']);start=time.monotonic();result={'passed':False};future=None;accepted=False;sent=False;reason='UNKNOWN'
    try:
        node=Bridge(out);stack.start()
        while time.monotonic()-start<task['wall_limit_s']+40 and time.time()<END-25:
            rclpy.spin_once(node,timeout_sec=.005)
            if stack.failed():raise RuntimeError('NAV2_SERVER_EXIT '+str(stack.failed()))
            if node.state_future is not None and node.state_future.done():node.active=node.state_future.result().current_state.id==3;node.state_future=None
            if not node.active and node.state_future is None and node.lifecycle.service_is_ready():node.state_future=node.lifecycle.call_async(GetState.Request())
            if not sent and node.active and node.latest:
                g=NavigateToPose.Goal();g.pose.header.frame_id='map';g.pose.header.stamp=node.get_clock().now().to_msg();g.pose.pose.position.x=task['goal_xy'][0];g.pose.pose.position.y=task['goal_xy'][1];g.pose.pose.orientation.z=math.sin(task['goal_yaw']/2);g.pose.pose.orientation.w=math.cos(task['goal_yaw']/2);future=node.action.send_goal_async(g);sent=True;node.goal_started=time.monotonic()
            if not sent and time.monotonic()-start>35:raise RuntimeError('NAV2_OR_NATIVE_STARTUP_TIMEOUT')
            if sent and time.monotonic()-node.latest['wall_monotonic']>.25:raise RuntimeError('PHYSICS_BACKEND_STOPPED_OR_STALE')
            if future is not None and future.done():
                if not accepted:
                    handle=future.result();assert handle.accepted,'NAV2_GOAL_REJECTED';accepted=True;future=handle.get_result_async()
                else:
                    response=future.result();result.update(action_status=response.status,action_error_code=response.result.error_code);result['passed']=response.status==4;reason='NAV2_SUCCEEDED'if result['passed']else'NAV2_FUNCTIONAL_FAILURE';break
        else:reason='BOUNDED_WALL_STOP'
    except BaseException as e:reason='ROS_INTERFACE_EXCEPTION';result.update(error=repr(e),traceback=traceback.format_exc())
    finally:
        result.update(reason=reason,wall_s=time.monotonic()-start)
        if node:
            result.update(odometry_messages=node.messages,plan_messages=len(node.plans),cmd_vel_messages=len(node.command_times),last_native_observation=node.latest,maximum_odometry_receive_age_s=max(node.observation_ages,default=None),maximum_scan_receive_age_s=max(node.scan_ages,default=None))
            node.send(dict(stop=True,reason=reason,wall_monotonic=time.monotonic()));(out/'COMMANDS.json').write_text(json.dumps(dict(cmd_vel=node.command_times,cmd_vel_nav=node.nav_times)));(out/'PLANS.json').write_text(json.dumps(node.plans));node.s.close();Path('runs/v858_nav2_verified/r.sock').unlink(missing_ok=True)
        (out/'ROS_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');(out/'STOP.json').write_text(json.dumps(dict(reason=reason))+'\n');stack.close()
        if node:node.destroy_node()
        rclpy.shutdown();print(json.dumps(result),flush=True)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
