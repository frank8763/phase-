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
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiments/v1346_measured_gear_handoff/software'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiments/v1346_measured_gear_handoff'))
from contract import observation, twist
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from planning_job import PlanningJob
from observed_route import revalidate
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

R = Path(__file__).resolve().parents[2]
C = R / 'experiments/v1346_measured_gear_handoff/software'
O = R / 'runs/v1347_cusp_segment_execution/controller_probe'


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
        self.publish_count=0
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
        self.publish_count+=1
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

