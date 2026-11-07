"""Fixed original WE573 native qualification; no new navigation or tuning."""
import copy,fcntl,gzip,json,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace,MethodType
from common import R,W,ROOT,read,dump,sha,unchanged
for name in ['runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1','runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','runtime/mk-mini/training/phase14_lidar_depth_nav/envs','experiments/v733_early_low_translation_scan','experiments/v753_coupled_progress_repaired']:
    sys.path.insert(0,str(R/name))
sys.path.insert(0,str(W))
import numpy as np
import mujoco
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from geometry_predictor import RobotPredictor
from self_geometry import SelfGeometry,containment_margin
from independent_norm import static_field
from exact_footprint import pose_values
from motion_tracker import Tracker,install_time_gate
from reserved_recovery import ReservedRecovery
from progress_record_independent import check as progress_check
from unseen_prior import set_public_origin
from sensor_model import packet as sense
from canonical_sensor_pose import sensor_pose
from packet_contract import packet_equal
from motion_evaluator import check_forecast
from union_belief import future_cells

PAIR=R/'runs/v848_goal_first_worker/v848_main_slot01/paired';CELL=PAIR/'geometry_memory';STEP=573


def load(path):
    with gzip.open(path,'rt')as stream:return json.load(stream)


def poses(q):
    q=np.asarray(q);return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]


def main():
    unchanged();out=ROOT/'component01';out.mkdir(exist_ok=False)
    deadline=min(float(os.environ['PHASE_MODEL_ABSOLUTE_DEADLINE']),time.time()+600.)
    os.environ['PHASE_PRIVATE_NATIVE_CAP']='7056'
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FIXED_COMPONENT_DEADLINE')));signal.setitimer(signal.ITIMER_REAL,deadline-time.time())
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    counts=dict(old_replay_native=0,private_native=0,actual_branch_native=0,repeat_branch_native=0,new_navigation=0,new24=0)
    status='RUNNING';predictor=None;maximum=0.;minimum=1e30;self_min=1e30;bad=0;records=[];stream=None;inflight=False
    dump(out/'ROUND_WINDOW.json',dict(started_unix=time.time(),absolute_deadline_unix=deadline,round_closed=False,pid=os.getpid()))
    try:
        protocol=read(PAIR/'STATIC_PROTOCOL.json');config=read(PAIR/'DYNAMIC_PROTOCOL.json');motion=Motion(config);noise=read(PAIR/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];bounds=np.asarray(protocol['footprint_bounds'])
        saved=load(CELL/'handover_certificates/handover_0573.json.gz');old=load(CELL/'recovery_contracts/contract_0569.json.gz');state=saved['forecast_state'];cursor=saved['old_native_cursor'];goal=np.asarray(protocol['goal_xy'])
        assert cursor==32 and old['recovery_kind']=='FORWARD_BRAKE'
        # Sensor truth is used only to reconstruct physical range returns and
        # for offline coverage, never by the control proposal or progress gate.
        set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();packets=0
        with gzip.open(CELL/'sensor_packets.jsonl.gz','rt')as source:
            for packet in map(json.loads,source):
                if packet['step']>STEP:break
                assert packet_equal(packet,sense(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,noise))
                _,observed=tracker.update_packet(packet,protocol['known_rectangles'],protocol['known_circles']);packets+=1
        assert packets==574 and observed==state,'FIXED_CAUSAL_TRACKER_STATE_NOT_EXACT'
        dump(out/'SENSOR_CALIBRATION.json',dict(raw_packets=packets,state_exact=True,truth_scope='physical sensor and offline evaluator only'))
        model=mujoco.MjModel.from_binary_path(str(PAIR/'scene_model.mjb'));data=mujoco.MjData(model);data.qpos[:]=protocol['start_qpos'];motion.apply(model,data);mujoco.mj_forward(model,data)
        geometry=SelfGeometry(model,mujoco);catalog=GeometryCatalog(model,mujoco,PAIR/'assets/isolated_indoor.xml');fixed={k:getattr(model,k).copy()for k in ['geom_pos','geom_size','geom_quat','geom_contype','geom_conaffinity']}
        static=static_field(protocol);spec=mujoco.mjtState.mjSTATE_INTEGRATION
        def full(d):
            x=np.empty(mujoco.mj_stateSize(model,spec));mujoco.mj_getState(model,d,x,spec);return x
        stream=gzip.open(out/'ACTUAL_NATIVE.jsonl.gz','xt');label='OLD_REPLAY'
        def advance(d,command,account):
            nonlocal minimum,self_min,bad
            assert time.time()<deadline;oldq=d.qpos.copy();oldv=d.qvel.copy();d.ctrl[:]=command
            assert np.array_equal(d.qpos,oldq)and np.array_equal(d.qvel,oldv)
            mujoco.mj_step(model,d);counts[account]+=1;motion.apply(model,d);mujoco.mj_kinematics(model,d);mujoco.mj_collision(model,d)
            box=geometry.actual(model,d);margin=float(containment_margin(box,bounds));truth=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(d.time),.1]])})
            clearance=float(pose_values(truth,poses(d.qpos[None]))[0]);minimum=min(minimum,clearance);self_min=min(self_min,margin)
            contacts=[catalog.classify(c,int(round(d.time/.01)),int(round(d.time/.08)),float(d.time))for c in d.contact]
            bad+=sum(c['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in contacts)
            stream.write(json.dumps(dict(context=label,time=float(d.time),qpos=d.qpos.tolist(),qvel=d.qvel.tolist(),ctrl=d.ctrl.tolist(),mocap=d.mocap_pos.tolist(),clearance_m=clearance,self_margin_m=margin,contacts=contacts))+'\n')
            assert clearance>=.15 and margin>=0 and bad==0 and all(np.array_equal(getattr(model,k),v)for k,v in fixed.items()),'COMPONENT_PHYSICAL_SAFETY'
        with gzip.open(CELL/'dynamic_native.jsonl.gz','rt')as source:
            for i,line in enumerate(source):
                if i>=STEP*8:break
                item=json.loads(line);advance(data,item['actual_ctrl'],'old_replay_native')
                error=max(np.max(abs(data.qpos-item['qpos_full'])),np.max(abs(data.qvel-item['qvel_full'])),np.max(abs(data.ctrl-item['actual_ctrl'])),np.max(abs(data.mocap_pos-item['mocap_pos'])))
                maximum=max(maximum,float(error));assert error<=1e-8,'FIXED_ORIGINAL_NATIVE_REPLAY_MISMATCH'
        assert counts['old_replay_native']==4584 and np.max(abs(data.qpos-saved['real_entry_qpos']))<=1e-8 and np.max(abs(data.qvel-saved['real_entry_qvel']))<=1e-8
        initial=mujoco.MjData(model);mujoco.mj_copyData(initial,model,data)
        predictor=RobotPredictor(SimpleNamespace(model=model,data=data),R/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;proposal=np.asarray(saved['first_command'])
        field=SimpleNamespace(**static.__dict__);field.pose_values=MethodType(pose_values,field);field.nominal_static_geometry=static;install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
        # Calibration of the exact old selected negative certificate before
        # evaluating the new policy over the unchanged finite tail library.
        scratch=mujoco.MjData(predictor.model);mujoco.mj_resetData(predictor.model,scratch)
        for name in ['qpos','qvel','act','qacc_warmstart']:getattr(scratch,name)[:]=getattr(data,name)
        scratch.time=data.time;scratch.ctrl[:]=0.;scratch.ctrl[ids]=proposal;mujoco.mj_forward(predictor.model,scratch);scratch.qacc_warmstart[:]=data.qacc_warmstart
        prefix=[];prefixv=[]
        for _ in range(8):
            mujoco.mj_step(predictor.model,scratch);predictor.prediction_steps+=1;prefix.append(scratch.qpos.copy());prefixv.append(scratch.qvel.copy())
        predictor.predict(scratch,np.asarray(saved['target']),ids,proposal,320,saved['brake_after_native_ticks'])
        calibration=max(float(np.max(abs(predictor.last_forecast_qpos-saved['qpos']))),float(np.max(abs(predictor.last_forecast_qvel-saved['qvel']))))
        assert calibration<=1e-8 and np.linalg.norm(data.qpos[:2]-goal)-np.linalg.norm(np.asarray(saved['qpos'])[-1,:2]-goal)<0,'OLD_NEGATIVE_CERTIFICATE_CALIBRATION'
        calibration_copy=out/'OLD_NEGATIVE_CERTIFICATE.json.gz'
        with gzip.open(calibration_copy,'xt')as target:json.dump(dict(old=saved,calibration_error=calibration),target)
        reserved=ReservedRecovery(predictor,mujoco,ids,out)
        for key in ['qpos','qvel','poses','controls','initial_qpos','initial_qvel','prefix_command','target','prefix_poses']:old[key]=np.asarray(old[key])
        route=next(r for r in map(json.loads,(CELL/'route_revalidation.jsonl').open())if r['step']==569)
        reserved.cache=old;reserved.cursor=cursor;reserved.executing=True;reserved.reference={'goal_xy':goal.tolist(),'path':route['reference_path'],'index':saved['metadata']['reference_index'],'wheel_base':.60}
        # Return admission only uses goal and forward-reference applicability;
        # it does not use reference following or invent a new control proposal.
        before=full(data).copy();inflight=True
        summary=reserved.try_handover(data,proposal,field,state,STEP,saved['metadata'],commit=True);inflight=False
        assert np.array_equal(full(data),before),'NEW_SELECTION_MUTATED_REAL_INTEGRATION_STATE'
        dump(out/'NEW_ADMISSION.json',dict(summary=summary,detail=reserved.last_handover_attempt))
        if summary is None:
            assert reserved.cache is old and reserved.cursor==32 and reserved.executing
            controls=np.asarray(old['controls'])[cursor:];expectedq=np.asarray(old['qpos'])[cursor:];expectedv=np.asarray(old['qvel'])[cursor:];mode='RETAIN_OLD_BETTER_CERTIFICATE'
            selected=dict(old_created_step=old['created_step'],old_cursor=cursor,remaining_native=len(controls),remaining_goal_gain_m=float(np.linalg.norm(data.qpos[:2]-goal)-np.linalg.norm(old['qpos'][-1,:2]-goal)))
            assert selected['remaining_goal_gain_m']>=.02
        else:
            cache=reserved.cache;proof=progress_check(cache,data,old,cursor);assert proof['mode']=='PROGRESS'
            controls=np.vstack((np.repeat([proposal],8,axis=0),cache['controls']));expectedq=np.vstack((prefix,cache['qpos']));expectedv=np.vstack((prefixv,cache['qvel']));mode='BETTER_FULL_PROGRESS_CERTIFICATE';selected=proof
        assert len(controls)in [288,328]
        np.savez_compressed(out/'EXPECTED_BRANCH.npz',qpos=expectedq,qvel=expectedv,controls=controls,initial_qpos=initial.qpos,initial_qvel=initial.qvel,initial_ctrl=initial.ctrl,initial_time=initial.time)
        dump(out/'SELECTED.json',dict(mode=mode,selected=selected,new_summary=summary,old_calibration_error=calibration))
        completed=[]
        for repeat in [False,True]:
            real=mujoco.MjData(model);mujoco.mj_copyData(real,model,initial);local=copy.deepcopy(tracker);label='REPEAT'if repeat else'ACTUAL';actual=[];observations=[];safety=[]
            for tick,command in enumerate(controls):
                if tick%8==0:predictor.command_map.assert_first(command,real.ctrl[ids])
                fullcmd=np.zeros(model.nu);fullcmd[ids]=command;advance(real,fullcmd,'repeat_branch_native'if repeat else'actual_branch_native')
                error=float(np.max(abs(real.qpos-expectedq[tick])))
                if expectedv is not None:error=max(error,float(np.max(abs(real.qvel-expectedv[tick]))))
                maximum=max(maximum,error);assert error<=1e-8,'COMPONENT_CERTIFICATE_REAL_MISMATCH'
                actual.append(full(real));safety.append([minimum,self_min])
                if tick%8==7:
                    public=STEP+(tick+1)//8;xy,yaw=sensor_pose(real.qpos);packet=sense(xy,yaw,float(real.time),public,protocol,motion,noise);_,observed=local.update_packet(packet,protocol['known_rectangles'],protocol['known_circles'])
                    coverage=check_forecast(config,observed);assert coverage['passed']
                    times=np.arange(657)*.01;lo,hi=future_cells(observed['outer_state_cells'],times);truth=np.asarray([motion.xy(observed['time']+t)for t in times]);excess=float(np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max());assert excess<=1e-7
                    assert np.max(np.linalg.norm(truth-truth[0],axis=1)-.08*times)<=1e-7
                    observations.append(dict(packet=packet,state=observed,execution329=coverage,planning657_excess_m=excess))
            assert np.linalg.norm(real.qvel[:2])<=.025 and np.linalg.norm(initial.qpos[:2]-goal)-np.linalg.norm(real.qpos[:2]-goal)>=.02
            np.savez_compressed(out/(label+'.npz'),integration=actual,controls=controls,qpos_end=real.qpos,qvel_end=real.qvel)
            with gzip.open(out/(label+'_OBSERVATIONS.json.gz'),'xt')as target:json.dump(observations,target)
            completed.append((np.asarray(actual),observations));records.append(dict(role=label,native=len(controls),terminal_speed=float(np.linalg.norm(real.qvel[:2])),goal_gain_m=float(np.linalg.norm(initial.qpos[:2]-goal)-np.linalg.norm(real.qpos[:2]-goal))))
        error=float(np.max(abs(completed[0][0]-completed[1][0])));assert error<=1e-8 and completed[0][1]==completed[1][1]
        assert predictor.prediction_steps<=7056,'FIXED_COMPONENT_PRIVATE_MAXIMUM'
        unchanged();status='FIXED_NATIVE_PROGRESS_COMPONENT_PASS';counts['private_native']=predictor.prediction_steps
        dump(out/'RESULT.json',dict(status=status,passed=True,mode=mode,records=records,counts=counts,maximum_native_state_error=maximum,maximum_full_integration_repeat_error=error,minimum_actual_clearance_m=minimum,minimum_actual_self_margin_m=self_min,bad_contacts=bad,source_exact=True,full_global_dynamic_passed=False))
    except BaseException as error:
        status='STOPPED_COMPONENT_EXCEPTION';dump(out/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc(),private_count_may_be_lower_bound=inflight));raise
    finally:
        if stream is not None:stream.close()
        signal.setitimer(signal.ITIMER_REAL,0)
        counts['private_native']=None if predictor is None else predictor.prediction_steps
        dump(out/'COMPLETION.json',dict(status=status,counts=counts,records=records,private_count_exact=not inflight,closed=True));window=read(out/'ROUND_WINDOW.json');window.update(round_closed=True,status=status,closed_unix=time.time());dump(out/'ROUND_WINDOW.json',window)


if __name__=='__main__':main()
