"""Model-free admission/retained-stop transactions; never actuates the car.

Only independently reviewed arrays may enter this seam. A manifest is not itself
a dynamics/geometry proof. The software caller must actually run every gate.
"""
import hashlib,json
import numpy as np

REQUIRED_CHECKS=frozenset({'finite','full_states','full_raw_geometry','full_200_stop','goal_upper','speed_yaw','legal_ctrl','legal_slew','complete2200stop','terminal_full_cycle_hold','path_cross_track'})
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()
def context(x):
    assert x['packet']['native_tick']==x['source']['source_native_tick'],'SOURCE_TICK_MISMATCH'
    assert x['source']['periodic']['source_tick']==x['packet']['native_tick'],'PERIODIC_SOURCE_MISMATCH'
    return dict(origin_native_tick=x['packet']['native_tick'],goal=x['goal'],origin_digest=digest(x['packet']),source_digest=digest(x['source']))
def admit(x,review,states,controls,requests):
    from kernel import initial,REQUIRED
    checks=review.get('checks',{})
    assert REQUIRED_CHECKS.issubset(checks),'MISSING_WHOLE_SOURCE_CHECK'
    assert review.get('passed') and all(checks[k] for k in REQUIRED_CHECKS),'WHOLE_GOAL_SOURCE_REJECTED'
    assert np.shape(states)==(len(requests)+1,8) and np.shape(controls)==(len(requests),4),'SOURCE_LENGTH_MISMATCH'
    assert np.max(abs(np.asarray(states)[0]-initial(x['packet'])['state']))<=1e-8,'SOURCE_ORIGIN_MISMATCH'
    assert np.isfinite(states).all() and np.isfinite(controls).all() and np.isfinite(requests).all(),'NONFINITE_SOURCE'
    assert np.linalg.norm(np.asarray(states)[-1,:2]-x['goal'])+.08<=.45,'SOURCE_DOES_NOT_REACH_GOAL'
    assert len(requests)>=2200 and np.array_equal(requests[-2200:],np.zeros((2200,3))),'COMPLETE_STOP_REQUIRED'
    moving=len(requests)-2200;expected=list(range(0,moving,125));stops=review.get('rolling_stops',[])
    assert [q['offset_native']for q in stops]==expected and expected,'STOP_COVERAGE_GAP'
    assert all(q['passed'] and q.get('full_stop_controls_passed')for q in stops),'ROLLING_STOP_REJECTED'
    raw_min=float(review['minimum_full_cycle_raw_m']);assert np.isfinite(raw_min) and raw_min>=REQUIRED,'RAW_CLEARANCE_REJECTED'
    return dict(**context(x),complete_goal_qualified=True,trajectory_native=len(requests),rolling_stop_offsets=expected,
        controller_source_sha256=hashlib.sha256(np.asarray(controls,dtype=np.float64).tobytes()).hexdigest(),minimum_full_cycle_raw_m=raw_min)

def select_after_recheck(current_context,retained_stop,replacement=None):
    """Pure selection: invalid replacement cannot erase an existing stop.

    A stop witness must start at THIS exact measured state/controller/source;
    stale witnesses are refused. Real online recertification is a later gate.
    """
    assert retained_stop is not None,'NO_RETAINED_STOP'
    assert retained_stop['context']==current_context,'STALE_STOP_SOURCE'
    requests=np.asarray(retained_stop['requests']);controls=np.asarray(retained_stop['controls'])
    assert retained_stop.get('independent_stop_passed') and requests.shape==(2200,3) and controls.shape==(2200,4),'UNCERTIFIED_STOP'
    assert np.array_equal(requests,np.zeros((2200,3))) and np.isfinite(controls).all(),'INVALID_STOP_SOURCE'
    manifest=(replacement or {}).get('manifest',{})
    bound=all(manifest.get(k)==v for k,v in current_context.items())
    if replacement is not None and replacement.get('context')==current_context and replacement.get('whole_goal_admitted') is True and manifest.get('complete_goal_qualified') is True and bound:
        return dict(mode='COMPLETE_GOAL_REFERENCE',selected=replacement,retained_stop=retained_stop)
    return dict(mode='RETAINED_COMPLETE_STOP',selected=retained_stop,retained_stop=retained_stop)
