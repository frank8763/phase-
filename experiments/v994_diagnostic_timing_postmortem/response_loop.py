"""Proposed execution seam; no factory, physics import, launch or model authority.

Qualifying this seam with a mock vehicle does not qualify physical response.
The closed V993 source and its failure are not changed or resumed.
"""
import importlib.util,json,time
from pathlib import Path

R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v994_existing_runtime_timing',R/'experiments/v882_runtime_evidence_repair/runtime_timing.py')
timers=importlib.util.module_from_spec(spec);spec.loader.exec_module(timers)

def run_fixed_response(vehicle,task,controls,out,absolute_task_deadline,clock=time,write_partial=None):
    out=Path(out);out.mkdir(exist_ok=False)
    timing=timers.Timing(task['maximum_new_native'],wall=clock.monotonic,cpu=clock.thread_time)
    window=timers.CyclicGCWindow();origin=vehicle.count;in_step=False;error=None;steps_exact=None
    def partial(data):(out/'PARTIAL.json').write_text(json.dumps(data)+'\n')
    write_partial=write_partial or partial
    try:
        window.enter();begun=clock.monotonic()
        for i in range(task['maximum_new_native']):
            assert clock.time()<absolute_task_deadline-45,'ROOT_OR_TASK_MODEL_RESERVE'
            target=begun+i*.01
            timing.call('pacing_wait',vehicle.count,clock.sleep,max(0.,target-clock.monotonic()))
            timing.lag(vehicle.count,target,clock.monotonic())
            assert timing.maximum_lag_s<=.1,'NATIVE_WALL_LAG'
            in_step=True
            timing.call('native_and_record',vehicle.count,vehicle.step,*controls(i,task,vehicle.probe_initial_curvature))
            in_step=False
            body=timing.call('body_read',vehicle.count,vehicle.body)
            assert abs(body[3])<=.13 and abs(body[4])<=.16,'ORIGINAL_BODY_SPEED_OR_YAW_CAP'
            if i%5==0:timing.call('scan',vehicle.count,vehicle.scan)
            if i%100==0:timing.call('partial_write',vehicle.count,write_partial,dict(new_actual_native=vehicle.count-origin,body=list(body),maximum_wall_lag_s=timing.maximum_lag_s))
        steps_exact=vehicle.count-origin
    except BaseException as e:
        error=repr(e);steps_exact=None if in_step else vehicle.count-origin
    finally:
        window.close()
        profile=timing.save(out)
        receipt=dict(passed=error is None,error=error,new_native_count=steps_exact,
            completed_new_native_lower_bound=vehicle.count-origin,maximum_wall_lag_s=timing.maximum_lag_s,
            overrun=timing.overrun,stage_timings=profile,full_response=error is None,
            gc_prior_flag_restored=timers.gc.isenabled()==window.was_enabled,
            grants_model_authority=False,physical_tracking_qualified=False)
        (out/'EXECUTION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt
