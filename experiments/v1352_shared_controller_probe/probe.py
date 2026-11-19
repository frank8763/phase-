"""One actual Nav2 controller, one frozen stationary saved input, no physics."""
import importlib.abc
import os
import statistics
import subprocess
import sys
import time
import traceback
from common import *


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'vehicle', 'torch', 'factory', 'physical'}:
            raise AssertionError('SOFTWARE_ONLY_IMPORT ' + name)


sys.meta_path.insert(0, NoPhysical())
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from geometry_msgs.msg import PoseStamped, TransformStamped, Twist
from nav_msgs.msg import Odometry, Path as NavPath, OccupancyGrid
from sensor_msgs.msg import LaserScan
from nav2_msgs.action import FollowPath
from lifecycle_msgs.srv import ChangeState
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster


class Fixture(Node):
    def __init__(self, task, saved):
        super().__init__('phase_v1352_saved_controller_fixture')
        self.task, self.saved = task, saved
        self.contract = load_contract()
        self.tf, self.static = TransformBroadcaster(self), StaticTransformBroadcaster(self)
        t = TransformStamped(); t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id, t.child_frame_id = 'base_link', 'base_scan'
        t.transform.rotation.w = 1.; t.transform.translation.x = .30
        self.static.sendTransform(t)
        self.odom = self.create_publisher(Odometry, 'odom', 10)
        self.scan = self.create_publisher(LaserScan, 'scan', 10)
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL, reliability=ReliabilityPolicy.RELIABLE)
        self.map_pub = self.create_publisher(OccupancyGrid, '/phase_public_static', qos)
        self.create_subscription(OccupancyGrid, '/local_costmap/costmap', self.receive_map, qos)
        self.create_subscription(Twist, 'cmd_vel', self.receive, 100)
        self.sequence, self.observations, self.rows, self.map_received = 0, [], [], None
        self.create_timer(.02, self.publish)
        self.create_timer(.1, self.publish_map)
        self.action = ActionClient(self, FollowPath, 'follow_path')
        self.change = self.create_client(ChangeState, 'controller_server/change_state')

    def receive_map(self, msg):
        self.map_received = dict(resolution=msg.info.resolution, width=msg.info.width, height=msg.info.height,
                                 origin=[msg.info.origin.position.x, msg.info.origin.position.y], data=list(msg.data))

    def publish_map(self):
        grid = self.saved['map_grid']; msg = OccupancyGrid()
        msg.header.frame_id = 'odom'; msg.header.stamp = self.get_clock().now().to_msg()
        msg.info.resolution = grid['resolution']; msg.info.width = grid['width']; msg.info.height = grid['height']
        msg.info.origin.position.x, msg.info.origin.position.y = grid['origin'][:2]
        msg.info.origin.orientation.w = 1.; msg.data = grid['data']; self.map_pub.publish(msg)

    def publish(self):
        stamp = self.get_clock().now().to_msg(); now = time.monotonic()
        packet = dict(schema=1, run_id=self.task['id'], sequence=self.sequence, sampled_at=now, **self.saved['fixture'])
        self.contract.observation(packet, run_id=self.task['id'], now=now, previous_sequence=self.sequence-1)
        self.observations.append(packet); self.sequence += 1
        x,y,yaw,v,w = packet['body']
        t = TransformStamped(); t.header.stamp, t.header.frame_id, t.child_frame_id = stamp, 'odom', 'base_link'
        t.transform.translation.x, t.transform.translation.y = x,y
        t.transform.rotation.z, t.transform.rotation.w = math.sin(yaw/2), math.cos(yaw/2); self.tf.sendTransform(t)
        od = Odometry(); od.header.stamp, od.header.frame_id, od.child_frame_id = stamp, 'odom', 'base_link'
        od.pose.pose.position.x, od.pose.pose.position.y = x,y; od.pose.pose.orientation = t.transform.rotation
        od.twist.twist.linear.x, od.twist.twist.angular.z = v,w; self.odom.publish(od)
        scan = LaserScan(); scan.header.stamp, scan.header.frame_id = stamp, 'base_scan'
        scan.angle_min, scan.angle_max, scan.angle_increment = 0., math.tau*31/32, math.tau/32
        scan.range_min, scan.range_max, scan.scan_time = .05, 3., .04
        scan.ranges = [float('inf') if v >= 2.999 else max(.05,v) for v in packet['ranges_m']]
        self.scan.publish(scan)

    def receive(self, msg):
        now = time.monotonic(); v,w = float(msg.linear.x),float(msg.angular.z)
        raw_error = None
        try: self.contract.twist(v,w)
        except ValueError as exc: raw_error = str(exc)
        age = now-self.observations[-1]['sampled_at'] if self.observations else None
        direction_ok = abs(v)<.005 or v*self.saved['segment']['gear']>0
        reason = raw_error or ('STALE_INPUT' if age is None or age>.2 else None) or ('SEGMENT_DIRECTION_REFUSED' if not direction_ok else None)
        envelope = dict(run_id=self.task['id'], sequence=len(self.rows), issued_at=now,
                        v=0. if reason else v, w=0. if reason else w)
        applied_at = time.monotonic()
        self.contract.command(envelope, run_id=self.task['id'], now=applied_at, previous_sequence=len(self.rows)-1)
        self.rows.append(dict(received_at=now, v=v, w=w, raw_contract_error=raw_error,
                              observation_age_s=age, direction_ok=direction_ok, adapter_reason=reason,
                              envelope=envelope, adapter_checked_at=applied_at, generation_to_receipt_age_s=None))


def main():
    task = read(C/'TASKS.json')[int(sys.argv[1])]; out = O/task['id']; out.mkdir(exist_ok=False)
    saved = read(R/task['input_file']); original_hash = saved.pop('common_input_sha256')
    assert digest(saved) == original_hash == task['common_input_sha256']
    saved['common_input_sha256'] = original_hash
    os.sched_setaffinity(0,{3}); os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    started = time.monotonic(); rclpy.init(); node = Fixture(task,saved); server = None
    result = dict(interface_qualified=False, task=task, models=0, physical_native=0, software_only=True,
                  common_input_sha256=original_hash, command_origin_age_known=False)
    log = (out/'controller.console').open('x')
    def wait(predicate, seconds):
        end = min(started+55, time.monotonic()+seconds)
        while time.monotonic()<end:
            rclpy.spin_once(node, timeout_sec=.005)
            if server is not None and server.poll() is not None: raise RuntimeError('CONTROLLER_SERVER_EXIT')
            if predicate(): return
        raise TimeoutError('SOFTWARE_STAGE_TIMEOUT')
    def settle(seconds):
        end = time.monotonic()+seconds; wait(lambda:time.monotonic()>=end, seconds+1)
    try:
        params = C/(task['method']+'_params.json')
        server = subprocess.Popen(['/opt/ros/jazzy/lib/nav2_controller/controller_server','--ros-args','--params-file',str(params)], stdout=log, stderr=subprocess.STDOUT)
        dump(out/'OWN_SERVER.json',dict(pid=server.pid, params_sha256=sha(params)))
        wait(node.change.service_is_ready,15)
        for transition in [1,3]:
            req = ChangeState.Request(); req.transition.id = transition
            future = node.change.call_async(req); wait(future.done,15)
            assert future.result().success, 'LIFECYCLE_REJECTED'
        wait(node.action.server_is_ready,5)
        wait(lambda:node.map_received is not None and any(v==100 for v in node.map_received['data']),5)
        settle(.5)
        dump(out/'DELIVERED_COSTMAP.json',node.map_received)
        required = ['libphase_executable_rpp.so'] if task['method']=='rpp' else ['libphase_deadband_mppi.so','libcoherent.so','libmppi_controller.so']
        maps = Path('/proc/%s/maps'%server.pid).read_text()
        assert all(name in maps for name in required), 'ACTUAL_PLUGIN_NOT_LOADED'
        result['loaded_actual_plugin_libraries'] = required
        path = NavPath(); path.header.frame_id='odom'; path.header.stamp=node.get_clock().now().to_msg()
        for x,y,yaw in saved['segment']['poses']:
            pose=PoseStamped(); pose.header=path.header; pose.pose.position.x,pose.pose.position.y=x,y
            pose.pose.orientation.z,pose.pose.orientation.w=math.sin(yaw/2),math.cos(yaw/2);path.poses.append(pose)
        goal=FollowPath.Goal();goal.path=path;goal.controller_id=task['plugin'];goal.goal_checker_id='goal_checker';goal.progress_checker_id='progress_checker'
        offset=len(node.rows);sent=time.monotonic(); future=node.action.send_goal_async(goal);wait(future.done,5)
        handle=future.result();assert handle.accepted,'FOLLOW_PATH_REJECTED';done=handle.get_result_async()
        wait(lambda:done.done() or len(node.rows)-offset>=24,5)
        terminal_before_cancel=done.done()
        if not terminal_before_cancel:
            cancel=handle.cancel_goal_async();wait(cancel.done,3);assert cancel.result().goals_canceling,'CANCEL_REJECTED';wait(done.done,3)
        settle(.1)
        rows=node.rows[offset:];moving=[v for v in rows if abs(v['v'])>=.005]
        admitted=[v for v in rows if abs(v['envelope']['v'])>=.005]
        gaps=[b['received_at']-a['received_at'] for a,b in zip(rows,rows[1:])]
        action_result=done.result(); result_fields={key:getattr(action_result.result,key) for key in action_result.result.get_fields_and_field_types()}
        anomaly=any(v['raw_contract_error'] or v['adapter_reason']=='STALE_INPUT' for v in rows)
        result.update(interface_qualified=not anomaly, action_accepted=True, terminal_before_cancel=terminal_before_cancel,
                      action_status=action_result.status, action_result=result_fields, raw_callbacks=len(rows),
                      raw_moving_commands=len(moving), admitted_moving_commands=len(admitted),
                      wrong_direction_commands=sum(not v['direction_ok'] for v in rows),
                      classification='CONTROL_OR_INPUT_ANOMALY' if anomaly else 'LEGAL_ADMITTED_COMMAND' if admitted else 'RECORDED_FUNCTIONAL_REFUSAL',
                      first_raw_after_goal_s=rows[0]['received_at']-sent if rows else None,
                      first_nonzero_after_goal_s=moving[0]['received_at']-sent if moving else None,
                      first_admitted_after_goal_s=admitted[0]['received_at']-sent if admitted else None,
                      callback_spacing_s=dict(median=statistics.median(gaps) if gaps else None, maximum=max(gaps,default=None)),
                      raw_moving_signs=sorted(set(1 if row['v']>0 else -1 for row in moving)),
                      maximum_observation_age_s=max((row['observation_age_s'] for row in rows),default=None),
                      goal_sent_monotonic=sent, measured_callback_offset=offset,
                      nav2_action_error_is_algorithm_outcome=terminal_before_cancel)
    except BaseException as exc:
        result.update(error=repr(exc),traceback=traceback.format_exc(),classification='INFRASTRUCTURE_OR_EVIDENCE_ANOMALY')
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try: server.wait(timeout=4)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=2)
        dump(out/'RAW_COMMANDS.json',node.rows);dump(out/'OBSERVATION_PLAYBACK.json',node.observations)
        result.update(wall_s=time.monotonic()-started,controller_server_exited=server is None or server.poll() is not None,
                      no_model_modules_loaded=not any(k in sys.modules for k in ['mujoco','vehicle','torch']))
        dump(out/'RESULT.json',result);log.close();node.destroy_node();rclpy.shutdown()
    print(json.dumps(result));return 0 if result['interface_qualified'] else 1


if __name__ == '__main__':raise SystemExit(main())
