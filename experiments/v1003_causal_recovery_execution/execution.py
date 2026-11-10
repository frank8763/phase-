"""Exact committed planned requests; every actual native pose independently monitored."""
import importlib.util,json,math,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1]
s=importlib.util.spec_from_file_location('v1003_timing',R/'experiments/v882_runtime_evidence_repair/runtime_timing.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t)

def execute(vehicle,task,out,deadline,clock=time):
    out=Path(out);out.mkdir(exist_ok=False)
    plan=json.loads((C/('PLAN_'+str(task['slot'])+'.json')).read_text())['plan']
    requests=plan['planned_body_requests'];states=np.asarray(plan['state_path'])
    assert plan['passed']and len(requests)==task['maximum_new_native']and len(states)==len(requests)+1
    assert np.max(abs(np.asarray(vehicle.body()[:3])-states[0,:3]))<=1e-8,'ACTUAL_INITIAL_STATE_DIFFERS_FROM_REFERENCE'
    assert np.max(abs(vehicle.adapter.last-plan['initial']['last_ctrl']))<=1e-8 and abs(vehicle.adapter.integral-plan['initial']['integral'])<=1e-8,'ACTUAL_CONTROLLER_MEMORY_DIFFERS'
    profile=t.Timing(len(requests),wall=clock.monotonic,cpu=clock.thread_time);gc=t.CyclicGCWindow();origin=vehicle.count
    inside=False;error=None;exact=None;maximum_position=maximum_heading=0.
    try:
        gc.enter()
        for i,request in enumerate(requests):
            assert clock.time()<deadline-45,'ROOT_OR_TASK_MODEL_RESERVE'
            inside=True;profile.call('native_and_record',vehicle.count,vehicle.step,*request);inside=False
            body=profile.call('body_read',vehicle.count,vehicle.body)
            assert abs(body[3])<=.13 and abs(body[4])<=.16,'ORIGINAL_BODY_SPEED_OR_YAW_CAP'
            position=float(np.linalg.norm(np.asarray(body[:2])-states[i+1,:2]));delta=body[2]-states[i+1,2];heading=abs(math.atan2(math.sin(delta),math.cos(delta)))
            maximum_position=max(maximum_position,position);maximum_heading=max(maximum_heading,heading)
            assert position<=.04+1e-12 and heading<=.035+1e-12,'ACTUAL_REFERENCE_TRACKING_ENVELOPE_EXCEEDED'
            if i%5==0:profile.call('scan',vehicle.count,vehicle.scan)
            if i%100==0:
                def save():
                    (out/'PARTIAL.json').write_text(json.dumps(dict(new_actual_native=vehicle.count-origin,body=list(body),maximum_position_error_m=maximum_position,maximum_heading_error_rad=maximum_heading))+'\n')
                profile.call('partial_write',vehicle.count,save)
        exact=vehicle.count-origin
    except BaseException as e:error=repr(e);exact=None if inside else vehicle.count-origin
    finally:
        gc.close();result=dict(passed=error is None,error=error,new_native_count=exact,completed_new_native_lower_bound=vehicle.count-origin,
            maximum_position_error_m=maximum_position,maximum_heading_error_rad=maximum_heading,
            execution_mode=task['execution_mode'],real_time_qualified=False,gc_prior_flag_restored=t.gc.isenabled()==gc.was_enabled)
        try:result['timing']=profile.save(out)
        except BaseException as e:result.update(passed=False,timing_save_error=repr(e))
        (out/'EXECUTION_RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
