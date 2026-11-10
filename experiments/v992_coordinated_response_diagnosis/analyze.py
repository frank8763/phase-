"""Closed V991 actual target/response diagnosis; zero new model work."""
import gzip,hashlib,importlib.abc,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v992_coordinated_response_diagnosis'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v991_coordinated_components'))
from independent_tracking import check
from tracking import TrackingGuard

def read(n):return json.loads((O/n).read_text())
def rms(x):return float(np.sqrt(np.mean(np.asarray(x)**2)))
def span(t):return dict(samples=len(t),first_native_tick=int(t[0])if len(t)else None,last_native_tick=int(t[-1])if len(t)else None)
def main():
    for row in read('LOCAL_SAVED_COPY.json')['files']:
        assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256']
    n=read('RESULT.json');plan=read('COMPONENT_REFERENCE.json')['proposal'];fault=read('ONLINE_TRACKING_FAULT.json')
    guard=TrackingGuard(plan);guard.mode='FOLLOW_RECOVERY'
    try:guard.monitor_body(fault['packet']);error=None
    except AssertionError as e:error=str(e)
    assert error=='ONLINE_RECOVERY_HEADING_ENVELOPE_FAILED'
    origin=n['historical_prefix_replay_native']
    with np.load(O/'physics/NATIVE_TRACE.npz')as z:q=z['qpos'];vel=z['qvel'];ctrl=z['ctrl']
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    poses=np.c_[q[:,:2],yaw];tracking=check(plan,poses[origin:])
    records=json.loads(gzip.decompress((O/'physics/ALLOCATION.json.gz').read_bytes()))
    moving=[z for z in records if not z['stale']and z['v']>=.005]
    ticks=np.array([z['native_tick']for z in moving]);index=ticks-1
    speed=vel[index,0]*np.cos(yaw[index])+vel[index,1]*np.sin(yaw[index])
    lateral=-vel[index,0]*np.sin(yaw[index])+vel[index,1]*np.cos(yaw[index])
    w=vel[index,5];angles=q[index][:,[7,9]];rate=vel[index][:,[6,8]].mean(axis=1)
    tan=np.tan(angles);steering_k=np.mean(tan/(.6+tan*np.array([.27,-.27])),axis=1)
    rear=vel[index][:,[10,11]];rear_w=.12*(rear[:,1]-rear[:,0])/.54
    rear_target=np.array([z['actual_ctrl'][2:]for z in moving]);k=np.array([z['proof']['selected_curvature']for z in moving])
    force=np.array([z['post_native_forces']['actuator_force'][:4]for z in moving])
    opposite=(steering_k>.01)&(w<-.005)
    rolling_w=speed*steering_k
    curve_target_w=np.array([z['proof']['selected_common']*.12*z['proof']['selected_curvature']for z in moving])
    original_actual_travel=float(np.linalg.norm(np.diff(q[origin-1:,:2],axis=0),axis=1).sum())
    audit=read('ACTUATION_AUDIT.json');assert audit['passed']and audit['new_control_rows']==len(records)==390
    assert n['replay']['passed']and n['replay_native']==6473 and n['new_branch_native']==390
    assert not tracking['passed']and len(moving)==132
    actual_force_relation=[]
    # Finite differences of observed yaw rate are descriptive only; neither a
    # mass/inertia matrix nor a counterfactual dynamics rollout is constructed.
    corr=lambda a,b:float(np.corrcoef(a,b)[0,1])if np.std(a)>0 and np.std(b)>0 else None
    witnesses=[]
    for tick in [int(ticks[0]),6150,6175,6200,6225,6250,6271,6274,6473]:
        z=next(z for z in records if z['native_tick']==tick);i=tick-1
        witnesses.append(dict(native_tick=tick,requested_v_w=[z['v'],z['w']],actual_body=z['post_native_body'],
            actual_steering=z['post_native_steering'],selected_curvature=z['proof']['selected_curvature'],
            actual_rear_velocity_rad_s=vel[i,[10,11]].tolist(),rear_target_rad_s=z['actual_ctrl'][2:],
            actuator_force=z['post_native_forces']['actuator_force'][:4],
            diagnostic_root_constraint_force=z['post_native_forces']['qfrc_constraint'][:6]))
    answer=dict(models=0,integrations=0,original_status='V991_NOT_PASSED',
        exact_counts=dict(vehicle_tasks_initialized=1,historical_native_restore=6083,new_actual_native=390,
            complete_own_trace_replay_native=6473,private_native=0,second_component_unexecuted=True,new_navigation=0,new24=0),
        original_online_guard_reproduced=True,online_fault_native_tick=fault['packet']['native_tick'],
        online_fault_new_native_tick=fault['packet']['native_tick']-origin,online_guard=guard.last_proof,
        full_stop_independent_tracking=tracking,actuation=audit,whole_replay=n['replay'],
        minimum_actual_clearance_m=n['minimum_actual_clearance_m'],bad_contacts=n['bad_contacts'],
        maximum_wall_lag_s=n['maximum_wall_lag_s'],maximum_observation_age_s=read('ROS_RESULT.json')['maximum_observation_age_s'],
        actual_new_branch_travel_m=original_actual_travel,moving_interval=span(ticks),
        first_fault_seconds_from_first_moving_command=(fault['packet']['native_tick']-int(ticks[0]))*.01,
        actual_response=dict(actual_front_positive_body_yaw_negative=span(ticks[opposite]),
            rear_velocity_target_error_rms_rad_s=[rms(rear[:,i]-rear_target[:,i])for i in [0,1]],
            body_yaw_minus_measured_steering_kinematic_rms_rad_s=rms(w-rolling_w),
            body_yaw_minus_measured_rear_wheels_kinematic_rms_rad_s=rms(w-rear_w),
            body_yaw_minus_joint_targets_kinematic_rms_rad_s=rms(w-curve_target_w),
            body_center_lateral_velocity_rms_m_s=rms(lateral),rear_axle_lateral_velocity_rms_m_s=rms(lateral-.30*w),
            steering_velocity_body_yaw_correlation=corr(rate,w),
            steering_torque_sum_body_yaw_correlation=corr(force[:,:2].sum(axis=1),w),
            maximum_abs_recorded_front_actuator_force=[float(abs(force[:,i]).max())for i in [0,1]],
            interpretation='Recorded targets are coordinated, actual wheel rates and chassis yaw still diverge during steering changes. Correlations are not unique proof of steering reaction torque, slip, friction or servo-load causality.'),
        outcome='Final four-target coordination is actually achieved and independently reconstructs, but does not repair the fixed-state physical heading envelope. No extra gain/threshold change or physical retry follows this closed batch.',
        secondary_audit_error='Missing CLOSED_HANDOFF after real online abort remains original overall-audit FAIL; it is not the primary heading failure and is not regraded.',
        next_design_requirement='Before another whole route or controller-gain revision, identify/qualify the steering-rate-to-chassis-yaw and rear-wheel-load transient on a fixed bounded component, with complete stop-tail budget. No new physical test is authorized by this analysis.',
        witnesses=witnesses)
    (O/'DIAGNOSIS.json').write_text(json.dumps(answer,indent=2)+'\n')
    print(json.dumps({k:answer[k]for k in ['exact_counts','full_stop_independent_tracking','moving_interval','actual_response','outcome']}))
if __name__=='__main__':main()
