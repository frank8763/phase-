"""One installed Smac proposal from live causal public inputs, no model access."""
import sys,json,hashlib,subprocess,importlib.util,time,os,signal
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=None
from bindings import PARAMETERS,REQUIRED
from time_geometry import interval_support
import numpy as np

def save(name,x):(O/name).write_text(json.dumps(x,indent=2)+'\n')

def prepare(x,output,radius_extra=0.):
    global O
    O=Path(output)
    res=.025;n=400;axis=-5+(np.arange(n)+.5)*res;xx,yy=np.meshgrid(axis,axis);half=res*np.sqrt(2)/2;occupied=np.zeros((n,n),bool)
    for cx,cy,hx,hy in x['setup']['known']['known_rectangles']:occupied|=(abs(xx-cx)<=hx+half)&(abs(yy-cy)<=hy+half)
    for cx,cy,r in x['setup']['known']['known_circles']:occupied|=np.hypot(xx-cx,yy-cy)<=r+half
    dt=.025;edges=np.arange(0,2*np.pi/.32,dt);bounds=interval_support(x['source']['periodic']['vertices'],edges-.075,edges+dt+.075).max(axis=0)+.1+half
    normal=np.c_[np.cos(np.arange(16)*np.pi/8),np.sin(np.arange(16)*np.pi/8)];actor=np.ones((n,n),bool)
    for (nx,ny),b in zip(normal,bounds):actor&=xx*nx+yy*ny<=b
    occupied|=actor;occupied[0,:]=occupied[-1,:]=True;occupied[:,0]=occupied[:,-1]=True
    data=np.where(occupied,100,0).astype(np.int8);np.save(O/'MAP.npy',data)
    # Circumscribed polygon of rectangle Minkowski safety disk; proposal only,
    # original continuous body geometry remains the independent admission.
    offset=PARAMETERS['lateral_discrete'][0]/PARAMETERS['gain_a'];max_k=np.tan(.42722137342572125)/.6
    radius=float(np.ceil((1/(PARAMETERS['gain_a']*max_k)+.02)*100)/100)+radius_extra
    root=np.array(x['packet']['body'][:3],float);root[:2]-=offset*np.array([np.cos(root[2]),np.sin(root[2])])
    goal=np.array([*x['goal'],x['goal_yaw']],float);goal[:2]-=offset*np.array([np.cos(goal[2]),np.sin(goal[2])])
    footprint=[];rad=REQUIRED/np.cos(np.pi/32)
    for cx,cy,start in [(offset+.44,.375,0),(offset-.44,.375,np.pi/2),(offset-.44,-.375,np.pi),(offset+.44,-.375,3*np.pi/2)]:
        for a in np.linspace(start,start+np.pi/2,9):footprint.append([cx+rad*np.cos(a),cy+rad*np.sin(a)])
    cfg=dict(resolution=res,source_native_tick=x['source']['source_native_tick'],map_sha256=hashlib.sha256(data.tobytes()).hexdigest(),occupied_cells=int(occupied.sum()),actor_cells=int(actor.sum()),footprint=footprint,
        body_half_extents=[.44,.375],raw_required_m=REQUIRED,raster_cell_enclosure_margin_m=half,actor_radius_m=.1,planner_reference_offset_m=offset,
        planner_root_pose=root.tolist(),planner_goal_pose=goal.tolist(),minimum_turning_radius_m=radius,reference_is_effective_model_point_not_measured_axle=True)
    save('CONFIG.json',cfg)
    params=dict(planner_server=dict(ros__parameters=dict(use_sim_time=False,expected_planner_frequency=1.,planner_plugins=['GridBased'],costmap_update_timeout=2.,GridBased=dict(plugin='nav2_smac_planner::SmacPlannerHybrid',
        tolerance=.25,allow_unknown=False,max_iterations=100000,max_on_approach_iterations=1000,max_planning_time=5.,motion_model_for_search='REEDS_SHEPP',angle_quantization_bins=72,
        analytic_expansion_ratio=3.5,analytic_expansion_max_length=float(np.ceil(4*radius*10)/10),minimum_turning_radius=radius,reverse_penalty=2.,change_penalty=0.,non_straight_penalty=1.2,cost_penalty=2.,retrospective_penalty=0.,lookup_table_size=5.,cache_obstacle_heuristic=False,smooth_path=False))),
        global_costmap=dict(global_costmap=dict(ros__parameters=dict(use_sim_time=False,update_frequency=5.,publish_frequency=1.,global_frame='map',robot_base_frame='base_link',resolution=res,track_unknown_space=True,
        plugins=['static_layer','inflation_layer'],static_layer=dict(plugin='nav2_costmap_2d::StaticLayer',map_topic='/phase_v1121_map',map_subscribe_transient_local=True,footprint_clearing_enabled=False),
        inflation_layer=dict(plugin='nav2_costmap_2d::InflationLayer',inflation_radius=.85,cost_scaling_factor=4.),footprint=json.dumps(footprint),footprint_padding=0.,transform_tolerance=.2,rolling_window=False,always_send_full_costmap=True))))
    # JSON is valid YAML and is already used by this repository's Nav2 configs.
    (O/'params.yaml').write_text(json.dumps(params,indent=2)+'\n');return x,cfg

def plan(x,output,radius_extra=0.):
 output=Path(output);output.mkdir(exist_ok=False);_,cfg=prepare(x,output,radius_extra);(output/'CAUSAL_INPUT.json').write_text(json.dumps(x,indent=2)+'\n')
 spec=importlib.util.spec_from_file_location('phase_v1121_ros_environment',R/'experiments/v856_nav2_foundation/ros_environment.py');env=importlib.util.module_from_spec(spec);spec.loader.exec_module(env);variables=env.environment();variables.update(ROS_LOG_DIR=str(output/'ros_logs'),ROS_DOMAIN_ID='159',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
 child=None
 try:
  with(output/'ros.console').open('x')as log:child=subprocess.Popen(env.command(['/usr/bin/python3','-B',str(C/'ros_plan.py'),str(output)]),cwd=R,env=variables,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);code=child.wait(timeout=130)
  assert code==0,'SMAC_HELPER_EXIT';p=json.loads((output/'PLANNER_RESULT.json').read_text())
 finally:
  if child is not None and child.poll()is None:
   try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 if not p['passed']:return dict(passed=False,planner=p)
 rear=np.array(p['path']);path=rear.copy();path[:,:2]+=cfg['planner_reference_offset_m']*np.c_[np.cos(rear[:,2]),np.sin(rear[:,2])];keep=[0]
 for i in range(1,len(path)):
  da=np.arctan2(np.sin(path[i,2]-path[keep[-1],2]),np.cos(path[i,2]-path[keep[-1],2]))
  if np.linalg.norm(path[i,:2]-path[keep[-1],:2])>1e-8 or abs(da)>1e-8:keep.append(i)
 path=path[keep];rear=rear[keep];gears=[]
 for i in range(len(path)-1):
  delta=rear[i+1,:2]-rear[i,:2];assert np.linalg.norm(delta)>1e-7,'SMAC_ROTATION_IN_PLACE';gears.append(1 if np.dot(delta,[np.cos(rear[i,2]),np.sin(rear[i,2])])>=0 else-1)
 answer=dict(passed=len(path)>1,path=path.tolist(),gear=gears,planner=p,config=cfg);(output/'PATH_GEARS.json').write_text(json.dumps(answer,indent=2)+'\n');return answer
