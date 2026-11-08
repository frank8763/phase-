"""Future real Nav2 bridge; module import stays model-free and ROS-free."""
import json,math,os,socket,sys,time,traceback
from pathlib import Path
import gzip
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"experiments/v862_ready_static"))
from handshake import NODES,file_sha,require,verify_sources,require_goal_allowed
from software_authority import authorized
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
def run(task,receipt,freeze_sha):
    deadline=authorized(task,receipt,time.time(),freeze_sha);verify_sources(R,C/'SOURCE_FREEZE.json')
    import rclpy
    from rclpy.node import Node
    from rclpy.action import ActionClient
    from rclpy.qos import qos_profile_sensor_data
    from geometry_msgs.msg import Twist,TransformStamped
    from sensor_msgs.msg import LaserScan
    from nav_msgs.msg import Odometry,Path as NavPath
    from nav2_msgs.action import NavigateToPose
    from nav2_msgs.srv import ManageLifecycleNodes
    from lifecycle_msgs.srv import GetState
    from tf2_ros import TransformBroadcaster,StaticTransformBroadcaster
    sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'))
    from ros_stack import Stack
    class Bridge(Node):
        def __init__(self):
            super().__init__('phase_ready_static_bridge');self.latest=None;self.command_sequence=0
            self.commands=[];self.nav_commands=[];self.plans=[];self.ages=[];self.scan_ages=[];self.lastscan=-1;self.odometry_messages=0
            self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
            self.address=str(Path(task['socket_dir'])/'ros.sock');require(not Path(self.address).exists(),'STALE_ROS_SOCKET')
            self.sock.bind(self.address);self.sock.setblocking(False)
            self.tf=TransformBroadcaster(self);self.static=StaticTransformBroadcaster(self);transforms=[]
            for parent,child in [('map','odom'),('base_link','base_scan')]:
                t=TransformStamped();t.header.stamp=self.get_clock().now().to_msg();t.header.frame_id=parent;t.child_frame_id=child;t.transform.rotation.w=1.;transforms.append(t)
            self.static.sendTransform(transforms)
            self.odom=self.create_publisher(Odometry,'odom',10);self.scan=self.create_publisher(LaserScan,'scan',qos_profile_sensor_data)
            self.create_subscription(Twist,'cmd_vel',self.command,10)
            self.create_subscription(Twist,'cmd_vel_nav',lambda m:self.nav_commands.append([time.monotonic(),m.linear.x,m.angular.z]),10)
            self.create_subscription(NavPath,'plan',lambda m:self.plans.append(dict(at=time.monotonic(),path=[[p.pose.position.x,p.pose.position.y,2*math.atan2(p.pose.orientation.z,p.pose.orientation.w)]for p in m.poses])),10)
            self.telemetry=[]
            from nav2_msgs.msg import Costmap
            from geometry_msgs.msg import PointStamped
            from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
            def save(kind,value):
                self.telemetry.append(dict(at=time.monotonic(),tick=None if self.latest is None else self.latest['native_tick'],kind=kind,value=value))
            def costmap(m):
                save('costmap_raw',dict(frame=m.header.frame_id,resolution=m.metadata.resolution,width=m.metadata.size_x,height=m.metadata.size_y,origin=[m.metadata.origin.position.x,m.metadata.origin.position.y],data=list(m.data)))
            def path(kind,m):save(kind,dict(frame=m.header.frame_id,path=[[p.pose.position.x,p.pose.position.y,2*math.atan2(p.pose.orientation.z,p.pose.orientation.w)]for p in m.poses]))
            self.create_subscription(Costmap,'local_costmap/costmap_raw',costmap,QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE))
            self.create_subscription(NavPath,'received_global_plan',lambda m:path('received_global_plan',m),10)
            self.create_subscription(NavPath,'lookahead_collision_arc',lambda m:path('lookahead_collision_arc',m),10)
            self.create_subscription(PointStamped,'lookahead_point',lambda m:save('lookahead_point',dict(frame=m.header.frame_id,xy=[m.point.x,m.point.y])),10)
            self.action=ActionClient(self,NavigateToPose,'navigate_to_pose');self.manager=self.create_client(ManageLifecycleNodes,'lifecycle_manager_navigation/manage_nodes')
            self.states={name:self.create_client(GetState,name+'/get_state')for name in NODES};self.create_timer(.005,self.read)
        def send(self,data):
            packet=dict(data,run_id=task['run_id'])
            try:self.sock.sendto(json.dumps(packet).encode(),str(Path(task['socket_dir'])/'physics.sock'))
            except (FileNotFoundError,ConnectionRefusedError,BlockingIOError):pass
        def command(self,m):
            # Nav2 may publish zero during activation; never forward before native ARM ACK.
            if not self.latest or self.latest['phase']!='RUNNING':return
            now=time.monotonic();self.command_sequence+=1;self.commands.append([now,m.linear.x,m.angular.z])
            self.send(dict(kind='command',sequence=self.command_sequence,issued_at=now,v=m.linear.x,w=m.angular.z))
        def read(self):
            packet=None
            for _ in range(128):
                try:packet=json.loads(self.sock.recv(65536))
                except BlockingIOError:break
            if packet is None:return
            require(packet.get('run_id')==task['run_id'],'FOREIGN_NATIVE_OBSERVATION');require(packet['kind']=='observation','WRONG_NATIVE_PACKET')
            now=time.monotonic();age=now-packet['sent_at'];require(-.05<=age<=.2,'NATIVE_HEARTBEAT_AGE');self.latest=packet
            self.odometry_messages+=1
            if packet['phase']!='WAITING':
                self.ages.append(now-packet['body_measured_at'])
                require(now-packet['body_measured_at']<=.2,'NATIVE_ODOMETRY_AGE')
            x,y,yaw,v,w=packet['body'];stamp=self.get_clock().now().to_msg();t=TransformStamped();t.header.stamp=stamp;t.header.frame_id='odom';t.child_frame_id='base_link';t.transform.translation.x=x;t.transform.translation.y=y;t.transform.rotation.z=math.sin(yaw/2);t.transform.rotation.w=math.cos(yaw/2);self.tf.sendTransform(t)
            od=Odometry();od.header.stamp=stamp;od.header.frame_id='odom';od.child_frame_id='base_link';od.pose.pose.position.x=x;od.pose.pose.position.y=y;od.pose.pose.orientation=t.transform.rotation;od.twist.twist.linear.x=v;od.twist.twist.angular.z=w;self.odom.publish(od)
            # Repeated pre-ARM publications are explicitly the same initial snapshot.
            s=packet['scan']
            if s['native_tick']!=self.lastscan or packet['phase']=='WAITING':
                self.lastscan=s['native_tick'];scan=LaserScan();scan.header.stamp=stamp;scan.header.frame_id='base_scan';scan.angle_min=0.;scan.angle_max=2*math.pi*31/32;scan.angle_increment=2*math.pi/32;scan.range_min=.05;scan.range_max=3.;scan.scan_time=.05;scan.ranges=[max(.05,float(r))if r<2.999 else float('inf')for r in s['ranges']];self.scan.publish(scan)
                if packet['phase']!='WAITING':
                    self.scan_ages.append(now-packet['scan_measured_at'])
                    require(now-packet['scan_measured_at']<=.2,'NATIVE_SCAN_AGE')
    def wait_for(node,predicate,until,message):
        while time.monotonic()<until and time.time()<deadline-25:
            rclpy.spin_once(node,timeout_sec=.005)
            require(not stack.failed(),'NAV2_SERVER_EXIT')
            if predicate():return
        raise TimeoutError(message)
    def query_states(node,startup_until,required_state):
        values={};at={}
        for name in NODES:
            client=node.states[name];wait_for(node,client.service_is_ready,min(startup_until,time.monotonic()+2.),'GET_STATE_SERVICE '+name)
            future=client.call_async(GetState.Request());wait_for(node,future.done,min(startup_until,time.monotonic()+2.),'GET_STATE_RESPONSE '+name)
            values[name]=future.result().current_state.id;at[name]=time.monotonic()
            require(values[name]==required_state,'UNEXPECTED_LIFECYCLE_STATE '+name)
        return values,at
    os.chdir(R);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:3]));out=Path(task['output']);rosout=out/'ros';rosout.mkdir(exist_ok=False)
    rclpy.init();node=None;stack=Stack(rosout,task['nav2_params']);start=time.monotonic();result=dict(passed=False,navigation_action_sent=False);reason='STARTUP';proof=[]
    try:
        node=Bridge();stack.start();until=start+35.
        wait_for(node,lambda:node.latest is not None,until,'REAL_T0_NOT_RECEIVED')
        require(node.latest['native_tick']==0 and node.latest['sim_time']==0.,'NATIVE_ADVANCED_DURING_STARTUP')
        for _ in range(2):proof.append(query_states(node,until,1))
        wait_for(node,node.manager.service_is_ready,until,'MANAGER_SERVICE_UNAVAILABLE');request=ManageLifecycleNodes.Request();request.command=0;future=node.manager.call_async(request)
        wait_for(node,future.done,until,'MANAGER_STARTUP_TIMEOUT');require(future.result().success,'MANAGER_STARTUP_REJECTED')
        states,checked=query_states(node,until,3);require(time.monotonic()-min(checked.values())<=1.,'ACTIVE_PROOF_TOO_OLD')
        arm=dict(kind='arm',native_tick=0,sim_time=0.,states=states,checked_at=checked,issued_at=time.monotonic());node.send(arm)
        result.update(active_states=states,active_checked_at=checked,arm_issued_at=arm['issued_at'])
        wait_for(node,lambda:node.latest['phase']=='RUNNING',until,'NATIVE_ARM_ACK_MISSING')
        require_goal_allowed(node.latest,task['run_id'],time.monotonic())
        g=NavigateToPose.Goal();g.pose.header.stamp=node.get_clock().now().to_msg();g.pose.header.frame_id='map';g.pose.pose.position.x=task['goal_xy'][0];g.pose.pose.position.y=task['goal_xy'][1];g.pose.pose.orientation.z=math.sin(task['goal_yaw']/2);g.pose.pose.orientation.w=math.cos(task['goal_yaw']/2)
        wait_for(node,node.action.server_is_ready,until,'NAVIGATION_ACTION_NOT_READY');future=node.action.send_goal_async(g);result['navigation_action_sent']=True
        result['goal_sent_at']=time.monotonic();goal_until=result['goal_sent_at']+task['wall_limit_s'];wait_for(node,future.done,goal_until,'NAVIGATION_GOAL_ACCEPT_TIMEOUT');handle=future.result();require(handle.accepted,'NAVIGATION_GOAL_REJECTED');future=handle.get_result_async()
        while not future.done():
            rclpy.spin_once(node,timeout_sec=.005)
            require(not stack.failed(),'NAV2_SERVER_EXIT');require(time.monotonic()-node.latest['sent_at']<=.25,'PHYSICS_STOPPED_OR_STALE')
            require(time.monotonic()<goal_until and time.time()<deadline-25,'NAVIGATION_DEADLINE')
        response=future.result();result.update(action_status=response.status,action_error_code=response.result.error_code,passed=response.status==4);reason='NAV2_SUCCEEDED'if result['passed']else'NAV2_FUNCTIONAL_FAILURE'
    except BaseException as e:reason='ROS_INTERFACE_OR_FUNCTIONAL_STOP';result.update(error=repr(e),traceback=traceback.format_exc())
    finally:
        result.update(reason=reason,wall_s=time.monotonic()-start,readiness_probes=proof)
        if node:
            node.send(dict(kind='stop',issued_at=time.monotonic(),reason=reason));result.update(odometry_messages=node.odometry_messages,cmd_vel_messages=len(node.commands),plan_messages=len(node.plans),maximum_observation_age_s=max(node.ages,default=None),maximum_scan_age_s=max(node.scan_ages,default=None),last_observation=node.latest)
            with gzip.open(out/'TELEMETRY.json.gz','wt')as tf:json.dump(node.telemetry,tf)
            (out/'COMMANDS.json').write_text(json.dumps(dict(cmd_vel=node.commands,cmd_vel_nav=node.nav_commands))+'\n');(out/'PLANS.json').write_text(json.dumps(node.plans)+'\n');node.sock.close();Path(node.address).unlink(missing_ok=True)
        (out/'ROS_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');stack.close()
        if node:node.destroy_node()
        rclpy.shutdown()
    return result
def main():
    task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text());result=run(task,receipt,file_sha(C/'SOURCE_FREEZE.json'));return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
