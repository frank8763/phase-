"""Independent actual tracking, physical state replay and input ownership audit."""
import gzip,hashlib,importlib.util,json,math,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1003_causal_recovery_execution'
sys.path[:0]=[str(R/'experiments/v993_steering_transient_diagnosis'),str(C)]
s=importlib.util.spec_from_file_location('v1003_original_actuation_audit',R/'experiments/v993_steering_transient_diagnosis/actuation_audit.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def read(p):return json.loads(Path(p).read_text())
def audit(task):
    out=Path(task['output']);p=out/'physics';n=read(out/'RESULT.json');setup=read(p/'SETUP.json');origin=task['origin_native_tick'];plan=read(C/('PLAN_'+str(task['slot'])+'.json'))['plan']
    with np.load(p/'NATIVE_TRACE.npz')as z:d={k:z[k]for k in z.files}
    with np.load(O/'prior_v974/physics/NATIVE_TRACE.npz')as old:errors={k:float(abs(d[k][:origin]-old[k][:origin]).max())for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
    q=d['qpos'];v=d['qvel'];count=len(q);yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    actual=np.c_[q[origin-1:,:2],yaw[origin-1:]];ref=np.array(plan['state_path'])[:,:3]
    position=np.linalg.norm(actual[:,:2]-ref[:,:2],axis=1);heading=abs(np.arctan2(np.sin(actual[:,2]-ref[:,2]),np.cos(actual[:,2]-ref[:,2])))
    commands=read(p/'BODY_COMMANDS.json');contacts=json.loads(gzip.decompress((p/'CONTACTS.json.gz').read_bytes()))
    records=json.loads(gzip.decompress((p/'ALLOCATION.json.gz').read_bytes()))
    progress=float(np.linalg.norm(actual[0,:2]-task['goal_xy'])-np.linalg.norm(actual[-1,:2]-task['goal_xy']))
    checks=dict(complete_native=count==origin+task['maximum_new_native']==n['native']['actual_native']==n['native']['fully_recorded_native'],
        complete_records=len(records)==task['maximum_new_native']and len(commands)==count and len(contacts)==count+1,
        only_committed_inputs=all(commands[origin+i][1:3]+[commands[origin+i][5]]==request for i,request in enumerate(plan['planned_body_requests'])),
        exact_original_history=max(errors.values())<=1e-8,finite=all(np.isfinite(a).all()for a in d.values()),
        native_clearance=float(d['clearance'].min())>=.15-1e-8,native_self=float(d['self_margin'].min())>=-1e-10,
        no_bad_contacts=not any(x[2]in {'robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'}for row in contacts for x in row),
        no_root_mutation=not(p/'v648_nonphysical_mutation.json').exists(),
        canonical_t0=read(p/'SELECTED_NATIVE_BINDING.json')['passed'],sensor_unchanged=read(p/'EXACT_SENSOR_BINDING.json')['passed'],
        actor_unchanged=setup['actor']['phase_rad']==task['phase']and setup['actor']['maximum_speed_m_s']==.08,
        full_stop_tail=float(np.linalg.norm(v[-50:,:2],axis=1).max())<=.03 and abs(v[-50:,5]).max()<=.03 and abs(v[-50:][:,setup['steering_qvel_addresses']]).max()<=.03,
        complete_own_replay=n['replay']['passed']and n['replay_native']==count and n['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8,
        all_native_position_tracking=float(position.max())<=.04,all_native_heading_tracking=float(heading.max())<=.035,
        actual_goal_progress=progress>=.4,complete_execution=n['execution']['passed'],
        native_dt=bool(np.allclose(np.diff(d['time']),.01,rtol=0,atol=1e-8)))
    actuation=m.check(out,task);checks['actual_ctrl_reconstructed']=actuation['passed']
    result=dict(passed=all(checks.values()),checks={k:bool(v)for k,v in checks.items()},actuation=actuation,models_during_audit=0,
        counts=dict(vehicle_tasks_initialized=1,historical_native=origin,new_actual_native=count-origin,own_trace_replay_native=count,private_native=0),
        original_history_max_errors=errors,minimum_actual_clearance_m=float(d['clearance'].min()),bad_contacts=n['native']['bad_contacts'],
        actual_goal_progress_m=progress,maximum_position_error_m=float(position.max()),maximum_heading_error_rad=float(heading.max()),
        component_only=True,navigation_passed=False,real_time_qualified=False)
    (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
