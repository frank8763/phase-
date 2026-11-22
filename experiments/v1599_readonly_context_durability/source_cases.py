"""Unclosed method12 source interfaces, explicitly SOFTWARE, never physics."""
import copy
import hashlib
import struct
from pathlib import Path
from types import SimpleNamespace as NS


def run(c,source,target,save,refused):
    tracker=c.load('v1599_target_signed_tracker',c.C/'tracker.py')
    policy_proofs=[]
    old=c.R/'runs/v1587_complete_runtime_source/source_target'
    for name in ('POLICY_1.json','POLICY_TERMINAL_1.json','REFUSAL_pending_reselect_1.json'):
        path=old/name;assert c.sha(path)==c.read(c.C/'REUSE_INPUTS.json')[str(path.relative_to(c.R))]
    policy_proofs.append(dict(gear=1,saved_decision_prefix_reused=True,complete_old_target_passed=False))
    for gear,endpoint in [(-1,[-1.,0.,0.])]:
        segment=dict(gear=gear,poses=[[0.,0.,0.],endpoint])
        p=tracker.SegmentTracker(segment,origin_body=[.3,0.,0.,0.,0.],origin_native=0,origin_sim_time=0.)
        d=p.select([.3,0.,0.,0.,0.],native_tick=0,sim_time=0.)
        assert abs(d['raw_row'][0])<=1e-14 and d['raw_row'][1:]==[.08 if gear==1 else -.03,0]
        refused('pending_reselect_'+str(gear),lambda:p.select([.3,0.,0.,0.,0.],native_tick=5,sim_time=.05))
        path=target/('POLICY_'+str(gear)+'.json')
        save(path,dict(scope='SOFTWARE_POLICY_NO_MODEL',decision=d,committed=False))
        assert c.read(path)['decision']==d
        p.commit(d,applied_native=5,applied_request_receipts_sha256=c.sha(path))
        body=[endpoint[0]+.3,endpoint[1],endpoint[2],0.,0.]
        terminal=p.select(body,native_tick=5,sim_time=.05)
        assert terminal['terminal_requested'] and terminal['body_request']==[0.,0.]
        save(target/('POLICY_TERMINAL_'+str(gear)+'.json'),dict(scope='SOFTWARE_NOT_ARRIVAL',decision=terminal))
        p.commit(terminal,applied_native=5,applied_request_receipts_sha256=c.sha(target/('POLICY_TERMINAL_'+str(gear)+'.json')))
        policy_proofs.append(dict(gear=gear,decision_sha256=c.sha(path),progress=p.progress))
    refused('unqualified_entry_capture',lambda:tracker.SegmentTracker(dict(gear=1,poses=[[0.,0.,0.],[1.,0.,0.]]),origin_body=[.5,0.,0.,0.,0.],origin_native=0,origin_sim_time=0.))
    p=tracker.SegmentTracker(dict(gear=1,poses=[[0.,0.,0.],[1.,0.,0.]]),origin_body=[.3,0.,0.,0.,0.],origin_native=0,origin_sim_time=0.)
    d=p.select([.3,0.,0.,0.,0.],native_tick=0,sim_time=0.)
    refused('commit_partial_receipts',lambda:p.commit(d,applied_native=4,applied_request_receipts_sha256='a'*64))
    assert p.failed and p.progress==0.
    save(target/'POLICY_REFUSAL.json',dict(scope='SOFTWARE',failed=p.failed,progress=p.progress,pending=p.pending))

    # Explicit synthetic schema values. No actual capture/provider update is
    # rerun, and no synthetic scan is delivered to a controller or a model.
    binder=c.load('v1599_target_current_method',c.C/'current_input.py')
    registration=c.read(c.R/'runs/v1577_goal_bound_segment_bridge/SCIENTIFIC_REVISION_REGISTRATION.json')
    tick=100;full=dict(time=1.,qpos=[0.],qvel=[0.],ctrl=[0.],mocap_pos=[],mocap_quat=[])
    packet=dict(native_tick=tick,sim_time=1.,body=[.3,0.,0.,0.,0.],steering=dict(position=[0.,0.],velocity=[0.,0.],native_tick=tick,measured_at=123.),body_measured_at=123.,controller_memory=dict(last_ctrl=[0.,0.,0.,0.],integral=0.),coupled_episode=False,steering_motion_active=False,parked_target=None)
    snapshot=dict(explicit_SOFTWARE_SCHEMA_ONLY=True)
    request=dict(run_id='SOFTWARE_METHOD_BINDING',event_index=0,event=dict(kind='CUSP_NEXT_SEGMENT_CHECK'),actual=dict(evidence_state_sha256=c.digest(full)),causal_forecast=dict(coefficient_snapshot_sha256=c.digest(snapshot)),next_segment=dict(gear=1,poses=[[0.,0.,0.],[1.,0.,0.]]))
    request['request_sha256']=c.digest(request)
    causal=dict(request_sha256=request['request_sha256'],run_id=request['run_id'],covered_native=tick,snapshot=snapshot,snapshot_sha256=c.digest(snapshot))
    mode=dict(covered_native=tick,coupled_episode=False,steering_motion_active=False,parked_target=None)
    gear=dict(gear=1,last_tick=tick-1,brake_start=None)
    capture=dict(role='CAPTURED_SOURCE_ONLY_NOT_METHOD_INPUT',physical_permission=False,numerical_permission=False,packet=packet,fullstate=full,causal_source=causal,mode_memory=mode,gear_memory=gear)
    proof=dict(passed=True,source_only=True,first_error=None,frozen_source_manifest_sha256=c.digest(source),current_packet_sha256=c.digest(packet),before_fullstate=full,before_fullstate_sha256=c.digest(full),fullstate_projection=dict(passed=True),canonical_receipt_content=dict(complete_prefix_native=tick),causal_content=dict(all_recorded_inputs_bound_to_actual_sent_wires=True),causal_source=causal)
    def describe(cap=capture,req=request,pr=proof,denied=False):
        def store(value):
            if denied:raise OSError('SOFTWARE_BINDING_PROOF_DENIED')
            save(target/('BINDING_PROOF_%03d.json'%describe.count),dict(scope='SOFTWARE_SCHEMA_NOT_ACTUAL_CAPTURE',proof=value))
            describe.count+=1
        return binder.describe(cap,req,pr,registration=registration,registration_sha256=c.digest(registration),source_manifest_sha256=c.digest(source),save_proof=store)
    describe.count=0
    method=describe();assert method['models_authorized']is method['physical_permission']is False
    assert method['actual_capture_runtime_qualified']is False
    save(target/'SOFTWARE_METHOD.json',dict(scope='SOFTWARE_NOT_MODEL_INPUT',method=method))
    for name,where,key,value in [('request_content','request','run_id','CHANGED'),('packet_content','packet','native_tick',101),('source_manifest','proof','frozen_source_manifest_sha256','b'*64),('fullstate_identity','proof','before_fullstate_sha256','b'*64),('receipt_coverage','receipt','complete_prefix_native',99),('causal_coverage','causal','covered_native',99),('permission','capture','physical_permission',True)]:
        cap=copy.deepcopy(capture);req=copy.deepcopy(request);pr=copy.deepcopy(proof)
        node={'request':req,'packet':cap['packet'],'proof':pr,'receipt':pr['canonical_receipt_content'],'causal':cap['causal_source'],'capture':cap}[where];node[key]=value
        refused(name,lambda cap=cap,req=req,pr=pr:describe(cap,req,pr))
    err=refused('binding_first_secondary',lambda:describe({},request,proof,denied=True))
    assert err.proof['first_error'] and err.secondary and 'SOFTWARE_BINDING_PROOF_DENIED'in err.secondary

    # The new before-Engine contract runs on the REAL strict2200 NativeStep
    # class allocated without __init__, backed only by SOFTWARE value ports.
    native_module=c.load('v1599_strict_definition_only',c.R/'experiments/v1567_epoch_scope_target/native_step.py')
    native=object.__new__(native_module.NativeStep)
    class Values:
        def __init__(self,value):self.value=value
        def tolist(self):return copy.deepcopy(self.value)
    vehicle=NS(count=tick,d=NS(time=1.),body=lambda:list(packet['body']),adapter=NS(last=Values(packet['controller_memory']['last_ctrl']),integral=0.),steering_sample=lambda:Values([0.]*4))
    native.vehicle=vehicle;native.applied=tick;native.bridge_started=False;native.in_step=False
    native.mode_memory=NS(snapshot=lambda _:copy.deepcopy(mode));native.gear=NS(**gear)
    geometry=NS(origin=tick,end=tick+10400)
    proposal=dict(passed=True,closed=True,segment_sha256=method['segment_sha256'],motion_native=5,nominal_native=2205)
    guard=NS(method=method,input_sha=method['response_method_sha256'],proposal=proposal,proposal_sha256='c'*64,generation_result_sha256='d'*64,phases_started=['CPP_PROPOSAL','CPP_GENERATION','PYTHON_AUDIT'],active_phase=None,geometry=geometry,require_current_event_input=lambda m:None)
    reader=NS(seal=dict(generation_result_sha256='d'*64,binding=dict(stage='CPP_GENERATION',response_method_sha256=method['response_method_sha256'],proposal_sha256='c'*64)))
    context=dict(method=method,guard=guard,proposal=proposal,generation_reader=reader,geometry=geometry)
    install=c.load('v1599_target_installation_boundary',c.C/'installation.py')
    check=install.before_current_engine(context,native);assert check['actual_runtime_qualified']is False
    save(target/'SOFTWARE_INSTALLATION.json',dict(scope='SOFTWARE_PORTS_NO_CONSTRUCTORS',proof=check))
    for name,key,value in [('wrong_installed_method','response_method_sha256','0'*64),('different_segment','segment_sha256','0'*64)]:
        bad=dict(context,method=copy.deepcopy(method));bad['method'][key]=value
        refused(name,lambda bad=bad:install.before_current_engine(bad,native))
    native.bridge_started=True
    refused('postbridge_reinstallation',lambda:install.before_current_engine(context,native));native.bridge_started=False
    reader.seal['binding']['stage']='PYTHON_AUDIT'
    refused('audit_reader_as_generation',lambda:install.before_current_engine(context,native));reader.seal['binding']['stage']='CPP_GENERATION'
    # Fixed-reference interface only, no physical/reference generation. The
    # constant SOFTWARE state bytes are never offered as a live certificate.
    fixed=c.load('v1599_fixed_reference_source_interface',c.C/'reference.py')
    states=[[.3,0.,0.,0.,0.,0.,0.,0.]for _ in range(2201)]
    identity=hashlib.sha256(b''.join(struct.pack('<8d',*v)for v in states)).hexdigest()
    reference=fixed.FixedResponse(states=states,origin_native=tick,origin_sim_time=1.,expected_state_bytes_sha256=identity,
        method_sha256=method['response_method_sha256'],nominal_native=2200)
    assessments=[reference.assess(packet['body'],tick),reference.assess(packet['body'],tick+1)]
    refused('fixed_reference_clock_not_reset',lambda:reference.assess(packet['body'],tick))
    refused('fixed_reference_pose_tube_unchanged',lambda:reference.assess([.33,0.,0.,0.,0.],tick+2))
    save(target/'SOFTWARE_FIXED_REFERENCE.json',dict(software_only=True,state_bytes_sha256=identity,assessments=assessments,model_native=0,physical_native=0))
    return dict(goal_bound_policy=policy_proofs,current_source_binding=dict(software_positive=True,actual_capture_qualified=False),same_input_installation=check),method
