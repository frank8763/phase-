"""Build measured full-cycle map, run official planner in Phase-only ROS ns."""
import sys,json,time,signal,hashlib,importlib.util,importlib.abc,subprocess,shutil,traceback,os
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1107_reference_frame_alignment'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy','factory'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'))
import numpy as np
from kernel import REQUIRED,ref,PARAMETERS,predict,checks
from time_geometry import interval_support
from prediction import Predictor,initial
def save(name,x):(O/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def environment():
    sp=importlib.util.spec_from_file_location('v1107_phase_ros',R/'experiments/v856_nav2_foundation/ros_environment.py');env=importlib.util.module_from_spec(sp);sp.loader.exec_module(env);return env
def prepare():
    x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());assert x['packet']['native_tick']==x['source']['source_native_tick']==21520
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
    radius=float(np.ceil((1/(PARAMETERS['gain_a']*max_k)+.02)*100)/100)
    root=np.array(x['packet']['body'][:3],float);root[:2]-=offset*np.array([np.cos(root[2]),np.sin(root[2])])
    goal=np.array([*x['goal'],np.pi],float);goal[:2]-=offset*np.array([np.cos(goal[2]),np.sin(goal[2])])
    footprint=[];rad=REQUIRED/np.cos(np.pi/32)
    for cx,cy,start in [(offset+.44,.375,0),(offset-.44,.375,np.pi/2),(offset-.44,-.375,np.pi),(offset+.44,-.375,3*np.pi/2)]:
        for a in np.linspace(start,start+np.pi/2,9):footprint.append([cx+rad*np.cos(a),cy+rad*np.sin(a)])
    cfg=dict(resolution=res,source_native_tick=21520,map_sha256=hashlib.sha256(data.tobytes()).hexdigest(),occupied_cells=int(occupied.sum()),actor_cells=int(actor.sum()),footprint=footprint,
        body_half_extents=[.44,.375],raw_required_m=REQUIRED,raster_cell_enclosure_margin_m=half,actor_radius_m=.1,planner_reference_offset_m=offset,
        planner_root_pose=root.tolist(),planner_goal_pose=goal.tolist(),minimum_turning_radius_m=radius,reference_is_effective_model_point_not_measured_axle=True)
    save('CONFIG.json',cfg)
    params=dict(planner_server=dict(ros__parameters=dict(use_sim_time=False,expected_planner_frequency=1.,planner_plugins=['GridBased'],costmap_update_timeout=2.,GridBased=dict(plugin='nav2_smac_planner::SmacPlannerHybrid',
        tolerance=.25,allow_unknown=False,max_iterations=100000,max_on_approach_iterations=1000,max_planning_time=5.,motion_model_for_search='REEDS_SHEPP',angle_quantization_bins=72,
        analytic_expansion_ratio=3.5,analytic_expansion_max_length=float(np.ceil(4*radius*10)/10),minimum_turning_radius=radius,reverse_penalty=2.,change_penalty=0.,non_straight_penalty=1.2,cost_penalty=2.,retrospective_penalty=0.,lookup_table_size=5.,cache_obstacle_heuristic=False,smooth_path=False))),
        global_costmap=dict(global_costmap=dict(ros__parameters=dict(use_sim_time=False,update_frequency=5.,publish_frequency=1.,global_frame='map',robot_base_frame='base_link',resolution=res,track_unknown_space=True,
        plugins=['static_layer','inflation_layer'],static_layer=dict(plugin='nav2_costmap_2d::StaticLayer',map_topic='/phase_v1107_map',map_subscribe_transient_local=True,footprint_clearing_enabled=False),
        inflation_layer=dict(plugin='nav2_costmap_2d::InflationLayer',inflation_radius=.85,cost_scaling_factor=4.),footprint=json.dumps(footprint),footprint_padding=0.,transform_tolerance=.2,rolling_window=False,always_send_full_costmap=True))))
    # JSON is valid YAML and is already used by this repository's Nav2 configs.
    (O/'params.yaml').write_text(json.dumps(params,indent=2)+'\n');return x,cfg
def main():
    assert not(O/'PLAN.json').exists();O.mkdir(exist_ok=True,parents=True)
    qualification=json.loads((O/'ENTRY_QUALIFICATION.json').read_text());assert qualification['passed'],'ENTRY_NOT_QUALIFIED'
    binding=json.loads((O/'SOURCE_FREEZE.json').read_text())
    for name,digest in binding.items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,'FROZEN_SOURCE_CHANGED '+name
    for p in C.iterdir():
        if p.suffix in {'.py','.md'}:shutil.copyfile(p,O/p.name)
    begun=time.monotonic();child=None
    def halt(*_):raise TimeoutError('BOUNDED240S_OFFICIAL_SMAC_QUALIFICATION')
    signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,240)
    save('PLAN.json',dict(scope='official Smac EW effective model reference/derived curvature; unchanged V1106 body-position tracker',models=0,physical_integrations=0,new_measurements=0,
        official_planner_only=True,no_controller_server=True,one_planner_call=True,search_budget_s=5,ROS_outer_s=130,inner_s=240,outer_s=250,automatic_physical_launch=False))
    answer=dict(passed=False,analytical_tracking_native=0,analytical_rolling_stop_native=0,analytical_retained_stop_native=0,official_internal_search_work='not instrumented; not zero');retained=None;replacement=None
    try:
        x,cfg=prepare();sys.path.insert(0,str(R/'experiments/v1103_connected_reference'));from reference_contract import context,admit,select_after_recheck;sys.path.insert(0,str(C))
        previous=R/'runs/v1103_connected_reference';previous_result=json.loads((previous/'COMPLETION.json').read_text());assert previous_result['retained_stop']['passed']
        with np.load(previous/'RETAINED_STOP.npz')as z:stop_s=z['states'].copy();stop_u=z['controls'].copy();stop_r=z['requests'].copy()
        assert np.max(abs(stop_s[0]-initial(x['packet'])['state']))<=1e-8,'RETAINED_STOP_ORIGIN_MISMATCH'
        answer['reused_retained_stop_native']=len(stop_r)
        retained=dict(context=context(x),requests=stop_r,controls=stop_u,independent_stop_passed=True)
        answer['retained_stop']=previous_result['retained_stop']
        env=environment();variables=env.environment();variables.update(ROS_LOG_DIR=str(O/'ros_logs'),ROS_DOMAIN_ID='159',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
        with(O/'ros.console').open('x')as log:child=subprocess.Popen(env.command(['/usr/bin/python3','-B',str(C/'plan.py')]),cwd=R,env=variables,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);code=child.wait(timeout=130)
        child=None;assert code==0 and(O/'PLANNER_RESULT.json').exists(),'OFFICIAL_PLANNER_OPERATION_FAILED';p=json.loads((O/'PLANNER_RESULT.json').read_text());answer['official_planner']={k:v for k,v in p.items()if k!='path'}
        if p['passed']:
            rear=np.array(p['path']);path=rear.copy();path[:,:2]+=cfg['planner_reference_offset_m']*np.c_[np.cos(rear[:,2]),np.sin(rear[:,2])];keep=[0]
            for i in range(1,len(path)):
                da=np.arctan2(np.sin(path[i,2]-path[keep[-1],2]),np.cos(path[i,2]-path[keep[-1],2]))
                if np.linalg.norm(path[i,:2]-path[keep[-1],:2])>1e-8 or abs(da)>1e-8:keep.append(i)
            path=path[keep];rear=rear[keep];assert len(path)>1,'DEGENERATE_OFFICIAL_PATH';samples=[];residual=[];rotation_only=0;gear=[]
            for idx,(a,b) in enumerate(zip(path[:-1],path[1:])):
                da=float(np.arctan2(np.sin(b[2]-a[2]),np.cos(b[2]-a[2])));d=float(np.linalg.norm(b[:2]-a[:2]));n=max(1,int(np.ceil((d+np.hypot(.44,.375)*abs(da))/.002)));t=(np.arange(n)+.5)/n
                samples.append(np.c_[a[:2]+t[:,None]*(b[:2]-a[:2]),a[2]+t*da]);residual.extend([(d+np.hypot(.44,.375)*abs(da))/(2*n)]*n)
                delta=rear[idx+1,:2]-rear[idx,:2];rotation_only+=int(np.linalg.norm(delta)<1e-7 and abs(da)>1e-4)
                gear.append(1 if np.dot(delta,[np.cos(rear[idx,2]),np.sin(rear[idx,2])])>=0 else-1)
            a=np.array(x['packet']['body'][:3]);b=path[0];da=float(np.arctan2(np.sin(b[2]-a[2]),np.cos(b[2]-a[2])));d=float(np.linalg.norm(b[:2]-a[:2]));n=max(1,int(np.ceil((d+np.hypot(.44,.375)*abs(da))/.002)));t=(np.arange(n)+.5)/n
            samples.append(np.c_[a[:2]+t[:,None]*(b[:2]-a[:2]),a[2]+t*da]);residual.extend([(d+np.hypot(.44,.375)*abs(da))/(2*n)]*n)
            poses=np.vstack(samples);st,dy=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(poses);low=float((np.minimum(st,dy)-residual).min())
            answer['independent_rigid_geometry']=dict(passed=low>=REQUIRED,continuous_raw_lower_m=low,required_raw_m=REQUIRED,samples=len(poses),rotation_in_place=rotation_only,goal_distance_m=float(np.linalg.norm(path[-1,:2]-x['goal'])),reverse_edges=sum(a<0 for a in gear),gear_changes=sum(a!=b for a,b in zip(gear[:-1],gear[1:])),car_execution_qualified=False)
            save('PATH_GEARS.json',dict(gear=gear,path=path.tolist(),planner_reference_path=rear.tolist(),reference_offset_m=cfg['planner_reference_offset_m']));answer['passed']=False;answer['path_geometry_passed']=low>=REQUIRED
            if low>=REQUIRED and rotation_only==0:
                try:
                    sys.path.insert(0,str(C));import track;from track import rollout
                    review,ss,uu,rr=rollout(x,path,gear);answer['original_controller_review']=review;answer['analytical_tracking_native']=len(rr);answer['analytical_rolling_stop_native']=2200*len(review.get('rolling_stops',[]));np.savez_compressed(O/'CONTROLLER_SOURCE.npz',states=ss,controls=uu,requests=rr);answer['passed']=review['passed']
                    if review['passed']:
                        manifest=admit(x,review,ss,uu,rr);save('COMPLETE_REFERENCE_CONTRACT.json',manifest);replacement=dict(context=context(x),whole_goal_admitted=True,manifest=manifest)
                except AssertionError as e:answer['original_controller_review']=dict(passed=False,error=str(e))
            answer['remaining_gate']='actual tracking/independent audit/complete route and repeat; this job never launches physics'
        answer.update(diagnostic_completed=True)
    except BaseException as e:answer.update(passed=False,error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=3)
            except BaseException:
                try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
                except ProcessLookupError:pass
        signal.setitimer(signal.ITIMER_REAL,0)
    if retained is not None:
        decision=select_after_recheck(context(x),retained,replacement);answer['handoff_selection']=dict(mode=decision['mode'],retained_stop_preserved=decision['retained_stop'] is retained,scope='saved-state software transaction, no command execution')
    answer['frozen_source_unchanged']=all(hashlib.sha256((R/name).read_bytes()).hexdigest()==digest for name,digest in binding.items())
    if 'track' in sys.modules:
        answer['preview_accounting']=dict(sys.modules['track'].COUNTS)
        if 'original_controller_review' not in answer:
            answer['analytical_tracking_native']=None;answer['analytical_rolling_stop_native']=None
            answer['interrupted_analytical_counts_unknown']=True
    if not answer['frozen_source_unchanged']:answer['passed']=False
    answer['guard_original']=hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest()==qualification['guard_sha256']
    if not answer['guard_original']:answer['passed']=False
    answer.update(closed=True,wall_s=time.monotonic()-begun,models=0,physical_integrations=0,new_measurements=0,automatic_physical_launch=False)
    save('COMPLETION.json',answer)
    pointer=R/'CURRENT_EXPERIMENT.json';current=json.loads(pointer.read_text())
    if current.get('active_run')=='runs/v1107_reference_frame_alignment':
        current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,automatic_additional_simulation=False,latest_software_experiment=dict(version='v1107',completion='runs/v1107_reference_frame_alignment/COMPLETION.json',passed=answer['passed'],closed=True,physical_integrations=0,whole_route_acceptance=False))
        temp=pointer.with_suffix('.v1107.tmp');temp.write_text(json.dumps(current,indent=2,ensure_ascii=False)+'\n');temp.replace(pointer)
    print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
