"""Closed actual-state component and full original-route audits, zero models."""
import copy,gzip,importlib.util,json,math,sys,traceback
from pathlib import Path
import numpy as np
from independent_tracking import check as dense_tracking
from component_contract import final_half_second,actual_packet,sensor_actor
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def component(task):
    out=Path(task['output']);p=out/'physics';n=json.loads((out/'RESULT.json').read_text());setup=json.loads((p/'SETUP.json').read_text())
    ros=json.loads((out/'ROS_RESULT.json').read_text());replay=json.loads((p/'REPLAY.json').read_text());prefix=json.loads((p/'PREFIX_RESTORE.json').read_text());origin=task['origin_native_tick']
    with np.load(p/'NATIVE_TRACE.npz')as z:data={k:z[k]for k in z.files}
    count=len(data['time']);q=data['qpos'];v=data['qvel'];ids=np.asarray(setup['actuator_ids']);limits=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])*.01
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));body=np.c_[q[:,:2],yaw,v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw),v[:,5]]
    contacts=json.loads(gzip.decompress((p/'CONTACTS.json.gz').read_bytes()));commands=json.loads((p/'BODY_COMMANDS.json').read_text())
    ctrl=data['ctrl'][:,ids];bad=sum(x[2]in {'robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'}for row in contacts for x in row)
    checks=dict(complete_native=count==n['actual_native']==n['fully_recorded_native']==n['root_guard_native_count']and count>origin,
                prefix_state_exact=prefix['passed']and prefix['historical_prefix_replay_native']==origin and prefix['maximum_all_state_control_error']<=1e-8,
                old_and_new_clock_continuous=bool(np.allclose(data['time'],np.arange(1,count+1)*.01,rtol=0,atol=1e-9)),
                finite_arrays=all(np.isfinite(x).all()for x in data.values()),native_clearance=bool(data['clearance'].min()>=.15-1e-8),
                native_self=bool(data['self_margin'].min()>=-1e-10),contacts_complete=len(contacts)==count+1 and len(commands)==count,
                no_bad_contacts=bad==n['bad_contacts']==0,ctrl_amplitude=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),
                ctrl_slew=bool((abs(np.diff(np.vstack([np.zeros((1,len(ids))),ctrl]),axis=0))<=rate+1e-10).all()),
                no_root_write=not(p/'v648_nonphysical_mutation.json').exists(),whole_trace_replay=replay['passed']and replay['replay_native']==count and replay['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and replay['contact_mismatched_ticks']==0,
                native_complete=n['status']=='NATIVE_COMPLETE',wall_pacing=n['maximum_wall_lag_s']<=.1,
                model_semantics=json.loads((p/'MODEL_BUILD_CONTRACT.json').read_text())['interface']['passed'],
                exact_true_t0_binding=json.loads((p/'SELECTED_NATIVE_BINDING.json').read_text())['passed'],
                component_origin_arm=sum(e['event']=='COMPONENT_ORIGIN_ARM_VALIDATED'for e in n['startup_events'])==1)
    arm_events=[e for e in n['startup_events']if e['event']=='COMPONENT_ORIGIN_ARM_VALIDATED']
    if len(arm_events)==1:
        e=arm_events[0];packet=e['actual_arm_packet']
        checks['independent_component_arm_origin']=(e['global_native_tick']==packet['native_tick']==origin and abs(e['global_sim_time']-task['origin_sim_time'])<=1e-9 and abs(packet['sim_time']-task['origin_sim_time'])<=1e-9)
        checks['independent_active_node_freshness']=len(packet['states'])==7 and all(v==3 for v in packet['states'].values()) and all(-.05<=packet['issued_at']-at<=1. for at in packet['checked_at'].values())
    stages=json.loads((out/'CLOSED_HANDOFF.json').read_text())['stages'];assert len(stages)==1
    row=stages[0];start=row['start_packet']['native_tick'];end=row['end_packet']['native_tick'];goal=np.asarray(task['goal_xy']);plan=row['proposal']
    sys.path.insert(0,str(R/'experiments/v977_state_consistent_recovery'))
    curve=load('v979_frozen_independent_curve_audit',R/'experiments/v977_state_consistent_recovery/corridor_audit.py')
    proof=curve.audit_reference(plan,setup['known'],row['start_source']['periodic']);tracking=dense_tracking(plan,body[start-1:,:3])
    progress=float(np.linalg.norm(body[start-1,:2]-goal)-np.linalg.norm(body[-1,:2]-goal));endpoint=float(np.linalg.norm(body[-1,:2]-np.asarray(plan['path'][-1][:2])))
    functional=dict(follow_success=row['follow_status']==ros.get('action_status')==4,complete_tracking=tracking['passed'],endpoint=endpoint<=.04,original_progress=progress>=.4,physical_stopped=np.linalg.norm(v[-1,:2])<=.03)
    functional['complete_final_half_second_stopped']=final_half_second(v,body,setup['steering_qvel_addresses'],origin)
    for label in ['start_packet','end_packet']:
        checks[label+'_actual_body_and_encoders']=actual_packet(row[label],body,q,v,setup)
    sensor=json.loads((p/'EXACT_SENSOR_BINDING.json').read_text())
    checks['original_sensor_actor_contract']=sensor_actor(sensor,setup,task)
    checks['current_causal_reference']=proof['passed']
    sys.path.insert(0,str(C))
    from tube_audit import audit_tubes
    from shaping_audit import audit as shaping_audit
    from motion_audit import audit as motion_audit
    from ingress_audit import check as ingress_check
    tubes=audit_tubes(out);shaping=shaping_audit(out);motion=motion_audit(out)
    # Direct FollowPath has no global planner calls. Keep the original full-route
    # outcome and state precisely which measured checks qualify this component.
    checks['causal_sensor_forecast_component']=(motion['original_observations_verified']>0 and motion['tracked_states_with_offline_true_center_covered']>0 and motion['forecast_publications_rebuilt']>0 and motion['periodic_future_support_checks']>0 and motion['causal_terminal_decisions_rebuilt']==0 and all(motion['postdetection_full_snapshots'].values()))
    checks['command_tubes']=tubes['passed'];checks['steering_source_and_rate']=shaping['passed']
    ingress=json.loads(gzip.decompress((out/'INGRESS.json.gz').read_bytes()))
    proofs=[z['proof']for z in json.loads(gzip.decompress((out/'COMMAND_TUBES.json.gz').read_bytes()))if z['proof']['passed']]
    # Affine change of tick origin only; all elapsed times and proof ages stay
    # identical. Never drop or replace a native execution/command row.
    translated=copy.deepcopy(ingress);translated_proofs=copy.deepcopy(proofs)
    def translate_proof(z):
        for key in ['source_native_tick','body_native_tick']:z[key]-=origin
    for z in translated_proofs:translate_proof(z)
    for z in translated['execution']:z['native_tick']-=origin
    for z in translated['receipts']:
        z['native_tick']-=origin
        if 'tube'in z['packet']:translate_proof(z['packet']['tube'])
    translated['local_stop_events']=[dict(e,native_tick=e['native_tick']-origin)for e in n['startup_events']if e['event']=='LOCAL_DEADLINE_STOP']
    ingress_result=ingress_check(translated,translated_proofs,body[origin:],task['run_id']);checks['all_new_native_ingress']=ingress_result['passed']
    result=dict(passed=all(checks.values())and all(functional.values()),checks={k:bool(v)for k,v in checks.items()},functional_checks={k:bool(v)for k,v in functional.items()},
                historical_prefix_replay_native=origin,new_branch_native=count-origin,own_full_trace_replay_native=replay['replay_native'],
                tracking=tracking,reference=proof,actual_goal_progress_m=progress,endpoint_distance_m=endpoint,
                minimum_actual_clearance_m=float(data['clearance'].min()),bad_contacts=bad,maximum_state_error=replay['maximum_qpos_qvel_ctrl_mocap_error'],
                causal_component_audit=motion,original_global_navigation_audit_passed=motion['passed'],
                direct_followpath_has_no_global_route_not_navigation_sample=True,tube=tubes,shaping=shaping,ingress=ingress_result,models_during_audit=0)
    return result

def audit(task):
    out=Path(task['output'])
    from actuation_audit import audit as audit_actuation
    actuation=audit_actuation(out,task)
    try:
        native=json.loads((out/'RESULT.json').read_text())
        if native.get('armed_at')is None:
            result=dict(passed=False,status=native.get('status','INITIALIZATION_OR_PREARM_ABORT'),reason='NO_ARM_COMPONENT_NOT_EXECUTED',
                exact_new_branch_native=native.get('new_branch_native'),original_native_error=native.get('error'),models_during_audit=0)
        elif task['stage']=='component':result=component(task)
        else:raise AssertionError('V987_COMPONENT_ONLY_NO_FULL_NAVIGATION_AUTHORITY')
    except BaseException as error:result=dict(passed=False,error=repr(error),traceback=traceback.format_exc(),models_during_audit=0)
    result['actuation']=actuation;result['passed']=bool(result['passed']and actuation['passed'])
    (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
