"""Genuine installed Smac actions on fixed saved maps; zero vehicle execution."""
import array,gzip,hashlib,importlib.abc,json,math,os,sys,time,traceback
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,*args):
        if fullname.split('.')[0]in {'mujoco','torch','vehicle','factory','physical'}:raise RuntimeError('FORBIDDEN_MODEL_IMPORT '+fullname)
sys.meta_path.insert(0,NoModel())
R=Path(__file__).resolve().parents[2];C=R/'experiments/v897_refuge_navigation'
O=R/'runs/v899_refuge_qualification'/('ros_refuge'if len(sys.argv)==1 else sys.argv[1]);O.mkdir(exist_ok=False)
sys.path[:0]=[str(C),str(R/'experiments/v887_exact_lidar_software'),str(R/'experiments/v881_timing_accounting_continuation')]
def main():
    import numpy as np
    import rclpy
    from rclpy.node import Node
    from rclpy.action import ActionClient
    from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy,qos_profile_sensor_data
    from nav_msgs.msg import OccupancyGrid,Odometry
    from sensor_msgs.msg import LaserScan
    from geometry_msgs.msg import TransformStamped
    from tf2_ros import TransformBroadcaster,StaticTransformBroadcaster
    from nav2_msgs.srv import ManageLifecycleNodes,GetCostmap
    from lifecycle_msgs.srv import GetState
    from nav2_msgs.action import ComputePathToPose
    from routing_stack import Stack
    from dynamic_proxy import DynamicPlannerProxy
    from support_envelope import SupportEnvelope,raster_support,polygon
    from exact_lidar import get_lidar_features
    from envelope import raster
    cfg=json.loads((R/'experiments/v897_refuge_navigation/A_motion.yaml').read_text())
    vertices=json.loads(cfg['global_costmap']['global_costmap']['ros__parameters']['footprint'])
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    base=O.parent;w=next(x for x in json.loads((base/'FIRST_TRIGGER_WITNESSES.json').read_text())if x['hold']==6)
    scans=json.loads(gzip.decompress((base/'inputs/physics__SENSORS.json.gz').read_bytes()));scan=next(p for p in scans if p['native_tick']==w['state']['native_tick'])
    from refuge_logic import choose_refuge
    original_choice=w['choice'];w['choice']=choose_refuge(w['body'],w['history'],w['state']['support_bounds'],w['age'],known);assert w['choice']is not None
    fixture=dict(xy=w['body'][:2],yaw=w['body'][2],time=w['state']['time'],ranges=scan['ranges'])
    support=np.asarray(w['state']['support_bounds'])+.1+.08*(w['age']+2.5);mode='support';rectangle=None
    rclpy.init();node=Node('phase_dynamic_consistency_zero_vehicle');stack=Stack(O,R/'experiments/v897_refuge_navigation/A_motion.yaml')
    end=time.monotonic()+90;result=dict(passed=False,models=0,integrations=0,navigate_goals=0,actuator_execution=0,source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in C.glob('*.py')});cases=[]
    def forecast():return polygon(support),dict(center_support_bounds=w['state']['support_bounds'],source_age_s=w['age'],fixed_saved_fixture=True,source_native_tick=w['state']['native_tick'])
    proxy=DynamicPlannerProxy(node,lambda:dict(sent_at=time.monotonic(),body=[*fixture['xy'],fixture['yaw'],0.,0.]),O,time.time()+100,forecast,vertices)
    proxy.refuge_mode=True;proxy.refuge_selection=w['choice']
    def wait(predicate,message):
        while time.monotonic()<end:
            rclpy.spin_once(node,timeout_sec=.005)
            if stack.failed():raise RuntimeError('SERVER_EXIT '+str(stack.failed()))
            if predicate():return
        raise TimeoutError(message)
    tf=TransformBroadcaster(node);static=StaticTransformBroadcaster(node);transforms=[]
    for parent,child in [('map','odom'),('base_link','base_scan')]:
        t=TransformStamped();t.header.frame_id=parent;t.child_frame_id=child;t.transform.rotation.w=1.;t.header.stamp=node.get_clock().now().to_msg();transforms.append(t)
    static.sendTransform(transforms);scanpub=node.create_publisher(LaserScan,'scan',qos_profile_sensor_data);odompub=node.create_publisher(Odometry,'odom',10)
    qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE)
    pub=node.create_publisher(OccupancyGrid,'phase_dynamic_envelope',qos);count=0
    def publish():
        nonlocal count
        stamp=node.get_clock().now().to_msg();x,y=fixture['xy'];a=fixture['yaw']
        t=TransformStamped();t.header.stamp=stamp;t.header.frame_id='odom';t.child_frame_id='base_link';t.transform.translation.x=x;t.transform.translation.y=y;t.transform.rotation.z=math.sin(a/2);t.transform.rotation.w=math.cos(a/2);tf.sendTransform(t)
        od=Odometry();od.header.stamp=stamp;od.header.frame_id='odom';od.child_frame_id='base_link';od.pose.pose.position.x=x;od.pose.pose.position.y=y;od.pose.pose.orientation=t.transform.rotation;odompub.publish(od)
        scan=LaserScan();scan.header.stamp=stamp;scan.header.frame_id='base_scan';scan.angle_min=0.;scan.angle_max=31*2*math.pi/32;scan.angle_increment=2*math.pi/32;scan.range_min=.05;scan.range_max=3.;scan.scan_time=.05;scan.ranges=[max(.05,float(z))if z<2.999 else float('inf')for z in fixture['ranges']];scanpub.publish(scan)
        if count%4==0:
            grid=OccupancyGrid();grid.header.stamp=stamp;grid.header.frame_id='map';grid.info.resolution=.01;grid.info.width=1000;grid.info.height=1000;grid.info.origin.position.x=-5.;grid.info.origin.position.y=-5.;grid.info.origin.orientation.w=1.
            grid.data=array.array('b',(raster(rectangle)if mode=='rectangle'else raster_support(support)).tobytes());pub.publish(grid)
        count+=1
    node.create_timer(.05,publish)
    try:
        stack.start()
        names=['map_server','planner_server','controller_server','behavior_server','velocity_smoother','collision_monitor','bt_navigator']
        for _ in range(2):
            for name in names:
                client=node.create_client(GetState,name+'/get_state');wait(client.service_is_ready,'GET_STATE_READY');f=client.call_async(GetState.Request());wait(f.done,'GET_STATE_REPLY');assert f.result().current_state.id==1;node.destroy_client(client)
        client=node.create_client(ManageLifecycleNodes,'lifecycle_manager_navigation/manage_nodes');wait(client.service_is_ready,'MANAGER_READY');req=ManageLifecycleNodes.Request();req.command=0;f=client.call_async(req);wait(f.done,'ACTIVATE');assert f.result().success
        action=ActionClient(node,ComputePathToPose,'compute_path_to_pose');wait(action.server_is_ready,'PLANNER_READY')
        labels=[('actual_first_trigger_refuge',True,'support')]
        for label,new_proxy,mode in labels:
            proxy.use_new=new_proxy;begun=time.monotonic();wait(lambda:time.monotonic()-begun>1.5,'MAP_SETTLE')
            request=ComputePathToPose.Goal();request.use_start=True;request.planner_id='GridBased'
            for p,x,y,a in [(request.start,*fixture['xy'],fixture['yaw']),(request.goal,*w['choice']['goal'])]:
                p.header.frame_id='map';p.header.stamp=node.get_clock().now().to_msg();p.pose.position.x=x;p.pose.position.y=y;p.pose.orientation.z=math.sin(a/2);p.pose.orientation.w=math.cos(a/2)
            f=action.send_goal_async(request);wait(f.done,'PLAN_ACCEPT');handle=f.result();assert handle.accepted;f=handle.get_result_async();wait(f.done,'PLAN_RESULT');answer=f.result()
            case=dict(label=label,status=answer.status,error_code=answer.result.error_code,scan_time=fixture['time'],pose=[*fixture['xy'],fixture['yaw']],path=[[p.pose.position.x,p.pose.position.y,2*math.atan2(p.pose.orientation.z,p.pose.orientation.w)]for p in answer.result.path.poses],router=proxy.rows[-1]);cases.append(case)
            print(json.dumps(dict(case=label,status=case['status'],error_code=case['error_code'],path_poses=len(case['path']))),flush=True)
        checks=dict(genuine_reeds_shepp_refuge_full_route=cases[0]['status']==4 and len(cases[0]['path'])>1,causal_returned_exit_contract_passed=cases[0]['router'].get('refuge_path_contract',{}).get('passed')is True)
        result.update(passed=all(checks.values()),checks=checks,cases=cases,selected_refuge=w['choice'],original_first_fit=original_choice,scope='Actual first6s-warning saved pose/set and admitted historical refuge; genuine installed Nav2 ComputePathToPose plus returned timed-exit guard, no NavigateToPose/model/control')
    except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc(),cases=cases)
    finally:
        stack.close();node.destroy_node();rclpy.shutdown();(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],error=result.get('error'),checks=result.get('checks'))),flush=True)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
