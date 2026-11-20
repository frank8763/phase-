"""Pure-software requested-speed/gear-clock checks; not a plant qualification."""
import math
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R,O,read,sha,json,load


def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    frozen=read(O/'GEAR_PROFILE_SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in frozen.items())
    old=load('profile_original_gear','experiments/v1346_measured_gear_handoff/gear_handoff.py')
    final=read(R/'runs/v858_nav2_verified/v1378/steering_response/FINAL_PACKET.json')
    feedback=dict(body=final['body'],last_ctrl=final['controller_memory']['last_ctrl'],encoders=final['steering']['position']+final['steering']['velocity'])
    # Memory is reconstructed exactly by gear_clock_diagnostic from32600 saved
    # metadata rows; no plant or actuator is reconstructed in these probes.
    def gate():
        g=old.GearHandoff();g.gear=1;g.last_tick=32599;return g
    g=gate();naive=[]
    for offset in range(251):
        request=-min(.1,.1*offset*.01)
        v,w,p=g.select(request,-.5*request,native_tick=32600+offset,**feedback)
        naive.append(dict(native_tick=32600+offset,request_v=request,applied_v=v,proof=p))
    early=[x for x in naive if 0<abs(x['request_v'])<.005 and x['applied_v']!=0]
    release=next(x for x in naive if x['proof']['released'])
    start=next(x for x in naive if x['proof']['brake_start'] is not None)
    assert len(early)==4 and release['applied_v']==-.1
    assert start['native_tick']==32605 and release['native_tick']==32805
    assert release['native_tick']-start['native_tick']==200
    # Candidate-local software specification: explicit reverse intent at the
    # original classifier threshold, not an alteration of GearHandoff itself.
    # Its release command is NONZERO; actual startup response is unqualified.
    g=gate();intent=[]
    for offset in range(201):
        v,w,p=g.select(-.005,.0025,native_tick=32600+offset,**feedback)
        intent.append(dict(native_tick=32600+offset,request_v=-.005,applied_v=v,proof=p))
        if offset<200:assert v==w==0
        else:assert v==-.005 and p['released']
    result=dict(models=0,physical_native=0,private_native=0,replay_native=0,
        saved_input_native_tick=32600,constant_feedback_probes_not_future_measurements=True,
        naive_wallclock_speed_ramp=naive,subthreshold_nonzero_before_gear_hold=early,
        naive_brake_start_native=start['native_tick'],naive_release_native=release['native_tick'],naive_release_request_m_s=release['request_v'],
        defect_scope='source-level classifier treats |v|<.005 as no requested gear but returns nonzero v; saved V1378 only requested exact zero, so no new actual unsafe execution is asserted',
        original_gate_unchanged=True,proposed_explicit_reverse_intent=intent,
        proposed_release_request_m_s=-.005,proposed_release_requires_actual_response_qualification=True,
        requested_release_step_over_native_dt_m_s2=.005/.01,
        nominal_acceleration_assumption_m_s2=.1,request_step_is_NOT_measured_acceleration=True,
        pre_release_rule='fresh explicit reverse intent at |v|=.005 is evaluated by original gate; only its zero output may reach the allocator until actual release',
        release_rule='bind profile clock to admitted release and include the -.005 release request explicitly; do not claim zero initial request or measured acceleration from a nominal ramp',
        timing_rule='forecast/source clock always advances on actual native ticks; motion-profile clock must not run through GEAR_BRAKE_HOLD; extra delay needs covered occupancy',
        measured_required=['fresh source/command binding','actual gear release proof','front position and velocity readiness','rear reference/body speed/yaw response','actual braking/200 zero tail','full state/ctrl/mocap <=1e-8 replay'],
        complete_physical_admission=False,moving_response_qualified=False,
        software_design_only=True,no_new_candidate_or_model_launch=True,
        unresolved='Explicit-intent release introduces a -.005 request from rest; actual response and a matching start/end/time tube must be qualified before execution. Existing shifted geometry is conditional, not this unexecuted command schedule certificate.')
    assert all(sha(R/p)==h for p,h in frozen.items())
    p=O/'GEAR_PROFILE_CONTRACT.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');assert read(p)==result
    print(json.dumps({'models':0,'subthreshold_pass_count':len(early),'naive_release_request_m_s':release['request_v'],'naive_first_hold_native':start['native_tick'],'naive_release_native':release['native_tick'],'explicit_intent_software_hold_native':200,'release_request_m_s':-.005,'physical_admission':False}))


if __name__=='__main__':main()
