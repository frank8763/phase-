"""Source-receipted actual route fork; lifecycle/method not admitted.

Preserves original HORIZON planner; complete native bridge proofs are required
before a queue segment is consumed. No saved tick/control replay rescue.
"""
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
from route_context import *
import importlib.util
_event_spec=importlib.util.spec_from_file_location('v1574_ros_event_source_session',C/'event_session.py');_event_session=importlib.util.module_from_spec(_event_spec);_event_spec.loader.exec_module(_event_session)
prepare_request=_event_session.prepare_request;Session=_event_session.Session
from route_event import validate_envelope
sys.path.insert(0, str(R / "experiments/v1370_overnight_controller_matrix"))
from map_gate import snapshot,inspect_map
sys.path.insert(0, str(R / 'experiments/v1288_baseline_interface'))
from contract import observation, command
_close_spec=importlib.util.spec_from_file_location('v1603_actual_source_closure',C/'provider_close.py');_source_close=importlib.util.module_from_spec(_close_spec);_close_spec.loader.exec_module(_source_close)
from causal_occupancy import CausalBall
_provider_spec=importlib.util.spec_from_file_location('v1574_actual_observation_provider',C/'causal_provider.py');_provider=importlib.util.module_from_spec(_provider_spec);_provider_spec.loader.exec_module(_provider)
from observed_route import nominal_clearance,revalidate
_plan_spec=importlib.util.spec_from_file_location('v1432_bounded_planning_job',R/'experiments/v1479_retirement_scope_binding/planning_job.py');_plan_module=importlib.util.module_from_spec(_plan_spec);_plan_spec.loader.exec_module(_plan_module);PlanningJob=_plan_module.PlanningJob
from segments import split, validate as validate_segment, direction_allowed
from recovery_guard import check as recovery_reserve
from dynamic_reserve import check as dynamic_reserve
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TransformStamped, TwistStamped
from stamped_contract import origin_from_header, local_zero, decode_origin
from evidence_io import Journal, PeerClosure, persist
from nav_msgs.msg import Odometry, Path as NavPath, OccupancyGrid
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from sensor_msgs.msg import LaserScan
from nav2_msgs.action import FollowPath
from lifecycle_msgs.srv import ChangeState
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster
import subprocess


def phase_clock(window,limits):
    # Explicit same frozen phase implementation as the canonical native owner.
    spec=importlib.util.spec_from_file_location('v1479_original_shared_phase_clock',R/'experiments/v1449_route_initializer_binding/phase_budget.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.PhaseBudget(window,limits)


def main():
    task = read(sys.argv[1]);task_check(task)
    if '--entry-check' in sys.argv:
        assert Path(task['nav2_params']).is_file() and task['controller_plugin'] in ['Deadband','RPP']
        print(__import__('json').dumps(dict(passed=True,actual_ros_imports_loaded=True,task_and_params_valid=True,controller_not_started=True,models=0,physical_native=0)))
        return 0
    startup_close='--startup-close-qualification'in sys.argv
    if startup_close:
        window=read(O/'STARTUP_CLOSE_WINDOW.json');authorize_startup_close(task,window)
        normal_end=dict(absolute_deadline_unix=window['absolute_deadline_unix']-5,hard_stop_monotonic=window['hard_stop_monotonic']-5)
    else:
        window=read(O/'ROUND_WINDOW.json');authorize(task,window)
        phases=phase_clock(window,read(C/'LIMITS.json'))
        normal_end=phases.boundary('normal')
    out = Path(task['output']); start = time.monotonic(); deadline = normal_end['hard_stop_monotonic']
    os.sched_setaffinity(0, {3}); rclpy.init(args=['--ros-args','--disable-external-lib-logs','--disable-rosout-logs'])
    node = Node('phase_overnight_baseline_route'); latest = None; received = -1; sequence = 0; rows = []; stopped = False; armed = False;published_scan_messages=0
    known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json');tracker=_provider.ObservedTracker(CausalBall(known,model=task['predictor_model'],forecast_kind=task['forecast_kind']),run_id=task['run_id'],output=Path(task['output']),save=dump)
    mode='track';brake_start=0;replan_reason=None;path_records=[];guard_records=[];center_body=None;sim_time=0.;native_tick=0;pending_novel=False
    measured_envelope=None;handoff_requests=[];bridge=None;bridge_notices=[];completed_bridge_events=0
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    address = str(out.relative_to(R) / 'ros.sock'); sock.bind(address); sock.setblocking(False)
    peer = str(out.relative_to(R) / 'native.sock')
    planner=PlanningJob(out/'planner_jobs',timeout_s=20.,hard_stop_monotonic=normal_end['hard_stop_monotonic'])
    planning_record=None;wait_origin=0;wait_cursor=0
    segment_queue=[];active_gear=1;segment_counter=0;segment_records=[];brake_action='plan';reserve_records=[];dynamic_reserve_records=[]
    tf = TransformBroadcaster(node); static = StaticTransformBroadcaster(node)
    odom = node.create_publisher(Odometry, 'odom', 10); scans = node.create_publisher(LaserScan, 'scan', 10)
    t = TransformStamped(); t.header.stamp = node.get_clock().now().to_msg(); t.header.frame_id = 'base_link'; t.child_frame_id = 'base_scan'; t.transform.rotation.w = 1.; t.transform.translation.x = .30; static.sendTransform(t)

    def send(x):
        try:
            sock.sendto(__import__('json').dumps(x).encode(), peer)
        except (FileNotFoundError, BlockingIOError, ConnectionRefusedError):
            pass

    origin_records=[];origin_rejections=[];pump_timings=[];peer_stop_flag=[False];closing=[False]
    raw_command_journal=Journal(out/'ROS_COMMANDS.jsonl')
    def check_peer_stop():
        if not closing[0] and (peer_stop_flag[0] or (out/'PEER_STOP_REQUEST.json').exists()):raise PeerClosure('PEER_REQUESTED_SAVE_AND_CLOSE')
    node.create_timer(.02,check_peer_stop)

    def emit(v,w,source,origin=None):
        nonlocal sequence
        if latest is None or stopped or not armed:return
        p=dict(run_id=task['run_id'],sequence=sequence,issued_at=time.monotonic(),v=float(v),w=float(w))
        command(p,run_id=task['run_id'],now=time.monotonic(),previous_sequence=sequence-1)
        origin=origin if origin is not None else local_zero(p['issued_at'])
        binding=dict(origin=origin,observation_sequence=latest['sequence'],observation_sampled_at=latest['sampled_at'],observation_native_tick=native_tick)
        row=dict(p,source=source,segment_index=segment_counter,expected_gear=active_gear,**binding)
        rows.append(row);raw_command_journal.append(row);sequence+=1;send(dict(kind='command',command_source=source,**p,**binding))

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
            if ball is not None and mode=='track':
                dynamic_ok,dynamic_proof=dynamic_reserve(center_body,[*ball[0],ball[1]],value.linear.x,value.angular.z)
                dynamic_reserve_records.append(dict(native_tick=native_tick,sim_time=sim_time,body=center_body[:],
                    ball=[*ball[0].tolist(),ball[1]],requested=[value.linear.x,value.angular.z],
                    allowed=dynamic_ok,proof=dynamic_proof,command_sequence=sequence))
                if not dynamic_ok:
                    begin_brake('CAUSAL_FUTURE_BALL_RESERVE')
                    guard_records[-1]['dynamic_reserve']=dynamic_proof
            if pending_novel and mode=='track':
                reserve_ok,reserve_proof=recovery_reserve(known,center_body,value.linear.x,value.angular.z)
                reserve_records.append(dict(native_tick=native_tick,body=center_body[:],requested=[value.linear.x,value.angular.z],allowed=reserve_ok,proof=reserve_proof,command_sequence=sequence))
                if not reserve_ok:
                    begin_brake('KNOWN_STATIC_RECOVERY_RESERVE')
                    guard_records[-1]['recovery_reserve']=reserve_proof
        if mode=='track' and not direction_allowed(value.linear.x,active_gear):
            begin_brake('SINGLE_SEGMENT_DIRECTION_MISMATCH')
        if mode in ('track','bridge_rpp'):
            if mode=='bridge_rpp' and not direction_allowed(value.linear.x,active_gear):raise AssertionError('BRIDGE_ORIGINAL_RPP_DIRECTION')
            emit(value.linear.x,value.angular.z,'CONTROLLER' if mode=='track' else 'ORIGINAL_RPP_WITH_SHARED_BRIDGE',origin)
        else:emit(0.,0.,'CAUSAL_BRAKE_HOLD')

    def brake_timer():
        if mode not in ('track','bridge_rpp'):emit(0.,0.,'CAUSAL_BRAKE_TIMER')
    node.create_timer(.05,brake_timer)

    def receive_twist(message):
        origin=decode_origin(message.header.stamp.sec*1000000000+message.header.stamp.nanosec,node.get_clock().now().nanoseconds,time.monotonic())
        origin_records.append(dict(origin=origin,native_tick=native_tick,sim_time=sim_time))
        if origin['receipt_age_s']>.2:
            origin_rejections.append(dict(origin=origin,native_tick=native_tick,raw_v=message.twist.linear.x,raw_w=message.twist.angular.z,reason='SOURCE_COMMAND_EXPIRED'))
            emit(0.,0.,'EXPIRED_SOURCE_ZERO')
            return
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
        nonlocal latest, received,center_body,sim_time,native_tick,pending_novel,measured_envelope,bridge,mode,h,f,segment_counter,active_gear,brake_start,brake_action,completed_bridge_events,published_scan_messages
        packet = None
        for _ in range(128):
            try:
                value = __import__('json').loads(sock.recv(1024*1024))
                assert not startup_close,'STARTUP_CLOSE_QUALIFICATION_REQUIRES_ZERO_WIRE'
                if value.get('kind','').startswith('BRIDGE_'):
                    assert bridge is not None,'UNSOLICITED_BRIDGE_NOTICE'
                    decision=bridge.accept(value);bridge_notices.append(dict(value=value,decision=decision))
                    dump(out/'BRIDGE_NOTICES.json',bridge_notices)
                    if decision.get('close_round'):raise PeerClosure('NATIVE_CURRENT_BRIDGE_REFUSED')
                    if decision.get('install_original_RPP_path'):
                        assert mode=='bridge_prepare' and segment_queue
                        active_gear=segment_queue[0]['gear'];h,f=send_path(segment_queue[0]['poses']);mode='bridge_rpp'
                    if decision.get('consume_segment'):
                        assert segment_queue;segment_queue.pop(0);segment_counter+=1;completed_bridge_events+=1
                        if value.get('whole_goal_center_distance_m',float('inf'))<=.45 and value.get('whole_forward_progress_m',-float('inf'))>=7.5:
                            mode='route_goal_ready'
                        else:
                            mode='brake';brake_start=value['final_native_tick']-200;brake_action='segment' if segment_queue else 'plan'
                        bridge=None
                    continue
                packet=value
            except BlockingIOError:
                break
        if packet is None:
            return
        measured_envelope=validate_envelope(packet,run_id=task['run_id'],now=time.monotonic(),previous_sequence=received)
        wire=measured_envelope['wire'];native_tick=wire['native_tick'];sim_time=wire['sim_time']
        packet={k:wire[k] for k in ('schema','run_id','sequence','sampled_at','body','ranges_m')}
        observation(packet, run_id=task['run_id'], now=time.monotonic(), previous_sequence=received)
        latest = packet; received = packet['sequence'];center_body=packet['body'][:]
        if task['dynamic']:
            prediction_started=time.monotonic()
            novel=tracker.observe(wire)
            pump_timings.append(dict(native_tick=native_tick,packet_received_age_s=prediction_started-packet['sampled_at'],prediction_wall_s=time.monotonic()-prediction_started))
            if novel and not pending_novel:
                pending_novel=True
                if armed:begin_brake('FIRST_CAUSAL_NOVEL_RETURN')
        x, y, yaw, v, w = packet['body']; x -= .30*math.cos(yaw); y -= .30*math.sin(yaw); stamp = node.get_clock().now().to_msg()
        t = TransformStamped(); t.header.stamp = stamp; t.header.frame_id = 'odom'; t.child_frame_id = 'base_link'; t.transform.translation.x = x; t.transform.translation.y = y; t.transform.rotation.z = math.sin(yaw / 2); t.transform.rotation.w = math.cos(yaw / 2); tf.sendTransform(t)
        od = Odometry(); od.header.stamp = stamp; od.header.frame_id = 'odom'; od.child_frame_id = 'base_link'; od.pose.pose.position.x = x; od.pose.pose.position.y = y; od.pose.pose.orientation = t.transform.rotation; od.twist.twist.linear.x = v; od.twist.twist.angular.z = w; odom.publish(od)
        scan = LaserScan(); scan.header.stamp = stamp; scan.header.frame_id = 'base_scan'; scan.angle_min = 0.; scan.angle_max = math.tau * 31 / 32; scan.angle_increment = math.tau / 32; scan.range_min = .05; scan.range_max = 3.; scan.scan_time = .05; scan.ranges = [max(.05, x) if x < 2.999 else float('inf') for x in packet['ranges_m']]; scans.publish(scan);published_scan_messages+=1

    node.create_timer(.01, publish)
    client = node.create_client(ChangeState, 'controller_server/change_state'); action = ActionClient(node, FollowPath, 'follow_path')
    log = (out / 'controller.console').open('x'); server = subprocess.Popen(['/opt/ros/jazzy/lib/nav2_controller/controller_server', '--ros-args', '--disable-external-lib-logs', '--disable-rosout-logs', '--params-file', task['nav2_params']], stdout=log, stderr=subprocess.STDOUT)
    result = dict(passed=False, physical_models_in_ros=0, commands=0)
    signal.signal(signal.SIGTERM,lambda *_:peer_stop_flag.__setitem__(0,True))

    def wait(predicate, seconds, message):
        until = min(deadline, time.monotonic() + seconds)
        while time.monotonic() < until and remaining(window) > 20:
            rclpy.spin_once(node, timeout_sec=.005)
            assert server.poll() is None, 'CONTROLLER_SERVER_EXIT'
            if predicate():
                return
        raise TimeoutError(message)

    try:
        if startup_close:
            wait(client.service_is_ready,15,'STARTUP_CONTROLLER_LIFECYCLE_SERVICE_MISSING')
            dump(out/'STARTUP_CLOSE_READY.json',dict(actual_cpu=sorted(os.sched_getaffinity(0)),inner_pid=os.getpid(),network_namespace=os.readlink('/proc/self/ns/net'),controller_pid=server.pid,controller_standby_only=True,controller_configured=False,controller_activated=False,FollowPath_called=False,models=0,physical_native=0,actual_wire_received=False,scan_messages=published_scan_messages,params_sha256=__import__('hashlib').sha256(Path(task['nav2_params']).read_bytes()).hexdigest(),source_sha256=__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest()))
            while time.monotonic()<deadline and remaining(window)>5:
                rclpy.spin_once(node,timeout_sec=.005)
                assert server.poll()is None,'STARTUP_STANDBY_CONTROLLER_EXIT'
                assert latest is None and received==-1 and not rows and published_scan_messages==0,'STARTUP_CLOSE_ZERO_INPUT_SCOPE_CHANGED'
            raise TimeoutError('STARTUP_CLOSE_COOPERATIVE_STOP_NOT_RECEIVED')
        wait(lambda: latest is not None and client.service_is_ready(), 45, 'ACTUAL_T0_OR_LIFECYCLE_MISSING')
        for transition in [1, 3]:
            req = ChangeState.Request(); req.transition.id = transition; future = client.call_async(req); wait(future.done, 20, 'LIFECYCLE_TIMEOUT'); assert future.result().success
        wait(action.server_is_ready, 5, 'FOLLOW_PATH_ACTION_MISSING')
        map_checks=[]
        def map_ready():
            if received_map[0] is None:return False
            actual=snapshot(received_map[0]);proof=inspect_map(actual,grid)
            map_checks.append(proof);dump(out/'MAP_ENTRY_CHECKS.json',map_checks);dump(out/'INITIAL_ACTUAL_COSTMAP.json',actual)
            return proof['passed']
        wait(map_ready,10,'CURRENT_ROLLING_PUBLIC_STATIC_MAP_NOT_READY')
        result['public_static_map_receipt']=dict(passed=True,source=grid['source_sha256'],window_proof=map_checks[-1])
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
        while min(normal_end['absolute_deadline_unix']-time.time(),normal_end['hard_stop_monotonic']-time.monotonic())>0:
            rclpy.spin_once(node,timeout_sec=.005)
            assert server.poll() is None,'CONTROLLER_SERVER_EXIT'
            if mode=='route_goal_ready':
                result.update(passed=True,functional_stop='WHOLE_GOAL_AFTER_NATIVE_VERIFIED_COMPLETE_BRIDGE',original_goal_distance_threshold_m=.45,shared_bridge_disclosed=True);break
            if f.done() and mode=='bridge_rpp':
                outcome=f.result()
                assert bridge is not None
                send(dict(kind='BRIDGE_RPP_ACTION_DONE',run_id=task['run_id'],event_index=bridge.event_index,
                    request_sha256=bridge.request_sha256,input_sha256=bridge.input_sha256,
                    certificate_sha256=bridge.certificate_sha256,status=outcome.status,error_code=outcome.result.error_code))
                mode='bridge_tail'
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
                    # Every cusp reaches the native certificate boundary, even
                    # when the geometric sufficient test passes. No tick rescue,
                    # stale component controls, queue discard or direct release.
                    packet=prepare_request(measured_envelope,segment,proof,tracker,
                        run_id=task['run_id'],event_index=len(handoff_requests),
                        brake_start=brake_start,now=time.monotonic())
                    bridge=Session(packet);handoff_requests.append(packet)
                    dump(out/'CURRENT_CUSP_REQUESTS.json',handoff_requests)
                    requests=out/'cusp_requests';requests.mkdir(exist_ok=True)
                    path=requests/('event%04d.json'%packet['request']['event_index']);assert not path.exists()
                    dump(path,packet)
                    send(dict(kind='BRIDGE_CERTIFICATE_REQUEST_FILE',run_id=task['run_id'],
                        event_index=packet['request']['event_index'],request_sha256=bridge.request_sha256,
                        path=str(path.relative_to(R)),file_sha256=__import__('hashlib').sha256(path.read_bytes()).hexdigest()))
                    mode='bridge_prepare'
                    continue
                if replans>=task['maximum_replans']:
                    result.update(passed=False,action_status=6,error_code=104,functional_stop='MAXIMUM_REPLANS');break
                mode='plan';ball=tracker.occupied_ball(sim_time);replans+=1
                planning_record=dict(index=replans,native_tick=native_tick,sim_time=sim_time,body=center_body[:],ball=None if ball is None else [*ball[0].tolist(),ball[1]],started_wall=time.monotonic())
                planner.start(dict(known=known,body=center_body[:],goal=task['goal_xy'],ball=planning_record['ball'],guard=task['planner_guard_m'],native_tick=native_tick,sim_time=sim_time,planner_mode=task['planner_mode']))
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
                        segment_records.append(dict(event='INSTALL_ORDERED_ROUTE',native_tick=native_tick,
                                                    plan_index=replans,segments=segments,body=center_body[:],
                                                    geometry=segment_proof,current_event_required=completed_bridge_events>0))
                        dump(out/'SEGMENT_RECORDS.json',segment_records)
                        if completed_bridge_events>0:
                            # Original planner wait is200; this distinct event never
                            # pretends that250 CUSP steps have already been applied.
                            segment_queue=segments;active_gear=segment['gear']
                            packet=prepare_request(measured_envelope,segment,segment_proof,tracker,
                                run_id=task['run_id'],event_index=len(handoff_requests),brake_start=brake_start,
                                now=time.monotonic(),event_kind='ORDERED_ROUTE_FIRST_SEGMENT_CHECK',
                                plan_index=replans,ordered_segments=segments,completed_bridge_events=completed_bridge_events)
                            bridge=Session(packet);handoff_requests.append(packet)
                            dump(out/'CURRENT_CUSP_REQUESTS.json',handoff_requests)
                            requests=out/'cusp_requests';requests.mkdir(exist_ok=True)
                            path=requests/('event%04d.json'%packet['request']['event_index']);assert not path.exists();dump(path,packet)
                            send(dict(kind='BRIDGE_CERTIFICATE_REQUEST_FILE',run_id=task['run_id'],event_index=packet['request']['event_index'],request_sha256=bridge.request_sha256,path=str(path.relative_to(R)),file_sha256=__import__('hashlib').sha256(path.read_bytes()).hexdigest()))
                            mode='bridge_prepare'
                        else:
                            segment_queue=segments[1:];active_gear=segment['gear'];segment_counter+=1
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
    except PeerClosure as exc:
        result.update(passed=False,functional_stop='COOPERATIVE_PEER_CLOSED',peer_close_reason=str(exc))
    except BaseException as exc:
        result.update(error=repr(exc), traceback=traceback.format_exc())
    finally:
        closing[0]=True;stopped=True
        source_journal_close=_source_close.close(tracker,result,lambda:send(dict(kind='stop',run_id=task['run_id'],passed=result['passed'],issued_at=time.monotonic())))
        artifacts=[('CAUSAL_SOURCE_JOURNAL_CLOSED.json',source_journal_close),('ROS_COMMANDS.json',rows),('CAUSAL_OBSERVATIONS.json',tracker.records),
          ('CAUSAL_BRAKE_RECORDS.json',guard_records),('CAUSAL_ROUTE_RECORDS.json',path_records),
          ('SEGMENT_RECORDS.json',segment_records),('CURRENT_CUSP_REQUESTS.json',handoff_requests),('BRIDGE_NOTICES.json',bridge_notices),('RECOVERY_RESERVE_RECORDS.json',reserve_records),
          ('DYNAMIC_RESERVE_RECORDS.json',dynamic_reserve_records),
          ('STAMPED_ORIGIN_RECORDS.json',origin_records),('STAMPED_REJECTIONS.json',origin_rejections),
          ('OBSERVATION_PUMP_TIMINGS.json',pump_timings),('FORECAST_RECORDS.json',tracker.forecasts),
          ('CAUSAL_PREDICTION_MODEL.json',tracker.snapshot())]
        result.update(ordered_segments_installed=segment_counter,commands=len(rows),wall_s=time.monotonic()-start,published_scan_messages=published_scan_messages,startup_close_qualification=startup_close,actual_wire_received=latest is not None,FollowPath_unexecuted_in_startup_scope=startup_close and not armed)
        result=persist(out,artifacts,result,closed=False)
        try:
            planner.cancel()
            if server.poll() is None:
                server.terminate()
                try:server.wait(timeout=4)
                except subprocess.TimeoutExpired:server.kill();server.wait(timeout=2)
        except BaseException as exc:result.update(passed=False,cleanup_error=repr(exc))
        finally:
            raw_command_journal.close()
            result.update(controller_server_exited=server.poll() is not None,wall_s=time.monotonic()-start)
            result=persist(out,artifacts,result,closed=True)
            sock.close();Path(address).unlink(missing_ok=True);log.close();node.destroy_node();rclpy.shutdown()
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    
    _entry_spec=importlib.util.spec_from_file_location('v1432_route_output_entry',R/'experiments/v1479_retirement_scope_binding/entry_boundary.py');_entry=importlib.util.module_from_spec(_entry_spec);_entry_spec.loader.exec_module(_entry);raise SystemExit(main()if '--entry-check'in sys.argv else _entry.run(main))
