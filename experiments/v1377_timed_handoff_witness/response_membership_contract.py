"""Offline measured-sample membership check, never physical admission.

Discrete, monotone reference matching is a sufficient test for the previously
declared conditional pose/time tube. It does not prove unmeasured future motion,
braking reserves, between-native dynamics, source authenticity or full replay.
"""
import math


def rear(body):
    return [body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]]


def audit(samples,reference,*,origin_tick,source_tick,evidence_kind,stage):
    assert evidence_kind in ['ACTUAL_SAVED_PREPARATION','SOFTWARE_REFERENCE_FIXTURE'],'UNDECLARED_EVIDENCE_KIND'
    assert stage in ['PREPARATION','MOVING'],'UNDECLARED_STAGE'
    assert stage!='MOVING' or evidence_kind=='SOFTWARE_REFERENCE_FIXTURE','NO_ACTUAL_MOVING_EVIDENCE_REGISTERED'
    assert type(origin_tick) is int and type(source_tick) is int and source_tick<=origin_tick,'FUTURE_SOURCE'
    assert len(samples)==len(reference)>=201,'NATIVE_COVERAGE_LENGTH'
    assert all(type(r['native_tick']) is int and r['native_tick']==origin_tick+i for i,r in enumerate(samples)),'NATIVE_TICKS_NOT_CONTIGUOUS'
    assert all(abs(r['sim_time']-r['native_tick']*.01)<=1e-8 for r in samples),'ACTUAL_SIM_TIME_BINDING'
    assert all(abs(r['relative_time_s']-(r['native_tick']-32210)*.01)<=1e-8 for r in samples),'RELATIVE_SOURCE_CLOCK_BINDING'
    assert all(len(r['body'])==5 and len(r['ctrl'])==4 and len(r['steering_velocity'])==2 for r in samples),'ACTUAL_FEEDBACK_SHAPE'
    assert all(math.isfinite(x) for r in samples for x in [*r['body'],*r['ctrl'],*r['steering_velocity']]),'NONFINITE_ACTUAL_FEEDBACK'
    assert all(len(r['rear'])==3 and all(math.isfinite(x) for x in r['rear']) for r in reference),'REFERENCE_POSE_SHAPE'
    assert all(abs(r['relative_time_s']-(origin_tick+i-32210)*.01)<=1e-8 for i,r in enumerate(reference)),'REFERENCE_CLOCK_CHANGED'
    # Greedy earliest feasible reference index is complete for nondecreasing
    # discrete-index correspondence: choosing it cannot block a later sample.
    previous=0;witness=[];maximum_position=maximum_yaw=maximum_time=0.
    for i,row in enumerate(samples):
        actual=rear(row['body']);candidates=[]
        lower=max(previous,i-20);upper=min(len(reference)-1,i+20)
        if i==0:lower=upper=0
        if i==len(samples)-1:lower=upper=len(reference)-1
        for j in range(lower,upper+1):
            ref=reference[j];dt=abs(row['relative_time_s']-ref['relative_time_s'])
            dp=math.dist(actual[:2],ref['rear'][:2]);dy=abs(math.atan2(math.sin(actual[2]-ref['rear'][2]),math.cos(actual[2]-ref['rear'][2])))
            if dt<=.2+1e-8 and dp<=.02+1e-8 and dy<=.1+1e-8:candidates.append((j,dp,dy,dt))
        assert candidates,'POSE_TIME_TUBE_NO_MONOTONE_MATCH_AT_'+str(row['native_tick'])
        j,dp,dy,dt=candidates[0];previous=j
        maximum_position=max(maximum_position,dp);maximum_yaw=max(maximum_yaw,dy);maximum_time=max(maximum_time,dt)
        witness.append(j)
    assert all(r['command']==[0.,0.] for r in samples[-200:]),'SHORT_OR_NONZERO_STOP_TAIL'
    assert max(abs(x) for x in samples[-1]['body'][3:])<=.003,'FINAL_BODY_NOT_REST'
    assert max(abs(x) for x in samples[-1]['steering_velocity'])<=.03,'FINAL_STEERING_NOT_REST'
    assert max(abs(x) for x in samples[-1]['ctrl'][2:])<=1e-10,'FINAL_REAR_TARGET_NOT_ZERO'
    return dict(sample_membership_passed=True,stage=stage,evidence_kind=evidence_kind,
        samples=len(samples),reference_indices=witness,
        maximum_rear_position_residual_m=maximum_position,maximum_yaw_residual_rad=maximum_yaw,maximum_phase_time_residual_s=maximum_time,
        continuous_response_bound_proven=False,physical_admission=False,
        actual_moving_response_qualified=False,
        source_authenticity_and_full_replay_must_be_separately_audited=True)
