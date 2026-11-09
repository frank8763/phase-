"""Exact-path ROS binding; imports ROS only when instantiated by its caller."""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'experiments/v938_rpccr_recovery_segments'))
from transaction import fingerprint


class FollowPathBinding:
    def __init__(self, node):
        from rclpy.action import ActionClient
        from nav2_msgs.action import FollowPath
        self.node = node
        self.kind = FollowPath
        self.client = ActionClient(node, FollowPath, 'follow_path')
        self.sent = False
        self.path_sha256 = None

    def send(self, event):
        from geometry_msgs.msg import PoseStamped
        assert not self.sent, 'DUPLICATE_RECOVERY_ACTION'
        assert event['action'] == 'SEND_FOLLOW_PATH_ONCE'
        assert fingerprint(event['path']) == event['path_sha256'], 'PATH_MUTATED_IN_BINDING'
        goal = self.kind.Goal()
        goal.controller_id = 'FollowPath'
        goal.goal_checker_id = 'general_goal_checker'
        goal.progress_checker_id = 'progress_checker'
        goal.path.header.frame_id = 'map'
        goal.path.header.stamp = self.node.get_clock().now().to_msg()
        for x, y, angle in event['path']:
            pose = PoseStamped()
            pose.header = goal.path.header
            pose.pose.position.x = x
            pose.pose.position.y = y
            pose.pose.orientation.z = math.sin(angle/2)
            pose.pose.orientation.w = math.cos(angle/2)
            goal.path.poses.append(pose)
        self.path_sha256 = fingerprint([
            [p.pose.position.x, p.pose.position.y,
             2*math.atan2(p.pose.orientation.z, p.pose.orientation.w)]
            for p in goal.path.poses])
        # Quaternion roundtrip can differ by roundoff, so compare original values numerically.
        for original, transmitted in zip(event['path'], goal.path.poses):
            angle = 2*math.atan2(transmitted.pose.orientation.z, transmitted.pose.orientation.w)
            assert abs(math.atan2(math.sin(angle-original[2]), math.cos(angle-original[2]))) <= 1e-12
            assert original[:2] == [transmitted.pose.position.x, transmitted.pose.position.y]
        self.sent = True
        return self.client.send_goal_async(goal)
