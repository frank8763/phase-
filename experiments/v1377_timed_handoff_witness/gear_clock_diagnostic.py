"""Saved gear-state metadata and mandatory clock delay, no physical replay.

Only the original pure-software GearHandoff transition function is evaluated.
Constant feedback probes are software counterfactuals, never future observations.
"""
import copy
import math
import os
from pathlib import Path
import signal
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R, O, RAW, read, sha, json, np, load, function, scalar_distance, SimpleNamespace
from audit_timed_nominal import independent_swept

ACTUAL = R/'runs/v858_nav2_verified/v1378/steering_response'


def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('ZERO_MODEL600_STOP')));signal.alarm(600)
    begin=time.monotonic();frozen=read(O/'GEAR_CLOCK_SOURCE_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in frozen.items())
    gear=load('original_gear_transition','experiments/v1346_measured_gear_handoff/gear_handoff.py')
    gate=gear.GearHandoff();journal=read(ACTUAL/'APPLIED_JOURNAL.json')
    for row in journal:
        vr,wr,proof=gate.select(*row['upstream_request'][:2],native_tick=row['before_native'],body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders'])
        assert [vr,wr,False]==row['request'] and proof==row['gear_handoff']
    assert gate.gear==1 and gate.brake_start is None and gate.last_tick==32599
    final=read(ACTUAL/'FINAL_PACKET.json')
    body=final['body'];ctrl=final['controller_memory']['last_ctrl'];enc=final['steering']['position']+final['steering']['velocity']
    assert max(abs(x) for x in body[3:])<.003 and max(abs(x) for x in ctrl[2:])==0
    probe=copy.deepcopy(gate);trace=[]
    for tick in range(32600,32801):
        v,w,p=probe.select(-.1,.05,native_tick=tick,body=body,last_ctrl=ctrl,encoders=enc)
        trace.append(dict(native_tick=tick,requested=[-.1,.05],output=[v,w],proof=p))
        if tick<32800:assert v==w==0 and not p['released']
        else:assert [v,w]==[-.1,.05] and p['released']
    assert trace[0]['proof']['brake_start']==32600 and trace[-1]['proof']['braking_native']==200
    zero=copy.deepcopy(gate)
    for tick in range(32600,32800):zero.select(0.,0.,native_tick=tick,body=body,last_ctrl=ctrl,encoders=enc)
    assert zero.gear==1 and zero.brake_start is None
    _,_,late=zero.select(-.1,.05,native_tick=32800,body=body,last_ctrl=ctrl,encoders=enc)
    assert late['brake_start']==32800 and late['braking_native']==0
    # A saved200-zero tail is not a negative intent and cannot reset memory.
    negatives=[]
    for name,changed in [('body_not_rest',dict(body=body[:3]+[.004,0.])),('steering_not_rest',dict(encoders=enc[:2]+[.04,0.])),('rear_not_zero',dict(last_ctrl=ctrl[:2]+[.02,.02]))]:
        q=copy.deepcopy(gate);args=dict(body=body,last_ctrl=ctrl,encoders=enc);args.update(changed)
        q.select(-.1,.05,native_tick=32600,**args)
        v,w,p=q.select(-.1,.05,native_tick=32800,**args)
        assert v==w==0 and not p['released'];negatives.append(name)
    q=copy.deepcopy(gate)
    q.select(-.1,.05,native_tick=32600,body=body,last_ctrl=ctrl,encoders=enc)
    v,w,p=q.select(-.04,.02,native_tick=32800,body=body,last_ctrl=ctrl,encoders=enc)
    assert [v,w]==[-.04,.02] and p['released'];negatives.append('cached_request_not_reused')
    try:q.select(-.04,.02,native_tick=32800,body=body,last_ctrl=ctrl,encoders=enc)
    except AssertionError:negatives.append('nonadvancing_tick')
    else:raise AssertionError('DUPLICATE_TICK_ACCEPTED')
    # Same path, state tube and voluntary wait0; the delay is forced by original
    # control memory. This is still nominal feedback, not a physical response.
    bridge=read(O/'OBSERVED_PREPARATION_BRIDGE.json')
    rear=np.asarray(bridge['nominal_rear_poses']);times=np.asarray(bridge['move_relative_times_s'])+2.
    offsets=np.linspace(-.1,.1,201);full=np.repeat(rear,201,axis=0);full[:,2]+=np.tile(offsets,len(rear))
    centers=full.copy();centers[:,:2]+=.3*np.c_[np.cos(full[:,2]),np.sin(full[:,2])]
    cell=np.floor(times/.1+1e-10).astype(int);indices=np.repeat(cell,201)
    swept=load('original_gear_timed_support','experiments/v1020_terminal_two_route_development/periodic_support.py')
    clipped=function('experiments/v1366_canonical_timed_lattice/build_polygons.py','clipped')
    distances=function('experiments/v934_rpccr_certified_recovery/polygon_geometry.py','distances')
    model=read(RAW/'CAUSAL_PREDICTION_MODEL.json');assert model['periodic']['source_tick']==32200
    polygons={};values=np.empty(len(full));support_error=0.
    for i in np.unique(indices):
        lower=model['last_observed_time']+max(0,i*.1-.22);upper=model['last_observed_time']+(i+1)*.1+.22
        bounds=swept.swept_bounds(model['periodic']['vertices'],lower,upper)+.1
        support_error=max(support_error,float(np.max(abs(bounds-independent_swept(model['periodic']['vertices'],lower,upper)))))
        polygon=clipped(np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)],bounds)
        polygons[str(i)]=polygon.tolist();mask=indices==i;values[mask]=distances(centers[mask],polygon)
    geometry=load('original_gear_static_footprint','experiments/v855_renewal_worker/exact_footprint.py');known=read(RAW/'physics/SETUP.json')['known']
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    static=geometry.pose_values(field,full)
    combined=np.minimum(values,static).reshape(len(rear),201);worst=np.argmin(combined,axis=1);distance_error=0.
    for t,k in enumerate(worst):
        q=t*201+int(k);distance_error=max(distance_error,abs(float(values[q])-scalar_distance(centers[q],polygons[str(indices[q])])))
    assert max(support_error,distance_error)<=1e-8
    continuous=bridge['continuous_interpolation_allowance_m'];angular=math.hypot(.74,.375)*.0005
    shifted_lower=float(combined.min())-.02-angular-continuous
    # During required zero-output hold, only a CONDITIONAL tube around final
    # rear pose is available; actual extra hold response has not been measured.
    hold_full=full[:201];hold_centers=centers[:201]
    lo=model['last_observed_time']+3.9-.22;hi=model['last_observed_time']+5.9+.22
    hold_support=swept.swept_bounds(model['periodic']['vertices'],lo,hi)+.1
    assert np.max(abs(hold_support-independent_swept(model['periodic']['vertices'],lo,hi)))<=1e-8
    hold_polygon=clipped(np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)],hold_support)
    hold_min=float(np.minimum(distances(hold_centers,hold_polygon),static[:201]).min())-.02-angular
    result=dict(models=0,physical_native=0,private_native=0,replay_native=0,
        scope='pure metadata transition reconstruction and conditional geometry; no new state/control physical replay',
        saved_metadata_rows_checked=len(journal),final_gear_memory=1,final_saved_tick=32600,
        old_zero_tail_does_not_clear_gear=True,mandatory_gear_brake_native=200,mandatory_minimum_gear_delay_s=2.,
        constant_feedback_probes_are_NOT_future_observations=True,software_probe_trace=trace,negative_cases=negatives,
        original_3p9s_move_start_does_not_include_required_gear_delay=True,
        uncorrected_nominal_clock_physical_use_allowed=False,
        voluntary_wait_s=0,nominal_shifted_move_start_s=5.9,nominal_shifted_total_s=float(times[-1]),
        conditional_shifted_moving_lower_m=shifted_lower,conditional_gear_hold_lower_m=hold_min,
        conditional_combined_lower_m=min(shifted_lower,hold_min),conditional_shifted_geometry_passed=min(shifted_lower,hold_min)>=.22,
        spatial_error_assumption=dict(rear_translation_m=.02,yaw_rad=.1),time_error_assumption_s=.2,
        time_error_and_moving_response_qualified=False,extra_gear_hold_response_qualified=False,
        complete_physical_admission=False,original_trajectory_and_endpoint_unchanged=True,
        shifted_interval_polygons=polygons,shifted_times_s=times.tolist(),
        independent_support_error_m=support_error,independent_limiting_geometry_error_m=distance_error,
        next_requirement='Pause or explicitly bind motion-profile time during GEAR_BRAKE_HOLD; prove actual release/velocity/braking envelopes instead of advancing the nominal clock during zeros.',
        wall_s=time.monotonic()-begin)
    assert all(sha(R/p)==h for p,h in frozen.items())
    target=O/'GEAR_CLOCK_DIAGNOSTIC.json';assert not target.exists()
    target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');assert read(target)==result
    print(json.dumps({k:v for k,v in result.items() if not isinstance(v,(list,dict))},allow_nan=False))


if __name__=='__main__':main()
