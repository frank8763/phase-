"""Independent completed diagnostic checks. Never grades navigation success."""
import gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v995_sim_time_response'
sys.path.insert(0,str(C))
from actuation_audit import check as reconstruct
from schedule import controls

def audit(task):
    out=Path(task['output']);p=out/'physics';n=json.loads((out/'RESULT.json').read_text())
    setup=json.loads((p/'SETUP.json').read_text());prefix=json.loads((p/'PREFIX_RESTORE.json').read_text());origin=task['origin_native_tick']
    with np.load(p/'NATIVE_TRACE.npz')as z:d={k:z[k]for k in z.files}
    with np.load(O/'prior_v974/physics/NATIVE_TRACE.npz')as old:
        errors={k:float(abs(d[k][:origin]-old[k][:origin]).max())for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
    assert max(errors.values())<=1e-8,'INDEPENDENT_ORIGINAL_HISTORY_MISMATCH'
    q=d['qpos'];v=d['qvel'];count=len(q);yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    body=np.c_[q[:,:2],yaw,v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw),v[:,5]]
    records=json.loads(gzip.decompress((p/'ALLOCATION.json.gz').read_bytes()))
    commands=json.loads((p/'BODY_COMMANDS.json').read_text())
    contacts=json.loads(gzip.decompress((p/'CONTACTS.json.gz').read_bytes()))
    initial=json.loads((p/'ACTIVE_ADAPTER_BINDING.json').read_text())['stopped_origin_curvature']
    checks=dict(complete_recorded_native=count==origin+800==n['native']['actual_native']==n['native']['fully_recorded_native'],
        complete_new_diagnostic=n['new_actual_native']==800 and len(records)==800,
        every_control_is_registered_stimulus=all(tuple(commands[origin+i][1:3]+[commands[origin+i][5]])==controls(i,task,initial)for i in range(800)),
        exact_history=max(errors.values())<=1e-8 and prefix['passed'],
        finite_arrays=all(np.isfinite(a).all()for a in d.values()),
        full_native_clearance=float(d['clearance'].min())>=.15-1e-8,
        full_native_self=float(d['self_margin'].min())>=-1e-10,
        contacts_and_commands_complete=len(contacts)==count+1 and len(commands)==count,
        no_bad_contacts=not any(x[2]in {'robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'}for row in contacts for x in row),
        no_root_mutation=not(p/'v648_nonphysical_mutation.json').exists(),
        unchanged_sensor=json.loads((p/'EXACT_SENSOR_BINDING.json').read_text())['passed'],
        canonical_true_t0=json.loads((p/'SELECTED_NATIVE_BINDING.json').read_text())['passed'],
        original_actor=setup['actor']['phase_rad']==task['phase']and setup['actor']['maximum_speed_m_s']==.08,
        native_body_caps=abs(body[origin:,3]).max()<=.13 and abs(body[origin:,4]).max()<=.16,
        complete_stop_tail=float(np.linalg.norm(v[-50:,:2],axis=1).max())<=.03 and abs(v[-50:,5]).max()<=.03 and abs(v[-50:][:,setup['steering_qvel_addresses']]).max()<=.03,
        complete_own_replay=n['replay']['passed']and n['replay_native']==count and n['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8,
        fixed_simulation_time_step=bool(np.allclose(np.diff(d['time']),.01,rtol=0,atol=1e-8)),
        offline_execution_complete=n['execution']['passed']and n['execution']['new_native_count']==800 and n['execution_mode']=='SIMULATION_TIME_FIXED_INPUT_NOT_REALTIME',
        diagnostic_not_navigation=task['stage']=='diagnostic'and n['diagnostic_only'])
    actuation=reconstruct(out,task);checks['actual_ctrl_reconstructed']=actuation['passed']
    post=np.asarray([r['post_native_steering']for r in records]);rate=post[:600,2:].mean(axis=1)
    k=np.asarray([r['proof']['selected_curvature']for r in records]);speed=body[origin:,3];w=body[origin:,4]
    time_s=np.arange(1,801)*.01
    expected_yaw=body[origin-1,2]+np.cumsum(speed*k*.01)
    residual=np.arctan2(np.sin(body[origin:,2]-expected_yaw),np.cos(body[origin:,2]-expected_yaw))
    steady=(time_s<=6)&(time_s>=4.5)
    active=(abs(rate)>.03)
    rms=lambda x:float(np.sqrt(np.mean(x**2)))
    output=dict(passed=all(checks.values()),checks={k:bool(v)for k,v in checks.items()},actuation=actuation,
        counts=dict(vehicle_tasks_initialized=1,historical_native=origin,new_actual_native=800,own_trace_replay_native=count,private_native=0),
        original_history_max_errors=errors,minimum_actual_clearance_m=float(d['clearance'].min()),bad_contacts=n['native']['bad_contacts'],
        independent_navigation_sample=False,navigation_passed=False,diagnostic_evidence_only=True,
        metrics=dict(maximum_abs_kinematic_heading_residual_rad=float(abs(residual).max()),
            final_kinematic_heading_residual_rad=float(residual[-1]),
            movement_yaw_residual_rms_rad_s=rms((w-speed*k)[:600]),
            final_moving_window_yaw_residual_rms_rad_s=rms((w-speed*k)[steady]),
            measured_steering_rate_body_yaw_correlation=float(np.corrcoef(rate,w[:600])[0,1])if np.std(rate)>1e-8 else None,
            active_steering_samples=int(active.sum()),
            maximum_steering_rate_rad_s=float(abs(post[:,2:]).max()),
            final_actual_steering_rad=post[-1,:2].tolist(),
            actual_translation_m=float(np.linalg.norm(np.diff(q[origin-1:,:2],axis=0),axis=1).sum())),
        reference_heading_residual_is_diagnostic_not_a_navigation_gate=True,real_time_qualified=False,models_during_audit=0)
    (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(output,indent=2)+'\n');return output
