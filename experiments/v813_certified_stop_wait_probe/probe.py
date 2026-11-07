"""One fixed, bounded stop-observe-resume component experiment.

Scene truth is confined to the unchanged sensor backend and physical evaluator.
No new complete navigation sample, no guessed future sensor input.
"""
import copy, fcntl, gzip, hashlib, importlib.util, json, math, os, signal, sys, time, traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco

repo=Path(os.environ['PHASE_REPO']);own=Path(__file__).parent
source=repo/'experiments/v812_soft_global_reference'
for p in ['runtime/mk-mini/training/phase14_lidar_depth_nav/envs',
          'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1',
          'experiments/v733_early_low_translation_scan',
          'experiments/v753_coupled_progress_repaired',
          'experiments/v798_legacy_tracking_transplant']:
    sys.path.insert(0,str(repo/p))
sys.path.insert(0,str(source))
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry, containment_margin
from geometry_predictor import RobotPredictor
from exact_footprint import build, pose_values
from reserved_recovery import ReservedRecovery
from motion_tracker import Tracker, install_time_gate
from motion_evaluator import check_forecast
from union_belief import future_cells
from current_guide import attach, route_world
from planner import spatial_search
from sensor_model import packet as sensed_packet
from packet_contract import packet_equal
from canonical_sensor_pose import sensor_pose
from unseen_prior import set_public_origin
from legacy_method import environment

read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v813_certified_stop_wait_probe/physical';root.mkdir(exist_ok=False)
def serial(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)
def dump(name,x):(root/name).write_text(json.dumps(x,default=serial,indent=2,allow_nan=False)+'\n')
def poses(q):
    q=np.asarray(q).reshape(-1,len(q[-1])if np.asarray(q).ndim>1 else len(q))
    return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]

os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
started=float(os.environ['PHASE_STOP_WAIT_STARTED']);deadline=float(os.environ['PHASE_STOP_WAIT_DEADLINE'])
assert abs(deadline-started-900)<1e-6 and time.time()<deadline
window=dict(started_unix=started,absolute_deadline_unix=deadline,round_closed=False,limit_s=900,pid=os.getpid())
dump('ROUND_WINDOW.json',window)
def timeout(*_):raise TimeoutError('V813_FIXED_COMPONENT_ABSOLUTE_STOP')
signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,deadline-time.time())
counts=dict(original_replay=0,branch_native=0,branch_replay=0,private_native=0,new_global_navigation=0,new_confirmation=0)
status='RUNNING';records=[];predictor=None;max_error=0.;minimum=float('inf');self_min=float('inf');bad=0;physical_log=None
try:
    freeze=read(own/'INPUT_FREEZE.json')
    assert all(sha(repo/n)==h for n,h in freeze['files'].items()),'FROZEN_INPUT_CHANGED'
    assert read(repo/'runs/v813_certified_stop_wait_probe/pre_navigation/RESULT.json')['status']=='FIXED_STOP_WAIT_SAVED_INPUTS_EXACT'
    with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        pair=repo/'runs/v812_soft_global_reference/main_slot01/paired';cell=pair/'geometry_memory'
        protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
        noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap']
        base_world=read(cell/'planning_0303.json')['causal_input']
        with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
        beliefs={}
        with(cell/'motion_estimate.jsonl').open()as f:
            for line in f:
                r=json.loads(line)
                if r['step']in[402,586]:beliefs[r['step']]={k:v for k,v in r.items()if k!='step'}
                if r['step']>=586:break
        set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();trackers={}
        for p in packets[:587]:
            _,state=tracker.update_packet(p,protocol['known_rectangles'],protocol['known_circles'])
            if p['step']in beliefs:
                assert state==beliefs[p['step']];trackers[p['step']]=copy.deepcopy(tracker)
        m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m)
        d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d)
        fixed_geom={name:getattr(m,name).copy()for name in ['geom_pos','geom_quat','geom_size','geom_contype','geom_conaffinity']}
        geometry=SelfGeometry(m,mujoco);bounds=np.asarray(protocol['footprint_bounds'])
        catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml')
        static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
        state_spec=mujoco.mjtState.mjSTATE_INTEGRATION
        def integration(real):
            value=np.empty(mujoco.mj_stateSize(m,state_spec));mujoco.mj_getState(m,real,value,state_spec);return value
        prefix_samples=[]
        def private(model,data):
            assert predictor.prediction_steps+1<=3000000,'PRIVATE_NATIVE_BUDGET'
            mujoco.mj_step(model,data);mujoco.mj_kinematics(model,data)
            prefix_samples.append((data.qpos.copy(),data.qvel.copy(),predictor.self_geometry.actual(model,data).copy()))
        predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,private)
        predictor.enable_differential=True;ids=predictor.command_map.ids
        original_predict=predictor.predict
        def bounded_predict(real,target,ids_,last,horizon=240,brake_after=None):
            assert predictor.prediction_steps+horizon<=3000000,'PRIVATE_NATIVE_BUDGET'
            return original_predict(real,target,ids_,last,horizon,brake_after)
        predictor.predict=bounded_predict
        physical_log=gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','wt');context='ORIGINAL_REPLAY'
        def physical(real,public):
            global minimum,self_min,bad
            box=geometry.actual(m,real);margin=float(containment_margin(box,bounds))
            true=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,
                    'circles':np.asarray([*protocol['known_circles'],[*motion.xy(real.time),config['radius_m']]])})
            clearance=float(pose_values(true,poses(real.qpos))[0]);minimum=min(minimum,clearance);self_min=min(self_min,margin)
            contacts=[catalog.classify(c,sum(counts[k]for k in['original_replay','branch_native','branch_replay']),public,float(real.time))for c in real.contact]
            bad+=sum(x['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for x in contacts)
            physical_log.write(json.dumps(dict(context=context,public=public,time=float(real.time),qpos=real.qpos.tolist(),qvel=real.qvel.tolist(),ctrl=real.ctrl.tolist(),mocap=real.mocap_pos.tolist(),clearance_m=clearance,self_margin_m=margin,actual_bounds=box.tolist(),contacts=contacts))+'\n')
            assert clearance>=.15 and margin>=0 and bad==0,'ACTUAL_NATIVE_SAFETY_FAILURE'
            assert all(np.array_equal(getattr(m,n),v)for n,v in fixed_geom.items()),'FIXED_MODEL_CHANGED'
            return [clearance,margin]
        def step_actual(real,command,public,account):
            if public is not None:predictor.command_map.assert_first(command,real.ctrl[ids])
            real.ctrl[:]=0.;real.ctrl[ids]=command;mujoco.mj_step(m,real);counts[account]+=1
            motion.apply(m,real);mujoco.mj_kinematics(m,real);mujoco.mj_collision(m,real)
            return physical(real,-1 if public is None else public)
        snapshots={};saved=[]
        with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:
            for i,line in enumerate(f):
                if i>=4688:break
                old=json.loads(line);j=i//8
                command=np.asarray(old['actual_ctrl'])[ids]
                safe=step_actual(d,command,j if i%8==0 else None,'original_replay')
                error=max(np.max(abs(d.qpos-old['qpos_full'])),np.max(abs(d.qvel-old['qvel_full'])),np.max(abs(d.ctrl-old['actual_ctrl'])),np.max(abs(d.mocap_pos-old['mocap_pos'])))
                max_error=max(max_error,float(error));assert error<=1e-8,'ORIGINAL_NATIVE_REPLAY_NOT_EXACT'
                saved.append(integration(d))
                public=(i+1)//8
                if (i+1)%8==0 and public in[402,586]:
                    snap=mujoco.MjData(m);mujoco.mj_copyData(snap,m,d);snapshots[public]=snap
        assert counts['original_replay']==4688 and set(snapshots)=={402,586}
        np.savez_compressed(root/'ORIGINAL_REPLAY.npz',integration=saved)
        spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
        def fields(state):
            world=copy.deepcopy(base_world);world['sensor_points']=[]
            world['circles']=protocol['known_circles'];world['rectangles']=[*protocol['known_rectangles'],state['current_outer_rectangle']]
            field=build(F,world);field.base_heuristic=F.base._heuristic_grid
            field.nominal_static_geometry=static;install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
            w,metadata=route_world(world,state);route=build(F,w);route.base_heuristic=F.base._heuristic_grid;attach(route,state)
            return field,route,w,metadata
        def coverage(state):
            first=check_forecast(config,state);assert first['passed'],'EXECUTION_329_COVERAGE_FAILURE'
            times=np.arange(657)*.01;lo,hi=future_cells(state['outer_state_cells'],times)
            truth=np.asarray([motion.xy(state['time']+t)for t in times])
            excess=float(np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max())
            assert excess<=1e-7,'PLANNING_657_COVERAGE_FAILURE'
            return dict(execution=first,planning_samples=657,planning_excess_m=excess)
        for checkpoint in[402,586]:
            branch=root/f'checkpoint_{checkpoint}';branch.mkdir();context=f'STOP_WAIT_{checkpoint}'
            snap=snapshots[checkpoint];mujoco.mj_copyData(d,m,snap);branch_start=integration(d).copy()
            local_tracker=copy.deepcopy(trackers[checkpoint]);state=beliefs[checkpoint];public=checkpoint
            observations=[dict(packet=packets[checkpoint],state=state,coverage=coverage(state))];chunks=[];branch_controls=[];branch_states=[];branch_observations=[]
            checkpoint_goal=float(np.linalg.norm(d.qpos[:2]-protocol['goal_xy']))
            def execute_chunk(label,q,v,controls):
                global public,state,max_error
                controls=np.asarray(controls);assert len(controls)%8==0
                init=integration(d).copy();native=[];safety=[];before_pose=poses(d.qpos)[0].copy()
                for tick,c in enumerate(controls):
                    safety.append(step_actual(d,c,public if tick%8==0 else None,'branch_native'))
                    error=max(np.max(abs(d.qpos-q[tick])),np.max(abs(d.qvel-v[tick])))
                    max_error=max(max_error,float(error));assert error<=1e-8,'CERTIFICATE_ACTUAL_NATIVE_MISMATCH'
                    current=integration(d);native.append(current);branch_controls.append(d.ctrl.copy());branch_states.append(current)
                    if tick%8==7:
                        public+=1;xy,yaw=sensor_pose(d.qpos)
                        pp=sensed_packet(xy,yaw,float(d.time),public,protocol,motion,noise)
                        _,state=local_tracker.update_packet(pp,protocol['known_rectangles'],protocol['known_circles'])
                        obs=dict(packet=pp,state=state,coverage=coverage(state));observations.append(obs);branch_observations.append(obs)
                target=branch/(label+'.npz');np.savez_compressed(target,initial=init,qpos=q,qvel=v,controls=controls,integration=native,safety=safety)
                after_pose=poses(d.qpos)[0];chunks.append(dict(label=label,file=str(target.relative_to(root)),native_ticks=len(controls),start_pose=before_pose.tolist(),end_pose=after_pose.tolist(),end_speed_m_s=float(np.linalg.norm(d.qvel[:2]))))
            with np.load(cell/'ordinary_certificates'/f'certificate_{checkpoint-1:04d}.npz')as z:
                assert max(np.max(abs(d.qpos-z['initial_qpos'])),np.max(abs(d.qvel-z['initial_qvel'])))<=1e-8
                assert np.all(z['target'][2:]==0.)
                execute_chunk('retained_brake',z['qpos'],z['qvel'],z['controls'])
            stopped_goal=float(np.linalg.norm(d.qpos[:2]-protocol['goal_xy']));stopped_xy=d.qpos[:2].copy()
            checks=[];selected_path=None;searches=[];last_reserve=None;resume_public=0;resume_start=None;outcome='NO_FORWARD_PATH_AFTER_FIXED_WAITS'
            def append(command,field,label):
                prefix_samples.clear();res=ReservedRecovery(predictor,mujoco,ids,branch)
                before=integration(d).copy();summary=res.admit_nominal(d,command,field,state,public)
                assert np.array_equal(before,integration(d)),'PRIVATE_CHECK_MUTATED_REAL'
                detail=copy.deepcopy(res.last_attempt);accepted=summary is not None and summary['recovery_kind']=='BRAKE_ONLY'
                item=dict(label=label,step=public,summary=summary,detail=detail,brake_only_accepted=accepted)
                checks.append(item)
                if not accepted:return None
                assert len(prefix_samples)==8
                q=np.vstack([np.asarray([p[0]for p in prefix_samples]),res.cache['qpos']]);v=np.vstack([np.asarray([p[1]for p in prefix_samples]),res.cache['qvel']])
                controls=np.vstack([np.repeat([command],8,axis=0),res.cache['controls']])
                cb=branch/(label+'_certificate.npz');np.savez_compressed(cb,qpos=q,qvel=v,controls=controls,initial=before,forecast_state=json.dumps(state),minimum=summary['reserve_minimum_clearance_m'],self_bounds=np.vstack([np.asarray([p[2]for p in prefix_samples]),predictor.last_self_bounds]))
                item['certificate_file']=str(cb.relative_to(root))
                return dict(q=q,v=v,controls=controls,summary=summary)
            for wait in range(3):
                field,route,world,metadata=fields(state);current=poses(d.qpos)[0]
                path,stats=spatial_search(route,current,protocol['goal_xy'],world['wheel_base'],world['max_steer'],guard=.18,budget=2.,dense_requested_guard=True,work_limit=4000,forward_only=True)
                if stats['status']!='GLOBAL_GOAL_PATH':
                    preferred,ps=path,stats
                    path,stats=spatial_search(route,current,protocol['goal_xy'],world['wheel_base'],world['max_steer'],guard=.155,budget=8.,resolution=.05,heading_bins=144,dense_requested_guard=True,work_limit=16000,forward_only=True)
                    if path is None and preferred is not None:path,stats=preferred,ps
                searches.append(dict(step=public,wait_index=wait,state=state,metadata=metadata,stats=stats,path=None if path is None else path.tolist()))
                if path is not None:selected_path=path;break
                if wait==2:break
                command=predictor.command_map.step(np.r_[d.ctrl[ids][:2],0.,0.],d.ctrl[ids])
                hold=append(command,field,f'hold_{wait}')
                if hold is None:outcome='NO_CERTIFIED_BRAKE_ONLY_WAIT';break
                execute_chunk(f'hold_{wait}',hold['q'],hold['v'],hold['controls'])
            if selected_path is not None:
                assert np.all(selected_path[:,3]>0);resume_start=d.qpos[:2].copy();outcome='FORWARD_RESUME_LIMIT'
                for iteration in range(40):
                    field,route,world,metadata=fields(state);current=poses(d.qpos)[0]
                    index=int(np.argmin(np.linalg.norm(selected_path[:,:2]-current[:2],axis=1)));index=min(index,len(selected_path)-2)
                    if float(route.pose_values(selected_path[index:min(len(selected_path),index+26),:3]).min())<.155-1e-6:
                        outcome='FORWARD_REFERENCE_BECAME_CURRENT_INVALID';break
                    target_index=index+1;arc=0.
                    while target_index<len(selected_path)-1 and arc<.45:
                        arc+=float(np.linalg.norm(selected_path[target_index+1,:2]-selected_path[target_index,:2]));target_index+=1
                    rel=selected_path[target_index,:2]-current[:2];lateral=-math.sin(current[2])*rel[0]+math.cos(current[2])*rel[1]
                    steer=float(np.clip(math.atan2(1.2*lateral,max(float(rel@rel),.02)),-world['control_candidate_max_steer'],world['control_candidate_max_steer']))
                    speed=min(.60,.50/(1+abs(steer)))
                    proxy=environment(d,m);proxy.inner.max_steer=world['control_candidate_max_steer'];proxy.goal_xy=np.asarray(protocol['goal_xy'])
                    before=integration(d).copy();proposal,gate=predictor.select(proxy,field,selected_path,index,current,steer,speed,d.ctrl[ids])
                    assert np.array_equal(before,integration(d));distinct=[];seen=set();found=None
                    for c in predictor.ranked_safe_candidates:
                        key=tuple(c[1])
                        if key not in seen:seen.add(key);distinct.append(c)
                    assert len(distinct)<=25
                    for rank,candidate in enumerate(distinct):
                        found=append(candidate[1],field,f'resume_{iteration:02d}_rank{rank:02d}')
                        if found is not None:break
                    if found is None:outcome='NO_FORWARD_PREFIX_WITH_BRAKE_ONLY_RESERVE';break
                    last_reserve=found;execute_chunk(f'resume_{iteration:02d}',found['q'][:8],found['v'][:8],found['controls'][:8]);resume_public+=1
                    assert predictor.prediction_steps<=3000000,'PRIVATE_NATIVE_BUDGET'
                if last_reserve is not None:
                    execute_chunk('complete_last_retained_tail',last_reserve['q'][8:],last_reserve['v'][8:],last_reserve['controls'][8:])
            terminal_goal=float(np.linalg.norm(d.qpos[:2]-protocol['goal_xy']));advance=stopped_goal-terminal_goal
            terminal_speed=float(np.linalg.norm(d.qvel[:2]));qualified=bool(resume_public and advance>=.30 and terminal_speed<=.025)
            final=integration(d).copy();actual_states=np.asarray(branch_states);actual_controls=np.asarray(branch_controls)
            replay=mujoco.MjData(m);mujoco.mj_copyData(replay,m,snap);context=f'BRANCH_REPLAY_{checkpoint}';replayed=[]
            for tick,c in enumerate(actual_controls):
                step_actual(replay,c[ids],checkpoint+tick//8 if tick%8==0 else None,'branch_replay')
                value=integration(replay);error=float(np.max(abs(value-actual_states[tick])));max_error=max(max_error,error)
                assert error<=1e-8,'FULL_INTEGRATION_BRANCH_REPLAY_MISMATCH';replayed.append(value)
            assert np.max(abs(integration(replay)-final))<=1e-8
            np.savez_compressed(branch/'FULL_BRANCH.npz',initial=branch_start,integration=actual_states,controls=actual_controls,replay_integration=replayed)
            with gzip.open(branch/'OBSERVATIONS.json.gz','wt')as stream:json.dump(observations,stream)
            record=dict(checkpoint=checkpoint,outcome=outcome,component_qualified=qualified,checkpoint_goal_m=checkpoint_goal,stopped_goal_m=stopped_goal,terminal_goal_m=terminal_goal,
                        resumed_goal_progress_m=advance,resume_public_steps=resume_public,terminal_speed_m_s=terminal_speed,chunks=chunks,admission_checks=checks,searches=searches,
                        physical_native=len(actual_controls),raw_sensor_packets=len(observations),full_global_dynamic_passed=False)
            records.append(record);dump('RESULTS.json',records);dump('ACTIVE.json',dict(checkpoint=checkpoint,completed=len(records),counts={**counts,'private_native':predictor.prediction_steps}))
            print(json.dumps({k:record[k]for k in['checkpoint','outcome','component_qualified','resumed_goal_progress_m','resume_public_steps','terminal_speed_m_s']}),flush=True)
        assert counts['branch_native']<=3232 and counts['branch_replay']==counts['branch_native'] and predictor.prediction_steps<=3000000
        assert all(sha(repo/n)==h for n,h in freeze['files'].items()),'FROZEN_INPUT_CHANGED_AFTER_RUN'
        status='FIXED_STOP_WAIT_COMPONENT_QUALIFIED'if all(r['component_qualified']for r in records)else'FIXED_STOP_WAIT_COMPONENT_NOT_QUALIFIED'
        dump('RESULT.json',dict(status=status,records=records,counts={**counts,'private_native':predictor.prediction_steps},maximum_full_state_error=max_error,minimum_actual_clearance_m=minimum,minimum_self_margin_m=self_min,bad_contacts=bad,
                    model_initializations=None,model_initialization_scope='One saved scene loaded and one original predictor constructed; internal compilation/load count uninstrumented.',new_global_navigation=0,full_global_dynamic_passed=False))
except BaseException as error:
    status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
    if physical_log is not None:physical_log.close()
    signal.alarm(0);counts['private_native']=0 if predictor is None else predictor.prediction_steps
    window.update(round_closed=True,status=status,elapsed_s=time.time()-started)
    dump('ROUND_WINDOW.json',window);dump('COMPLETION.json',dict(status=status,counts=counts,completed_checkpoints=len(records),records=records))
