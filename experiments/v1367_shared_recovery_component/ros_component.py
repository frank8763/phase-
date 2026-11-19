"""One actual installed controller on real feedback; frozen safe recovery only."""
import importlib.abc
import math
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import traceback


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*extra):
        if name.split('.')[0] in {'mujoco','vehicle','torch','factory','physical'}:raise AssertionError('ROS_PHYSICAL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoPhysical())
from component_context import *
sys.path.insert(0,str(R/'experiments/v1288_baseline_interface'))
from contract import command,observation
from stamped_contract import decode_origin,local_zero
from evidence_io import Journal,persist,PeerClosure
sys.path.insert(0,str(R/'experiments/v1361_dynamic_reserve_consistency'))
from observed_route import nominal_clearance
from recovery_guard import check as recovery_reserve
from dynamic_reserve import check as dynamic_reserve
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
from geometry_msgs.msg import TransformStamped,TwistStamped,PoseStamped
from nav_msgs.msg import Odometry,Path as NavPath,OccupancyGrid
from sensor_msgs.msg import LaserScan
from lifecycle_msgs.srv import ChangeState
from nav2_msgs.action import FollowPath
from tf2_ros import TransformBroadcaster,StaticTransformBroadcaster


def main():
    task=read(sys.argv[1]);task_check(task)
    if '--entry-check' in sys.argv:
        assert Path(task['nav2_params']).is_file() and task['controller_plugin'] in ['RPP','Deadband']
        print(json.dumps(dict(passed=True,actual_ros_imports=True,models=0,physical_native=0,origin=15105)));return 0
    window=read(O/'ROUND_WINDOW.json');authorize(task,window);out=Path(task['output'])
    os.sched_setaffinity(0,{3,4,5});started=time.monotonic();rclpy.init();node=Node('phase_shared_recovery_component')
    latest=None;received=-1;native_tick=15105;sequence=0;armed=False;closing=False;stop_requested=[False]
    rows=[];origins=[];refusals=[];reserve=[];known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json');ball=task['causal_ball']
    sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=str(out.relative_to(R)/'ros.sock');sock.bind(address);sock.setblocking(False)
    peer=str(out.relative_to(R)/'native.sock');journal=Journal(out/'ROS_COMMANDS.jsonl')
    tf=TransformBroadcaster(node);static=StaticTransformBroadcaster(node)
    t=TransformStamped();t.header.frame_id='base_link';t.child_frame_id='base_scan';t.header.stamp=node.get_clock().now().to_msg();t.transform.translation.x=.3;t.transform.rotation.w=1.;static.sendTransform(t)
    odom=node.create_publisher(Odometry,'odom',10);scanpub=node.create_publisher(LaserScan,'scan',10)
    qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE)
    mappub=node.create_publisher(OccupancyGrid,'/phase_public_static',qos);received_map=[None]
    node.create_subscription(OccupancyGrid,'/local_costmap/costmap',lambda value:received_map.__setitem__(0,value),qos)
    grid=read(C/'COMMON_GRID.json')

    def send(value):
        try:sock.sendto(json.dumps(value).encode(),peer)
        except (FileNotFoundError,ConnectionRefusedError,BlockingIOError):pass

    def emit(v,w,source,origin=None):
        nonlocal sequence
        if not armed or closing or latest is None:return
        now=time.monotonic();packet=dict(run_id=task['run_id'],sequence=sequence,issued_at=now,v=float(v),w=float(w))
        command(packet,run_id=task['run_id'],now=now,previous_sequence=sequence-1)
        binding=dict(origin=origin or local_zero(now),observation_sequence=latest['sequence'],
                     observation_sampled_at=latest['sampled_at'],observation_native_tick=native_tick)
        row=dict(packet,source=source,expected_gear=-1,**binding);rows.append(row);journal.append(row);sequence+=1
        send(dict(kind='command',**packet,**binding))

    def receive(message):
        origin=decode_origin(message.header.stamp.sec*1000000000+message.header.stamp.nanosec,node.get_clock().now().nanoseconds,time.monotonic())
        origins.append(dict(native_tick=native_tick,origin=origin))
        if not armed or latest is None:return
        v,w=float(message.twist.linear.x),float(message.twist.angular.z)
        command(dict(run_id=task['run_id'],sequence=sequence,issued_at=time.monotonic(),v=v,w=w),run_id=task['run_id'],now=time.monotonic(),previous_sequence=sequence-1)
        if origin['receipt_age_s']>.2:
            refusals.append(dict(native_tick=native_tick,reason='SOURCE_EXPIRED',requested=[v,w],origin=origin));emit(0.,0.,'EXPIRED_ZERO');return
        allowed,proof=dynamic_reserve(latest['body'],ball,v,w);static_ok,static_proof=recovery_reserve(known,latest['body'],v,w)
        direction=abs(v)<.005 or v<0.
        reserve.append(dict(native_tick=native_tick,body=latest['body'],requested=[v,w],dynamic_allowed=allowed,
                            dynamic_proof=proof,static_allowed=static_ok,static_proof=static_proof,direction_ok=direction,command_sequence=sequence))
        if not allowed or not static_ok or not direction:
            refusals.append(dict(native_tick=native_tick,reason='RECOVERY_FIELD_OR_DIRECTION_REFUSAL',requested=[v,w]))
            emit(0.,0.,'RESERVE_OR_DIRECTION_ZERO');return
        emit(v,w,'CONTROLLER',origin)

    node.create_subscription(TwistStamped,'cmd_vel',receive,10)

    def publish():
        nonlocal latest,received,native_tick
        if stop_requested[0] or (out/'PEER_STOP_REQUEST.json').exists():raise PeerClosure('PEER_REQUESTED_CLOSE')
        packet=None
        for _ in range(128):
            try:packet=json.loads(sock.recv(65536))
            except BlockingIOError:break
        if packet is None:return
        native_tick=packet.pop('native_tick');sim_time=packet.pop('sim_time')
        assert native_tick>=task['origin_native_tick'] and abs(sim_time-native_tick*.01)<1e-7,'ORIGIN_CLOCK_MISMATCH'
        observation(packet,run_id=task['run_id'],now=time.monotonic(),previous_sequence=received);latest=packet;received=packet['sequence']
        x,y,yaw,v,w=packet['body'];x-=.3*math.cos(yaw);y-=.3*math.sin(yaw);stamp=node.get_clock().now().to_msg()
        transform=TransformStamped();transform.header.frame_id='odom';transform.child_frame_id='base_link';transform.header.stamp=stamp
        transform.transform.translation.x=x;transform.transform.translation.y=y;transform.transform.rotation.z=math.sin(yaw/2);transform.transform.rotation.w=math.cos(yaw/2);tf.sendTransform(transform)
        od=Odometry();od.header.frame_id='odom';od.child_frame_id='base_link';od.header.stamp=stamp;od.pose.pose.position.x=x;od.pose.pose.position.y=y;od.pose.pose.orientation=transform.transform.rotation;od.twist.twist.linear.x=v;od.twist.twist.angular.z=w;odom.publish(od)
        scan=LaserScan();scan.header.frame_id='base_scan';scan.header.stamp=stamp;scan.angle_min=0.;scan.angle_max=math.tau*31/32;scan.angle_increment=math.tau/32;scan.range_min=.05;scan.range_max=3.;scan.scan_time=.05
        scan.ranges=[max(.05,value) if value<2.999 else float('inf') for value in packet['ranges_m']];scanpub.publish(scan)

    def publish_map():
        message=OccupancyGrid();message.header.frame_id='odom';message.header.stamp=node.get_clock().now().to_msg()
        message.info.width=grid['width'];message.info.height=grid['height'];message.info.resolution=grid['resolution'];message.info.origin.position.x=grid['origin'][0];message.info.origin.position.y=grid['origin'][1];message.info.origin.orientation.w=1.;message.data=grid['data'];mappub.publish(message)
    node.create_timer(.01,publish);node.create_timer(.1,publish_map)
    change=node.create_client(ChangeState,'controller_server/change_state');action=ActionClient(node,FollowPath,'follow_path')
    log=(out/'controller.console').open('x');server=subprocess.Popen(['/opt/ros/jazzy/lib/nav2_controller/controller_server','--ros-args','--params-file',task['nav2_params']],stdout=log,stderr=subprocess.STDOUT)
    signal.signal(signal.SIGTERM,lambda *_:stop_requested.__setitem__(0,True))
    result=dict(passed=False,physical_models_in_ros=0,scope='one safe recovery component, not goalnavigation')

    def wait(predicate,seconds):
        end=min(time.monotonic()+seconds,window['hard_stop_monotonic']-100)
        while time.monotonic()<end:
            rclpy.spin_once(node,timeout_sec=.005);assert server.poll() is None,'CONTROLLER_EXIT'
            if predicate():return
        raise TimeoutError('COMPONENT_ROS_STAGE_TIMEOUT')

    try:
        wait(lambda:latest is not None and change.service_is_ready(),30)
        assert native_tick==15105,'MODEL_MOVED_BEFORE_COMPONENT_ARM'
        for transition in [1,3]:
            request=ChangeState.Request();request.transition.id=transition;future=change.call_async(request);wait(future.done,15);assert future.result().success
        loaded=['libphase_executable_rpp.so'] if task['controller_plugin']=='RPP' else ['libphase_deadband_mppi.so','libcoherent.so','libmppi_controller.so']
        maps=Path('/proc/%d/maps'%server.pid).read_text();assert all(name in maps for name in loaded),'ACTUAL_CONTROLLER_LIBRARY_MISSING'
        result['actual_loaded_libraries']=loaded
        wait(lambda:action.server_is_ready() and received_map[0] is not None,10)
        cm=received_map[0];px,py=-3.15,0.;ix=int((px-cm.info.origin.position.x)/cm.info.resolution);iy=int((py-cm.info.origin.position.y)/cm.info.resolution)
        assert 0<=ix<cm.info.width and 0<=iy<cm.info.height and cm.data[iy*cm.info.width+ix]==100
        result['public_static_map_receipt']=dict(passed=True,source=sha(C/'COMMON_GRID.json'))
        dump(out/'INITIAL_ACTUAL_COSTMAP.json',dict(width=cm.info.width,height=cm.info.height,resolution=cm.info.resolution,origin=[cm.info.origin.position.x,cm.info.origin.position.y],data=list(cm.data)))
        path=NavPath();path.header.frame_id='odom';path.header.stamp=node.get_clock().now().to_msg()
        for x,y,yaw in task['reference_path']:
            p=PoseStamped();p.header=path.header;p.pose.position.x=x;p.pose.position.y=y;p.pose.orientation.z=math.sin(yaw/2);p.pose.orientation.w=math.cos(yaw/2);path.poses.append(p)
        goal=FollowPath.Goal();goal.path=path;goal.controller_id=task['controller_plugin'];goal.goal_checker_id='goal_checker';goal.progress_checker_id='progress_checker'
        future=action.send_goal_async(goal);wait(future.done,5);handle=future.result();assert handle.accepted
        done=handle.get_result_async();armed=True;send(dict(kind='arm',run_id=task['run_id'],issued_at=time.monotonic()));result['action_accepted']=True
        wait(lambda:done.done() or native_tick-15105>=4000 or bool(refusals),100)
        if done.done():
            outcome=done.result();distance=math.dist(latest['body'][:2],task['component_goal_xy'])
            result.update(passed=outcome.status==4 and distance<=.08,action_status=outcome.status,error_code=outcome.result.error_code,component_goal_distance_m=distance)
        else:
            result['functional_stop']='COMPONENT_NATIVE_LIMIT_OR_GUARD_REFUSAL'
            cancel=handle.cancel_goal_async();wait(cancel.done,3);wait(done.done,3)
    except PeerClosure as exc:result['functional_stop']=str(exc)
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        closing=True;send(dict(kind='stop',run_id=task['run_id'],issued_at=time.monotonic(),passed=result['passed']))
        artifacts=[('ROS_COMMANDS.json',rows),('STAMPED_ORIGIN_RECORDS.json',origins),('RESERVE_RECORDS.json',reserve),('ROS_REFUSALS.json',refusals)]
        result.update(commands=len(rows),origin_native=15105,final_native=native_tick,wall_s=time.monotonic()-started)
        result=persist(out,artifacts,result,closed=False)
        if server.poll() is None:
            server.terminate()
            try:server.wait(timeout=4)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=2)
        journal.close();result.update(controller_server_exited=server.poll() is not None,no_physical_modules_loaded=not any(k in sys.modules for k in ['mujoco','vehicle','torch']))
        result=persist(out,artifacts,result,closed=True);sock.close();Path(address).unlink(missing_ok=True);log.close();node.destroy_node();rclpy.shutdown()
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
