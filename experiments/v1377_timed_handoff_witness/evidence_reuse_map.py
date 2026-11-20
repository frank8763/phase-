"""Explicit claim/evidence map for the existing candidate, no experiment launch."""
import json
import math
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R,O,read,sha


def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    frozen=read(O/'EVIDENCE_MAP_SOURCE_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in frozen.items())
    sources={};rows=[]
    for version,name in [(1375,'actual_capture_component'),(1376,'prepared_capture_component'),(1378,'steering_response_32210')]:
        base=R/f'runs/v{version}_{name}'
        completion=read(base/'COMPLETION.json');account=read(base/'ACCOUNTING.json')
        assert completion['closed'] and completion['new_navigation']==0 and completion['source_unchanged']
        assert account['new_navigation']==0 and account['unknown']==[]
        sources[version]=dict(completion=completion,accounting=account,finalized=read(base/'FINALIZED.json'),path=str(base.relative_to(R)))
        for row in account['rows']:rows.append(dict(row,version=version))
    assert len(rows)==4
    assert sum(x['actual_total_native'] for x in rows)==64600
    assert sum(x['historical_reconstruction_native'] for x in rows)==60380
    assert sum(x['new_component_native'] for x in rows)==4220
    assert sum(x['own_replay_native'] for x in rows)==64600
    assert sum(x['canonical_vehicle_initializations'] for x in rows)==4
    assert all(x['internal_factory_model_constructions'] is None for x in rows)
    assert not sources[1375]['completion']['passed'] and sources[1375]['completion']['unexecuted']==['capture_repeat']
    assert sources[1376]['completion']['passed'] and len(sources[1376]['accounting']['rows'])==2
    assert sources[1376]['finalized']['capture_component_pair_passed']
    assert sources[1378]['completion']['passed'] and len(sources[1378]['accounting']['rows'])==1
    assert sources[1378]['finalized']['steering_response_passed']
    clock=read(O/'NATIVE_CLOCK_COMMAND_CONTRACT.json');allocator=read(O/'CONCRETE_ALLOCATOR_METADATA_QUALIFICATION.json')
    response=read(O/'RESPONSE_MEMBERSHIP_QUALIFICATION.json');tail=read(O/'ACTION_TAIL_QUALIFICATION.json')
    assert clock['conditional_full_tube_geometry_passed'] and clock['physical_admission'] is False
    assert allocator['passed'] and allocator['physical_admission'] is False and allocator['prediction_calls']==0
    assert response['passed'] and not response['actual_moving_response_qualified']
    assert tail['passed'] and tail['full_action_wrapper_required'] and not tail['physical_admission']
    fixed=read(O/'FIXED_INPUTS.json');assert fixed['source_native_tick']==32210 and fixed['causal_coefficient_source_tick']==32200
    assert all(sha(R/p)==h for p,h in fixed['files'].items())
    def claim(key,status,evidence,permits,does_not_permit,missing=None):
        return dict(id=key,status=status,evidence=evidence,can_reuse_for=permits,
            cannot_promote_to=does_not_permit,missing=missing or [])
    claims=[
        claim('original9390_pose_capture_pair','ACTUAL_COMPONENT_PAIR_PASSED',
            ['runs/v1376_prepared_capture_component/COMPLETION.json','runs/v1376_prepared_capture_component/FINALIZED.json'],
            ['exact fixed9390 pose-capture response and same-version full repeat'],
            ['full9390 next-segment continuation','arbitrary initial steering states','independent fresh navigation sample']),
        claim('original32210_steering_preparation','ACTUAL_SINGLE_COMPONENT_PASSED',
            ['runs/v1378_steering_response_32210/COMPLETION.json','runs/v1378_steering_response_32210/FINALIZED.json'],
            ['exact saved32210 zero-drive steering190+stop200 response; resulting32600 state'],
            ['extra200 gear-hold physical response','moving tracking/braking/time bound','complete same-input repeat']),
        claim('concrete_request_clock','SOFTWARE_QUALIFIED',
            ['runs/v1377_timed_handoff_witness/NATIVE_CLOCK_COMMAND_CONTRACT.json'],
            ['original wire/expiry/gear logical compatibility for this fixed request schedule'],
            ['actual release time','measured speed acceleration braking','physical source delivery performance']),
        claim('original_allocator_metadata','SOFTWARE_QUALIFIED_SCOPED',
            ['runs/v1377_timed_handoff_witness/CONCRETE_ALLOCATOR_METADATA_QUALIFICATION.json'],
            ['exact saved control-memory re-evaluation; fixed <=.1 unguarded branch target legality'],
            ['predicted vehicle states','physical encoder/body tracking','other allocator branches']),
        claim('space_time_geometry','CONDITIONAL_GEOMETRY_PASSED',
            ['runs/v1377_timed_handoff_witness/NATIVE_CLOCK_COMMAND_CONTRACT.json'],
            ['full footprint conditional clearance for registered request-arc reference'],
            ['empirically qualified response tube','future recursive safety','complete arrival']),
        claim('response_sample_and_action_audit','SOFTWARE_QUALIFIED',
            ['runs/v1377_timed_handoff_witness/RESPONSE_MEMBERSHIP_QUALIFICATION.json','runs/v1377_timed_handoff_witness/ACTION_TAIL_QUALIFICATION.json'],
            ['sample monotone phase membership and N actions/N+1 states tail rejection logic'],
            ['new actual response observations','continuous-time invariant proof','authenticity/model/contact/replay replacement']),
        claim('full32210_handoff','NOT_QUALIFIED',[],[],['full route navigation admission'],
            ['actual exact schedule gear-wait/move/brake/tail','measured spatial/time response bounds','full independent original control/contact/source/model/state/replay evidence','complete actual same-input repeat']),
        claim('full9390_handoff','NOT_QUALIFIED',[],[],['full route navigation admission'],
            ['post-capture complete executable causal next-segment continuation','complete actual continuation main and successful repeat with all original gates']),
        claim('WE_dynamic_main_repeat','UNEXECUTED',[],[],['new24/comparison conclusion'],
            ['both full handoffs independently qualified and finalized','new authorized bounded model scope after today slot exhaustion']),
    ]
    required_inputs=[
        'original same-task canonical t0/model/map/actor/noise/sensor and exact frozen control/source closure',
        'full qpos/qvel/ctrl/mocap and controller/gear/sampling memory reconstructed from native0; no root-state injection',
        'original32200 causal coefficients and <=32210 observations, original endpoint; no future truth as controller input',
        'complete request sequence with source and reference clocks separately bound, release intent and low-speed cutoff explicit',
        'full-horizon spatial/time and braking/steering-response witness with genuinely supported error bounds',
        'fresh bounded physical authorization, available component slots, root deadline and original execution isolation/lock',
    ]
    required_outputs=[
        'all native state/control/mocap/encoder/body/contacts and root/time guard records including historical prefix and full tail',
        'actual observation acquisitions/command origin/delivery/expiry, causal coefficient provenance and freshness bindings',
        'gear memory/hold/release and actual speed/steering readiness; N applied transitions with N+1 states',
        'actual rear/yaw/time response against the precise registered reference including move/brake/stop; report any refusal/failure',
        'original .12m/.20rad terminal, .22 predictive/.15 physical, self/legal control/slew and full200 actual zero-tail checks',
        'full qpos/qvel/ctrl/mocap <=1e-8 own replay, exact/unknown private/history/new/replay/init accounting',
        'independent producer-compatible complete audit, frozen sources/sourceSHA/archive memberSHA/32MiB reassembly readback FINALIZED',
        'success-dependent complete actual repeat kept distinct from independent navigation confirmation',
    ]
    result=dict(models=0,physical_native=0,private_native=0,replay_native=0,
        registered_candidate='TIME_BOUND_NEXT_SEGMENT',new_scientific_candidates=0,
        claims=claims,physical_attempt_rows=rows,
        day_counts=dict(components=4,component_limit=4,navigations=0,actual_native=64600,historical_native=60380,new_component_native=4220,own_replay_native=64600,canonical_initializations=4,internal_factory_constructions=None),
        required_actual_inputs=required_inputs,required_actual_outputs=required_outputs,
        actual_moving_witness=None,full9390_handoff_qualified=False,full32210_handoff_qualified=False,
        physical_admission=False,models_authorized=False,deadline_unix=1795165200,storage_limit_bytes=2147483648,
        old_failures_and_unexecuted_preserved=True,
        no_more_software_fixture_tests_can_supply_missing_actual_motion=True,
        software_preparation_boundary='core existing-candidate request/clock/allocator/audit/conditional geometry and missing-evidence inventory complete; do not grow new candidates or rerun qualification fixtures to imply physical progress',
        next_work='read-only consistency of this closure and existing source/evidence; targeted zero-model correction only on concrete newly found issue. No new model task today.',
        input_sha256={p:h for p,h in frozen.items()})
    assert all(sha(R/p)==h for p,h in frozen.items())
    p=O/'EVIDENCE_REUSE_MAP.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');assert read(p)==result
    print(json.dumps(dict(passed=True,claims=len(claims),physical_attempts=4,actual_native=64600,own_replay_native=64600,new_models=0,physical_admission=False,core_software_preparation_complete=True)))


if __name__=='__main__':main()
