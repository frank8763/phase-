"""Two fixed native whole-certificate branches and full repeats; no navigation."""
import copy,fcntl,gzip,json,os,signal,sys,time,traceback
from types import SimpleNamespace,MethodType
from common import *
for folder in ['runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1','runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','runtime/mk-mini/training/phase14_lidar_depth_nav/envs','experiments/v733_early_low_translation_scan','experiments/v753_coupled_progress_repaired']:sys.path.insert(0,str(R/folder))
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
from unseen_prior import set_public_origin
from sensor_model import packet as sense
from canonical_sensor_pose import sensor_pose
from packet_contract import packet_equal
from motion_evaluator import check_forecast
from union_belief import future_cells
from audit_maneuver import check_certificate


def main():
    variant=sys.argv[1];assert variant in dict(VARIANTS);assert int(os.environ['PHASE_MANEUVER_COMMIT_NATIVE'])==dict(VARIANTS)[variant]
    unchanged();out=ROOT/('component_'+variant);out.mkdir(exist_ok=False);end=min(DEADLINE,float(os.environ['PHASE_MODEL_ABSOLUTE_DEADLINE']),time.time()+900)
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FIXED_COMPONENT_DEADLINE')));signal.setitimer(signal.ITIMER_REAL,end-time.time())
    lock=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    pair=R/'runs/v851_profile_output_worker/v851_main_slot01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];motion=Motion(config);bounds=np.asarray(protocol['footprint_bounds']);static=static_field(protocol);plans=[read(p)for p in cell.glob('planning_*.json')];trace=read(cell/'trace.json')
    counts=dict(old_replay_native=0,private_native=0,actual_branch_native=0,repeat_branch_native=0);rows=[];status='RUNNING';inflight=False;predictor=None
    dump(out/'ROUND_WINDOW.json',dict(started_unix=time.time(),absolute_deadline_unix=end,root_deadline_unix=DEADLINE,round_closed=False));stream=gzip.open(out/'ALL_ACTUAL_NATIVE.jsonl.gz','xt')
    try:
        for step in [399,1148]:
            dest=out/f'step{step:04d}';dest.mkdir();saved=json.load(gzip.open(cell/'progress_certificates'/f'certificate_{step:04d}.json.gz','rt'));set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();packets=0
            for packet in map(json.loads,gzip.open(cell/'sensor_packets.jsonl.gz','rt')):
                if packet['step']>step:break
                assert packet_equal(packet,sense(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,noise));_,state=tracker.update_packet(packet,protocol['known_rectangles'],protocol['known_circles']);packets+=1
            assert state==saved['forecast_state']and packets==step+1
            m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d);geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml');fixed={k:getattr(m,k).copy()for k in ['geom_pos','geom_size','geom_quat','geom_contype','geom_conaffinity']};minimum=1e30;self_min=1e30;maximum=0.;bad=0
            def advance(real,ctrl,account,label):
                nonlocal minimum,self_min,bad
                assert time.time()<end;real.ctrl[:]=ctrl;mujoco.mj_step(m,real);counts[account]+=1;motion.apply(m,real);mujoco.mj_kinematics(m,real);mujoco.mj_collision(m,real);box=geometry.actual(m,real);margin=float(containment_margin(box,bounds));truth=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(real.time),.1]])});clearance=float(pose_values(truth,ReservedRecovery.poses(real.qpos[None]))[0]);minimum=min(minimum,clearance);self_min=min(self_min,margin);contacts=[catalog.classify(c,int(round(real.time/.01)),int(round(real.time/.08)),float(real.time))for c in real.contact];bad+=sum(c['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in contacts);assert clearance>=.15 and margin>=0 and bad==0 and all(np.array_equal(getattr(m,k),v)for k,v in fixed.items()),'COMPONENT_PHYSICAL_ANOMALY'
                stream.write(json.dumps(dict(checkpoint=step,role=label,time=float(real.time),qpos=real.qpos.tolist(),qvel=real.qvel.tolist(),ctrl=real.ctrl.tolist(),mocap=real.mocap_pos.tolist(),clearance_m=clearance,self_margin_m=margin,contacts=contacts))+'\n')
            for i,item in enumerate(map(json.loads,gzip.open(cell/'dynamic_native.jsonl.gz','rt'))):
                if i>=step*8:break
                advance(d,item['actual_ctrl'],'old_replay_native','OLD_REPLAY');error=max(np.max(abs(d.qpos-item['qpos_full'])),np.max(abs(d.qvel-item['qvel_full'])),np.max(abs(d.ctrl-item['actual_ctrl'])),np.max(abs(d.mocap_pos-item['mocap_pos'])));maximum=max(maximum,float(error));assert error<=1e-8,'SAVED_PREFIX_NATIVE_MISMATCH'
            initial=mujoco.MjData(m);mujoco.mj_copyData(initial,m,d);predictor=RobotPredictor(SimpleNamespace(model=m,data=d),R/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;field=SimpleNamespace(**static.__dict__);field.pose_values=MethodType(pose_values,field);field.nominal_static_geometry=static;install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);reserved=ReservedRecovery(predictor,mujoco,ids,dest);route=max((p for p in plans if p['step']<=step),key=lambda p:p['step']);reserved.set_reference(route['path'],trace[step]['path_index'],protocol['goal_xy'],.60)
            inflight=True;summary=reserved.admit_nominal(d,np.asarray(saved['prefix_command']),field,state,step);inflight=False;counts['private_native']+=predictor.prediction_steps;dump(dest/'ADMISSION.json',dict(summary=summary,detail=reserved.last_attempt))
            if summary is None or not reserved.cache.get('maneuver_contract',{}).get('normal_allowed'):
                status='SAFE_COMPONENT_FUNCTIONAL_NOT_PASSED';break
            selected=reserved.cache;proof=check_certificate(selected);assert proof['normal_allowed'];controls=np.vstack((np.repeat([selected['prefix_command']],8,axis=0),selected['controls']));q=np.asarray(selected['qpos']);v=np.asarray(selected['qvel']);dump(dest/'SELECTED.json',dict(proof=proof,summary=summary));
            with gzip.open(dest/'CERTIFICATE.json.gz','xt')as f:json.dump(selected,f,default=lambda x:x.tolist()if isinstance(x,np.ndarray)else x.item())
            sequences=[];observations=[]
            for repeat in [False,True]:
                real=mujoco.MjData(m);mujoco.mj_copyData(real,m,initial);local=copy.deepcopy(tracker);actual=[];sensed=[];spec=mujoco.mjtState.mjSTATE_INTEGRATION
                for tick,ctrl in enumerate(controls):
                    if tick%8==0:predictor.command_map.assert_first(ctrl,real.ctrl[ids])
                    full=np.zeros(m.nu);full[ids]=ctrl;advance(real,full,'repeat_branch_native'if repeat else'actual_branch_native','REPEAT'if repeat else'ACTUAL')
                    expectedq=selected['prefix_native_qpos'][tick]if tick<8 else q[tick-8];expectedv=selected['prefix_native_qvel'][tick]if tick<8 else v[tick-8]
                    if expectedq is not None:
                        error=max(float(np.max(abs(real.qpos-expectedq))),float(np.max(abs(real.qvel-expectedv))));maximum=max(maximum,error);assert error<=1e-8,'NEW_FULL_CERTIFICATE_ACTUAL_MISMATCH'
                    statevector=np.empty(mujoco.mj_stateSize(m,spec));mujoco.mj_getState(m,real,statevector,spec);actual.append(statevector)
                    if tick%8==7:
                        xy,yaw=sensor_pose(real.qpos);packet=sense(xy,yaw,float(real.time),step+(tick+1)//8,protocol,motion,noise);_,observed=local.update_packet(packet,protocol['known_rectangles'],protocol['known_circles']);coverage=check_forecast(config,observed);assert coverage['passed'];times=np.arange(657)*.01;lo,hi=future_cells(observed['outer_state_cells'],times);truth=np.asarray([motion.xy(observed['time']+t)for t in times]);excess=float(np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max());assert excess<=1e-7 and np.max(np.linalg.norm(truth-truth[0],axis=1)-.08*times)<=1e-7;sensed.append(dict(packet=packet,state=observed,execution329=coverage,planning657_excess_m=excess))
                assert np.linalg.norm(real.qvel[:2])<=.025;sequences.append(np.asarray(actual));observations.append(sensed);np.savez_compressed(dest/('REPEAT.npz'if repeat else'ACTUAL.npz'),integration=actual,controls=controls)
            error=float(np.max(abs(sequences[0]-sequences[1])));assert error<=1e-8 and observations[0]==observations[1]
            with gzip.open(dest/'OBSERVATIONS.json.gz','xt')as f:json.dump(observations,f)
            rows.append(dict(checkpoint=step,passed=True,maximum_native_error=maximum,full_integration_repeat_error=error,minimum_actual_clearance_m=minimum,minimum_actual_self_margin_m=self_min,bad_contacts=bad,proof=proof,native_actual=328,native_repeat=328,private_native=predictor.prediction_steps))
        if len(rows)==2:status='TWO_FIXED_COMPONENTS_AND_FULL_REPEATS_PASS'
        dump(out/'RESULT.json',dict(status=status,passed=len(rows)==2,rows=rows,counts=counts))
    except BaseException as e:
        status='FATAL_COMPONENT_EXCEPTION';dump(out/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc(),private_exact=not inflight));raise
    finally:
        stream.close();signal.setitimer(signal.ITIMER_REAL,0);dump(out/'COMPLETION.json',dict(status=status,counts=counts,private_count_exact=not inflight,rows=rows,closed=True));window=read(out/'ROUND_WINDOW.json');window.update(round_closed=True,status=status,closed_unix=time.time());dump(out/'ROUND_WINDOW.json',window)


if __name__=='__main__':main()
