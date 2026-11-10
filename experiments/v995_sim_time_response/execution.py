"""Simulation-time fixed stimulus only; no ROS, sleep, model factory or authority."""
import importlib.util,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v995_existing_timing',R/'experiments/v882_runtime_evidence_repair/runtime_timing.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t)

def execute(vehicle,task,controls,out,deadline,clock=time):
    out=Path(out);out.mkdir(exist_ok=False)
    profile=t.Timing(task['maximum_new_native'],wall=clock.monotonic,cpu=clock.thread_time)
    gc=t.CyclicGCWindow();origin=vehicle.count;inside=False;error=None;exact=None
    try:
        gc.enter()
        for i in range(task['maximum_new_native']):
            assert clock.time()<deadline-45,'ROOT_OR_TASK_MODEL_RESERVE'
            inside=True
            profile.call('native_and_record',vehicle.count,vehicle.step,*controls(i,task,vehicle.probe_initial_curvature))
            inside=False
            body=profile.call('body_read',vehicle.count,vehicle.body)
            assert abs(body[3])<=.13 and abs(body[4])<=.16,'ORIGINAL_BODY_SPEED_OR_YAW_CAP'
            if i%5==0:profile.call('scan',vehicle.count,vehicle.scan)
            if i%100==0:
                def save():
                    (out/'PARTIAL.json').write_text(json.dumps(dict(new_actual_native=vehicle.count-origin,body=list(body),execution_mode=task['execution_mode']))+'\n')
                profile.call('partial_write',vehicle.count,save)
        exact=vehicle.count-origin
    except BaseException as e:error=repr(e);exact=None if inside else vehicle.count-origin
    finally:
        gc.close()
        result=dict(passed=error is None,error=error,new_native_count=exact,completed_new_native_lower_bound=vehicle.count-origin,
            execution_mode='SIMULATION_TIME_FIXED_INPUT_NOT_REALTIME',real_time_qualified=False,
            wall_lag_is_not_a_gate_for_offline_fixed_input=True,gc_prior_flag_restored=t.gc.isenabled()==gc.was_enabled)
        try:result['timing']=profile.save(out)
        except BaseException as e:result.update(passed=False,timing_save_error=repr(e))
        (out/'EXECUTION_RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
