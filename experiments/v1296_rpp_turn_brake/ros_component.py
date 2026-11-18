"""Real upstream RPP on actual body/scan only. No vehicle imports in ROS."""
import importlib.abc
import math
import os
from pathlib import Path
import socket
import sys
import time
import traceback


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'vehicle', 'torch', 'factory', 'physical'}:
            raise AssertionError('ROS_PHYSICAL_IMPORT_FORBIDDEN ' + name)


sys.meta_path.insert(0, NoPhysical())
from component_context import *
sys.path.insert(0, str(R / 'experiments/v1288_baseline_interface'))
from contract import observation, command
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TransformStamped, Twist
from nav_msgs.msg import Odometry, Path as NavPath
from sensor_msgs.msg import LaserScan
from nav2_msgs.action import FollowPath
from lifecycle_msgs.srv import ChangeState
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster
import subprocess


def main():
    task = read(sys.argv[1]); window = read(O / 'ROUND_WINDOW.json'); authorize(task, window)
    out = Path(task['output']); start = time.monotonic(); deadline = start + 285
    os.sched_setaffinity(0, {3, 4, 5}); rclpy.init()
    node = Node('phase_current_rpp_component'); latest = None; received = -1; sequence = 0; rows = []; stopped = False; armed = False
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    address = str(out.relative_to(R) / 'ros.sock'); sock.bind(address); sock.setblocking(False)
    peer = str(out.relative_to(R) / 'native.sock')
    tf = TransformBroadcaster(node); static = StaticTransformBroadcaster(node)
    odom = node.create_publisher(Odometry, 'odom', 10); scans = node.create_publisher(LaserScan, 'scan', 10)
    t = TransformStamped(); t.header.stamp = node.get_clock().now().to_msg(); t.header.frame_id = 'base_link'; t.child_frame_id = 'base_scan'; t.transform.rotation.w = 1.; static.sendTransform(t)

    def send(x):
        try:
            sock.sendto(__import__('json').dumps(x).encode(), peer)
        except (FileNotFoundError, BlockingIOError, ConnectionRefusedError):
            pass

    def receive_twist(value):
        nonlocal sequence
        if latest is None or stopped or not armed:
            return
        p = dict(run_id=task['run_id'], sequence=sequence, issued_at=time.monotonic(), v=float(value.linear.x), w=float(value.angular.z))
        rows.append(p); command(p, run_id=task['run_id'], now=time.monotonic(), previous_sequence=sequence - 1)
        sequence += 1; send(dict(kind='command', **p))

    node.create_subscription(Twist, 'cmd_vel', receive_twist, 10)

    def publish():
        nonlocal latest, received
        packet = None
        for _ in range(128):
            try:
                packet = __import__('json').loads(sock.recv(65536))
            except BlockingIOError:
                break
        if packet is None:
            return
        observation(packet, run_id=task['run_id'], now=time.monotonic(), previous_sequence=received)
        latest = packet; received = packet['sequence']; x, y, yaw, v, w = packet['body']; stamp = node.get_clock().now().to_msg()
        t = TransformStamped(); t.header.stamp = stamp; t.header.frame_id = 'odom'; t.child_frame_id = 'base_link'; t.transform.translation.x = x; t.transform.translation.y = y; t.transform.rotation.z = math.sin(yaw / 2); t.transform.rotation.w = math.cos(yaw / 2); tf.sendTransform(t)
        od = Odometry(); od.header.stamp = stamp; od.header.frame_id = 'odom'; od.child_frame_id = 'base_link'; od.pose.pose.position.x = x; od.pose.pose.position.y = y; od.pose.pose.orientation = t.transform.rotation; od.twist.twist.linear.x = v; od.twist.twist.angular.z = w; odom.publish(od)
        scan = LaserScan(); scan.header.stamp = stamp; scan.header.frame_id = 'base_scan'; scan.angle_min = 0.; scan.angle_max = math.tau * 31 / 32; scan.angle_increment = math.tau / 32; scan.range_min = .05; scan.range_max = 3.; scan.scan_time = .05; scan.ranges = [max(.05, x) if x < 2.999 else float('inf') for x in packet['ranges_m']]; scans.publish(scan)

    node.create_timer(.01, publish)
    client = node.create_client(ChangeState, 'controller_server/change_state'); action = ActionClient(node, FollowPath, 'follow_path')
    log = (out / 'controller.console').open('x'); server = subprocess.Popen(['/opt/ros/jazzy/lib/nav2_controller/controller_server', '--ros-args', '--params-file', str(C / 'params.json')], stdout=log, stderr=subprocess.STDOUT)
    result = dict(passed=False, physical_models_in_ros=0, commands=0)

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
        wait(action.server_is_ready, 5, 'RPP_ACTION_MISSING')
        path = NavPath(); path.header.frame_id = 'odom'; path.header.stamp = node.get_clock().now().to_msg()
        for x, y, yaw in task['reference_path']:
            p = PoseStamped(); p.header = path.header; p.pose.position.x = x; p.pose.position.y = y; p.pose.orientation.z = math.sin(yaw / 2); p.pose.orientation.w = math.cos(yaw / 2); path.poses.append(p)
        g = FollowPath.Goal(); g.path = path; g.controller_id = 'RPP'; g.goal_checker_id = 'goal_checker'; g.progress_checker_id = 'progress_checker'; future = action.send_goal_async(g); wait(future.done, 5, 'GOAL_ACCEPT_TIMEOUT'); h = future.result(); assert h.accepted; f = h.get_result_async(); result['action_accepted'] = True
        armed = True; send(dict(kind='arm', run_id=task['run_id'], issued_at=time.monotonic()))
        wait(f.done, 180, 'RPP_COMPONENT_NAVIGATION_180S')
        result.update(action_status=f.result().status, error_code=f.result().result.error_code, passed=f.result().status == 4)
    except BaseException as exc:
        result.update(error=repr(exc), traceback=traceback.format_exc())
    finally:
        stopped = True; send(dict(kind='stop', run_id=task['run_id'], passed=result['passed'], issued_at=time.monotonic()))
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=4)
            except subprocess.TimeoutExpired:
                server.kill(); server.wait(timeout=2)
        result.update(commands=len(rows), wall_s=time.monotonic() - start); dump(out / 'ROS_COMMANDS.json', rows); dump(out / 'ROS_RESULT.json', result); sock.close(); Path(address).unlink(missing_ok=True); log.close(); node.destroy_node(); rclpy.shutdown()
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
