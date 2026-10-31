"""Pure-physics static-unknown scene pilot. All planner inputs are prior map and causal sensor returns."""
import argparse,fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback,shutil
from pathlib import Path
from types import MethodType
import numpy as np
from factory import initialize
from instrumentation import Audit,dump,install_physical_contract
from planner import PointMemory,search,wrap
from robot_predictor import RobotPredictor
from perception import measured_points
from circle_memory import CircleMemory
from range_circle_memory import RangeCircleMemory
from tracking import switch_if_settled
from control_contract import planner_steering_bound
from geometry_predictor import RobotPredictor as GeometryPredictor,SELF_DOMAIN
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import build as exact_field

p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--preflight-only',action='store_true');p.add_argument('--feasibility-only',action='store_true');p.add_argument('--wall-seconds',type=int,default=900);p.add_argument('--seed',type=int,default=73105157);p.add_argument('--conditions',default='geometry_memory');p.add_argument('--scene',choices=['single_event','legacy_two'],default='single_event');p.add_argument('--max-steps',type=int,default=1200);a=p.parse_args()
repo=Path(os.environ['PHASE_REPO']);outer=Path(os.environ['PHASE_RUNS'])/'v652_static_confirmation'/a.name;outer.mkdir(parents=True,exist_ok=False)
execution_lock=(Path(os.environ['PHASE_RUNS'])/'v648_static_unknown'/'execution.lock').open('a+')
fcntl.flock(execution_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
source_snapshot=outer/'source_snapshot';source_snapshot.mkdir()
source_hashes={}
for source_path in Path(__file__).parent.glob('*.py'):
    shutil.copy2(source_path,source_snapshot/source_path.name);source_hashes[source_path.name]=hashlib.sha256(source_path.read_bytes()).hexdigest()
dump(source_snapshot/'SHA256.json',source_hashes)
dump(source_snapshot/'INVOCATION.json',{'argv':sys.argv,'protocol_sha256':hashlib.sha256((Path(__file__).parent/'PROTOCOL.md').read_bytes()).hexdigest()})
shutil.copy2(Path(__file__).parent/'PROTOCOL.md',source_snapshot/'PROTOCOL.md')
started=time.monotonic()
def timeout(*_):raise TimeoutError('STATIC_PILOT_900S_HARD_BUDGET')
signal.signal(signal.SIGALRM,timeout);signal.alarm(a.wall_seconds)
context=None;status='FAILED';error=None;results=[]
try:
    context,native=initialize(a.seed,outer/'paired');out=context['out'];env=context['env'];B=context['B'];shift=context['shift'];model=context['model'];F=context['F'];H=context['H']
    import mujoco
    import phase_v345_runtime as sensor_backend
    from contact_contract import GeometryCatalog,ContactRecorder
    changed=install_physical_contract(env)
    # Disable the old replanning algorithm equally in all arms; the baseline is explicitly frozen-SAC/fixed-prior-path.
    env.phase21_v3_enable_detour=False
    env.REVALIDATE_MAX_REPLANS=0
    env._phase21_v8_replan=MethodType(lambda self,*a,**k:False,env)
    env.inner.goal_threshold=.45
    env._phase21_v4_known_map_obstacles=MethodType(B.clean_map,env)
    gid=mujoco.mj_name2id(env.model,mujoco.mjtObj.mjOBJ_GEOM,sensor_backend.EVENT_NAME)
    assert gid>=0 and int(env.model.geom_bodyid[gid])==0
    if a.seed==73105157:xy=np.array([-.7150000333786011,2.7150001525878906])
    else:
        rect0,circ0=env._phase21_v4_known_map_obstacles()
        prior=np.asarray(env.inner.dense_path,float);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(prior,axis=0),axis=1))]
        candidates=[(abs(float(d)-2.2),pt[:2]) for d,pt in zip(arc,prior) if 1.6<=d<=3.2 and sensor_backend.distance_to_known(pt[:2],.25,(rect0,circ0))>=.30]
        if not candidates:raise RuntimeError('SCENE_INVALID_NO_STATIC_OBSTACLE_PLACEMENT')
        xy=min(candidates,key=lambda x:x[0])[1]
    env.model.geom_pos[gid]=[float(xy[0]),float(xy[1]),.25];env.model.geom_contype[gid]=1;env.model.geom_conaffinity[gid]=1;env.model.geom_rgba[gid,3]=1.
    mujoco.mj_forward(env.model,env.data)
    # Rebuild, rather than append: the sensor backend must contain exactly the
    # active physical scene, including every unknown obstacle in this task.
    from scene_sensors import synchronize_sensor_arrays
    physical_unknown=[];setup_removed=[]
    for hidden_name in env.HIDDEN_GEOM_NAMES:
        hid=mujoco.mj_name2id(env.model,mujoco.mjtObj.mjOBJ_GEOM,hidden_name)
        if hid<0:continue
        active=(env.model.geom_contype[hid]!=0 or env.model.geom_conaffinity[hid]!=0) and env.model.geom_pos[hid,2]>-1
        if not active:continue
        entry={'name':hidden_name,'xy':env.model.geom_pos[hid,:2].copy(),'radius':float(env.model.geom_size[hid,0])}
        if a.scene=='single_event' and hid!=gid:
            setup_removed.append(entry)
            env.model.geom_contype[hid]=0;env.model.geom_conaffinity[hid]=0;env.model.geom_pos[hid,2]=-10;env.model.geom_rgba[hid,3]=0
        else:physical_unknown.append(entry)
    mujoco.mj_forward(env.model,env.data)
    rect,circ=env._phase21_v4_known_map_obstacles()
    sensor_sync=synchronize_sensor_arrays(env,rect,circ,[[*x['xy'],x['radius']]for x in physical_unknown])
    dump(out/'sensor_geometry_sync.json',sensor_sync)
    obs=env._phase19_refresh_initial_observation(context['obs'])
    assert B.audit_known_map(env)['known_map_source_gate_pass']
    rect,circ=env._phase21_v4_known_map_obstacles()
    assert not any(np.linalg.norm(np.asarray(c[:2])-xy)<1e-5 for c in circ)
    bounds=F.extract_self_envelope(env,mujoco)['bounds_xy']
    geometry_mode=a.conditions=='geometry_memory'
    if 'geometry_memory'in a.conditions.split(',')and not geometry_mode:raise ValueError('GEOMETRY_MODE_REQUIRES_SEPARATE_RUN')
    if geometry_mode:
        bounds=SELF_DOMAIN.tolist();mujoco.mj_kinematics(env.model,env.data)
        assert containment_margin(SelfGeometry(env.model,mujoco).actual(env.model,env.data),bounds)>=.002,'INITIAL_SELF_CONFIGURATION_OUTSIDE_DOMAIN'
    original_apply=env.inner._apply_wheel_ctrl
    planner_steer_limit,planner_contract=planner_steering_bound(env,mujoco)
    dump(out/'PLANNER_CONTROL_CONTRACT.json',planner_contract)
    initial_obs=obs.copy()
    snapshot=B.Snapshot(env,shift)
    scene_pos=env.model.geom_pos[gid].copy()
    mujoco.mj_saveModel(env.model,str(out/'scene_model.mjb'),None)
    dump(out/'STATIC_PROTOCOL.json',{'full_model_snapshot':'scene_model.mjb','full_model_sha256':B.sha(out/'scene_model.mjb'),'seed':a.seed,'scene':a.scene,'physical_unknown_obstacles':physical_unknown,'removed_at_scene_construction':setup_removed,'goal_xy':env.goal_xy,'start_qpos':env.data.qpos,'event_xy':xy,'event_radius':float(env.model.geom_size[gid,0]),'obstacle_present_from_initial_time':True,'obstacle_in_planning_prior':False,'known_rectangles':rect,'known_circles':circ,'footprint_bounds':bounds,'physics_contract':changed,'conditions':a.conditions.split(','),'model_sha256':B.sha(B.MODEL),'comparison_scope':'new pure-physics contract; not comparable to legacy pose-assisted success rates','planning_hard_floor_m':.15,'goal_tolerance_m':.45})
    # Offline t0 task audit. This physical-geometry field never enters the planner.
    audit_world=H.world_input(env,[]);audit_world['footprint_bounds']=bounds
    audit_world['circles']=[*audit_world['circles'],*[[*u['xy'],u['radius']]for u in physical_unknown]]
    audit_field=F.FootprintMap(audit_world)
    initial_yaw=float(env.robot_yaw);start_pose=[*env.data.qpos[:2],initial_yaw]
    initial_margin=float(audit_field.pose_values([start_pose])[0])
    dump(out/'PREFLIGHT.json',{'seed':a.seed,'scene':a.scene,'initial_physical_envelope_clearance_m':initial_margin,'eligible_initial_task':initial_margin>=.15-1e-8,'actual_navigation_steps':0,'scope':'t0 task construction/evaluation only, hidden truth not used by online planner','goal_xy':env.goal_xy,'start_pose':start_pose,'unknown_count':len(physical_unknown)})
    if not a.preflight_only and initial_margin<.15-1e-8:
        raise RuntimeError('INITIAL_TASK_MARGIN_INVALID_BEFORE_NAVIGATION')
    if a.feasibility_only:
        from task_preflight import certify
        feasibility=certify(audit_world,start_pose,env.goal_xy,float(env.inner.wheel_base),planner_steer_limit,F,initial_margin)
        dump(out/'TASK_FEASIBILITY.json',feasibility)
    static_ids=np.array([mujoco.mj_name2id(env.model,mujoco.mjtObj.mjOBJ_GEOM,u['name'])for u in physical_unknown],int)
    static_positions=env.model.geom_pos[static_ids].copy()
    for condition in ([] if a.preflight_only or a.feasibility_only else a.conditions.split(',')):
        if condition in ('circle_repeat','memory_repeat') and not any(r['strict_safe_arrival']for r in results if r['condition']!='frozen_sac'):
            dump(out/(condition+'_skipped.json'),{'status':'SKIPPED_DEPENDENT_ON_PRIOR_RECOVERY_SUCCESS','actual_physics_steps':0})
            continue
        snapshot.restore(shift)
        obs=initial_obs.copy()
        env.inner._apply_wheel_ctrl=original_apply
        cell=out/condition;cell.mkdir()
        audit=Audit();audit.begin(env,cell,condition)
        recorder=ContactRecorder(GeometryCatalog(env.model,mujoco,context['xml']),cell)
        count=[0];public=[-1];self_margins=[];actual_self=SelfGeometry(env.model,mujoco)if geometry_mode else None
        def observed(m,d,*args,**kwargs):
            audit.before_native(m,d);native(m,d,*args,**kwargs);audit.after_native(m,d)
            count[0]+=1;recorder.record(d,count[0],public[0])
            assert np.array_equal(m.geom_pos[static_ids],static_positions),'STATIC_OBSTACLE_MOVED_AT_NATIVE_TICK'
            if actual_self is not None:
                mujoco.mj_kinematics(m,d)
                margin=float(containment_margin(actual_self.actual(m,d),bounds));self_margins.append(margin)
                if margin<0:raise RuntimeError('ACTUAL_SELF_GEOMETRY_ESCAPED_ADMISSION_DOMAIN')
        mujoco.mj_step=observed
        predictor=(GeometryPredictor if geometry_mode else RobotPredictor)(env,B.PROJECT,mujoco,native) if condition!='frozen_sac' else None
        memory=PointMemory();circle_memory=CircleMemory();range_memory=RangeCircleMemory();path=None;index=0;events=[];rows=[];last_plan=-999;last_command=np.zeros(4);overrides=0;backup_remaining=0;backup_speed=0.;backup_attempts=0;backup_steps=0;planning_wall=0.;outcome='HORIZON';last_field=None;speed_integral=0.
        branch_start=time.monotonic();initial_hash,initial_parts=B.state_hash(env,shift,include_model=True,components=True)
        dump(cell/'initial_state_components.json',initial_parts)
        excluded=[k for k in initial_parts if k.endswith('.real_indoor_xml')]
        assert len(excluded)==1
        normalized_initial_hash=B.fingerprint({k:v for k,v in initial_parts.items()if k not in excluded})
        dump(cell/'state_hash_normalization.json',{'full_hash':initial_hash,'normalized_hash':normalized_initial_hash,'excluded_components':excluded,'reason':'only generated XML output path; actual scene model and XML content hashes retained'})
        def pose():
            q=env.data.qpos;return np.array([q[0],q[1],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))])
        desired=[None]
        def direct_control(self,lf,rf,lr,rr):
            global last_command,overrides
            command=desired[0]
            if command is None:return original_apply(lf,rf,lr,rr)
            overrides+=int(np.max(np.abs(np.asarray([lf,rf,lr,rr])-command))>1e-6)
            # Bounded actuator commands only; no qpos/qvel/model writes.
            command=np.asarray(command,float)
            command[:2]=np.clip(command[:2],last_command[:2]-.10,last_command[:2]+.10)
            command[2:]=np.clip(command[2:],last_command[2:]-.70,last_command[2:]+.70)
            env.data.ctrl[:]=0.
            for aid,value in zip([self.id_lf_steer,self.id_rf_steer,self.id_lr_wheel,self.id_rr_wheel],command):
                lo,hi=env.model.actuator_ctrlrange[aid];env.data.ctrl[aid]=np.clip(value,lo,hi)
            self.last_lf_steer,self.last_rf_steer,self.last_lr_wheel,self.last_rr_wheel=map(float,command)
            last_command=command.copy()
        if condition!='frozen_sac':env.inner._apply_wheel_ctrl=MethodType(direct_control,env.inner)
        try:
            for step in range(a.max_steps):
                public[0]=step;current=pose();distance=float(np.linalg.norm(current[:2]-env.goal_xy))
                if distance<=.45:outcome='GOAL';break
                assert np.array_equal(env.model.geom_pos[static_ids],static_positions),'STATIC_OBSTACLE_MOVED'
                if condition!='frozen_sac':
                    sensor,_,sensor_stats=measured_points(env,bounded=condition!='legacy_memory')
                    with (cell/'sensor_censoring.jsonl').open('a') as stream:stream.write(json.dumps({'step':step,**sensor_stats})+'\n')
                    points=memory.update(sensor,rect,circ,step,persist=condition!='no_memory')
                    need=(path is None)
                    world=H.world_input(env,points);world['footprint_bounds']=bounds;world['max_steer']=planner_steer_limit;world['control_candidate_max_steer']=float(env.inner.max_steer);world['wheel_base']=float(env.inner.wheel_base)
                    if condition in ('circle_memory','circle_repeat'):
                        assert a.scene=='single_event','CYLINDER_MODEL_SCOPE_IS_SINGLE_EVENT'
                        estimated,fit_stats=circle_memory.update(sensor,rect,circ,step,current[:2])
                        with (cell/'circle_estimate.jsonl').open('a')as stream:stream.write(json.dumps({'step':step,**fit_stats})+'\n')
                        if estimated is not None:
                            world['sensor_points']=[]
                            world['circles']=[*world['circles'],estimated.tolist()]
                    elif condition in ('range_memory','geometry_memory'):
                        estimated,unmodeled,fit_stats=range_memory.update(env,rect,circ,step)
                        with (cell/'range_estimate.jsonl').open('a')as stream:stream.write(json.dumps({'step':step,**fit_stats})+'\n')
                        world['sensor_points']=unmodeled.tolist()
                        world['circles']=[*world['circles'],*estimated.tolist()]
                    # Field reconstruction tracks only past/current measured points and the known prior.
                    field=exact_field(F,world)if geometry_mode else F.FootprintMap(world);field.guard=.15;field.base_heuristic=F.base._heuristic_grid
                    last_field=field
                    clearance=float(field.pose_values([current])[0])
                    if clearance<.15-1e-5:
                        dump(cell/'hard_floor_rejection.json',{'step':step,'clearance_m':clearance,'hard_floor_m':.15,'pose':current,'footprint_bounds':bounds})
                        outcome='INITIAL_TASK_MARGIN_INVALID' if step==0 else 'OBSERVED_HARD_FLOOR_BREACH';break
                    if path is not None and backup_remaining==0:
                        active_gear=int(path[min(index+1,len(path)-1),3])
                        segment_end=index+1
                        while segment_end<len(path)-1 and int(path[segment_end+1,3])==active_gear:segment_end+=1
                        distances=np.linalg.norm(path[index:min(segment_end+1,index+40),:2]-current[:2],axis=1)
                        # A nearest-point update cannot bypass the stopped-cusp gate.
                        nearest_index=index+int(np.argmin(distances))
                        index=min(nearest_index,segment_end-1) if segment_end<len(path)-1 else nearest_index
                        index,transition=switch_if_settled(path,index,current,env.data.qvel)
                        if transition is not None:
                            with (cell/'gear_transitions.jsonl').open('a')as stream:stream.write(json.dumps({'step':step,**transition})+'\n')
                        if np.min(field.pose_values(path[index:min(len(path),index+26),:3]))<(.155-1e-6 if geometry_mode else .18):need=True
                        if index>=len(path)-4:need=True
                        # Replan on execution divergence or measured stagnation, never on a
                        # hidden-world cost. Preserve a minimum replanning dwell time.
                        heading_error=abs(wrap(current[2]-path[index,2]))
                        if step-last_plan>=12 and (float(np.min(distances))>.20 or heading_error>.50):need=True
                        if step-last_plan>=30 and len(rows)>=30:
                            previous=np.asarray(rows[-30]['pose'])
                            if np.linalg.norm(current[:2]-previous[:2])<.04 and abs(wrap(current[2]-previous[2]))<.06:need=True
                    if need and backup_remaining==0:
                        t=time.monotonic();candidate,stats=search(field,current,env.goal_xy,float(env.inner.wheel_base),planner_steer_limit,guard=.18,budget=2. if geometry_mode else 6.,dense_requested_guard=geometry_mode)
                        if geometry_mode and stats['status']!='GLOBAL_GOAL_PATH':
                            preferred=candidate;preferred_stats=stats
                            candidate,stats=search(field,current,env.goal_xy,float(env.inner.wheel_base),planner_steer_limit,guard=.155,budget=8.,resolution=.05,heading_bins=144,dense_requested_guard=True)
                            if candidate is None and preferred is not None:candidate,stats=preferred,preferred_stats
                            stats['preferred_search']=preferred_stats
                        planning_wall+=time.monotonic()-t;last_plan=step
                        event={'step':step,'pose':current,'sensor_points':len(sensor),'memory_points':len(points),'stats':stats,'path':candidate}
                        events.append(event);dump(cell/f'planning_{step:04d}.json',{'causal_input':world,**event})
                        print('V649_PLAN',condition,step,stats,flush=True)
                        if candidate is None:
                            outcome='NO_SAFE_PROGRESS_PATH';break
                        path=candidate;index=0
                    # Track the geometric segment in its planned gear, allowing low-speed reverse recovery.
                    gear=int(path[min(index+1,len(path)-1),3]);target_index=index+1;arc=0.
                    while target_index<len(path)-1 and arc<.45 and int(path[target_index+1,3])==gear:
                        arc+=float(np.linalg.norm(path[target_index+1,:2]-path[target_index,:2]));target_index+=1
                    target=path[target_index,:2];rel=target-current[:2]
                    lateral=-math.sin(current[2])*rel[0]+math.cos(current[2])*rel[1]
                    steer=float(np.clip(math.atan2(2*float(env.inner.wheel_base)*lateral,max(float(rel@rel),.02)),-env.inner.max_steer,env.inner.max_steer))
                    speed=gear*min(.60,.50/(1+abs(steer)))
                    if distance<1.:speed*=.65
                    # Commands are standard Ackermann geometry, with differential rear-wheel speeds.
                    radius=float(env.inner.wheel_radius)
                    actual_speed=float(env.data.qvel[0]*math.cos(current[2])+env.data.qvel[1]*math.sin(current[2]))
                    speed_integral=float(np.clip(speed_integral+(speed-actual_speed)*.08,-.35,.35))
                    wheel=(speed+1.3*(speed-actual_speed)+.7*speed_integral)/radius
                    wheel=float(np.clip(wheel,-12.,12.))
                    lf,rf,lr,rr=env.inner._ackermann_from_steer_speed(steer,wheel)
                    desired_yaw_rate=speed*math.tan(steer)/float(env.inner.wheel_base)
                    yaw_error=float(np.clip(desired_yaw_rate-float(env.data.qvel[5]),-.6,.6))
                    delta=.8*yaw_error*float(env.inner.track_width)/(2*radius)
                    if backup_remaining>0:
                        proposal,model_gate=predictor.select(env,field,path,index,current,steer,backup_speed,last_command,escape=True)
                    else:
                        proposal,model_gate=predictor.select(env,field,path,index,current,steer,speed,last_command)
                        if proposal is None:
                            backup_speed=-gear*.25;backup_remaining=16;backup_attempts+=1
                            proposal,model_gate=predictor.select(env,field,path,index,current,steer,backup_speed,last_command,escape=True)
                    if proposal is None:
                        dump(cell/'rejected_control.json',{'step':step,'pose':current,'current_clearance_m':clearance,'gate':model_gate})
                        outcome='MPC_AND_BACKUP_NO_SAFE_COMMAND';break
                    if backup_remaining>0:
                        backup_steps+=1;backup_remaining-=1
                        if backup_remaining==0:path=None
                    desired[0]=proposal
                    with (cell/'model_admission.jsonl').open('a') as stream:stream.write(json.dumps({'step':step,**model_gate})+'\n')
                action,_=model.predict(obs,deterministic=True)
                before_count=count[0]
                obs,_,term,trunc,info=B.finish_api(env.step(action))
                audit.after_public(env,step)
                if count[0]==before_count:raise RuntimeError('PUBLIC_STEP_WITHOUT_PHYSICS')
                actual=pose();distance=float(np.linalg.norm(actual[:2]-env.goal_xy))
                row={'step':step,'pose':actual,'goal_distance_m':distance,'nominal_sac_action':action,'applied_ctrl':env.data.ctrl.copy(),'memory_points':len(memory.cells),'physical_step':count[0],'path_index':index,'active_gear':None if path is None else int(path[min(index+1,len(path)-1),3])}
                rows.append(row)
                if step%25==0:
                    dump(cell/'partial_progress.json',{'step':step,'public_steps':len(rows),'physics_steps':count[0],'elapsed_s':time.monotonic()-branch_start,'goal_distance_m':distance,'contacts':recorder.summary(),'outcome':'IN_PROGRESS'})
                    print('V649_PROGRESS',condition,step,'distance',round(distance,3),'pose',np.round(actual,3).tolist(),flush=True)
                if recorder.first_anomaly is not None:outcome='CONTACT_OR_UNKNOWN';break
                if distance<=.45:outcome='GOAL';break
                if term or trunc:outcome='NATIVE_TERMINATION';break
            contacts=recorder.summary();distance=float(np.linalg.norm(pose()[:2]-env.goal_xy))
            strict=bool(distance<=.45 and contacts['robot_obstacle_contact_records']==0 and contacts['unknown_contact_records']==0)
            record={'condition':condition,'seed':a.seed,'outcome':outcome,'strict_safe_arrival':strict,'goal_distance_m':distance,'public_steps':len(rows),'physics_steps':count[0],'contacts':contacts,'backup_attempts':backup_attempts,'backup_steps':backup_steps,'planning_attempts':len(events),'planning_wall_s':planning_wall,'command_overrides':overrides,'elapsed_s':time.monotonic()-branch_start,'initial_state_hash':initial_hash,'normalized_initial_state_hash':normalized_initial_hash,'minimum_actual_self_domain_margin_m':min(self_margins)if self_margins else None,'self_geometry_checked_native_ticks':len(self_margins),'static_obstacle_pose_unchanged':np.array_equal(env.model.geom_pos[static_ids],static_positions),'root_mutations_outside_mjstep':0,'source_revision':'progress_29_joint_consistent_projection'if geometry_mode else 'stability_25_stopped_cusp','prediction_steps':0 if predictor is None else predictor.prediction_steps}
            dump(cell/'result.json',record)
            dump(cell/'trace.json',rows)
            results.append(record);dump(out/'results_so_far.json',results);print('V649_RESULT',json.dumps(record),flush=True)
        finally:
            if not (cell/'result.json').exists():
                dump(cell/'interrupted.json',{'outcome':'INTERRUPTED','strict_safe_arrival':False,'public_steps':len(rows),'physics_steps':count[0],'contacts':recorder.summary(),'elapsed_s':time.monotonic()-branch_start,'initial_state_hash':initial_hash})
                dump(cell/'trace.json',rows)
            recorder.close();mujoco.mj_step=native;env.inner._apply_wheel_ctrl=original_apply
    status='PREFLIGHT_COMPLETE'if a.preflight_only or a.feasibility_only else 'COMPLETE'
except BaseException as e:
    error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()};print(json.dumps(error),flush=True)
finally:
    signal.alarm(0)
    target=(context['out'] if context is not None else (outer/'paired' if (outer/'paired').exists() else outer))/'completion.json'
    dump(target,{'status':status,'seed':a.seed,'results':results,'error':error,'elapsed_s':time.monotonic()-started,'sac_training_updates':0})
if status not in ('COMPLETE','PREFLIGHT_COMPLETE'):sys.exit(1)
