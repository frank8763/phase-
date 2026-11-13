"""Genuine installed Smac planner only: no controller server or physical model."""
import sys,os,json,time,signal,subprocess,math,array,traceback,hashlib,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1107_reference_frame_alignment'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','factory'}:raise AssertionError('NO_PHYSICAL_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
def main():
    import numpy as np,rclpy
    from rclpy.node import Node
    from rclpy.action import ActionClient
    from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
    from nav_msgs.msg import OccupancyGrid
    from geometry_msgs.msg import TransformStamped
    from tf2_ros import StaticTransformBroadcaster
    from lifecycle_msgs.srv import GetState,ChangeState
    from nav2_msgs.srv import GetCostmap
    from nav2_msgs.action import ComputePathToPose
    if '--check'in sys.argv:
        print(json.dumps(dict(passed=True,official_planner_python_interfaces=True,models=0,physical_integrations=0)));return
    assert not(O/'PLANNER_RESULT.json').exists();x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());griddata=np.load(O/'MAP.npy');cfg=json.loads((O/'CONFIG.json').read_text());root=cfg['planner_root_pose'];end=time.monotonic()+120;job=None
    rclpy.init();node=Node('phase_v1107_saved_state_planning');static=StaticTransformBroadcaster(node);tf=TransformStamped();tf.header.frame_id='map';tf.child_frame_id='base_link';tf.header.stamp=node.get_clock().now().to_msg();tf.transform.translation.x=root[0];tf.transform.translation.y=root[1];tf.transform.rotation.z=math.sin(root[2]/2);tf.transform.rotation.w=math.cos(root[2]/2);static.sendTransform(tf)
    qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE);pub=node.create_publisher(OccupancyGrid,'/phase_v1107_map',qos)
    def publish():
        msg=OccupancyGrid();msg.header.frame_id='map';msg.header.stamp=node.get_clock().now().to_msg();msg.info.resolution=cfg['resolution'];msg.info.width=griddata.shape[1];msg.info.height=griddata.shape[0];msg.info.origin.position.x=-5.;msg.info.origin.position.y=-5.;msg.info.origin.orientation.w=1.;msg.data=array.array('b',griddata.tobytes());pub.publish(msg)
    node.create_timer(.25,publish);publish()
    def wait(predicate,label):
        while time.monotonic()<end:
            rclpy.spin_once(node,timeout_sec=.01)
            if job is not None and job.poll()is not None:raise RuntimeError('OFFICIAL_PLANNER_EXIT '+str(job.returncode))
            if predicate():return
        raise TimeoutError(label)
    answer=dict(passed=False,models=0,physical_integrations=0,actuator_commands=0)
    try:
        with(O/'planner_server.console').open('x')as log:
            job=subprocess.Popen(['/opt/ros/jazzy/lib/nav2_planner/planner_server','--ros-args','--params-file',str(O/'params.yaml')],stdout=log,stderr=subprocess.STDOUT)
            state=node.create_client(GetState,'planner_server/get_state');change=node.create_client(ChangeState,'planner_server/change_state');wait(state.service_is_ready,'STATE_READY');wait(change.service_is_ready,'CHANGE_READY')
            for transition,expected in [(1,2),(3,3)]:
                req=ChangeState.Request();req.transition.id=transition;f=change.call_async(req);wait(f.done,'LIFECYCLE_TRANSITION');assert f.result().success,'LIFECYCLE_REFUSED';f=state.call_async(GetState.Request());wait(f.done,'LIFECYCLE_STATE');assert f.result().current_state.id==expected
            def subscriber_bound():
                endpoints=node.get_subscriptions_info_by_topic('/phase_v1107_map')
                return any(e.node_name=='global_costmap' for e in endpoints)
            wait(subscriber_bound,'ABSOLUTE_MAP_SUBSCRIBER_BINDING')
            answer['absolute_map_subscriber_verified']=True
            client=node.create_client(GetCostmap,'global_costmap/get_costmap');wait(client.service_is_ready,'COSTMAP_READY')
            def map_ready():
                f=client.call_async(GetCostmap.Request());wait(f.done,'COSTMAP_READ');m=f.result().map;data=np.asarray(m.data,dtype=np.uint8)
                if m.metadata.size_x!=griddata.shape[1]or m.metadata.size_y!=griddata.shape[0]or len(data)!=griddata.size:return False
                if np.any(data==255):return False
                assert abs(m.metadata.resolution-cfg['resolution'])<1e-7 and abs(m.metadata.origin.position.x+5)<1e-7 and abs(m.metadata.origin.position.y+5)<1e-7,'MASTER_MAP_FRAME_MISMATCH'
                occupied=griddata.reshape(-1)==100
                if not np.all(data[occupied]>=254):return False
                np.savez_compressed(O/'ACTUAL_MASTER_COSTMAP.npz',data=data,size=[m.metadata.size_x,m.metadata.size_y]);return True
            wait(map_ready,'FULL_COSTMAP_BINDING')
            action=ActionClient(node,ComputePathToPose,'compute_path_to_pose');wait(action.server_is_ready,'SMAC_ACTION_READY');req=ComputePathToPose.Goal();req.planner_id='GridBased';req.use_start=True
            for msg,pose in [(req.start,root[:3]),(req.goal,cfg['planner_goal_pose'])]:
                msg.header.frame_id='map';msg.header.stamp=node.get_clock().now().to_msg();msg.pose.position.x=pose[0];msg.pose.position.y=pose[1];msg.pose.orientation.z=math.sin(pose[2]/2);msg.pose.orientation.w=math.cos(pose[2]/2)
            begun=time.monotonic();f=action.send_goal_async(req);wait(f.done,'SMAC_ACCEPT');handle=f.result();assert handle.accepted;f=handle.get_result_async();wait(f.done,'SMAC_RESULT');response=f.result()
            path=[[p.pose.position.x,p.pose.position.y,2*math.atan2(p.pose.orientation.z,p.pose.orientation.w)]for p in response.result.path.poses]
            answer.update(passed=response.status==4 and response.result.error_code==0 and len(path)>1,status=response.status,error_code=response.result.error_code,path=path,planning_wall_s=time.monotonic()-begun,
                master_occupied_cells_verified=True,master_unknown_cells=0,scope='official Smac Hybrid-A* path at effective model reference point; convert back to original body frame before independent admission')
    except BaseException as e:answer.update(passed=False,error=repr(e),traceback=traceback.format_exc())
    finally:
        if job is not None and job.poll()is None:
            job.send_signal(signal.SIGINT)
            try:job.wait(timeout=3)
            except subprocess.TimeoutExpired:job.kill();job.wait()
        node.destroy_node();rclpy.shutdown();(O/'PLANNER_RESULT.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps({k:v for k,v in answer.items()if k!='path'}),flush=True)
if __name__=='__main__':main()
