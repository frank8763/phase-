"""Closed V982 saved-state/transient audit. No model, ROS, prediction or replay."""
import gzip,hashlib,importlib.abc,json,math,sys
from pathlib import Path
import numpy as np
C=Path(__file__).parent;R=C.resolve().parents[1];O=R/'runs/v983_saved_transient_diagnosis';REC=R/'records/nav2_v982_20261110'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v982_precise_recovery_gate'))
from tracking import TrackingGuard
from independent_tracking import check as independent_tracking
from component_contract import final_half_second,actual_packet,sensor_actor

def read(p):return json.loads(p.read_text())
def main():
    assert read(REC/'FINALIZED.json')['remote_verified']and read(R/'runs/v982_precise_recovery_gate/COMPLETION.json')['closed']
    for row in read(O/'REMOTE_RESTORE_RECEIPT.json')['files']:
        p=R/row['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
    native=read(O/'RESULT.json');fault=read(O/'ONLINE_TRACKING_FAULT.json');saved=read(O/'COMPONENT_REFERENCE.json');plan=saved['proposal']
    setup=read(O/'physics/SETUP.json');replay=read(O/'physics/REPLAY.json');origin=native['historical_prefix_replay_native']
    with np.load(O/'physics/NATIVE_TRACE.npz')as z:data={k:z[k]for k in z.files}
    with np.load(O/'prior/physics/NATIVE_TRACE.npz')as z:old={k:z[k]for k in z.files}
    q=data['qpos'];v=data['qvel'];count=len(q);yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    body=np.c_[q[:,:2],yaw,v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw),v[:,5]]
    history_error={k:float(abs(data[k][:origin]-old[k][:origin]).max())if data[k][:origin].size else 0. for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
    guard=TrackingGuard(plan);guard.mode='FOLLOW_RECOVERY'
    try:guard.monitor_body(fault['packet'])
    except AssertionError as error:reason=str(error)
    else:reason=None
    fault_online=guard.last_proof.copy();fault_independent=independent_tracking(plan,[fault['packet']['body'][:3]])
    actual=body[origin:,:3];full=independent_tracking(plan,actual)
    sampled_maximum=0.;maximum_tick=None;first_true_violation=None;rows=[]
    for i,pose in enumerate(actual,origin+1):
        try:guard.monitor_body(dict(body=pose.tolist()))
        except AssertionError:pass
        proof=guard.last_proof
        if proof['heading_error_rad']>sampled_maximum:sampled_maximum=proof['heading_error_rad'];maximum_tick=i
        if first_true_violation is None and proof['heading_error_rad']>.035:first_true_violation=i
        if i in {origin+1,origin+25,origin+50,origin+75,origin+100,origin+125,fault['packet']['native_tick'],count}:
            rows.append(dict(native_tick=i,body=body[i-1].tolist(),tracking=proof.copy(),measured_steering=q[i-1,setup['steering_qpos_addresses']].tolist()))
    commands=read(O/'physics/BODY_COMMANDS.json');old_commands=read(O/'prior/physics/BODY_COMMANDS.json')
    contacts=json.loads(gzip.decompress((O/'physics/CONTACTS.json.gz').read_bytes()))
    bad=sum(c[2]in {'robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'}for row in contacts for c in row)
    ctrl=data['ctrl'][:,setup['actuator_ids']];limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])*.01
    tubes=json.loads(gzip.decompress((O/'COMMAND_TUBES.json.gz').read_bytes()));positive_opposite=[]
    for row in tubes:
        p=row['packet'];command=row['proof']
        if command['v']>0 and command['w']>0 and p['body'][4]<-.03:
            positive_opposite.append(dict(native_tick=p['native_tick'],body_v_w=p['body'][3:],dispatched_v_w=[command['v'],command['w']],measured_steering=p['steering']['position']))
    branch_distance=float(np.linalg.norm(np.diff(q[origin-1:,:2],axis=0),axis=1).sum())
    stop_tail=final_half_second(v,body,setup['steering_qvel_addresses'],origin)
    checks=dict(historical_complete_state_control_exact=max(history_error.values())<=1e-8,
                historical_executed_v_w_stale_exact=all([a[1],a[2],a[5]]==[b[1],b[2],b[5]]for a,b in zip(commands[:origin],old_commands[:origin])),
                complete_native=count==native['actual_native']==native['fully_recorded_native']==native['root_guard_native_count'],
                exact_separate_accounting=count-origin==native['new_branch_native']==native['native_api_calls_completed'],
                fully_recorded_commands_contacts=len(commands)==count and len(contacts)==count+1,
                finite_native=all(np.isfinite(x).all()for x in data.values()),
                native_clock=bool(np.allclose(data['time'],np.arange(1,count+1)*.01,rtol=0,atol=1e-9)),
                actual_clearance=bool(data['clearance'].min()>=.15),no_bad_contacts=bad==native['bad_contacts']==0,
                self_margin=bool(data['self_margin'].min()>=0),
                ctrl_limits=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),
                ctrl_slew=bool((abs(np.diff(np.vstack([np.zeros((1,len(setup['actuator_ids']))),ctrl]),axis=0))<=rates+1e-10).all()),
                own_replay_exact=replay['passed']and replay['replay_native']==count and replay['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and replay['contact_mismatched_ticks']==0,
                maximum_native_wall_lag=native['maximum_wall_lag_s']<=.1,
                actual_fault_packet_matches_native=actual_packet(fault['packet'],body,q,v,setup),
                actual_reference_start_packet_matches_native=actual_packet(saved['packet'],body,q,v,setup),
                original_sensor_actor=sensor_actor(read(O/'physics/EXACT_SENSOR_BINDING.json'),setup,dict(phase=.6573753567727383)),
                full_final_half_second_stopped=stop_tail)
    # Existing certificate budget, evaluated analytically only. This is not a new
    # tracking limit or an accepted modification of the failed physical batch.
    rho=math.hypot(.44,.375)
    reference_raw=plan['minimum_raw_full_cycle_clearance_m']
    reserve_except_heading=.04+.1*(.13+rho*.16)+.02*(.13+rho*.16+.08)
    gap=.0125/2*(1+rho*.758770385)
    illustrative_capacity=(reference_raw-.155-reserve_except_heading-gap)/rho
    report=dict(models=0,integrations=0,private_predictions=0,physical_outcome_unchanged='V982_NOT_PASSED',
                exact_accounting=dict(models_initialized=1,historical_restore_native=origin,new_branch_native=count-origin,whole_own_control_replay_native=replay['replay_native'],private_native=0,unexecuted_components=1,full_navigation_tasks=0,new24=0),
                saved_prefix_native_checks=checks,all_saved_prefix_native_checks_passed=all(checks.values()),
                scope='Available complete prefix safety/state/control/stop checks only; original full component audit failed before completion evidence. Not functional acceptance.',
                old_full_component_audit_error='CLOSED_HANDOFF.json absent because FollowPath did not finish; original failed audit retained',
                initial_actual_body=saved['packet']['body'],actual_stopped_at_reference_install=True,
                fault_tick=fault['packet']['native_tick'],fault_new_branch_tick=fault['packet']['native_tick']-origin,
                original_heading_limit_rad=.035,fault_online=fault_online,fault_independent=fault_independent,
                full_new_branch_tracking=full,first_saved_sample_exceeding_nominal_heading_limit=first_true_violation,
                maximum_saved_heading_error_rad=sampled_maximum,maximum_heading_tick=maximum_tick,
                actual_branch_travel_m=branch_distance,actual_reference_progress_m=float(np.linalg.norm(body[origin-1,:2]-plan['original_goal'])-np.linalg.norm(body[-1,:2]-plan['original_goal'])),
                final_actual_body=body[-1].tolist(),true_initial_nonzero_residual_yaw_cause_not_supported=abs(saved['packet']['body'][4])<1e-6,
                alternate_motion_selections=sum(row.get('recovery')is not None for row in tubes),command_decisions=len(tubes),
                positive_steering_requests_with_negative_actual_body_yaw=positive_opposite,
                minimum_actual_clearance_m=float(data['clearance'].min()),bad_contacts=bad,
                maximum_observation_age_s=read(O/'ROS_RESULT.json')['maximum_observation_age_s'],
                maximum_scan_age_s=read(O/'ROS_RESULT.json')['maximum_scan_age_s'],
                maximum_native_wall_lag_s=native['maximum_wall_lag_s'],history_state_control_errors=history_error,
                historical_command_wall_timestamps_identical=all(a[0]==b[0]for a,b in zip(commands[:origin],old_commands[:origin])),
                historical_wall_timestamp_scope='Different wall execution times are metadata, not a physical state or body-control identity requirement',
                selected_native_tracking_witnesses=rows,
                geometry_budget_diagnostic_only=dict(raw_saved_reference_clearance_m=reference_raw,original_heading_budget_rad=.035,illustrative_lipschitz_budget_capacity_rad=illustrative_capacity,
                     original_prediction_clearance_m=.155,no_new_budget_adopted=True,not_a_control_or_stop_feasibility_proof=True),
                conclusion='First precision guard upper barely crosses .035, while the complete actual stop tail reaches >.0405 rad, so the remaining failure is physical closed-loop/reference transient mismatch rather than only coarse sampling. No alternate-motion controller takeover is recorded. Exact internal mechanical cause is not identified from these states/commands alone.')
    assert reason=='ONLINE_RECOVERY_HEADING_ENVELOPE_FAILED'and not full['passed']and full['maximum_heading_error_rad']>.035
    (O/'DIAGNOSIS.json').write_text(json.dumps(report,indent=2)+'\n')
    REC.mkdir(exist_ok=True);(REC/'SAVED_TRANSIENT_DIAGNOSIS.json').write_bytes((O/'DIAGNOSIS.json').read_bytes())
    print(json.dumps({k:report[k]for k in ['exact_accounting','all_saved_prefix_native_checks_passed','fault_online','full_new_branch_tracking','actual_branch_travel_m','alternate_motion_selections','minimum_actual_clearance_m','bad_contacts','geometry_budget_diagnostic_only']}))
if __name__=='__main__':main()
