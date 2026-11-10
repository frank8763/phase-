"""Saved actual arrays only; never imports a model factory or steps a model."""
import gzip, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2]
C=R/'experiments/v993_steering_transient_diagnosis'
O=R/'runs/v994_diagnostic_timing_postmortem'
sys.path.insert(0,str(C))
from actuation_audit import check

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())

def main():
    tasks=read(C/'TASKS.json');results=read(R/'runs/v993_steering_transient_diagnosis/RESULTS.json')
    rows=[]
    for task,row in zip(tasks,results):
        out=Path(task['output']);p=out/'physics';origin=task['origin_native_tick'];n=row['result']
        commands=read(p/'BODY_COMMANDS.json');records=json.loads(gzip.decompress((p/'ALLOCATION.json.gz').read_bytes()))
        contacts=json.loads(gzip.decompress((p/'CONTACTS.json.gz').read_bytes()))
        with np.load(p/'NATIVE_TRACE.npz')as z:d={k:z[k]for k in z.files}
        with np.load(R/'runs/v993_steering_transient_diagnosis/prior_v974/physics/NATIVE_TRACE.npz')as z:
            errors={k:float(np.max(abs(d[k][:origin]-z[k][:origin])))for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
        count=len(d['qpos']);new=count-origin
        assert new==n['new_actual_native']==len(records) and count==len(commands)==len(contacts)-1
        assert max(errors.values())<=1e-8
        reconstruction=check(out,task)
        q=d['qpos'];v=d['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
        speed=v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw);w=v[:,5]
        k=np.array([x['proof']['selected_curvature']for x in records])
        predicted=yaw[origin-1]+np.cumsum(speed[origin:]*k*.01)
        residual=np.arctan2(np.sin(yaw[origin:]-predicted),np.cos(yaw[origin:]-predicted))
        stamps=np.array([x[0]for x in commands[origin:]]);gaps=np.diff(stamps);index=int(np.argmax(gaps))
        steering=np.array([x['post_native_steering']for x in records])
        rate=steering[:,2:].mean(axis=1);rho=float(np.corrcoef(rate,w[origin:])[0,1])if np.std(rate)>1e-8 else None
        bad=sum(x[2]in {'robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'}for row in contacts for x in row)
        checks=dict(finite=all(np.isfinite(a).all()for a in d.values()),clearance=float(d['clearance'].min())>=.15-1e-8,
                    self_margin=float(d['self_margin'].min())>=-1e-10,contacts=bad==0,
                    native_body_caps=abs(speed[origin:]).max()<=.13 and abs(w[origin:]).max()<=.16,
                    control_map=reconstruction['passed'],history=max(errors.values())<=1e-8,
                    no_root_mutation=not(p/'v648_nonphysical_mutation.json').exists())
        rows.append(dict(slot=task['slot'],name=task['name'],original_passed=row['passed'],models=1,
            historical_native=origin,new_actual_native=new,own_trace_replay_native=n['replay_native'],private_native=0,
            saved_prefix_checks={x:bool(y)for x,y in checks.items()},original_history_max_errors=errors,
            full_stop_recorded=new==800,full_own_replay_recorded=n['replay_native']==count,
            maximum_abs_kinematic_heading_residual_rad=float(abs(residual).max()),
            steering_rate_body_yaw_correlation=rho,maximum_actual_steering_rate_rad_s=float(abs(steering[:,2:]).max()),
            maximum_body_command_timestamp_gap_s=float(gaps[index]),gap_between_new_completed_steps=[index+1,index+2],
            final_translation_speed_m_s=float(np.linalg.norm(v[-1,:2])),
            minimum_clearance_m=float(d['clearance'].min()),bad_contacts=bad,actuator_reconstruction=reconstruction,
            exact_failing_lag_s=None if not row['passed']else n['maximum_wall_lag_s'],
            timing_attribution='Unknown: timestamps are post-step; no per-stage wall/thread/GC timings were saved',
            physical_navigation_passed=False))
    freeze=read(C/'SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in freeze.items())
    total={k:sum(x[k]for x in rows)for k in ['models','historical_native','new_actual_native','own_trace_replay_native','private_native']}
    result=dict(status='V993_NOT_PASSED_TIMING_INTERRUPTION',models_during_analysis=0,integrations_during_analysis=0,
        original_source_files_verified=len(freeze),original_failure_unchanged=True,counts=total,tasks=rows,
        unexecuted_slots=[2,3],new_navigation_trials=0,unexecuted_scientific_candidates=1,
        registered_physical_chain_closed=True,deadline_unix=1794312000.,
        unique_gc_disk_or_scheduler_cause_proven=False,
        missing_fault_time_log_is_instrumentation_defect=True,
        physical_conclusion='Held-angle diagnostic complete; fast straightening only 3.01s, no full stop or own replay. No recovery/navigation qualification.')
    (O/'SAVED_PREFIX_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],counts=total,prefix_checks=[all(x['saved_prefix_checks'].values())for x in rows],
                         gaps=[x['maximum_body_command_timestamp_gap_s']for x in rows])))

if __name__=='__main__':main()
