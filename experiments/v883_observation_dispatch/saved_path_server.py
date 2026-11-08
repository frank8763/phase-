"""Diagnostic action server: return the exact previously saved global reference."""
import json,math,time
from pathlib import Path
R=Path(__file__).resolve().parents[2]
class PlannerProxy:
    def __init__(self,node,latest,out,deadline):
        from rclpy.action import ActionServer
        from rclpy.callback_groups import ReentrantCallbackGroup
        from nav2_msgs.action import ComputePathToPose
        from nav_msgs.msg import Path as NavPath
        self.node=node;self.out=Path(out);self.latest=latest;self.deadline=deadline;self.kind=ComputePathToPose;self.rows=[];self.force_forward=False
        task=json.loads((self.out/'TASK.json').read_text());self.fixture=json.loads((R/'runs/v883_observation_dispatch/FIXTURES.json').read_text())[task['fixture_key']];self.diagnostic_route_busy_s=task.get('diagnostic_route_busy_s',0.)
        self.publisher=node.create_publisher(NavPath,'plan',10);self.server=ActionServer(node,ComputePathToPose,'compute_path_to_pose',self.execute,callback_group=ReentrantCallbackGroup())
    async def execute(self,handle):
        from nav_msgs.msg import Path as NavPath
        from geometry_msgs.msg import PoseStamped
        result=self.kind.Result();path=NavPath();path.header.frame_id='map';path.header.stamp=self.node.get_clock().now().to_msg()
        until=time.monotonic()+self.diagnostic_route_busy_s
        while time.monotonic()<until:pass
        for x,y,a in self.fixture['path']:
            p=PoseStamped();p.header=path.header;p.pose.position.x=x;p.pose.position.y=y;p.pose.orientation.z=math.sin(a/2);p.pose.orientation.w=math.cos(a/2);path.poses.append(p)
        result.path=path;result.error_code=0;handle.succeed();self.publisher.publish(path)
        self.rows.append(dict(passed=True,source=self.fixture['source'],saved_reference_only=True,actual_vehicle_models=0));(self.out/'ROUTER_REQUESTS.json').write_text(json.dumps(self.rows,indent=2)+'\n');return result
