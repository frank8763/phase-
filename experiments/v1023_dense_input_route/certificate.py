"""Independent full-profile admission boundary; partial route never passes.

The supplied minimum, 'passed' bit and goal upper are not trusted. Recreate the
whole schedule with the frozen controller predictor and recheck its full body
against the input causal scene. Source qualification grants NO actuation.
"""
import hashlib,json,math
import numpy as np
from geometry_model import REQUIRED,ref
from whole_input import predict,checks,EDGE_TICKS,MAX_EDGES,public_setup

def binding(packet,source,setup,goal,scope):
    value=dict(packet=packet,source=source,setup=public_setup(setup),original_goal=list(goal),certificate_scope=scope)
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def audit(plan,packet,source,setup,goal):
    check={};metrics={}
    try:
        scope=plan['certificate_scope'];assert scope in ('pre_detection_static','post_detection_full_cycle'),'UNKNOWN_SCOPE'
        assert plan['original_goal']==list(goal),'ORIGINAL_GOAL_CHANGED'
        assert plan['full_goal_route_required']is True and plan['partial_progress_never_success']is True,'PARTIAL_SUCCESS_ALLOWED'
        assert plan['physical_ready']is False and plan['actuation_authority']is False,'UNQUALIFIED_PHYSICAL_AUTHORITY'
        assert plan.get('snapshot_binding_sha256')==binding(packet,source,setup,goal,scope),'SNAPSHOT_BINDING_CHANGED'
        if scope=='post_detection_full_cycle':
            ref.snapshot_state(packet,source,packet['body_measured_at']);prior=source['periodic']
        else:
            assert source is None and packet.get('dynamic_discovered')is False and packet['native_tick']==0 and packet['sim_time']==0.,'STATIC_CERTIFICATE_AFTER_DISCOVERY'
            prior=None
        check['causal_scope_goal_and_snapshot']=True
        targets=np.asarray(plan['edge_targets'],float);n=len(targets)*EDGE_TICKS+200
        assert targets.ndim==1 and 0<len(targets)<=MAX_EDGES and np.isfinite(targets).all(),'INVALID_TARGET_SCHEDULE'
        assert plan['movement_ticks']==n-200 and plan['brake_ticks']==200 and plan['analytical_prediction_steps']==n,'INCOMPLETE_TAIL_OR_DURATION'
        states=np.asarray(plan['state_path'],float);control=np.asarray(plan['predicted_actuator_controls'],float);requests=np.asarray(plan['planned_body_requests'],float)
        assert states.shape==(n+1,8)and control.shape==(n,4)and requests.shape==(n,3),'TRUNCATED_PROFILE'
        assert np.isfinite(states).all()and np.isfinite(control).all()and np.isfinite(requests).all(),'NONFINITE_PROFILE'
        reference,original_control,original_requests=predict(setup,packet,targets)
        state_error=float(abs(states-reference).max());ctrl_error=float(abs(control-original_control).max())
        check['entire_original_predictor_reconstructed']=state_error<=1e-10 and ctrl_error<=1e-10 and np.array_equal(requests,original_requests)
        check['entire_path_matches_prediction']=bool(np.array_equal(np.asarray(plan['path']),states[:,:3]))
        a,b=ref._old.Geometry(setup['known'],prior).clearances(reference[:,:3]);minimum=float(np.minimum(a,b).min())
        original_checks,upper=checks(reference,original_control,original_requests,packet,setup,goal,minimum,REQUIRED)
        check.update(original_checks)
        check['no_safety_threshold_reduction']=abs(plan['required_raw_clearance_m']-REQUIRED)<=1e-14
        check['goal_upper_recomputed']=abs(plan['terminal_goal_distance_upper_m']-upper)<=1e-10
        check['minimum_recomputed']=abs(plan['minimum_raw_full_cycle_clearance_m']-minimum)<=1e-10
        metrics.update(minimum_full_raw_m=minimum,required_raw_m=REQUIRED,terminal_goal_upper_m=upper,
            original_predictor_state_error=state_error,original_predictor_ctrl_error=ctrl_error,complete_native_predicted_steps=n)
    except (AssertionError,KeyError,ValueError,TypeError,IndexError)as error:
        return dict(passed=False,checks=check,error=str(error),models=0,integrations=0,physical_ready=False,actuation_authority=False)
    return dict(passed=all(check.values()),checks=check,metrics=metrics,models=0,integrations=0,physical_ready=False,actuation_authority=False)
