"""Engineering coherentMPPI on one current-event modeled origin/path/causal map.

No saved handoff tick or source path is a production input. No LaserScan is
published. Interface fixtures are not current physical evidence.
"""
import argparse
import hashlib
import importlib.abc
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','factory','physical'}:raise AssertionError('NO_PHYSICAL_MPPI_PEER '+name)
sys.meta_path.insert(0,NoPhysical())
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
io=load('rpp_peer_json',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
data=load('rpp_peer_grid',R/'experiments/v1352_shared_controller_probe/common.py')
contract=data.load_contract()
stamped=load('rpp_peer_stamped',R/'experiments/v1370_overnight_controller_matrix/stamped_contract.py')
map_gate=load('mppi_peer_map',R/'experiments/v1370_overnight_controller_matrix/map_gate.py')
identity_contract=load('v1483_exact_MPPI_identity',C/'controller_identity.py')

def validate_request(value,run_id,previous,*,input_sha256,origin_native,controller_identity_sha256):
    assert value['kind']=='MODELED_BODY_CAUSAL_MAP_NOT_SENSOR','NOT_MODELED_INPUT'
    assert value['run_id']==run_id and type(value['sequence']) is int and value['sequence']>previous,'RPC_ID_OR_SEQUENCE'
    assert len(value['body'])==5 and all(math.isfinite(x) for x in value['body']),'RPC_BODY'
    assert type(value['native_tick']) is int and value['native_tick']>=origin_native,'RPC_NATIVE'
    assert value['input_sha256']==input_sha256 and value['controller_identity_sha256']==controller_identity_sha256,'RPC_CURRENT_INPUT_OR_CONTROLLER_CHANGED'
    assert 0<=time.monotonic()-value['sent_monotonic']<=2.,'RPC_DELIVERY_TOO_OLD'
    return value

def main():
    import rclpy
    from rclpy.node import Node
    from rclpy.action import ActionClient
    from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
    from geometry_msgs.msg import PoseStamped,TransformStamped,TwistStamped
    from nav_msgs.msg import Odometry,Path as NavPath,OccupancyGrid
    from nav2_msgs.action import FollowPath
    from lifecycle_msgs.srv import ChangeState
    from tf2_ros import TransformBroadcaster
    parser=argparse.ArgumentParser();parser.add_argument('output');parser.add_argument('run_id');parser.add_argument('--entry-check',action='store_true');args=parser.parse_args()
    out=Path(args.output);assert out.is_relative_to(R/'runs')
    fixed=data.read(out/'CURRENT_INPUT.json');controller_sha=identity_contract.verify_current(fixed);identity_contract.verify_environment(fixed['controller_binding'],role='MODELED_ROS');params=identity_contract.PARAMS
    clean=dict(fixed);identity=clean.pop('input_sha256')
    assert hashlib.sha256(json.dumps(clean,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==identity,'CURRENT_INPUT_CHANGED'
    assert fixed['next_segment']['gear'] in (-1,1) and fixed['physical_admission'] is False
    assert fixed['bridge_forecast']['invariant_for_all_future_under_declared_class'] is True
    if args.entry_check:
        assert data.read(params)['controller_server']['ros__parameters']['Deadband']['plugin']=='phase_deadband/DeadbandMPPI'
        print(json.dumps(dict(passed=True,models=0,physical_native=0,real_ros_imports=True,no_synthetic_scan_publisher=True)));return 0
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));os.chdir(R)
    grid=data.read(R/'experiments/v1331_common_static_map/PUBLIC_STATIC_GRID.json');ball=[*fixed['bridge_forecast']['center'],fixed['bridge_forecast']['radius_m']];forecast_grid,occupied=data.raster_ball(grid,ball)
    started=time.monotonic();deadline=min(started+1800,started+max(0,1795395600-time.time()));stopping=[False]
    signal.signal(signal.SIGTERM,lambda *_:stopping.__setitem__(0,True));signal.signal(signal.SIGINT,lambda *_:stopping.__setitem__(0,True))
    sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=str(out.relative_to(R)/'peer.sock');sock.bind(address);sock.setblocking(False)
    rclpy.init(args=['--ros-args','--disable-external-lib-logs','--disable-rosout-logs']);node=Node('phase_current_event_modeled_mppi');tf=TransformBroadcaster(node)
    odom=node.create_publisher(Odometry,'odom',10);qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE)
    maps=node.create_publisher(OccupancyGrid,'/phase_public_static',qos);received=[None]
    node.create_subscription(OccupancyGrid,'/local_costmap/costmap',lambda value:received.__setitem__(0,value),qos)
    state=[None];peer=[None];first_tf=[None];answered=[-1];requests=[];commands=[];server=None;handle=None;done=None
    result=dict(passed=False,models=0,physical_native=0,analytical_native=0,physical_admission=False,synthetic_scan_messages=0,fixture_or_model_only=True,controller_identity_sha256=controller_sha,algorithm='ENGINEERING_COHERENT_MPPI',MPPI_internal_optimizer_rollouts=None,pure_ROS_controller_math_not_response_model_integrations=True)
    def publish_map():
        message=OccupancyGrid();message.header.frame_id='odom';message.header.stamp=node.get_clock().now().to_msg();message.info.resolution=forecast_grid['resolution'];message.info.width=forecast_grid['width'];message.info.height=forecast_grid['height'];message.info.origin.position.x=forecast_grid['origin'][0];message.info.origin.position.y=forecast_grid['origin'][1];message.info.origin.orientation.w=1.;message.data=forecast_grid['data'];maps.publish(message)
    def publish_body():
        if state[0] is None:return
        b=state[0]['body'];x=b[0]-.3*math.cos(b[2]);y=b[1]-.3*math.sin(b[2]);stamp=node.get_clock().now().to_msg()
        t=TransformStamped();t.header.stamp=stamp;t.header.frame_id='odom';t.child_frame_id='base_link';t.transform.translation.x=x;t.transform.translation.y=y;t.transform.rotation.z=math.sin(b[2]/2);t.transform.rotation.w=math.cos(b[2]/2);tf.sendTransform(t)
        message=Odometry();message.header=t.header;message.child_frame_id='base_link';message.pose.pose.position.x=x;message.pose.pose.position.y=y;message.pose.pose.orientation=t.transform.rotation;message.twist.twist.linear.x=b[3];message.twist.twist.angular.z=b[4];odom.publish(message)
        if first_tf[0] is None:first_tf[0]=stamp.sec*1000000000+stamp.nanosec
    def receive_command(message):
        if state[0] is None or first_tf[0] is None or handle is None or answered[0]==state[0]['sequence']:return
        ns=message.header.stamp.sec*1000000000+message.header.stamp.nanosec
        if ns<first_tf[0]:return
        now=time.monotonic();origin=stamped.origin_from_header(ns,node.get_clock().now().nanoseconds,now)
        v,w=float(message.twist.linear.x),float(message.twist.angular.z);contract.twist(v,w)
        assert abs(v)<.005 or v*fixed['next_segment']['gear']>0.,'ORIGINAL_SEGMENT_DIRECTION_REJECTED'
        reply=dict(kind='COHERENT_MPPI_MODELED_COMMAND',input_sha256=identity,run_id=args.run_id,sequence=state[0]['sequence'],native_tick=state[0]['native_tick'],body=state[0]['body'],v=v,w=w,origin=origin,controller_identity_sha256=controller_sha,first_tf_ros_ns=first_tf[0],command_ros_ns=ns,reply_monotonic=now,not_measured_response=True)
        sock.sendto(json.dumps(reply,allow_nan=False).encode(),peer[0]);answered[0]=reply['sequence'];commands.append(reply)
    node.create_subscription(TwistStamped,'cmd_vel',receive_command,10);node.create_timer(.02,publish_body);node.create_timer(.1,publish_map)
    action=ActionClient(node,FollowPath,'follow_path');change=node.create_client(ChangeState,'controller_server/change_state')
    def spin():
        assert not stopping[0] and time.monotonic()<deadline,'MPPI_PEER_STOP'
        if server is not None:assert server.poll() is None,'MPPI_CONTROLLER_SERVER_EXIT'
        try:
            payload,sender=sock.recvfrom(65536);value=json.loads(payload)
            if value.get('kind')=='STOP' and value.get('run_id')==args.run_id:stopping[0]=True;return
            validate_request(value,args.run_id,-1 if state[0] is None else state[0]['sequence'],input_sha256=identity,origin_native=fixed['origin']['native_tick'],controller_identity_sha256=controller_sha);state[0]=value;peer[0]=sender;first_tf[0]=None;requests.append(value)
        except BlockingIOError:pass
        rclpy.spin_once(node,timeout_sec=.005)
    def wait(predicate,seconds):
        end=min(deadline,time.monotonic()+seconds)
        while time.monotonic()<end:
            spin()
            if predicate():return
        raise TimeoutError('MPPI_PEER_LIFECYCLE_OR_MAP_TIMEOUT')
    log=(out/'controller.console').open('x')
    try:
        wait(lambda:state[0] is not None,15)
        server=subprocess.Popen(['/opt/ros/jazzy/lib/nav2_controller/controller_server','--ros-args','--disable-external-lib-logs','--disable-rosout-logs','--params-file',str(params)],stdout=log,stderr=subprocess.STDOUT)
        server_record=identity_contract.process_identity(server.pid)
        io.atomic(out/'OWN_SERVER.json',dict(**server_record,params_sha256=data.sha(params),forecast_only=True,controller_identity_sha256=controller_sha))
        wait(change.service_is_ready,20)
        for transition in [1,3]:
            req=ChangeState.Request();req.transition.id=transition;future=change.call_async(req);wait(future.done,15);assert future.result().success
        wait(action.server_is_ready,5)
        wait(lambda:received[0] is not None and map_gate.inspect_map(map_gate.snapshot(received[0]),forecast_grid)['passed'],10)
        io.atomic(out/'DELIVERED_CAUSAL_MAP.json',map_gate.snapshot(received[0]))
        loaded=identity_contract.verify_loaded(server_record,role='MODELED_ROS',value=fixed['controller_binding']);io.atomic(out/'CONTROLLER_LOADED_IDENTITY.json',loaded)
        path=NavPath();path.header.frame_id='odom';path.header.stamp=node.get_clock().now().to_msg()
        for x,y,yaw in fixed['next_segment']['poses']:
            pose=PoseStamped();pose.header=path.header;pose.pose.position.x=x;pose.pose.position.y=y;pose.pose.orientation.z=math.sin(yaw/2);pose.pose.orientation.w=math.cos(yaw/2);path.poses.append(pose)
        goal=FollowPath.Goal();goal.path=path;goal.controller_id='Deadband';goal.goal_checker_id='goal_checker';goal.progress_checker_id='progress_checker';future=action.send_goal_async(goal);wait(future.done,5);handle=future.result();assert handle.accepted;done=handle.get_result_async()
        io.atomic(out/'READY.json',dict(passed=True,engineering_MPPI_plugin_loaded=True,no_synthetic_scans=True,causal_source_tick=fixed['bridge_forecast']['periodic_source_tick'],input_sha256=identity,controller_identity_sha256=controller_sha,models=0))
        while not stopping[0] and time.monotonic()<deadline:
            spin()
            if done.done() and state[0] is not None and answered[0]!=state[0]['sequence']:
                value=done.result();sock.sendto(json.dumps(dict(kind='MPPI_ACTION_DONE',run_id=args.run_id,sequence=state[0]['sequence'],status=value.status,error_code=value.result.error_code,input_sha256=identity,controller_identity_sha256=controller_sha,native_tick=state[0]['native_tick'],body=state[0]['body'],not_measured_response=True)).encode(),peer[0]);answered[0]=state[0]['sequence']
        result.update(passed=stopping[0],engineering_MPPI_plugin_loaded=True,exact_engineering_parameters_sha256=data.sha(params),causal_ball_raster_cells=occupied)
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:server.wait(timeout=4)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=2)
        io.atomic(out/'MODELED_REQUESTS.json',requests);io.atomic(out/'ENGINEERING_MPPI_COMMANDS.json',commands);result.update(closed=True,wall_s=time.monotonic()-started,commands=len(commands),controller_exited=server is None or server.poll() is not None)
        io.atomic(out/'PEER_RESULT.json',result);sock.close();Path(address).unlink(missing_ok=True);log.close();node.destroy_node();rclpy.shutdown()
    print(json.dumps(result,allow_nan=False));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
