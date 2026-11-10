"""One selected recovery controller, exact committed path, no actuator publisher."""
import math
from transaction import fingerprint


class FollowPathBinding:
    def __init__(self,node):
        from rclpy.action import ActionClient
        from nav2_msgs.action import FollowPath
        self.node=node;self.kind=FollowPath;self.client=ActionClient(node,FollowPath,'follow_path');self.sent=False

    def send(self,event):
        from geometry_msgs.msg import PoseStamped
        assert not self.sent,'DUPLICATE_RECOVERY_ACTION'
        assert event['action']=='SEND_FOLLOW_PATH_ONCE' and event['controller_id']=='RecoveryFollowPath','WRONG_RECOVERY_OWNER'
        assert event['goal_checker_id']=='recovery_goal_checker','WRONG_RECOVERY_GOAL_CHECKER'
        assert fingerprint(event['path'])==event['path_sha256'],'PATH_MUTATED_IN_BINDING'
        goal=self.kind.Goal();goal.controller_id=event['controller_id'];goal.goal_checker_id=event['goal_checker_id'];goal.progress_checker_id='progress_checker'
        goal.path.header.frame_id='map';goal.path.header.stamp=self.node.get_clock().now().to_msg()
        for x,y,a in event['path']:
            pose=PoseStamped();pose.header=goal.path.header;pose.pose.position.x=x;pose.pose.position.y=y
            pose.pose.orientation.z=math.sin(a/2);pose.pose.orientation.w=math.cos(a/2);goal.path.poses.append(pose)
        self.sent=True
        return self.client.send_goal_async(goal)
