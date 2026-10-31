"""Pure-physics static-unknown scene pilot. All planner inputs are prior map and causal sensor returns."""
import argparse,fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback,shutil
from pathlib import Path
from types import MethodType
import numpy as np
from factory import initialize
from instrumentation import Audit,dump,install_physical_contract
from planner import PointMemory,search,wrap

p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--seed',type=int,default=73105157);p.add_argument('--conditions',default='frozen_sac,memory,no_memory,memory_repeat');p.add_argument('--max-steps',type=int,default=600);a=p.parse_args()
repo=Path(os.environ['PHASE_REPO']);outer=Path(os.environ['PHASE_RUNS'])/'v648_static_unknown'/a.name;outer.mkdir(parents=True,exist_ok=False)
execution_lock=(Path(os.environ['PHASE_RUNS'])/'v648_static_unknown'/'execution.lock').open('a+')
fcntl.flock(execution_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
source_snapshot=outer/'source_snapshot';source_snapshot.mkdir()
source_hashes={}
for source_path in Path(__file__).parent.glob('*.py'):
    shutil.copy2(source_path,source_snapshot/source_path.name);source_hashes[source_path.name]=hashlib.sha256(source_path.read_bytes()).hexdigest()
dump(source_snapshot/'SHA256.json',source_hashes)
started=time.monotonic()
def timeout(*_):raise TimeoutError('STATIC_PILOT_900S_HARD_BUDGET')
signal.signal(signal.SIGALRM,timeout);signal.alarm(900)
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
    sensor_hooks=sensor_backend.install_sensor_hooks(env,mujoco)
    obs=env._phase19_refresh_initial_observation(context['obs'])
    assert B.audit_known_map(env)['known_map_source_gate_pass']
    rect,circ=env._phase21_v4_known_map_obstacles()
    assert not any(np.linalg.norm(np.asarray(c[:2])-xy)<1e-5 for c in circ)
    bounds=F.extract_self_envelope(env,mujoco)['bounds_xy']
    original_apply=env.inner._apply_wheel_ctrl
    initial_obs=obs.copy()
    snapshot=B.Snapshot(env,shift)
    scene_pos=env.model.geom_pos[gid].copy()
    dump(out/'STATIC_PROTOCOL.json',{'seed':a.seed,'goal_xy':env.goal_xy,'start_qpos':env.data.qpos,'event_xy':xy,'event_radius':float(env.model.geom_size[gid,0]),'obstacle_present_from_initial_time':True,'obstacle_in_planning_prior':False,'known_rectangles':rect,'known_circles':circ,'footprint_bounds':bounds,'physics_contract':changed,'conditions':a.conditions.split(','),'model_sha256':B.sha(B.MODEL),'comparison_scope':'new pure-physics contract; not comparable to legacy pose-assisted success rates','planning_hard_floor_m':.15,'goal_tolerance_m':.45})
    for condition in a.conditions.split(','):
        snapshot.restore(shift)
        obs=initial_obs.copy()
        env.inner._apply_wheel_ctrl=original_apply
        cell=out/condition;cell.mkdir()
        audit=Audit();audit.begin(env,cell,condition)
        recorder=ContactRecorder(GeometryCatalog(env.model,mujoco,context['xml']),cell)
        count=[0];public=[-1]
        def observed(m,d,*args,**kwargs):
            audit.before_native(m,d);native(m,d,*args,**kwargs);audit.after_native(m,d)
            count[0]+=1;recorder.record(d,count[0],public[0])
        mujoco.mj_step=observed
        memory=PointMemory();path=None;index=0;events=[];rows=[];last_plan=-999;last_command=np.zeros(4);overrides=0;planning_wall=0.;outcome='HORIZON';last_field=None;speed_integral=0.
        branch_start=time.monotonic();initial_hash=B.state_hash(env,shift,include_model=True)
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
                assert np.array_equal(env.model.geom_pos[gid],scene_pos),'STATIC_OBSTACLE_MOVED'
                if condition!='frozen_sac':
                    sensor,_=env._phase21_sensor_points()
                    points=memory.update(sensor,rect,circ,step,persist=condition!='no_memory')
                    need=(path is None)
                    world=H.world_input(env,points);world['footprint_bounds']=bounds
                    # Field reconstruction tracks only past/current measured points and the known prior.
                    field=F.FootprintMap(world);field.guard=.15;field.base_heuristic=F.base._heuristic_grid
                    last_field=field
                    clearance=float(field.pose_values([current])[0])
                    if clearance<.15-1e-5:
                        dump(cell/'hard_floor_rejection.json',{'step':step,'clearance_m':clearance,'hard_floor_m':.15,'pose':current,'footprint_bounds':bounds})
                        outcome='INITIAL_TASK_MARGIN_INVALID' if step==0 else 'OBSERVED_HARD_FLOOR_BREACH';break
                    if path is not None:
                        distances=np.linalg.norm(path[index:min(len(path),index+40),:2]-current[:2],axis=1)
                        index+=int(np.argmin(distances))
                        if np.min(field.pose_values(path[index:min(len(path),index+26),:3]))<.18:need=True
                        if index>=len(path)-4:need=True
                    if need:
                        t=time.monotonic();candidate,stats=search(field,current,env.goal_xy,float(env.inner.wheel_base),float(env.inner.max_steer),budget=6.)
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
                    desired[0]=np.array([lf,rf,lr-delta,rr+delta],float)
                action,_=model.predict(obs,deterministic=True)
                before_count=count[0]
                obs,_,term,trunc,info=B.finish_api(env.step(action))
                audit.after_public(env,step)
                if count[0]==before_count:raise RuntimeError('PUBLIC_STEP_WITHOUT_PHYSICS')
                actual=pose();distance=float(np.linalg.norm(actual[:2]-env.goal_xy))
                row={'step':step,'pose':actual,'goal_distance_m':distance,'nominal_sac_action':action,'applied_ctrl':env.data.ctrl.copy(),'memory_points':len(memory.cells),'physical_step':count[0]}
                rows.append(row)
                if step%25==0:print('V649_PROGRESS',condition,step,'distance',round(distance,3),'pose',np.round(actual,3).tolist(),flush=True)
                if recorder.first_anomaly is not None:outcome='CONTACT_OR_UNKNOWN';break
                if distance<=.45:outcome='GOAL';break
                if term or trunc:outcome='NATIVE_TERMINATION';break
            contacts=recorder.summary();distance=float(np.linalg.norm(pose()[:2]-env.goal_xy))
            strict=bool(distance<=.45 and contacts['robot_obstacle_contact_records']==0 and contacts['unknown_contact_records']==0)
            record={'condition':condition,'seed':a.seed,'outcome':outcome,'strict_safe_arrival':strict,'goal_distance_m':distance,'public_steps':len(rows),'physics_steps':count[0],'contacts':contacts,'planning_attempts':len(events),'planning_wall_s':planning_wall,'command_overrides':overrides,'elapsed_s':time.monotonic()-branch_start,'initial_state_hash':initial_hash,'static_obstacle_pose_unchanged':np.array_equal(env.model.geom_pos[gid],scene_pos),'root_mutations_outside_mjstep':0,'source_revision':'pilot_05_guide_and_velocity_feedback'}
            dump(cell/'result.json',record)
            dump(cell/'trace.json',rows)
            results.append(record);dump(out/'results_so_far.json',results);print('V649_RESULT',json.dumps(record),flush=True)
        finally:
            recorder.close();mujoco.mj_step=native;env.inner._apply_wheel_ctrl=original_apply
    status='COMPLETE'
except BaseException as e:
    error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()};print(json.dumps(error),flush=True)
finally:
    signal.alarm(0)
    target=(context['out'] if context is not None else outer)/'completion.json'
    dump(target,{'status':status,'seed':a.seed,'results':results,'error':error,'elapsed_s':time.monotonic()-started,'sac_training_updates':0})
if status!='COMPLETE':sys.exit(1)
