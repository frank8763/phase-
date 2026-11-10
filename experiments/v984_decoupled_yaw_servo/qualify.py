"""Saved observations and actuator-map negatives only; not closed-loop physics."""
import copy,hashlib,json,math,time,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from control_fixture import R,frozen,make,copy_state
from vehicle_control import Adapter,transfer_restored_state,MAX_EQUIVALENT_YAW
C=Path(__file__).parent;O=R/'runs/v984_decoupled_yaw_servo';SAVED=R/'runs/v983_saved_transient_diagnosis'

def main():
    checks={};old=make(frozen.Adapter);candidate=make(Adapter)
    cmd=json.loads((SAVED/'physics/BODY_COMMANDS.json').read_text());setup=json.loads((SAVED/'physics/SETUP.json').read_text())
    before=None;front_error=rate_excess=limit_excess=common_error=0.;changed=0;projections=0;new=[];feedback_samples=[]
    timings=[]
    for i,row in enumerate(cmd):
        if i+1==6175:before=copy_state(old,frozen.Adapter)
        previous=candidate.last.copy();nominal=copy_state(candidate,frozen.Adapter)
        expected=nominal.compute(row[1],row[2],row[3],row[4],row[5])
        start=time.perf_counter();control=candidate.compute(row[1],row[2],row[3],row[4],row[5]);timings.append(time.perf_counter()-start)
        original=old.compute(row[1],row[2],row[3],row[4],row[5])
        front_error=max(front_error,float(abs(control[:2]-original[:2]).max()))
        common_error=max(common_error,abs(control[2:].mean()-expected[2:].mean()))
        rate=np.asarray(candidate.commands.rate)*candidate.dt/.08
        rate_excess=max(rate_excess,float((abs(control-previous)-rate).max()))
        limit_excess=max(limit_excess,float((control-candidate.commands.upper).max()),float((candidate.commands.lower-control).max()))
        if not row[5]and row[1]>=.005:
            changed+=int(abs(control[2:]-expected[2:]).max()>1e-12)
        else:assert np.max(abs(control-expected))<=1e-12
        if candidate.last_yaw_proof.get('applied'):
            projections+=int(candidate.last_yaw_proof['projection_limited'])
            assert abs(candidate.last_yaw_proof['equivalent_yaw_target'])<=MAX_EQUIVALENT_YAW
            assert np.all(control[2:]*expected[2:]>=-1e-12)
        if 6165<=i+1<=6215 and(i+1)%5==0:
            feedback_samples.append(dict(native_tick=i+1,old_measured_body_v_w=row[3:5],requested_v_w=row[1:3],original_control=original.tolist(),counterfactual_control=control.tolist(),proof=copy.deepcopy(candidate.last_yaw_proof)))
        new.append(control)
    checks['all_saved_front_steering_exact']=front_error<=1e-12
    checks['longitudinal_common_matches_original_from_same_memory']=common_error<=1e-12
    checks['all_original_motor_limits']=limit_excess<=1e-10
    checks['all_original_motor_slew']=rate_excess<=1e-10
    checks['nontrivial_rear_feedback_on_actual_failed_witness']=changed>0
    checks['brake_stale_nonforward_exact_same_memory']=True
    row=cmd[6174]
    ideal=make(Adapter);bad=make(Adapter);opposite=make(Adapter)
    for x in [ideal,bad,opposite]:transfer_restored_state(before,x)
    u0=ideal.compute(row[1],row[2],row[3],row[2],False)
    un=bad.compute(row[1],row[2],row[3],row[4],False)
    up=opposite.compute(row[1],row[2],row[3],.06,False)
    checks['negative_actual_yaw_increases_positive_differential']=(un[3]-un[2])>(u0[3]-u0[2])+1e-6
    checks['positive_actual_yaw_reduces_differential']=(up[3]-up[2])<(u0[3]-u0[2])-1e-6
    checks['same_front_commands_in_three_measured_yaw_cases']=bool(np.array_equal(u0[:2],un[:2])and np.array_equal(u0[:2],up[:2]))
    negatives=[]
    for k in range(4):
        args=[.05,.01,.04,0.,False];args[k]=float('nan')
        try:make(Adapter).compute(*args)
        except (ValueError,AssertionError):negatives.append(True)
        else:negatives.append(False)
    checks['nonfinite_input_rejected']=all(negatives)
    straight_old=make(frozen.Adapter);straight=make(Adapter)
    for _ in range(100):
        assert np.array_equal(straight_old.compute(.05,0.,.05,0.),straight.compute(.05,0.,.05,0.))
    checks['straight_zero_error_identity']=True
    # Dense fixed boundary sweep over the admitted driving state/rate domain.
    sweep=0
    for requested_v in [.005,.03,.05,.10]:
        for curvature in [-.758770385,0.,.758770385]:
            for actual_yaw in [-.16,-.06,0.,.06,.16]:
                for common in [0.,.2,1.,5.9]:
                    a=make(Adapter);a.last=np.array([.1,-.1,common+.01,common-.01]);previous=a.last.copy()
                    u=a.compute(requested_v,requested_v*curvature,.04,actual_yaw)
                    assert a.commands.legal(u)and (abs(u-previous)<=np.asarray(a.commands.rate)*.01/.08+1e-10).all()
                    sweep+=1
    checks['fixed_boundary_projection_cases']=sweep==240
    old=make(frozen.Adapter)
    for row in cmd[:6083]:old.compute(row[1],row[2],row[3],row[4],row[5])
    a=make(Adapter);transfer=transfer_restored_state(old,a)
    checks['restored_origin_memory_exact_no_step']=np.array_equal(a.last,old.last)and a.integral==old.integral and transfer['integrations']==0
    from authority import authorized
    try:authorized()
    except PermissionError:checks['no_model_authority']=True
    else:checks['no_model_authority']=False
    result=dict(passed=all(checks.values()),checks={k:bool(v)for k,v in checks.items()},models=0,actual_native=0,private_native=0,replay_native=0,
                old_observation_rows_recomputed=len(cmd),new_rear_control_rows=changed,projection_limited_rows=projections,boundary_cases=sweep,
                maximum_front_control_difference=front_error,maximum_common_difference=common_error,maximum_rate_excess=rate_excess,maximum_limit_excess=limit_excess,
                measured_map_runtime_s=dict(median=float(np.median(timings)),p99=float(np.quantile(timings,.99)),maximum=max(timings)),
                baseline_witness_new_controls=dict(no_yaw_error=u0.tolist(),negative_measured_yaw=un.tolist(),positive_measured_yaw=up.tolist()),
                saved_feedback_witnesses=feedback_samples,restored_transfer=transfer,
                counterfactual_controls_on_old_observations=True,new_trajectory_generated=False,closed_loop_tracking_qualified=False,physical_ready=False,
                old_physical_outcome='V982_NOT_PASSED',limitations='No closed-loop physical improvement inferred; old observations are not responses to the proposed controls. Independent rear drive is required on future hardware.')
    (O/'CONTROL_MAP_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['saved_feedback_witnesses']}));assert result['passed']
if __name__=='__main__':main()
