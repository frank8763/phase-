"""Identity/queue transaction and exact finite-controller software checks."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
from types import SimpleNamespace
from session import prepare_request,Session,R
from method_dispatch import choose,ReverseBridge

C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));O.mkdir(exist_ok=False)
    source=json.loads((R/'runs/v1398_current_event_witness/peer_qualification02/CURRENT_INPUT.json').read_text())
    b=source['origin']['body'];tick=source['origin']['native_tick'];now=100.
    wire=dict(schema=1,run_id='session-software-fixture',sequence=0,sampled_at=now,body=b,ranges_m=[3.]*32,native_tick=tick,sim_time=source['origin']['sim_time'],sensor_frame=dict(native_tick=tick,time=source['origin']['sim_time'],xy=b[:2],yaw=b[2],sampled_at=now))
    feedback=dict(native_tick=tick,sim_time=wire['sim_time'],body=b,encoders=[0.,0.,0.,0.],last_ctrl=[0.,0.,0.,0.],integral=0.,parked_target=None,steering_motion_active=False,gear_memory=dict(gear=1,brake_start=None,last_tick=tick-1))
    envelope=dict(kind='ROUTE_ACTUAL_FRAME',wire=wire,feedback=feedback,evidence_state_sha256='0'*64)
    snapshot=dict(model='PERIODIC',online_actor_truth=False,class_assumptions=dict(amplitude_m=.25,maximum_center_displacement_m=.5,omega_rad_s=.32,norm_speed_m_s=.08),periodic=source['bridge_forecast']['input_periodic'])
    tracker=SimpleNamespace(snapshot=lambda:copy.deepcopy(snapshot));segment=source['next_segment'];rear=[b[0]-.3*math.cos(b[2]),b[1]-.3*math.sin(b[2]),b[2]];p=segment['poses'][0]
    geometry=dict(start_distance_m=math.dist(rear[:2],p[:2]),start_heading_rad=abs(math.atan2(math.sin(rear[2]-p[2]),math.cos(rear[2]-p[2]))),minimum_clearance_m=.21)
    packet=prepare_request(envelope,segment,geometry,tracker,run_id=wire['run_id'],event_index=0,brake_start=0,now=now);session=Session(packet)
    base=dict(run_id=wire['run_id'],event_index=0,request_sha256=session.request_sha256,input_sha256='1'*64,certificate_sha256='2'*64)
    negative=[]
    def reject(name,fn):
        try:fn()
        except AssertionError:negative.append(name)
        else:raise AssertionError('BAD_TRANSACTION_ACCEPTED:'+name)
    complete=dict(base,kind='BRIDGE_COMPLETE',complete_actual_native_coverage=True,complete200_applied_zero_tail=True,source_control_state_gates_passed=True,endpoint_position_m=.1,endpoint_heading_rad=.1)
    reject('complete_before_certificate',lambda:session.accept(complete))
    ready=dict(base,kind='BRIDGE_CERTIFICATE_READY',model_generation_passed=True,independent_model_audit_passed=True)
    reject('wrong_event',lambda:session.accept(dict(ready,event_index=1)))
    reject('generation_without_audit',lambda:session.accept(dict(ready,independent_model_audit_passed=False)))
    assert not session.accept(ready)['consume_segment']
    reject('changed_certificate_hash',lambda:session.accept(dict(base,kind='BRIDGE_RPP_READY',certificate_sha256='3'*64)))
    assert session.accept(dict(base,kind='BRIDGE_RPP_READY'))['install_original_RPP_path']
    reject('incomplete_actual_zero_tail',lambda:session.accept(dict(complete,complete200_applied_zero_tail=False)))
    reject('negative_endpoint_error',lambda:session.accept(dict(complete,endpoint_position_m=-1.)))
    assert session.accept(complete)['consume_segment']and session.consumed
    reject('consume_same_segment_twice',lambda:session.accept(complete))
    entry=json.loads((R/'experiments/v1383_exact_timed_handoff/ENTRY.json').read_text());request=copy.deepcopy(packet['request']);request['next_segment']=entry['target_segment'];request['event']['body']=[0.,0.,0.,0.,0.];request['event']['geometry']=dict(start_distance_m=.075,start_heading_rad=.035,minimum_clearance_m=.14)
    method=choose(request);assert method['method']=='ORIGINAL_BOUNDED_STEERING_THEN_GEAR_RELEASE_TIMED_REVERSE'
    reject('same_sign_reverse_has_no_original_release',lambda:choose(dict(request,actual=dict(request['actual'],feedback=dict(feedback,gear_memory=dict(gear=-1,brake_start=None,last_tick=tick-1))))))
    target=-.5;pair=[math.atan(.6*target/(1-.27*target)),math.atan(.6*target/(1+.27*target))];enc=[*pair,0.,0.];memory=[*pair,0.,0.]
    sequences=[]
    for offset in [0,12345]:
        control=ReverseBridge(method['task']);outputs=[]
        outputs.append(control.select([0.,0.,0.,0.,0.],100+offset,enc,memory)[:2]);outputs.append(control.select([0.,0.,0.,0.,0.],120+offset,enc,memory)[:2])
        control.observe_gear(320+offset,dict(released=True,requested_gear=-1,braking_native=200))
        outputs.append(control.select([0.,0.,0.,0.,0.],325+offset,enc,memory)[:2]);sequences.append(outputs)
    assert sequences[0]==sequences[1]
    proof=dict(passed=True,scope='current snapshot transaction and original finite method software only',synthetic_envelope_not_measured_fresh=True,
               current_full_coefficient_snapshot_bound=True,segment_only_consumed_after_complete_native_receipt=True,negative_cases=negative,
               original_reverse_steering_and_timed_sources_reused=True,clock_translation_invariant=True,
               models=0,analytical_native=0,physical_native=0,replay_native=0,physical_admission=False,actual_route_not_qualified=True)
    (O/'SESSION_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n')
    files=[p for p in C.glob('*')if p.is_file()]
    (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files},qualification='runs/v1404_route_bridge_session/SESSION_QUALIFICATION.json',physical_admission=False),indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':main()
