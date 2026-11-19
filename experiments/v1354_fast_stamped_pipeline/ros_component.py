"""Real upstream RPP on actual body/scan only. No vehicle imports in ROS."""
import importlib.abc
import math
import os
from pathlib import Path
import socket
import sys
import time
import traceback
import signal


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'vehicle', 'torch', 'factory', 'physical'}:
            raise AssertionError('ROS_PHYSICAL_IMPORT_FORBIDDEN ' + name)


sys.meta_path.insert(0, NoPhysical())
from component_context import *
sys.path.insert(0, str(R / 'experiments/v1288_baseline_interface'))
from contract import observation, command
from causal_occupancy import CausalBall
from observed_route import nominal_clearance,revalidate
from planning_job import PlanningJob
from segments import split, validate as validate_segment, direction_allowed
from recovery_guard import check as recovery_reserve
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TransformStamped, TwistStamped
from stamped_contract import origin_from_header, local_zero
from nav_msgs.msg import Odometry, Path as NavPath, OccupancyGrid
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from sensor_msgs.msg import LaserScan
from nav2_msgs.action import FollowPath
from lifecycle_msgs.srv import ChangeState
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster
import subprocess


def main():
    task = read(sys.argv[1]); window = read(O / 'ROUND_WINDOW.json'); authorize(task, window)
    if '--entry-check' in sys.argv:
        assert Path(task['nav2_params']).is_file() and task['controller_plugin'] in ['Deadband','RPP']
        print(__import__('json').dumps(dict(passed=True,actual_ros_imports_loaded=True,task_and_params_valid=True,controller_not_started=True,models=0,physical_native=0)))
        return 0
    out = Path(task['output']); start = time.monotonic(); deadline = start + 1380
    os.sched_setaffinity(0, {3, 4, 5}); rclpy.init()
    node = Node('phase_overnight_baseline_route'); latest = None; received = -1; sequence = 0; rows = []; stopped = False; armed = False
    known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json');tracker=CausalBall(known)
    mode='track';brake_start=0;replan_reason=None;path_records=[];guard_records=[];center_body=None;sim_time=0.;native_tick=0;pending_novel=False
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    address = str(out.relative_to(R) / 'ros.sock'); sock.bind(address); sock.setblocking(False)
    peer = str(out.relative_to(R) / 'native.sock')
    planner=PlanningJob(out/'planner_jobs',timeout_s=20.,hard_stop_monotonic=window['hard_stop_monotonic'])
    planning_record=None;wait_origin=0;wait_cursor=0
    segment_queue=[];active_gear=1;segment_counter=0;segment_records=[];brake_action='plan';reserve_records=[]
    tf = TransformBroadcaster(node); static = StaticTransformBroadcaster(node)
    odom = node.create_publisher(Odometry, 'odom', 10); scans = node.create_publisher(LaserScan, 'scan', 10)
    t = TransformStamped(); t.header.stamp = node.get_clock().now().to_msg(); t.header.frame_id = 'base_link'; t.child_frame_id = 'base_scan'; t.transform.rotation.w = 1.; t.transform.translation.x = .30; static.sendTransform(t)

    def send(x):
        try:
            sock.sendto(__import__('json').dumps(x).encode(), peer)
        except (FileNotFoundError, BlockingIOError, ConnectionRefusedError):
            pass

    origin_records=[]

    def emit(v,w,source,origin=None):
        nonlocal sequence
        if latest is None or stopped or not armed:return
        p=dict(run_id=task['run_id'],sequence=sequence,issued_at=time.monotonic(),v=float(v),w=float(w))
        command(p,run_id=task['run_id'],now=time.monotonic(),previous_sequence=sequence-1)
        origin=origin if origin is not None else local_zero(p['issued_at'])
        binding=dict(origin=origin,observation_sequence=latest['sequence'],observation_sampled_at=latest['sampled_at'],observation_native_tick=native_tick)
        rows.append(dict(p,source=source,segment_index=segment_counter,expected_gear=active_gear,**binding));sequence+=1;send(dict(kind='command',**p,**binding))

    def begin_brake(reason):
        nonlocal mode,brake_start,replan_reason,brake_action
        if mode=='track':
            mode='brake';brake_start=native_tick;replan_reason=reason;brake_action='segment' if reason=='GEAR_CUSP_COMPLETE' else 'plan'
            guard_records.append(dict(native_tick=native_tick,sim_time=sim_time,reason=reason,body=center_body))

    def receive_body_twist(value,origin):
        if latest is None or stopped or not armed:return
        command(dict(run_id=task['run_id'],sequence=sequence,issued_at=time.monotonic(),v=float(value.linear.x),w=float(value.angular.z)),run_id=task['run_id'],now=time.monotonic(),previous_sequence=sequence-1)
        if task['dynamic']:
            ball=tracker.occupied_ball(sim_time)
            if ball is not None and nominal_clearance(center_body,*ball)<=.25:begin_brake('CAUSAL_FUTURE_BALL_RESERVE')
            if pending_novel and mode=='track':
                reserve_ok,reserve_proof=recovery_reserve(known,center_body,value.linear.x,value.angular.z)
                reserve_records.append(dict(native_tick=native_tick,body=center_body[:],requested=[value.linear.x,value.angular.z],allowed=reserve_ok,proof=reserve_proof,command_sequence=sequence))
                if not reserve_ok:
                    begin_brake('KNOWN_STATIC_RECOVERY_RESERVE')
                    guard_records[-1]['recovery_reserve']=reserve_proof
        if mode=='track' and not direction_allowed(value.linear.x,active_gear):
            begin_brake('SINGLE_SEGMENT_DIRECTION_MISMATCH')
        if mode=='track':emit(value.linear.x,value.angular.z,'CONTROLLER',origin)
        else:emit(0.,0.,'CAUSAL_BRAKE_HOLD')

    def brake_timer():
        if mode!='track':emit(0.,0.,'CAUSAL_BRAKE_TIMER')
    node.create_timer(.05,brake_timer)

    def receive_twist(message):
        origin=origin_from_header(message.header.stamp.sec*1000000000+message.header.stamp.nanosec,node.get_clock().now().nanoseconds,time.monotonic())
        origin_records.append(dict(origin=origin,native_tick=native_tick,sim_time=sim_time))
        receive_body_twist(message.twist,origin)
    node.create_subscription(TwistStamped, 'cmd_vel', receive_twist, 10)
    grid=read(R/'experiments/v1331_common_static_map/PUBLIC_STATIC_GRID.json')
    qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE)
    map_pub=node.create_publisher(OccupancyGrid,'/phase_public_static',qos)
    received_map=[None]
    node.create_subscription(OccupancyGrid,'/local_costmap/costmap',lambda value:received_map.__setitem__(0,value),qos)
    def publish_map():
        message=OccupancyGrid();message.header.frame_id='odom';message.header.stamp=node.get_clock().now().to_msg()
        message.info.resolution=grid['resolution'];message.info.width=grid['width'];message.info.height=grid['height']
        message.info.origin.position.x=grid['origin'][0];message.info.origin.position.y=grid['origin'][1];message.info.origin.orientation.w=1.
        message.data=tracker.raster(grid,sim_time).ravel().tolist() if task['dynamic'] else grid['data'];map_pub.publish(message)
    node.create_timer(.1,publish_map)

    def publish():
        nonlocal latest, received,center_body,sim_time,native_tick,pending_novel
        packet = None
        for _ in range(128):
            try:
                packet = __import__('json').loads(sock.recv(65536))
            except BlockingIOError:
                break
        if packet is None:
            return
        native_tick=packet.pop('native_tick');sim_time=packet.pop('sim_time')
        observation(packet, run_id=task['run_id'], now=time.monotonic(), previous_sequence=received)
        latest = packet; received = packet['sequence'];center_body=packet['body'][:]
        if task['dynamic']:
            novel=tracker.update(native_tick=native_tick,sim_time=sim_time,center_body=center_body,ranges=packet['ranges_m'])
            if novel and not pending_novel:
                pending_novel=True
                if armed:begin_brake('FIRST_CAUSAL_NOVEL_RETURN')
        x, y, yaw, v, w = packet['body']; x -= .30*math.cos(yaw); y -= .30*math.sin(yaw); stamp = node.get_clock().now().to_msg()
        t = TransformStamped(); t.header.stamp = stamp; t.header.frame_id = 'odom'; t.child_frame_id = 'base_link'; t.transform.translation.x = x; t.transform.translation.y = y; t.transform.rotation.z = math.sin(yaw / 2); t.transform.rotation.w = math.cos(yaw / 2); tf.sendTransform(t)
        od = Odometry(); od.header.stamp = stamp; od.header.frame_id = 'odom'; od.child_frame_id = 'base_link'; od.pose.pose.position.x = x; od.pose.pose.position.y = y; od.pose.pose.orientation = t.transform.rotation; od.twist.twist.linear.x = v; od.twist.twist.angular.z = w; odom.publish(od)
        scan = LaserScan(); scan.header.stamp = stamp; scan.header.frame_id = 'base_scan'; scan.angle_min = 0.; scan.angle_max = math.tau * 31 / 32; scan.angle_increment = math.tau / 32; scan.range_min = .05; scan.range_max = 3.; scan.scan_time = .05; scan.ranges = [max(.05, x) if x < 2.999 else float('inf') for x in packet['ranges_m']]; scans.publish(scan)

    node.create_timer(.01, publish)
    client = node.create_client(ChangeState, 'controller_server/change_state'); action = ActionClient(node, FollowPath, 'follow_path')
    log = (out / 'controller.console').open('x'); server = subprocess.Popen(['/opt/ros/jazzy/lib/nav2_controller/controller_server', '--ros-args', '--params-file', task['nav2_params']], stdout=log, stderr=subprocess.STDOUT)
    result = dict(passed=False, physical_models_in_ros=0, commands=0)
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('PEER_STOP_OR_ROOT_DEADLINE')))

    def wait(predicate, seconds, message):
        until = min(deadline, time.monotonic() + seconds)
        while time.monotonic() < until and remaining(window) > 20:
            rclpy.spin_once(node, timeout_sec=.005)
            assert server.poll() is None, 'CONTROLLER_SERVER_EXIT'
            if predicate():
                return
        raise TimeoutError(message)

    try:
        wait(lambda: latest is not None and client.service_is_ready(), 45, 'ACTUAL_T0_OR_LIFECYCLE_MISSING')
        for transition in [1, 3]:
            req = ChangeState.Request(); req.transition.id = transition; future = client.call_async(req); wait(future.done, 20, 'LIFECYCLE_TIMEOUT'); assert future.result().success
        wait(action.server_is_ready, 5, 'FOLLOW_PATH_ACTION_MISSING')
        wait(lambda:received_map[0] is not None,5,'PUBLIC_STATIC_MAP_NOT_RECEIVED')
        cm=received_map[0];px,py=-3.15,0.;ix=int((px-cm.info.origin.position.x)/cm.info.resolution);iy=int((py-cm.info.origin.position.y)/cm.info.resolution)
        assert 0<=ix<cm.info.width and 0<=iy<cm.info.height and cm.data[iy*cm.info.width+ix]==100,'PUBLIC_STATIC_OBSTACLE_MISSING'
        result['public_static_map_receipt']=dict(passed=True,checked_world=[px,py],value=100,source=grid['source_sha256'])
        dump(out/'INITIAL_ACTUAL_COSTMAP.json',dict(width=cm.info.width,height=cm.info.height,resolution=cm.info.resolution,origin=[cm.info.origin.position.x,cm.info.origin.position.y],data=list(cm.data)))
        def send_path(poses):
            path=NavPath();path.header.frame_id='odom';path.header.stamp=node.get_clock().now().to_msg()
            for x,y,yaw in poses:
                p=PoseStamped();p.header=path.header;p.pose.position.x=float(x);p.pose.position.y=float(y);p.pose.orientation.z=math.sin(yaw/2);p.pose.orientation.w=math.cos(yaw/2);path.poses.append(p)
            g=FollowPath.Goal();g.path=path;g.controller_id=task['controller_plugin'];g.goal_checker_id='goal_checker';g.progress_checker_id='progress_checker'
            future=action.send_goal_async(g);wait(future.done,5,'GOAL_ACCEPT_TIMEOUT');handle=future.result();assert handle.accepted
            return handle,handle.get_result_async()
        h,f=send_path(task['reference_path']);result['action_accepted']=True
        armed=True;send(dict(kind='arm',run_id=task['run_id'],issued_at=time.monotonic()))
        start_nav=time.monotonic();replans=0;wait_native=0
        while time.monotonic()-start_nav<1200 and remaining(window)>100:
            rclpy.spin_once(node,timeout_sec=.005)
            assert server.poll() is None,'CONTROLLER_SERVER_EXIT'
            if f.done() and mode=='track':
                outcome=f.result();distance=math.hypot(center_body[0]-task['goal_xy'][0],center_body[1]-task['goal_xy'][1])
                if outcome.status==4 and distance<=.45:
                    result.update(passed=True,action_status=4,error_code=outcome.result.error_code);break
                if not task['dynamic']:
                    result.update(passed=False,action_status=outcome.status,error_code=outcome.result.error_code);break
                begin_brake('GEAR_CUSP_COMPLETE' if outcome.status==4 and segment_queue else 'LOCAL_SEGMENT_COMPLETE_OR_REFUSED')
            if mode=='brake' and native_tick-brake_start>=(250 if brake_action=='segment' else 200) and max(abs(v) for v in center_body[3:])<=.003:
                if not f.done():
                    cancel=h.cancel_goal_async();wait(cancel.done,5,'REPLAN_CANCEL_TIMEOUT');wait(f.done,5,'REPLAN_CANCEL_RESULT_TIMEOUT')
                if brake_action=='segment' and segment_queue:
                    segment=segment_queue[0];ball=tracker.occupied_ball(sim_time)
                    valid,proof=validate_segment(segment,center_body,known,ball,task['planner_guard_m'])
                    segment_records.append(dict(event='CUSP_NEXT_SEGMENT_CHECK',native_tick=native_tick,
                                                brake_start=brake_start,body=center_body[:],gear=segment['gear'],
                                                geometry=proof,accepted=valid))
                    dump(out/'SEGMENT_RECORDS.json',segment_records)
                    if valid:
                        segment_queue.pop(0);active_gear=segment['gear'];segment_counter+=1
                        h,f=send_path(segment['poses']);mode='track'
                        continue
                    segment_queue=[];brake_action='plan'
                if replans>=task['maximum_replans']:
                    result.update(passed=False,action_status=6,error_code=104,functional_stop='MAXIMUM_REPLANS');break
                mode='plan';ball=tracker.occupied_ball(sim_time);replans+=1
                planning_record=dict(index=replans,native_tick=native_tick,sim_time=sim_time,body=center_body[:],ball=None if ball is None else [*ball[0].tolist(),ball[1]],started_wall=time.monotonic())
                planner.start(dict(known=known,body=center_body[:],goal=task['goal_xy'],ball=planning_record['ball'],guard=task['planner_guard_m'],native_tick=native_tick,sim_time=sim_time))
                # Main loop resumes immediately; ROS packets/TF/map/brake timers
                # continue while a separate pure-data process searches.
            if mode=='plan':
                value=planner.poll()
                if value is not None:
                    assert not value.get('error'),'PLANNER_WORKER_ERROR '+str(value.get('error'))
                    planning_record.update(completed_native=native_tick,completed_sim_time=sim_time,wall_s=time.monotonic()-planning_record['started_wall'],report=value.get('report'),functional_timeout=value.get('functional_timeout',False))
                    poses=value.get('path');ball=tracker.occupied_ball(sim_time)
                    valid,validation=revalidate(known,poses,center_body,ball,guard=task['planner_guard_m'])
                    planning_record['live_result_validation']=validation
                    if valid:
                        rear=[row[:3] for row in poses];planning_record['rear_path_with_gears']=poses;planning_record['rear_path']=rear
                        path_records.append(planning_record);dump(out/'CAUSAL_ROUTE_RECORDS.json',path_records)
                        segments=split(poses);segment=segments[0]
                        valid_segment,segment_proof=validate_segment(segment,center_body,known,ball,task['planner_guard_m'])
                        if not valid_segment:
                            planning_record['first_segment_refusal']=segment_proof
                            dump(out/'CAUSAL_ROUTE_RECORDS.json',path_records)
                            mode='wait';wait_origin=native_tick;wait_cursor=native_tick
                            continue
                        segment_queue=segments[1:];active_gear=segment['gear'];segment_counter+=1
                        segment_records.append(dict(event='INSTALL_ORDERED_ROUTE',native_tick=native_tick,
                                                    plan_index=replans,segments=segments,body=center_body[:],
                                                    geometry=segment_proof))
                        dump(out/'SEGMENT_RECORDS.json',segment_records)
                        h,f=send_path(segment['poses']);mode='track'
                    else:
                        path_records.append(planning_record);dump(out/'CAUSAL_ROUTE_RECORDS.json',path_records)
                        mode='wait';wait_origin=native_tick;wait_cursor=native_tick
            if mode=='wait':
                wait_native+=max(0,native_tick-wait_cursor);wait_cursor=native_tick
                if wait_native>=task['maximum_wait_native']:
                    result.update(passed=False,action_status=6,error_code=104,functional_stop='NO_CAUSAL_ROUTE_AFTER_BOUNDED_WAIT');break
                if native_tick-wait_origin>=500:mode='brake';brake_start=native_tick-200
        else:result.update(passed=False,action_status=6,error_code=104,functional_stop='BOUNDED_NAVIGATION_WALL')
        result.update(causal_observation_updates=len(tracker.records),causal_route_proposals=replans,wait_native_report_only=wait_native)
    except BaseException as exc:
        result.update(error=repr(exc), traceback=traceback.format_exc())
    finally:
        planner.cancel()
        stopped = True; send(dict(kind='stop', run_id=task['run_id'], passed=result['passed'], issued_at=time.monotonic()))
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=4)
            except subprocess.TimeoutExpired:
                server.kill(); server.wait(timeout=2)
        dump(out/'CAUSAL_OBSERVATIONS.json',tracker.records);dump(out/'CAUSAL_BRAKE_RECORDS.json',guard_records);dump(out/'CAUSAL_ROUTE_RECORDS.json',path_records)
        dump(out/'SEGMENT_RECORDS.json',segment_records)
        dump(out/'RECOVERY_RESERVE_RECORDS.json',reserve_records)
        dump(out/'STAMPED_ORIGIN_RECORDS.json',origin_records)
        result.update(ordered_segments_installed=segment_counter,commands=len(rows), wall_s=time.monotonic() - start); dump(out / 'ROS_COMMANDS.json', rows); dump(out / 'ROS_RESULT.json', result); sock.close(); Path(address).unlink(missing_ok=True); log.close(); node.destroy_node(); rclpy.shutdown()
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
