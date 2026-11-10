"""Completed actual traces only; measured-future explanatory fit is not prediction."""
import gzip,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v996_response_decomposition';D=R/'runs/v995_sim_time_response'
def read(p):return json.loads(p.read_text())
def angle(q):return np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
def virtual(q):
    z=np.tan(q);k=np.column_stack([z[:,0]/(.6+.27*z[:,0]),z[:,1]/(.6-.27*z[:,1])]).mean(axis=1)
    return np.arctan(.6*k),k
def rms(x):return float(np.sqrt(np.mean(np.asarray(x)**2)))
def load(task):
    p=Path(task['output']);origin=task['origin_native_tick'];n=read(p/'RESULT.json');assert n['passed']and read(p/'INDEPENDENT_AUDIT.json')['passed']
    setup=read(p/'physics/SETUP.json')
    with np.load(p/'physics/NATIVE_TRACE.npz')as z:q=z['qpos'];vel=z['qvel']
    assert len(q)==origin+800 and n['replay_native']==len(q)
    ix=setup['steering_qpos_addresses'];q0=q[origin-1:];v0=vel[origin-1:];yaw=angle(q0)
    observed=np.arctan2(np.sin(np.diff(yaw)),np.cos(np.diff(yaw)))/.01
    speed=v0[:,0]*np.cos(yaw)+v0[:,1]*np.sin(yaw);midv=(speed[:-1]+speed[1:])/2
    delta,k=virtual(q0[:,ix]);deltarate=np.diff(delta)/.01;midk=(k[:-1]+k[1:])/2
    records=json.loads(gzip.decompress((p/'physics/ALLOCATION.json.gz').read_bytes()))
    target=np.array([x['proof']['selected_curvature']for x in records]);x=midv*midk;cmd=midv*target
    return dict(task=task,observed=observed,x=x,command=cmd,delta=delta,deltarate=deltarate,
                time=np.arange(800)*.01,logged_omega=(v0[:-1,5]+v0[1:,5])/2)
def metrics(observed,predicted):
    error=observed-predicted;cumulative=np.cumsum(error)*.01
    return dict(yaw_rate_rms_rad_s=rms(error),maximum_heading_residual_rad=float(abs(cumulative).max()),final_heading_residual_rad=float(cumulative[-1]),
                movement_heading_residual_rad=float(cumulative[599]),stop_heading_increment_rad=float(cumulative[-1]-cumulative[599]))
if __name__=='__main__':
    done=read(D/'COMPLETION.json');assert done['diagnostic_evidence_passed']and done['bridge_equivalence_passed']
    root=read(R/'runs/sim_time_recovery_20261110/ROUND_WINDOW.json');end=min(root['deadline_unix'],done['closed_unix']+1500.)
    assert time.time()<end,'CANDIDATE_PREPARATION_BUDGET_ENDED'
    rows=[load(t)for t in read(R/'experiments/v995_sim_time_response/TASKS.json')]
    held,fast=rows[:2];mask=(held['time']>=2)&(held['time']<6)&(abs(held['deltarate'])<.03)
    assert mask.sum()>=100 and float(held['x'][mask]@held['x'][mask])>1e-10
    a=float(held['x'][mask]@held['observed'][mask]/(held['x'][mask]@held['x'][mask]))
    active=(fast['time']<6)&(abs(fast['deltarate'])>.03);assert active.sum()>=10
    z=fast['deltarate'][active];res=fast['observed'][active]-a*fast['x'][active];b=float(z@res/(z@z))
    details=[];qualified=.2<=a<=2 and abs(b)<=.5
    for i,row in enumerate(rows):
        corrected=a*row['x']+b*row['deltarate'];plain=metrics(row['observed'],row['x']);fit=metrics(row['observed'],corrected)
        if i>=2:qualified=qualified and fit['maximum_heading_residual_rad']<=.015 and fit['maximum_heading_residual_rad']*2<=plain['maximum_heading_residual_rad']
        item=dict(slot=i,name=row['task']['name'],fit_partition='gain_calibration'if i==0 else'steer_rate_calibration'if i==1 else'held_out_schedule',
            target_kinematics=metrics(row['observed'],row['command']),encoder_kinematics=plain,teacher_forced_two_coefficient=fit,
            target_to_encoder_rate_rms=rms(row['x']-row['command']),encoder_to_body_rate_rms=rms(row['observed']-row['x']),
            body_rate_log_vs_quaternion_difference_rms=rms(row['observed']-row['logged_omega']),
            net_actual_virtual_steering_change_rad=float(row['delta'][-1]-row['delta'][0]),
            maximum_actual_virtual_steering_rate_rad_s=float(abs(row['deltarate']).max()))
        details.append(item)
    result=dict(models=0,integrations=0,private_predictions=0,physics_replay=0,root_deadline_unix=root['deadline_unix'],candidate_preparation_deadline_unix=end,
        four_fixed_diagnostics_complete=True,coefficient_gain_a=a,coefficient_steer_rate_b=b,held_steady_samples=int(mask.sum()),fast_active_samples=int(active.sum()),
        descriptive_transient_hypothesis_supported=bool(qualified),teacher_forced_future_actual_inputs=True,
        open_loop_predictor_qualified=False,controller_qualified=False,physical_safety_bound_proven=False,unique_mechanical_cause_proven=False,tasks=details)
    (O/'RESPONSE_DECOMPOSITION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
