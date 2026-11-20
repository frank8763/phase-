"""Full original command/expiry/gear software chain; conditional pose geometry."""
import copy
import math
import os
from pathlib import Path
import signal
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R,O,RAW,read,sha,json,np,load,function,scalar_distance,SimpleNamespace
from audit_timed_nominal import independent_swept
from native_clock_contract import Timeline


def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('ZERO_MODEL600_STOP')));signal.alarm(600)
    begin=time.monotonic();frozen=read(O/'NATIVE_CLOCK_SOURCE_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in frozen.items())
    gate_module=load('original_clock_gear','experiments/v1346_measured_gear_handoff/gear_handoff.py')
    contract=load('original_clock_wire','experiments/v1288_baseline_interface/contract.py')
    expiry=load('original_clock_expiry','experiments/v1378_steering_response_32210/stamped_contract.py')
    final=read(R/'runs/v858_nav2_verified/v1378/steering_response/FINAL_PACKET.json')
    body=final['body'];ctrl=final['controller_memory']['last_ctrl'];enc=final['steering']['position']+final['steering']['velocity']
    start=np.array([body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]])
    goal=np.asarray(read(O/'ORIGINAL_SEGMENT_ALL_FUTURE_POLYGON.json')['original_segment_unchanged']['poses'][-1])
    length=float(np.linalg.norm(goal[:2]-start[:2]))
    def new():
        gate=gate_module.GearHandoff();gate.gear=1;gate.last_tick=32599
        return Timeline(gate,length)
    timeline=new();trace=[];sequence=-1;delivery=None;packet=None;wire_checked=0
    for tick in range(32600,34600):
        row=timeline.step(tick,body,ctrl,enc)
        now=1000.+(tick-32600)*.01  # Explicit synthetic unit-test clock.
        if row['callback']:
            sequence+=1;v,w=row['request']
            packet=dict(run_id='SOFTWARE_CLOCK_FIXTURE',sequence=sequence,issued_at=now,v=v,w=w)
            contract.command(packet,run_id=packet['run_id'],now=now,previous_sequence=sequence-1)
            delivery=dict(origin=dict(kind='SOFTWARE_CLOCK_FIXTURE',generated_monotonic=now),observation_sampled_at=now)
            wire_checked+=1
        fresh_v,fresh_w,proof=expiry.before_step(*row['request'],delivery,now)
        assert [fresh_v,fresh_w]==row['request'] and proof['fresh']
        contract.twist(*row['admitted'])
        trace.append(row)
        if row['state']=='DONE':break
    else:raise AssertionError('SOFTWARE_TIMELINE_NOT_COMPLETE')
    releases=[x for x in trace if x['gear_proof']['released']];assert len(releases)==1 and releases[0]['before_native']==32800
    assert all(x['admitted']==[0.,0.] and x['profile_phase_s'] is None for x in trace[:200])
    assert trace[200]['profile_phase_s']==.05 and trace[200]['admitted']==[-.005,.0025]
    assert sum(x['admitted']==[0.,0.] for x in trace[-200:])==200 and trace[-1]['zero_tail_native']==200
    # Explain the previous isolated-gear probe in the complete strict interface.
    wire_rejected=[]
    for v in [-.001,-.002,-.003,-.004]:
        try:contract.twist(v,-.5*v)
        except ValueError as e:assert str(e)=='ROTATION_WITHOUT_DRIVE';wire_rejected.append(v)
        else:raise AssertionError('CURVED_SUBTHRESHOLD_WIRE_ACCEPTED')
    negatives=[]
    stale=copy.deepcopy(delivery);stale['origin']['generated_monotonic']-=.201
    assert expiry.before_step(-.01,.005,stale,now)[:2]==(0.,0.);negatives.append('expired_source')
    future=copy.deepcopy(delivery);future['origin']['generated_monotonic']=now+.01
    try:expiry.before_step(-.01,.005,future,now)
    except AssertionError:negatives.append('future_source')
    else:raise AssertionError('FUTURE_SOURCE_ACCEPTED')
    bad=copy.deepcopy(packet);bad['sequence']=sequence
    try:contract.command(bad,run_id=bad['run_id'],now=now,previous_sequence=sequence)
    except ValueError:negatives.append('duplicate_command')
    else:raise AssertionError('DUPLICATE_COMMAND_ACCEPTED')
    probe=new()
    try:probe.step(32601,body,ctrl,enc)
    except AssertionError:negatives.append('skipped_native_clock')
    else:raise AssertionError('SKIPPED_NATIVE_ACCEPTED')
    # Complete nominal pose proxy uses the actual admitted request sequence,
    # including the nonzero release request and zero-order command holds.
    arc=np.array([x['nominal_arc_before_m'] for x in trace]+[trace[-1]['nominal_arc_after_m']])
    yaw=start[2]-.5*arc
    rear=np.c_[start[0]+(np.sin(yaw)-math.sin(start[2]))/-.5,
               start[1]-(np.cos(yaw)-math.cos(start[2]))/-.5,yaw]
    times=np.array([x['source_relative_time_s'] for x in trace]+[(trace[-1]['before_native']+1-32210)*.01])
    assert np.max(abs(np.diff(times)-.01))<1e-8
    endpoint_position=float(np.linalg.norm(rear[-1,:2]-goal[:2]));endpoint_heading=abs(math.atan2(math.sin(rear[-1,2]-goal[2]),math.cos(rear[-1,2]-goal[2])))
    offsets=np.linspace(-.1,.1,201);full=np.repeat(rear,201,axis=0);full[:,2]+=np.tile(offsets,len(rear))
    centers=full.copy();centers[:,:2]+=.3*np.c_[np.cos(full[:,2]),np.sin(full[:,2])]
    indices=np.repeat(np.floor(times/.1+1e-10).astype(int),201)
    model=read(RAW/'CAUSAL_PREDICTION_MODEL.json');assert model['periodic']['source_tick']==32200
    swept=load('clock_original_support','experiments/v1020_terminal_two_route_development/periodic_support.py')
    clipped=function('experiments/v1366_canonical_timed_lattice/build_polygons.py','clipped')
    distances=function('experiments/v934_rpccr_certified_recovery/polygon_geometry.py','distances')
    normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
    dynamic=np.empty(len(full));polygons={};support_error=0.
    for i in np.unique(indices):
        lower=model['last_observed_time']+max(0,i*.1-.22);upper=model['last_observed_time']+(i+1)*.1+.22
        support=swept.swept_bounds(model['periodic']['vertices'],lower,upper)+.1
        support_error=max(support_error,float(np.max(abs(support-independent_swept(model['periodic']['vertices'],lower,upper)))))
        polygon=clipped(normals,support);polygons[str(i)]=polygon.tolist();mask=indices==i;dynamic[mask]=distances(centers[mask],polygon)
    geometry=load('clock_original_static','experiments/v855_renewal_worker/exact_footprint.py');known=read(RAW/'physics/SETUP.json')['known']
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    static=geometry.pose_values(field,full);combined=np.minimum(dynamic,static).reshape(len(rear),201);worst=np.argmin(combined,axis=1);scalar_error=0.
    for t,k in enumerate(worst):
        q=t*201+int(k);scalar_error=max(scalar_error,abs(float(dynamic[q])-scalar_distance(centers[q],polygons[str(indices[q])])))
    assert max(scalar_error,support_error)<1e-8
    angular=math.hypot(.74,.375)*.0005
    continuous=(.1+math.hypot(.74,.375)*.05)*.01/2
    lower=float(combined.min())-.02-angular-continuous
    result=dict(models=0,physical_native=0,private_native=0,replay_native=0,
        qualification_scope='original wire/expiry/gear metadata with constant saved feedback; conditional command-arc geometry, not plant response',
        constant_feedback_not_future_measurements=True,synthetic_clock_not_physical_latency_measurement=True,
        exact_actual_start_tick=32600,actual_saved_gear_memory=1,source_coefficient_tick=32200,
        command_callback_native=5,command_packets_checked=wire_checked,software_native_decisions=len(trace),
        gear_hold_native=200,release_native=32800,release_request_m_s=-.005,reference_phase_at_release_s=.05,
        profile_clock_paused_during_hold=True,source_clock_never_paused=True,
        complete_zero_request_tail_native=200,zero_tail_is_software_only=True,
        interface_subthreshold_curve_requests_rejected=wire_rejected,
        earlier_isolated_gear_counterexample_not_full_pipeline_evidence=True,
        source_interface_and_gear_unchanged=True,negative_cases=negatives,
        nominal_arc_distance_m=-float(arc[-1]),original_nominal_length_m=length,
        command_proxy_endpoint_position_m=endpoint_position,command_proxy_endpoint_heading_rad=endpoint_heading,
        command_proxy_endpoint_passed=endpoint_position<=.12 and endpoint_heading<=.20,
        conditional_full_tube_lower_m=lower,conditional_full_tube_geometry_passed=lower>=.22,
        full_pose_cases=len(full),rear_translation_error_assumption_m=.02,yaw_error_assumption_rad=.1,time_error_assumption_s=.2,
        independent_support_error_m=support_error,independent_limiting_geometry_error_m=scalar_error,
        conditional_pose_reference='closed-form fixed-curvature arc from admitted request sums, not an executed or identified vehicle prediction',
        actual_moving_response_qualified=False,actual_acceleration_and_braking_qualified=False,
        physical_admission=False,control_allocation_qualification=False,new_physical_authority=False,
        next_gap='Saved-state exact allocator/encoder/control-memory qualification and response bounds for this concrete request schedule; today has no remaining physical slot.',
        relative_times_s=times.tolist(),command_arc_rear_poses=rear.tolist(),software_trace=trace,
        wall_s=time.monotonic()-begin)
    assert all(sha(R/p)==h for p,h in frozen.items())
    p=O/'NATIVE_CLOCK_COMMAND_CONTRACT.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');assert read(p)==result
    print(json.dumps({k:v for k,v in result.items() if not isinstance(v,(list,dict))},allow_nan=False))


if __name__=='__main__':main()
