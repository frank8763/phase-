"""Actual installed Nav2 controllers on stationary synthetic observations only."""
import importlib.abc
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
import traceback


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'vehicle', 'torch', 'factory', 'physical'}:
            raise AssertionError('SOFTWARE_ONLY_IMPORT ' + name)


sys.meta_path.insert(0, NoPhysical())
from contract import observation, twist
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TransformStamped, Twist
from nav_msgs.msg import Odometry, Path as NavPath, OccupancyGrid
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from sensor_msgs.msg import LaserScan
from nav2_msgs.action import FollowPath
from lifecycle_msgs.srv import ChangeState, GetState
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster

R = Path(__file__).resolve().parents[3]
C = Path(__file__).resolve().parent
O = R / 'runs/v1332_common_map_static_campaign/software'


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def percentile(values, fraction):
    return sorted(values)[min(len(values) - 1, int((len(values) - 1) * fraction))] if values else None


class Fixture(Node):
    def __init__(self):
        super().__init__('phase_baseline_software_fixture')
        self.tf = TransformBroadcaster(self)
        self.static = StaticTransformBroadcaster(self)
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        t.child_frame_id = 'base_scan'
        t.transform.rotation.w = 1.
        t.transform.translation.x = .30
        self.static.sendTransform(t)
        self.odom = self.create_publisher(Odometry, 'odom', 10)
        self.scan = self.create_publisher(LaserScan, 'scan', 10)
        self.rows, self.packets = [], []
        self.label, self.sequence = 'startup', 0
        self.fixture = json.loads((C / 'SAVED_INPUT.json').read_text())
        self.map_grid=json.loads((R/'experiments/v1331_common_static_map/PUBLIC_STATIC_GRID.json').read_text())
        self.costmap=None
        qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE)
        self.map_pub=self.create_publisher(OccupancyGrid,'/phase_public_static',qos)
        self.create_subscription(OccupancyGrid,'/local_costmap/costmap',lambda value:setattr(self,'costmap',value),qos)
        self.create_timer(.1,self.publish_map)
        self.create_subscription(Twist, 'cmd_vel', self.receive, 100)
        self.create_timer(.02, self.publish)
        self.action = ActionClient(self, FollowPath, 'follow_path')
        self.state = self.create_client(GetState, 'controller_server/get_state')
        self.change = self.create_client(ChangeState, 'controller_server/change_state')

    def publish_map(self):
        message=OccupancyGrid(); message.header.frame_id='odom';message.header.stamp=self.get_clock().now().to_msg()
        message.info.resolution=self.map_grid['resolution'];message.info.width=self.map_grid['width'];message.info.height=self.map_grid['height']
        message.info.origin.position.x=self.map_grid['origin'][0];message.info.origin.position.y=self.map_grid['origin'][1];message.info.origin.orientation.w=1.
        message.data=self.map_grid['data'];self.map_pub.publish(message)

    def receive(self, value):
        error = None
        try:
            twist(value.linear.x, value.angular.z)
        except ValueError as exc:
            error = str(exc)
        self.rows.append(dict(label=self.label, received_at=time.monotonic(),
                              v=float(value.linear.x), w=float(value.angular.z), contract_error=error))

    def publish(self):
        now = time.monotonic()
        p = dict(schema=1, run_id='v1288-stationary-software', sequence=self.sequence,
                 sampled_at=now, body=self.fixture['body'], ranges_m=self.fixture['ranges_m'])
        observation(p, run_id=p['run_id'], now=now, previous_sequence=self.sequence - 1)
        self.sequence += 1
        self.packets.append(p)
        stamp = self.get_clock().now().to_msg()
        t = TransformStamped()
        t.header.stamp, t.header.frame_id, t.child_frame_id = stamp, 'odom', 'base_link'
        t.transform.translation.x, t.transform.translation.y = p['body'][:2]
        t.transform.rotation.z = math.sin(p['body'][2]/2)
        t.transform.rotation.w = math.cos(p['body'][2]/2)
        self.tf.sendTransform(t)
        od = Odometry()
        od.header.stamp, od.header.frame_id, od.child_frame_id = stamp, 'odom', 'base_link'
        od.pose.pose.position.x, od.pose.pose.position.y = p['body'][:2]
        od.pose.pose.orientation = t.transform.rotation
        od.twist.twist.linear.x, od.twist.twist.angular.z = p['body'][3:]
        self.odom.publish(od)
        scan = LaserScan()
        scan.header.stamp, scan.header.frame_id = stamp, 'base_scan'
        scan.angle_min, scan.angle_max, scan.angle_increment = 0., math.tau * 31 / 32, math.tau / 32
        scan.range_min, scan.range_max, scan.scan_time = .05, 3., .04
        scan.ranges = [float('inf') if x >= 2.999 else max(.05,x) for x in p['ranges_m']]
        self.scan.publish(scan)


def main():
    started = time.monotonic()
    os.sched_setaffinity(0, {2, 3, 4, 5})
    os.nice(max(0, 19 - os.getpriority(os.PRIO_PROCESS, 0)))
    rclpy.init()
    node = Fixture()
    server = None
    result = dict(passed=False, models=0, physical_native=0, analytical_vehicle_propagation=0,
                  navigation_trials=0, synthetic_stationary_fixture=True, cases=[],
                  scope='Actual upstream controller software interface, not physical navigation')
    log = (O / 'controller_server.console').open('x')

    def wait(predicate, seconds, message):
        until = min(started + 240, time.monotonic() + seconds)
        while time.monotonic() < until:
            rclpy.spin_once(node, timeout_sec=.005)
            if server is not None and server.poll() is not None:
                raise RuntimeError('CONTROLLER_SERVER_EXIT ' + str(server.returncode))
            if predicate():
                return
        raise TimeoutError(message)

    def settle(seconds):
        end = time.monotonic() + seconds
        wait(lambda: time.monotonic() >= end, seconds + 1, 'SETTLE_TIMEOUT')

    try:
        server = subprocess.Popen(['/opt/ros/jazzy/lib/nav2_controller/controller_server',
                                   '--ros-args', '--params-file', str(C / 'params.json')],
                                  stdout=log, stderr=subprocess.STDOUT)
        dump(O / 'SERVER_PROCESS.json', dict(pid=server.pid, namespace_isolated=True))
        wait(node.state.service_is_ready, 10, 'LIFECYCLE_NOT_READY')
        initial = node.state.call_async(GetState.Request())
        wait(initial.done, 5, 'INITIAL_STATE_TIMEOUT')
        assert initial.result().current_state.id == 1, 'NOT_UNCONFIGURED'
        for transition, state in [(1, 2), (3, 3)]:
            req = ChangeState.Request()
            req.transition.id = transition
            future = node.change.call_async(req)
            wait(future.done, 20, 'LIFECYCLE_TRANSITION_TIMEOUT')
            assert future.result().success, 'LIFECYCLE_REJECTED'
            future = node.state.call_async(GetState.Request())
            wait(future.done, 5, 'STATE_TIMEOUT')
            assert future.result().current_state.id == state, 'WRONG_LIFECYCLE_STATE'
        result['controller_active'] = True
        wait(node.action.server_is_ready, 10, 'FOLLOW_PATH_SERVER_ABSENT')
        settle(.5)
        cases = json.loads((C / 'TASKS.json').read_text())
        for case in cases:
            node.label = case['id']
            node.fixture = case['fixture']
            settle(1.2)
            wait(lambda: node.costmap is not None, 5, 'ACTUAL_COSTMAP_NOT_RECEIVED')
            assert any(v==100 for v in node.costmap.data),'STATIC_OBSTACLE_NOT_IN_ACTUAL_COSTMAP'
            offset = len(node.rows)
            path = NavPath()
            path.header.frame_id = 'odom'
            path.header.stamp = node.get_clock().now().to_msg()
            for x, y, yaw in case['path']:
                pose = PoseStamped()
                pose.header = path.header
                pose.pose.position.x, pose.pose.position.y = float(x), float(y)
                pose.pose.orientation.z, pose.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
                path.poses.append(pose)
            goal = FollowPath.Goal()
            goal.path, goal.controller_id, goal.goal_checker_id = path, case['plugin'], 'goal_checker'
            goal.progress_checker_id = 'progress_checker'
            sent = time.monotonic()
            future = node.action.send_goal_async(goal)
            wait(future.done, 5, 'ACTION_ACCEPT_TIMEOUT')
            handle = future.result()
            assert handle.accepted, 'FOLLOW_PATH_REJECTED'
            completed = handle.get_result_async()
            wait(lambda: completed.done() or len(node.rows) - offset >= 24,
                 8, 'CONTROLLER_COMMAND_TIMEOUT')
            if case['kind'] == 'goal':
                wait(completed.done, 4, 'TERMINAL_ACTION_NOT_COMPLETE')
            elif not completed.done():
                cancel = handle.cancel_goal_async()
                wait(cancel.done, 4, 'CANCEL_ACK_TIMEOUT')
                assert cancel.result().goals_canceling, 'CANCEL_NOT_ACCEPTED'
                wait(completed.done, 4, 'CANCEL_RESULT_TIMEOUT')
            settle(.15)
            rows = node.rows[offset:]
            moving = [x for x in rows if abs(x['v']) > .005 or abs(x['w']) > 1e-6]
            gaps = [b['received_at'] - a['received_at'] for a, b in zip(rows, rows[1:])]
            checks = dict(action_accepted=True, raw_commands_legal=all(x['contract_error'] is None for x in rows))
            if case['kind'] == 'blocked':
                checks.update(no_forward_from_known_unsafe_state=not any(x['v'] > .005 for x in moving),static_costmap_received=node.costmap is not None)
            elif case['kind'] == 'goal':
                checks.update(goal_at_origin_action_succeeded=completed.result().status == 4, no_movement_requested=not moving)
            else:
                checks.update(at_least20_commands=len(rows) >= 20,
                              nonzero_forward=any(x['v'] > .005 for x in rows),
                              action_cancelled=completed.result().status == 5)
                if case['turn']:
                    checks['correct_median_turn'] = bool(moving and statistics.median(x['w'] for x in moving) * case['turn'] > 0)
            entry = dict(id=case['id'], plugin=case['plugin'], kind=case['kind'],
                         passed=all(checks.values()), checks=checks, action_status=completed.result().status,
                         action_error_code=completed.result().result.error_code, raw_commands=len(rows),
                         first_command_after_goal_s=rows[0]['received_at'] - sent if rows else None,
                         command_receive_interval_s=dict(p50=percentile(gaps, .5), p95=percentile(gaps, .95),
                                                        maximum=max(gaps, default=None)),
                         median_moving_w=statistics.median(x['w'] for x in moving) if moving else None,
                         no_physical_execution=True)
            result['cases'].append(entry)
            dump(O / 'PARTIAL.json', result)
        result['passed'] = len(result['cases']) == len(cases) and all(x['passed'] for x in result['cases'])
    except BaseException as exc:
        result.update(error=repr(exc), traceback=traceback.format_exc())
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=4)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=2)
        if node.costmap is not None:
            m=node.costmap
            dump(O/'ACTUAL_COSTMAP.json',dict(width=m.info.width,height=m.info.height,resolution=m.info.resolution,origin=[m.info.origin.position.x,m.info.origin.position.y],data=list(m.data)))
        result.update(wall_s=time.monotonic() - started,
                      no_model_modules_loaded=not any(k in sys.modules for k in ['mujoco', 'vehicle', 'torch']),
                      controller_server_exited=server is None or server.poll() is not None)
        dump(O / 'RAW_COMMANDS.json', node.rows)
        dump(O / 'SYNTHETIC_OBSERVATIONS.json', node.packets)
        dump(O / 'CONTROLLER_RESULT.json', result)
        log.close()
        node.destroy_node()
        rclpy.shutdown()
    print(json.dumps(result, allow_nan=False), flush=True)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
