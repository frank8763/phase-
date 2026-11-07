"""Exact old-prefix replay and the two original complete brake-only branches."""
import copy,fcntl,gzip,hashlib,importlib.util,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
repo=Path(os.environ['PHASE_REPO']);own=Path(__file__).parent
for p in ['runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1','runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','runtime/mk-mini/training/phase14_lidar_depth_nav/envs',
          'experiments/v733_early_low_translation_scan','experiments/v753_coupled_progress_repaired',
          'experiments/v812_soft_global_reference','experiments/v817_tracked_norm_qualification']:
    sys.path.insert(0,str(repo/p))
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from geometry_predictor import RobotPredictor
from exact_footprint import build,pose_values
from reserved_recovery import ReservedRecovery
from motion_tracker import Tracker,install_time_gate
from motion_evaluator import check_forecast
from union_belief import future_cells
from norm_gate import refine
from sensor_model import packet as sensed_packet
from packet_contract import packet_equal
from canonical_sensor_pose import sensor_pose
from unseen_prior import set_public_origin

read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v819_tracked_norm_native_entry';root.mkdir(exist_ok=False)
def serial(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)
def dump(n,x):(root/n).write_text(json.dumps(x,indent=2,default=serial,allow_nan=False)+'\n')
def poses(q):
    q=np.asarray(q).reshape(-1,np.asarray(q).shape[-1]);return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
started=float(os.environ['PHASE_NORM_STARTED']);deadline=float(os.environ['PHASE_NORM_DEADLINE'])
assert abs(deadline-started-900)<1e-6 and time.time()<deadline
window=dict(started_unix=started,absolute_deadline_unix=deadline,round_closed=False,pid=os.getpid());dump('ROUND_WINDOW.json',window)
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('NORM_COMPONENT_900S')));signal.setitimer(signal.ITIMER_REAL,deadline-time.time())
counts=dict(old_replay_native=0,private_native=0,component_native=0,component_replay_native=0,new_navigation=0,new_confirmation=0)
predictor=None;contact_log=None;status='RUNNING';records=[];minimum=float('inf');self_min=float('inf');max_error=0.;bad=0
try:
    freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
    assert read(repo/'runs/v817_tracked_norm_qualification/ARCHIVE_VERIFIED.json')['status']=='ALL_STAGE_SOURCES_AND_DECOMPRESSED_SHA_VERIFIED'
    with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        pair=repo/'runs/v812_soft_global_reference/main_slot01/paired';cell=pair/'geometry_memory'
        protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
        noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap']
        entries=read(repo/'experiments/v817_tracked_norm_qualification/FIXED_INPUTS.json')
        with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old_packets=[json.loads(s)for s in f][:599]
        set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();trackers={}
        states={e['step']:e['state']for e in entries}
        for packet in old_packets:
            assert packet_equal(packet,sensed_packet(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,noise))
            _,state=tracker.update_packet(packet,protocol['known_rectangles'],protocol['known_circles'])
            if packet['step']in states:
                assert state==states[packet['step']];trackers[packet['step']]=copy.deepcopy(tracker)
        dump('SENSOR_CAUSAL_CALIBRATION.json',dict(raw_packets=len(old_packets),full_raw_packets_exact=True,causal_states_exact=[586,598],models=0,integrations=0))
        m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m)
        d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d)
        geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds'])
        fixed={k:getattr(m,k).copy()for k in ['geom_pos','geom_size','geom_quat','geom_contype','geom_conaffinity']}
        static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
        state_spec=mujoco.mjtState.mjSTATE_INTEGRATION
        def full(data):
            value=np.empty(mujoco.mj_stateSize(m,state_spec));mujoco.mj_getState(m,data,value,state_spec);return value
        samples=[]
        def private(model,data):
            mujoco.mj_step(model,data);mujoco.mj_kinematics(model,data);samples.append(dict(qpos=data.qpos.copy(),qvel=data.qvel.copy(),self_bounds=predictor.self_geometry.actual(model,data).copy()))
        predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,private);ids=predictor.command_map.ids
        contact_log=gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','wt');context='OLD_REPLAY'
        def physical(data,public):
            global minimum,self_min,bad
            box=geometry.actual(m,data);margin=float(containment_margin(box,bounds));truth=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(data.time),.1]])})
            clearance=float(pose_values(truth,poses(data.qpos))[0]);minimum=min(minimum,clearance);self_min=min(self_min,margin)
            # Contact event step is the original simulation-time native tick,
            # so identical complete branches retain identical event records.
            # Cumulative work remains separately recorded in counts.
            contacts=[catalog.classify(c,int(round(float(data.time)/.01)),public,float(data.time))for c in data.contact]
            bad+=sum(c['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in contacts)
            contact_log.write(json.dumps(dict(context=context,public=public,time=float(data.time),qpos=data.qpos.tolist(),qvel=data.qvel.tolist(),ctrl=data.ctrl.tolist(),mocap=data.mocap_pos.tolist(),actual_bounds=box.tolist(),clearance_m=clearance,self_margin_m=margin,contacts=contacts))+'\n')
            assert clearance>=.15 and margin>=0 and bad==0 and all(np.array_equal(getattr(m,k),v)for k,v in fixed.items()),'PHYSICAL_SAFETY_OR_STATIC_MODEL_FAILURE'
            return [clearance,margin]
        def advance(data,command,public,account):
            if public is not None:predictor.command_map.assert_first(command,data.ctrl[ids])
            data.ctrl[:]=0.;data.ctrl[ids]=command;mujoco.mj_step(m,data);counts[account]+=1;motion.apply(m,data);mujoco.mj_kinematics(m,data);mujoco.mj_collision(m,data)
            return physical(data,-1 if public is None else public)
        snapshots={};replay=[]
        with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as stream:
            for i,line in enumerate(stream):
                if i>=4784:break
                old=json.loads(line);safe=advance(d,np.asarray(old['actual_ctrl'])[ids],i//8 if i%8==0 else None,'old_replay_native')
                error=max(np.max(abs(d.qpos-old['qpos_full'])),np.max(abs(d.qvel-old['qvel_full'])),np.max(abs(d.ctrl-old['actual_ctrl'])),np.max(abs(d.mocap_pos-old['mocap_pos'])))
                max_error=max(max_error,float(error));assert error<=1e-8,'ORIGINAL_NATIVE_PREFIX_NOT_EXACT';replay.append(full(d))
                public=(i+1)//8
                if (i+1)%8==0 and public in states:
                    snap=mujoco.MjData(m);mujoco.mj_copyData(snap,m,d);snapshots[public]=snap
        assert counts['old_replay_native']==4784;np.savez_compressed(root/'OLD_4784_NATIVE_REPLAY.npz',integration=replay)
        spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
        base=read(cell/'planning_0303.json')['causal_input']
        for e in entries:
            step=e['step'];state=e['state'];snap=snapshots[step];mujoco.mj_copyData(d,m,snap)
            initial=full(d).copy();field=build(F,base);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);refine(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
            samples.clear();reserved=ReservedRecovery(predictor,mujoco,ids,root);before=predictor.prediction_steps
            summary=reserved.admit_nominal(d,np.asarray(e['first_command']),field,state,step)
            assert np.array_equal(full(d),initial),'PREDICTION_MUTATED_REAL'
            assert summary is not None and summary['recovery_kind']=='BRAKE_ONLY'and predictor.prediction_steps-before==328
            cache=reserved.cache;q=np.vstack([[x['qpos']for x in samples],cache['qpos']]);v=np.vstack([[x['qvel']for x in samples],cache['qvel']]);self_bounds=np.vstack([[x['self_bounds']for x in samples],predictor.last_self_bounds])
            controls=np.vstack([np.repeat([e['first_command']],8,axis=0),cache['controls']]);expected_poses=np.load(repo/e['witness_file'])['poses'];pose_error=float(np.max(abs(poses(q)-expected_poses)))
            assert pose_error<=1e-8,'ORIGINAL_FULL_328_KINEMATICS_NOT_EXACT'
            value=field.trajectory_values(poses(q),.01);assert value.min()>=.155
            folder=root/f'step{step:04d}';folder.mkdir();np.savez_compressed(folder/'CERTIFICATE.npz',qpos=q,qvel=v,controls=controls,poses=poses(q),self_bounds=self_bounds,initial=initial,causal_values=value,forecast_state=json.dumps(state))
            runs=[]
            for repeat in [False,True]:
                context=f'S{step}_'+('REPEAT'if repeat else'ACTUAL');real=mujoco.MjData(m);mujoco.mj_copyData(real,m,snap);local=copy.deepcopy(trackers[step]);actual=[];safety=[];observations=[]
                for tick,c in enumerate(controls):
                    safety.append(advance(real,c,step+tick//8 if tick%8==0 else None,'component_replay_native'if repeat else'component_native'))
                    error=max(np.max(abs(real.qpos-q[tick])),np.max(abs(real.qvel-v[tick])));max_error=max(max_error,float(error));assert error<=1e-8,'ORIGINAL_PREDICTION_SCENE_STATE_MISMATCH'
                    actual.append(full(real))
                    if tick%8==7:
                        public=step+(tick+1)//8;xy,yaw=sensor_pose(real.qpos);packet=sensed_packet(xy,yaw,float(real.time),public,protocol,motion,noise)
                        _,observed=local.update_packet(packet,protocol['known_rectangles'],protocol['known_circles'])
                        coverage=check_forecast(config,observed);assert coverage['passed'],'EXECUTION_329_COVERAGE_FAILURE'
                        times=np.arange(657)*.01;lo,hi=future_cells(observed['outer_state_cells'],times);truth=np.asarray([motion.xy(observed['time']+t)for t in times])
                        excess=float(np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max());assert excess<=1e-7,'PLANNING_657_COVERAGE_FAILURE'
                        observations.append(dict(packet=packet,state=observed,execution_coverage=coverage,planning_excess_m=excess))
                runs.append(dict(integration=np.asarray(actual),observations=observations))
                name='REPEAT'if repeat else'ACTUAL';np.savez_compressed(folder/(name+'.npz'),integration=actual,safety=safety)
                with gzip.open(folder/(name+'_OBSERVATIONS.json.gz'),'wt')as stream:json.dump(observations,stream)
            repeat_error=float(np.max(abs(runs[0]['integration']-runs[1]['integration'])));assert repeat_error<=1e-8 and runs[0]['observations']==runs[1]['observations'],'COMPLETE_REPEAT_NOT_EXACT'
            records.append(dict(step=step,original_complete_pose_error=pose_error,minimum_refined_causal_clearance_m=float(value.min()),terminal_speed_m_s=float(np.linalg.norm(v[-1,:2])),predicted_self_margin_m=float(containment_margin(self_bounds,bounds).min()),
                full_state_control_repeat_error=repeat_error,raw_packet_repeat_exact=True,private_native=328,actual_native=328,repeat_native=328,actual_sensor_packets=41,original_source=e))
            dump('RESULTS.json',records);print(json.dumps({k:v for k,v in records[-1].items()if k!='original_source'}),flush=True)
        assert predictor.prediction_steps==656 and counts['component_native']==counts['component_replay_native']==656
        assert all(sha(repo/n)==h for n,h in freeze['files'].items())
        status='DECLARED_NORM_NATIVE_COMPONENT_COMPLETE';dump('RESULT.json',dict(status=status,records=records,counts={**counts,'private_native':predictor.prediction_steps},minimum_actual_clearance_m=minimum,minimum_self_margin_m=self_min,maximum_native_state_ctrl_error=max_error,bad_contacts=bad,model_initializations=None,model_initialization_scope='Saved scene load and original predictor construction; internal compiled/load count not separately instrumented.',new_global_navigation=0,full_global_dynamic_passed=False))
except BaseException as error:
    status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
    if contact_log is not None:contact_log.close()
    signal.alarm(0);counts['private_native']=0 if predictor is None else predictor.prediction_steps
    window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window);dump('COMPLETION.json',dict(status=status,counts=counts,completed_inputs=len(records)))
