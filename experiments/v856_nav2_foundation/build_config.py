"""Generate robot-specific Nav2 configuration from pinned upstream Jazzy defaults."""
import json,math,os,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v856_nav2_foundation'

def build(mode='smoke'):
    # JSON is valid YAML and avoids an extra authoring-time Python dependency.
    rootfs=OUT/'rootfs';sys.path.insert(0,str(rootfs/'usr/lib/python3/dist-packages'));import yaml
    config=yaml.safe_load((C/'nav2_jazzy_original.yaml').read_text());nodes=['map_server','planner_server','controller_server','behavior_server','velocity_smoother','collision_monitor','bt_navigator']
    for name in nodes:config.setdefault(name,{}).setdefault('ros__parameters',{})['use_sim_time']=False
    config['bt_navigator']['ros__parameters'].update(global_frame='map',robot_base_frame='base_link',odom_topic='odom',default_nav_to_pose_bt_xml=str(C/'phase_bt.xml'),default_nav_through_poses_bt_xml=str(C/'phase_bt.xml'),bt_loop_duration=10,default_server_timeout=100,wait_for_service_timeout=5000)
    cp=config['controller_server']['ros__parameters'];cp.update(controller_frequency=20.0,min_x_velocity_threshold=.001,min_y_velocity_threshold=.001,min_theta_velocity_threshold=.001,failure_tolerance=.3)
    cp['progress_checker'].update(required_movement_radius=.20,movement_time_allowance=20.0);cp['general_goal_checker'].update(xy_goal_tolerance=.35,yaw_goal_tolerance=3.141592653589793,stateful=True)
    follow=cp['FollowPath'];follow.update(time_steps=56,model_dt=.05,batch_size=1000,iteration_count=1,vx_max=.30,vx_min=-.15,vy_max=0.0,wz_max=.24,ax_max=.40,ax_min=-.40,ay_max=0.0,ay_min=0.0,az_max=.4,vx_std=.10,vy_std=0.0,wz_std=.12,visualize=False,publish_optimal_trajectory=False,motion_model='Ackermann',enforce_path_inversion=True,inversion_xy_tolerance=.16,inversion_yaw_tolerance=.25,temperature=.3,gamma=.015,regenerate_noises=True)
    follow['AckermannConstraints']=dict(min_turning_r=1.32);follow['CostCritic'].update(consider_footprint=True,near_goal_distance=.45);follow['GoalCritic']['threshold_to_consider']=1.4;follow['PathAngleCritic']['mode']=2
    footprint='[[0.44,0.375],[0.44,-0.375],[-0.44,-0.375],[-0.44,0.375]]'
    for name,frame in [('local_costmap','odom'),('global_costmap','map')]:
        p=config[name][name]['ros__parameters'];p.update(use_sim_time=False,global_frame=frame,robot_base_frame='base_link',resolution=.05,footprint=footprint,footprint_padding=.15,always_send_full_costmap=False,update_frequency=10. if name=='local_costmap' else 2.,publish_frequency=1.,transform_tolerance=.15,plugins=['static_layer','obstacle_layer','inflation_layer']);p.pop('robot_radius',None);p['static_layer']=dict(plugin='nav2_costmap_2d::StaticLayer',map_subscribe_transient_local=True);p['obstacle_layer']=dict(plugin='nav2_costmap_2d::ObstacleLayer',enabled=True,observation_sources='scan',combination_method=1,scan=dict(topic='scan',max_obstacle_height=2.,clearing=True,marking=True,data_type='LaserScan',raytrace_max_range=3.,raytrace_min_range=.05,obstacle_max_range=2.99,obstacle_min_range=.05,inf_is_valid=True));p['inflation_layer']=dict(plugin='nav2_costmap_2d::InflationLayer',cost_scaling_factor=4.,inflation_radius=.85)
        if name=='local_costmap':p.update(rolling_window=True,width=6,height=6)
        else:p.update(track_unknown_space=True,rolling_window=False)
        p.pop('filters',None);p.pop('keepout_filter',None)
    pp=config['planner_server']['ros__parameters'];pp.update(expected_planner_frequency=1.,planner_plugins=['GridBased']);pp['GridBased']=dict(plugin='nav2_smac_planner::SmacPlannerHybrid',tolerance=.25,downsample_costmap=False,allow_unknown=False,max_iterations=100000,max_on_approach_iterations=1000,max_planning_time=.5,motion_model_for_search='REEDS_SHEPP',angle_quantization_bins=72,analytic_expansion_ratio=3.5,analytic_expansion_max_length=3.,minimum_turning_radius=1.32,reverse_penalty=2.,change_penalty=0.,non_straight_penalty=1.2,cost_penalty=2.,retrospective_penalty=.015,lookup_table_size=10.,cache_obstacle_heuristic=True,smooth_path=True)
    bp=config['behavior_server']['ros__parameters'];bp.update(robot_base_frame='base_link',local_frame='odom',global_frame='map',transform_tolerance=.15,behavior_plugins=['backup','wait']);bp['backup']=dict(plugin='nav2_behaviors::BackUp')
    sp=config['velocity_smoother']['ros__parameters'];sp.update(smoothing_frequency=20.,feedback='CLOSED_LOOP',max_velocity=[.30,0.,.24],min_velocity=[-.15,0.,-.24],max_accel=[.40,0.,.40],max_decel=[-.40,0.,-.40],odom_topic='odom',odom_duration=.10,velocity_timeout=.20)
    cm=config['collision_monitor']['ros__parameters'];cm.update(base_frame_id='base_link',odom_frame_id='odom',cmd_vel_in_topic='cmd_vel_smoothed',cmd_vel_out_topic='cmd_vel',transform_tolerance=.15,source_timeout=.25,polygons=['FootprintApproach'],observation_sources=['scan']);cm['FootprintApproach'].update(time_before_collision=1.5,min_points=1,simulation_time_step=.05);cm['scan'].update(topic='scan',enabled=True)
    config['map_server']['ros__parameters']['yaml_filename']=str(OUT/'map.yaml')
    config['lifecycle_manager_navigation']={'ros__parameters':dict(use_sim_time=False,autostart=True,node_names=nodes,bond_timeout=4.,attempt_respawn_reconnection=False)}
    target=C/'phase_nav2_params.yaml';target.write_text(json.dumps(config,indent=2)+'\n')
    # Closed empty-map software smoke, distinct from physical field acceptance.
    resolution=.05;width=200;height=200;cells=bytearray([254]*(width*height))
    for y in range(height):
        for x in range(width):
            if x<2 or y<2 or x>=width-2 or y>=height-2:cells[(height-y-1)*width+x]=0
    (OUT/'map.pgm').write_bytes(f'P5\n{width} {height}\n255\n'.encode()+cells);(OUT/'map.yaml').write_text(json.dumps(dict(image=str(OUT/'map.pgm'),mode='trinary',resolution=resolution,origin=[-5.,-5.,0.],negate=0,occupied_thresh=.65,free_thresh=.196),indent=2)+'\n')
    return target,nodes
if __name__=='__main__':print(build())
