"""Genuine Nav2 layer ingestion/clearing checks; no model, goal, or actuator execution."""
import array,importlib.abc,json,math,os,sys,time,traceback
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,*args):
        if fullname.split('.')[0]in {'mujoco','torch','vehicle','factory','physical'}:raise RuntimeError('FORBIDDEN_MODEL_IMPORT '+fullname)
sys.meta_path.insert(0,NoModel())
R=Path(__file__).resolve().parents[2];O=R/'runs/v889_motion_envelope_software'/('ros_layer'if len(sys.argv)==1 else sys.argv[1]);C=R/'experiments/v890_motion_envelope_dynamic'
sys.path[:0]=[str(R/'experiments/v881_timing_accounting_continuation'),str(R/'experiments/v889_motion_envelope_software')]
def main():
    import numpy as np
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy,qos_profile_sensor_data
    from nav_msgs.msg import OccupancyGrid,Odometry
    from sensor_msgs.msg import LaserScan
    from geometry_msgs.msg import TransformStamped
    from tf2_ros import TransformBroadcaster,StaticTransformBroadcaster
    from nav2_msgs.srv import ManageLifecycleNodes,GetCostmap
    from lifecycle_msgs.srv import GetState
    from routing_stack import Stack
    from envelope import raster
    O.mkdir(exist_ok=False);rclpy.init();node=Node('phase_motion_layer_zero_vehicle_qualification');stack=Stack(O,C/'A_motion.yaml');result=dict(passed=False,models=0,integrations=0,actual_navigation_goals=0,actuator_execution=0);deadline=time.monotonic()+65
    from planner_proxy import PlannerProxy
    proxy=PlannerProxy(node,lambda:dict(sent_at=time.monotonic(),body=[.5,-1.5,0.,0.,0.]),O,time.time()+65)
    import gzip
    scans_saved=json.loads(gzip.decompress((O.parent/'inputs/physics__SENSORS.json.gz').read_bytes()))
    fixture=min(scans_saved,key=lambda p:abs(p['time']-60.01));pose_xy=fixture['xy'];pose_yaw=fixture['yaw']
    def wait(predicate,message):
        while time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=.01)
            if stack.failed():raise RuntimeError('SERVER_EXIT '+str(stack.failed()))
            if predicate():return
        raise TimeoutError(message)
    tf=TransformBroadcaster(node);static=StaticTransformBroadcaster(node);transforms=[]
    for parent,child in [('map','odom'),('base_link','base_scan')]:
        t=TransformStamped();t.header.frame_id=parent;t.child_frame_id=child;t.transform.rotation.w=1.;t.header.stamp=node.get_clock().now().to_msg();transforms.append(t)
    static.sendTransform(transforms);scanpub=node.create_publisher(LaserScan,'scan',qos_profile_sensor_data);odompub=node.create_publisher(Odometry,'odom',10)
    qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE);pub=node.create_publisher(OccupancyGrid,'phase_dynamic_envelope',qos);rectangle=[1.65,-1.05,1.95,-.75];generation=0;published=0
    def publish():
        nonlocal published
        stamp=node.get_clock().now().to_msg();t=TransformStamped();t.header.stamp=stamp;t.header.frame_id='odom';t.child_frame_id='base_link';t.transform.translation.x=pose_xy[0];t.transform.translation.y=pose_xy[1];t.transform.rotation.z=math.sin(pose_yaw/2);t.transform.rotation.w=math.cos(pose_yaw/2);tf.sendTransform(t)
        od=Odometry();od.header.stamp=stamp;od.header.frame_id='odom';od.child_frame_id='base_link';od.pose.pose.position.x=pose_xy[0];od.pose.pose.position.y=pose_xy[1];od.pose.pose.orientation=t.transform.rotation;odompub.publish(od)
        scan=LaserScan();scan.header.stamp=stamp;scan.header.frame_id='base_scan';scan.angle_min=0.;scan.angle_max=31*2*math.pi/32;scan.angle_increment=2*math.pi/32;scan.range_min=.05;scan.range_max=3.;scan.scan_time=.05;scan.ranges=[float('inf')]*32;scanpub.publish(scan)
        if published%4==0:
            grid=OccupancyGrid();grid.header.stamp=stamp;grid.header.frame_id='map';grid.info.resolution=.01;grid.info.width=1000;grid.info.height=1000;grid.info.origin.position.x=-5.;grid.info.origin.position.y=-5.;grid.info.origin.orientation.w=1.;grid.data=array.array('b',raster(rectangle).tobytes());pub.publish(grid)
        published+=1
    timer=node.create_timer(.05,publish)
    def costmaps():
        maps={}
        for name in ['global_costmap','local_costmap']:
            client=node.create_client(GetCostmap,name+'/get_costmap');wait(client.service_is_ready,'COSTMAP_SERVICE '+name);future=client.call_async(GetCostmap.Request());wait(future.done,'COSTMAP_RESULT '+name);m=future.result().map;meta=m.metadata;data=np.asarray(m.data,np.uint8).reshape(meta.size_y,meta.size_x);maps[name]=(meta,data);node.destroy_client(client)
            np.savez_compressed(O/(name+'_'+str(generation)+'.npz'),data=data,origin=[meta.origin.position.x,meta.origin.position.y],resolution=meta.resolution)
        return maps
    def value(item,x,y):
        meta,data=item;i=int(math.floor((x-meta.origin.position.x)/meta.resolution));j=int(math.floor((y-meta.origin.position.y)/meta.resolution));return int(data[j,i])
    try:
        stack.start()
        # Use the same two real pre-activation state probes as the production bridge.
        for probe in range(2):
            for name in ['map_server','planner_server','controller_server','behavior_server','velocity_smoother','collision_monitor','bt_navigator']:
                client=node.create_client(GetState,name+'/get_state');wait(client.service_is_ready,'PREACTIVATE_STATE_READY');future=client.call_async(GetState.Request());wait(future.done,'PREACTIVATE_STATE_REPLY');assert future.result().current_state.id==1;node.destroy_client(client)
        manager=node.create_client(ManageLifecycleNodes,'lifecycle_manager_navigation/manage_nodes');wait(manager.service_is_ready,'MANAGER_READY');req=ManageLifecycleNodes.Request();req.command=0;future=manager.call_async(req);wait(future.done,'MANAGER_ACTIVATE');assert future.result().success
        states={}
        for name in ['map_server','planner_server','controller_server','behavior_server','velocity_smoother','collision_monitor','bt_navigator']:
            client=node.create_client(GetState,name+'/get_state');wait(client.service_is_ready,'STATE_READY');future=client.call_async(GetState.Request());wait(future.done,'STATE_REPLY');states[name]=future.result().current_state.id;node.destroy_client(client)
        assert all(x==3 for x in states.values())
        start=time.monotonic();wait(lambda:time.monotonic()-start>1.5,'FIRST_MAP_WAIT');first=costmaps()
        checks={}
        for name,item in first.items():
            checks[name+'_forecast_box_lethal']=value(item,1.8,-.9)==254
            checks[name+'_known_static_preserved']=value(item,0.,-3.)==254
            checks[name+'_resolution_stays_original']=abs(item[0].resolution-.01)<1e-8
        rectangle=[2.45,-.85,2.75,-.55];generation=1;start=time.monotonic();wait(lambda:time.monotonic()-start>1.5,'SECOND_MAP_WAIT');second=costmaps()
        for name,item in second.items():
            checks[name+'_old_dynamic_lethal_cleared']=value(item,1.8,-.9)<254
            checks[name+'_new_dynamic_lethal_present']=value(item,2.6,-.7)==254
            checks[name+'_static_not_erased_by_free_update']=value(item,0.,-3.)==254
        if len(sys.argv)>1 and sys.argv[1].startswith('planner_'):
            import gzip
            from rclpy.action import ActionClient
            from nav2_msgs.action import ComputePathToPose
            states_saved=json.loads(gzip.decompress((O.parent/'CAUSAL_ENVELOPE_STATES.json.gz').read_bytes()))
            forecast=min(states_saved,key=lambda x:abs(x['state']['time']-60.01))
            rectangle=forecast['rectangle'];generation=2;start=time.monotonic();wait(lambda:time.monotonic()-start>1.5,'SAVED_FORECAST_MAP_WAIT')
            client=ActionClient(node,ComputePathToPose,'compute_path_to_pose');wait(client.server_is_ready,'PLANNER_ACTION_READY')
            request=ComputePathToPose.Goal();request.use_start=True;request.planner_id='GridBased'
            for pose,x,y,a in [(request.start,*pose_xy,pose_yaw),(request.goal,4.,-2.,0.)]:pose.header.frame_id='map';pose.header.stamp=node.get_clock().now().to_msg();pose.pose.position.x=x;pose.pose.position.y=y;pose.pose.orientation.z=math.sin(a/2);pose.pose.orientation.w=math.cos(a/2)
            future=client.send_goal_async(request);wait(future.done,'SOFTWARE_PLAN_ACCEPT');handle=future.result();assert handle.accepted;future=handle.get_result_async();wait(future.done,'SOFTWARE_PLAN_RESULT');answer=future.result()
            checks['genuine_planner_returns_full_route_with_saved_dynamic_forecast']=answer.status==4 and len(answer.result.path.poses)>1
            result['saved_forecast_plan']=dict(source_scan_time=forecast['state']['time'],rectangle=rectangle,action_status=answer.status,error_code=answer.result.error_code,path=[[p.pose.position.x,p.pose.position.y,2*math.atan2(p.pose.orientation.z,p.pose.orientation.w)]for p in answer.result.path.poses])
        result.update(passed=all(checks.values()),checks=checks,active_states=states,map_publications=published//4,scope='Real installed Nav2 global/local motion-map layer ingestion and replacement; zero vehicle models, no action goal or command execution')
    except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc())
    finally:
        stack.close();node.destroy_node();rclpy.shutdown();(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
