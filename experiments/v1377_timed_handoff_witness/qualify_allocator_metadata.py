"""Re-evaluate controller metadata, no physical state/control replay or models."""
import copy
import math
import os
from pathlib import Path
import signal
import sys
import time
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R,O,read,sha,json,np
from allocator_metadata_binding import binding,FORBIDDEN_PREVIEW_CALLS
from native_clock_contract import Timeline


def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('ZERO_MODEL600_STOP')));signal.alarm(600)
    begin=time.monotonic();frozen=read(O/'ALLOCATOR_METADATA_SOURCE_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in frozen.items())
    raw=R/'runs/v858_nav2_verified/v1378/steering_response'
    journal=read(raw/'APPLIED_JOURNAL.json');initial=read(raw/'INITIAL_PACKET.json');final=read(raw/'FINAL_PACKET.json');setup=read(raw/'physics/SETUP.json')
    assert all(abs(r['request'][0])<=.1+1e-12 and abs(r['request'][0]-.125)>1e-12 for r in journal)
    Adapter=binding();assert Path(Adapter.compute.__code__.co_filename)==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
    limits=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])*.01;cursor=[None]
    owner=object.__new__(Adapter)
    # Same literal setup as the original V856 constructor, without calling the
    # model/CommandMap constructor. SETUP supplies original physical limits.
    owner.wheelbase=.6;owner.track=.54;owner.radius=.12;owner.center_limit=.42722137342572125
    owner.max_curvature=math.tan(owner.center_limit)/owner.wheelbase;owner.dt=.01;owner.virtual_rate=.6
    owner.last=np.asarray(initial['controller_memory']['last_ctrl']);owner.integral=initial['controller_memory']['integral']
    owner.parked_target=None;owner._steering_motion_active=False;owner._speed_episode=False
    owner.commands=SimpleNamespace(lower=limits[:,0],upper=limits[:,1],rate=np.asarray(setup['slew_per_second'])*.08,
        legal=lambda u:bool(np.isfinite(u).all() and (u>=limits[:,0]-1e-10).all() and (u<=limits[:,1]+1e-10).all()))
    owner.encoders=lambda:np.asarray(cursor[0])
    memory_error=control_error=0.
    for i,row in enumerate(journal):
        cursor[0]=row['encoders'];assert not owner._speed_episode
        memory_error=max(memory_error,float(np.max(abs(owner.last-row['last_ctrl']))),abs(owner.integral-row['integral']))
        assert owner._steering_motion_active==row['steering_motion_active_before']
        owner.parked_target=row['parked_target']
        u=owner.compute(*row['request'][:2],*row['body'][3:],False)
        expected=journal[i+1]['last_ctrl'] if i+1<len(journal) else final['controller_memory']['last_ctrl']
        control_error=max(control_error,float(np.max(abs(u-expected))))
    assert max(memory_error,control_error)<=1e-8 and not FORBIDDEN_PREVIEW_CALLS
    assert abs(owner.integral-final['controller_memory']['integral'])<=1e-8
    saved_owner=copy.deepcopy(owner)
    # The concrete schedule below uses CONSTANT measured feedback, intentionally
    # a software fixture. It supplies no physical movement/settling evidence.
    from snapshot_diagnostic import load
    gear=load('allocator_original_gear','experiments/v1346_measured_gear_handoff/gear_handoff.py')
    gate=gear.GearHandoff();gate.gear=1;gate.last_tick=32599
    prior=read(O/'NATIVE_CLOCK_COMMAND_CONTRACT.json');length=prior['original_nominal_length_m'];timeline=Timeline(gate,length)
    body=final['body'];enc=final['steering']['position']+final['steering']['velocity'];cursor[0]=enc
    metadata=[];maximum_slew=0.;front_error=0.;rear_error=0.;peak_rear=0.
    for old in prior['software_trace']:
        assert not owner._speed_episode
        row=timeline.step(old['before_native'],body,owner.last.tolist(),enc)
        assert row['request']==old['request'] and row['admitted']==old['admitted'] and row['state']==old['state']
        previous=owner.last.copy();owner.parked_target=None
        u=owner.compute(*row['admitted'],*body[3:],False)
        assert owner.commands.legal(u) and np.max(abs(u-previous)-rate)<=1e-10
        maximum_slew=max(maximum_slew,float(np.max(abs(u-previous)/.01)))
        tangent=np.tan(u[:2]);ks=np.array([tangent[0]/(.6+.27*tangent[0]),tangent[1]/(.6-.27*tangent[1])])
        front_error=max(front_error,float(abs(ks[0]-ks[1])))
        k=float(ks.mean());common=float(u[2:].mean());factors=np.array([1-.27*k,1+.27*k])
        rear_error=max(rear_error,float(np.max(abs(u[2:]-common*factors))));peak_rear=max(peak_rear,float(np.max(abs(u[2:]))))
        if row['release_native'] is None:assert np.max(abs(u[2:]))==0.
        metadata.append(dict(before_native=row['before_native'],request=row['request'],admitted=row['admitted'],
            ctrl=u.tolist(),integral=float(owner.integral),mode=owner.mode,gear_proof=row['gear_proof'],state=row['state']))
    assert timeline.state=='DONE' and timeline.zero_steps==200 and max(abs(x) for x in owner.last[2:])==0
    assert max(front_error,rear_error)<=1e-8 and not FORBIDDEN_PREVIEW_CALLS
    negative=[]
    for name,command,changed in [('reverse_entry_not_rest',[-.005,.0025],[.004,0.]),('nonfinite_body',[-.005,.0025],[math.nan,0.])]:
        candidate=copy.deepcopy(saved_owner)
        try:candidate.compute(*command,*changed,False)
        except (AssertionError,ValueError):negative.append(name)
        else:raise AssertionError('UNSAFE_ALLOCATOR_INPUT_ACCEPTED '+name)
    candidate=copy.deepcopy(saved_owner);candidate.last[0]+=.01
    try:candidate.compute(-.005,.0025,*body[3:],False)
    except AssertionError:negative.append('uncoordinated_previous_front')
    else:raise AssertionError('UNCOORDINATED_FRONT_ACCEPTED')
    assert sorted(os.sched_getaffinity(0))==[4]
    assert not any(name in sys.modules for name in ['mujoco','vehicle','torch','physical','factory','rclpy'])
    result=dict(passed=True,models=0,physical_native=0,private_native=0,replay_native=0,
        qualification_scope='actual original allocator methods on controller metadata only; no vehicle/model constructor or predictor call',
        constructor_not_called=True,prediction_calls=0,scope_limited_to_original_unguarded_speed_episode=True,
        unused_prediction_import_excluded=True,controller_method_source_unchanged=True,
        historical_metadata_rows_checked=len(journal),historical_control_error=control_error,historical_memory_error=memory_error,
        concrete_schedule_metadata_calls=len(metadata),constant_measured_feedback_not_actual_moving_response=True,
        original_limits_slew_front_rear_coordination_passed=True,front_curvature_coordination_error=front_error,rear_coordination_error=rear_error,
        maximum_individual_actuator_slew_per_s=maximum_slew,maximum_rear_target_rad_s=peak_rear,
        final_rear_targets_zero=True,software_zero_request_tail_native=200,negative_cases=negative,
        controller_metadata=metadata,physical_admission=False,actual_tracking_acceleration_braking_timing_qualified=False,
        no_stage_access=True,cpu_affinity=[4],wall_s=time.monotonic()-begin)
    assert all(sha(R/p)==h for p,h in frozen.items())
    p=O/'CONCRETE_ALLOCATOR_METADATA_QUALIFICATION.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');assert read(p)==result
    print(json.dumps({k:v for k,v in result.items() if not isinstance(v,(list,dict))},allow_nan=False))


if __name__=='__main__':main()
