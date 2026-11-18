"""Installed Smac planner on saved causal observations; no physical imports."""
import importlib.abc
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import traceback

class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch'}:raise AssertionError('PHYSICAL_IMPORT_FORBIDDEN')
sys.meta_path.insert(0,NoPhysical())
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
from geometry_msgs.msg import PoseStamped,TransformStamped
from nav_msgs.msg import OccupancyGrid
from nav2_msgs.action import ComputePathToPose
from lifecycle_msgs.srv import ChangeState
from tf2_ros import TransformBroadcaster
from causal_occupancy import CausalBall

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1342_dynamic_relay_preparation/planner_fresh'


def main():
    import gzip
    raw=R/'runs/v858_nav2_verified/v1341/rpp_default_dynamic_main'
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    with gzip.open(raw/'physics/SENSORS.json.gz','rt') as stream:scans=json.load(stream)
    trace=np.load(raw/'physics/NATIVE_TRACE.npz');saved=[x for x in scans if x['native_tick']<=4505]
    tracker=CausalBall(known)
    for scan in saved:tracker.update(native_tick=scan['native_tick'],sim_time=scan['time'],center_body=[*scan['xy'],scan['yaw']],ranges=scan['ranges'])
    scan=saved[-1];q=trace['qpos'][scan['native_tick']-1];yaw=float(np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2)))
    current=[float(q[0]-.3*np.cos(yaw)),float(q[1]-.3*np.sin(yaw)),yaw]
    grid=json.loads((R/'experiments/v1331_common_static_map/PUBLIC_STATIC_GRID.json').read_text());data=tracker.raster(grid,scan['time']).ravel().tolist()
    rclpy.init();node=Node('phase_saved_causal_planner');tf=TransformBroadcaster(node)
    qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE);pub=node.create_publisher(OccupancyGrid,'/phase_public_static',qos)
    def publish():
        now=node.get_clock().now().to_msg();t=TransformStamped();t.header.stamp=now;t.header.frame_id='odom';t.child_frame_id='base_link';t.transform.translation.x=current[0];t.transform.translation.y=current[1];t.transform.rotation.z=math.sin(current[2]/2);t.transform.rotation.w=math.cos(current[2]/2);tf.sendTransform(t)
        m=OccupancyGrid();m.header.frame_id='odom';m.header.stamp=now;m.info.resolution=grid['resolution'];m.info.width=grid['width'];m.info.height=grid['height'];m.info.origin.position.x=grid['origin'][0];m.info.origin.position.y=grid['origin'][1];m.info.origin.orientation.w=1.;m.data=data;pub.publish(m)
    node.create_timer(.05,publish);client=node.create_client(ChangeState,'planner_server/change_state');action=ActionClient(node,ComputePathToPose,'compute_path_to_pose')
    log=(O/'planner.console').open('x');server=subprocess.Popen(['/opt/ros/jazzy/lib/nav2_planner/planner_server','--ros-args','--params-file',str(C/'planner_reeds_params.json')],stdout=log,stderr=subprocess.STDOUT)
    begin=time.monotonic();result=dict(passed=False,models=0,physical_native=0)
    def wait(fn,seconds):
        until=time.monotonic()+seconds
        while time.monotonic()<until:
            assert server.poll() is None,'PLANNER_SERVER_EXIT'
            rclpy.spin_once(node,timeout_sec=.01)
            if fn():return
        raise TimeoutError('PLANNER_QUALIFICATION_TIMEOUT')
    try:
        wait(client.service_is_ready,15)
        for tid in [1,3]:
            req=ChangeState.Request();req.transition.id=tid;f=client.call_async(req);wait(f.done,15);assert f.result().success
        wait(action.server_is_ready,5)
        until=time.monotonic()+1.
        wait(lambda:time.monotonic()>until,2)
        goal=ComputePathToPose.Goal();goal.planner_id='GridBased';goal.use_start=True
        for field,pose in [('start',current),('goal',[3.7697966113566173,-1.4696797266583148,-.6989847198957886])]:
            p=PoseStamped();p.header.frame_id='odom';p.header.stamp=node.get_clock().now().to_msg();p.pose.position.x=pose[0];p.pose.position.y=pose[1];p.pose.orientation.z=math.sin(pose[2]/2);p.pose.orientation.w=math.cos(pose[2]/2);setattr(goal,field,p)
        f=action.send_goal_async(goal);wait(f.done,5);h=f.result();assert h.accepted;f=h.get_result_async();wait(f.done,8)
        value=f.result();path=value.result.path
        poses=[]
        for p in path.poses:
            ori=p.pose.orientation;angle=math.atan2(2*ori.w*ori.z,1-2*ori.z*ori.z);poses.append([p.pose.position.x,p.pose.position.y,angle])
        result.update(passed=value.status==4 and len(poses)>10,status=value.status,error_code=value.result.error_code,poses=poses,start=current,causal_ball=dict(point=tracker.center.tolist(),radius=tracker.occupied_ball(scan['time'])[1]),saved_tick=scan['native_tick'],causal_updates=len(tracker.records))
    except BaseException as error:result.update(error=repr(error),traceback=traceback.format_exc())
    finally:
        if server.poll() is None:
            server.terminate()
            try:server.wait(timeout=4)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=2)
        result['wall_s']=time.monotonic()-begin;(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');log.close();node.destroy_node();rclpy.shutdown()
    print(json.dumps({k:v for k,v in result.items() if k!='poses'}));return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
