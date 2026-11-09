"""Actual RPP action and cancellation against a nonmoving synthetic saved-state peer."""
import array
import copy
import hashlib
import importlib.abc
import json
import math
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).parent
OUT = ROOT/'runs/v939_rpccr_rpp_handoff'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'torch', 'factory', 'physical', 'vehicle'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0, NoModel())
sys.path[:0] = [str(CODE), str(ROOT/'experiments/v938_rpccr_recovery_segments'),
               str(ROOT/'experiments/v934_rpccr_certified_recovery'),
               str(ROOT/'experiments/v891_dynamic_consistency_software'),
               str(ROOT/'experiments/v881_timing_accounting_continuation')]


def read(path):
    return json.loads(path.read_text())


def main():
    import rclpy
    from rclpy.node import Node
    from rclpy.action import ActionClient
    from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, qos_profile_sensor_data
    from geometry_msgs.msg import TransformStamped, Twist
    from nav_msgs.msg import OccupancyGrid, Odometry
    from sensor_msgs.msg import LaserScan
    from nav2_msgs.action import NavigateToPose
    from nav2_msgs.srv import ManageLifecycleNodes
    from lifecycle_msgs.srv import GetState
    from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster
    from binding import FollowPathBinding
    from transaction import RecoveryTransaction, fingerprint
    from routing_stack import Stack
    from support_envelope import raster_support
    from periodic_support import swept_bounds
    from cycle_backup import cycle_upper
    from command_tube import admit, MAX_CURVATURE

    saved = ROOT/'runs/v936_rpccr_corridor_search'
    first = read(saved/'ENTRY_QUALIFICATION.json')['first_actual_trigger']
    proposal = read(ROOT/'runs/v938_rpccr_recovery_segments/CORRIDORS.json')[0]['proposal']
    known = read(saved/'saved/SETUP.json')['known']
    config = ROOT/'experiments/v934_rpccr_certified_recovery/A_motion.yaml'
    assert read(config)['controller_server']['ros__parameters']['FollowPath'] == read(ROOT/'experiments/v884_feasible_rpp/A_feasible.yaml')['controller_server']['ros__parameters']['FollowPath']
    packet, source = first['packet'], first['source']
    rclpy.init()
    node = Node('phase_rpccr_recovery_zero_vehicle')
    (OUT/'ros').mkdir(exist_ok=False)
    stack = Stack(OUT/'ros', config)
    until = time.monotonic()+90.
    commands, states, events = [], {}, []
    result = dict(passed=False, models=0, integrations=0, actuator_commands_executed=0,
                  synthetic_fixed_pose=True, actual_navigation_success=False)
    handle = None

    def wait(predicate, message, seconds=10.):
        end = min(until, time.monotonic()+seconds)
        while time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=.005)
            assert not stack.failed(), 'ROS_CHILD_EXIT '+str(stack.failed())
            if predicate():
                return
        raise TimeoutError(message)

    tf = TransformBroadcaster(node)
    static = StaticTransformBroadcaster(node)
    transforms = []
    for parent, child in [('map', 'odom'), ('base_link', 'base_scan')]:
        transform = TransformStamped()
        transform.header.frame_id = parent; transform.child_frame_id = child
        transform.transform.rotation.w = 1.
        transform.header.stamp = node.get_clock().now().to_msg()
        transforms.append(transform)
    static.sendTransform(transforms)
    scanpub = node.create_publisher(LaserScan, 'scan', qos_profile_sensor_data)
    odompub = node.create_publisher(Odometry, 'odom', 10)
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     reliability=ReliabilityPolicy.RELIABLE)
    globalpub = node.create_publisher(OccupancyGrid, 'phase_dynamic_reference', qos)
    localpub = node.create_publisher(OccupancyGrid, 'phase_dynamic_envelope', qos)
    reference = cycle_upper(source['periodic'])+.1+.06
    start = source['source_scan_sim_time']
    forecast = swept_bounds(source['periodic']['vertices'], start, start+2.5)+.1
    # These are fixed saved-pose synthetic maps, not newly observed future scans.
    payloads = [array.array('b', raster_support(x).tobytes()) for x in [reference, forecast]]

    def publish():
        stamp = node.get_clock().now().to_msg()
        x, y, angle = packet['body'][:3]
        transform = TransformStamped()
        transform.header.stamp = stamp; transform.header.frame_id = 'odom'
        transform.child_frame_id = 'base_link'
        transform.transform.translation.x = x; transform.transform.translation.y = y
        transform.transform.rotation.z = math.sin(angle/2); transform.transform.rotation.w = math.cos(angle/2)
        tf.sendTransform(transform)
        odom = Odometry(); odom.header.stamp = stamp; odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'; odom.pose.pose.position.x = x; odom.pose.pose.position.y = y
        odom.pose.pose.orientation = transform.transform.rotation; odompub.publish(odom)
        scan = LaserScan(); scan.header.stamp = stamp; scan.header.frame_id = 'base_scan'
        scan.angle_min = 0.; scan.angle_max = 31*math.pi/16; scan.angle_increment = math.pi/16
        scan.range_min = .05; scan.range_max = 3.; scan.scan_time = .05
        scan.ranges = [max(.05, float(v)) if v<2.999 else float('inf') for v in packet['scan']['ranges']]
        scanpub.publish(scan)
        for publisher, data in zip([globalpub, localpub], payloads):
            grid = OccupancyGrid(); grid.header.stamp = stamp; grid.header.frame_id = 'map'
            grid.info.resolution = .01; grid.info.width = 1000; grid.info.height = 1000
            grid.info.origin.position.x = -5.; grid.info.origin.position.y = -5.
            grid.info.origin.orientation.w = 1.; grid.data = data; publisher.publish(grid)

    node.create_timer(.05, publish)

    def command(message):
        now = time.monotonic()
        p, s = copy.deepcopy(packet), copy.deepcopy(source)
        p['body_measured_at'] = now; p['sent_at'] = now
        s['decision_at'] = now
        proof = admit(p, s, message.linear.x, message.angular.z, known, now)
        commands.append(dict(v=message.linear.x, w=message.angular.z, proof=proof,
                             fixture='SYNTHETIC_FROZEN_POSE_NO_ACTUATION'))

    node.create_subscription(Twist, 'cmd_vel_nav', command, 10)
    transaction = RecoveryTransaction([4., -2.], known)
    binding = FollowPathBinding(node)
    try:
        stack.start()
        names = ['map_server', 'planner_server', 'controller_server', 'behavior_server',
                 'velocity_smoother', 'collision_monitor', 'bt_navigator']
        for name in names:
            client = node.create_client(GetState, name+'/get_state')
            wait(client.service_is_ready, 'GET_STATE_READY', 35.)
            future = client.call_async(GetState.Request()); wait(future.done, 'GET_STATE_REPLY')
            assert future.result().current_state.id == 1
            node.destroy_client(client)
        manager = node.create_client(ManageLifecycleNodes, 'lifecycle_manager_navigation/manage_nodes')
        wait(manager.service_is_ready, 'LIFECYCLE_MANAGER_READY')
        request = ManageLifecycleNodes.Request(); request.command = 0
        future = manager.call_async(request); wait(future.done, 'ACTIVATE', 25.)
        assert future.result().success
        for name in names:
            client = node.create_client(GetState, name+'/get_state')
            wait(client.service_is_ready, 'ACTIVE_STATE_READY')
            future = client.call_async(GetState.Request()); wait(future.done, 'ACTIVE_STATE_REPLY')
            states[name] = future.result().current_state.id; assert states[name] == 3
            node.destroy_client(client)
        normal = ActionClient(node, NavigateToPose, 'navigate_to_pose')
        wait(normal.server_is_ready, 'NAVIGATE_ACTION_READY')
        goal = NavigateToPose.Goal(); goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = node.get_clock().now().to_msg()
        goal.pose.pose.position.x = 4.; goal.pose.pose.position.y = -2.; goal.pose.pose.orientation.w = 1.
        future = normal.send_goal_async(goal); wait(future.done, 'NORMAL_GOAL_ACCEPT')
        normal_handle = future.result(); assert normal_handle.accepted
        transaction.request(packet, source, packet['body_measured_at'])
        cancellation = normal_handle.cancel_goal_async(); wait(cancellation.done, 'NORMAL_CANCEL_ACK')
        completion = normal_handle.get_result_async(); wait(completion.done, 'NORMAL_CANCEL_RESULT')
        normal_status = completion.result().status
        assert normal_status in [5, 6], 'NORMAL_ACTION_STILL_ACTIVE'
        events.append(dict(kind='NORMAL_QUIESCENT', result_status=normal_status,
                           cancel_code=cancellation.result().return_code))
        transaction.canceled(True)
        event = transaction.install(proposal, packet, source, packet['body_measured_at'])
        wait(binding.client.server_is_ready, 'FOLLOW_ACTION_READY')
        before = len(commands)
        future = binding.send(event); wait(future.done, 'FOLLOW_GOAL_ACCEPT')
        handle = future.result(); assert handle.accepted
        transaction.accepted(True)
        wait(lambda:sum(abs(row['v'])>=.005 for row in commands[before:])>=20,
             'TWENTY_REAL_RPP_NONZERO_OUTPUTS', 10.)
        action = handle.cancel_goal_async(); wait(action.done, 'FOLLOW_CANCEL_ACK')
        completion = handle.get_result_async(); wait(completion.done, 'FOLLOW_CANCEL_RESULT')
        rows = commands[before:]
        checks = dict(all_seven_real_nodes_active=all(x==3 for x in states.values()) and len(states)==7,
                      normal_action_quiescent_before_handoff=normal_status in [5, 6],
                      exact_proposal_path_in_transaction=transaction.path_sha256==fingerprint(proposal['path']),
                      binding_sends_once=binding.sent,
                      twenty_real_rpp_nonzero_commands=sum(abs(row['v'])>=.005 for row in rows)>=20,
                      every_real_twist_uses_original_command_certificate=all(row['proof']['passed'] for row in rows),
                      original_speed_curvature_preserved=all(abs(row['v'])<=.1+1e-10 and abs(row['w'])<=abs(row['v'])*MAX_CURVATURE+1e-9 for row in rows),
                      follow_cancel_acknowledged=completion.result().status==5 and action.result().return_code==0,
                      no_synthetic_vehicle_integration=True)
        result.update(passed=all(checks.values()), checks=checks,
                      follow_result_status=completion.result().status,
                      path_sha256=transaction.path_sha256)
    except BaseException as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        stack.close(); node.destroy_node(); rclpy.shutdown()
        result.update(commands=commands, real_lifecycle_states=states, events=events,
                      transaction_events=transaction.events,
                      scope='Real Nav2/RPP action software with fixed saved-pose peer; no physical movement or arrival.')
        (OUT/'RESULT.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['commands', 'transaction_events']}, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
