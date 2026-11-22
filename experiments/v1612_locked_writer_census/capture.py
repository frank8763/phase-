"""Acquire canonical owner source once; no method/model/live permission."""
import copy
import hashlib
import json
import math
from pathlib import Path
import time
import importlib.util
R=Path(__file__).resolve().parents[2]
NATIVE='experiments/v1567_epoch_scope_target/native_step.py'
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def exact(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

provider=exact('v1574_actual_causal_content',Path(__file__).with_name('causal_provider.py'))
projection=exact('v1574_unchanged_fullstate_coordinates',R/'experiments/v1528_fixed_we_evaluation_contract/origin_binding.py')
recorded=exact('v1574_unchanged_applied_receipts',R/'experiments/v1423_integrated_route_audit/recorded.py')

def prefix_coverage(native,output):
    """Content check of durable source receipts, no model/gear recomputation.

    Source acquisition currently stops at the first event. Strict2200 bridge
    installation and its poststate receipts require their own future runtime.
    Never resume the t0 observer after bridge_started.
    """
    assert not native.bridge_started, 'POST_BRIDGE_SOURCE_RECEIPTS_NOT_YET_QUALIFIED'
    v=native.vehicle
    path=Path(output)/'ACTUAL_OWNER_JOURNAL.jsonl'
    assert not path.is_symlink()and path.resolve()==path and path.stat().st_size<=64*1024**2
    root=recorded.lines(path)
    rows=recorded.receipts(root,before_kind='BEFORE_ORIGINAL_PREFIX_NATIVE',after_kind='AFTER_ORIGINAL_PREFIX_NATIVE',bound_hash=False)
    assert [r['before_native']for r in rows]==list(range(v.count)), 'ACTUAL_PREFIX_RECEIPT_GAP'
    assert len(v.commands)==len(v.rows)==len(native.events)==len(rows)==v.audit.native_count
    initial_path=Path(output)/'SOURCE_T0_IDENTITY.json'
    assert not initial_path.is_symlink()and initial_path.resolve()==initial_path
    initial=json.loads(initial_path.read_text())
    assert initial['run_id']==native.run_id and initial['canonical_native']==0
    assert digest(initial['fullstate'])==initial['fullstate_sha256']
    for tick,(row,event,command,state)in enumerate(zip(rows,native.events,v.commands,v.rows)):
        assert event['original_normal_route_prefix_observation']is True and event['applied']is True
        assert all(event[k]==value for k,value in row.items()), 'OWNER_DURABLE_PREFIX_CHANGED'
        assert len(command)==6 and [command[1],command[2],command[5]]==row['request'], 'APPLIED_COMMAND_RECEIPT_CHANGED'
        assert abs(state['time']-.01*(tick+1))<=1e-8, 'APPLIED_ROW_CLOCK_CHANGED'
        if tick==0:
            assert initial['fullstate_sha256']==row['source_full_state_sha256'], 'PREFIX_T0_STATE_SOURCE_CHANGED'
        if tick:
            prior=v.rows[tick-1]
            prior_state=dict(time=float(prior['time']),**{k:prior[k].tolist()for k in ('qpos','qvel','ctrl','mocap_pos','mocap_quat')})
            assert digest(prior_state)==row['source_full_state_sha256'], 'PREFIX_STATE_SOURCE_GAP'
    if rows:
        last=v.rows[-1]
        assert fullstate(v)==dict(time=float(last['time']),**{k:last[k].tolist()for k in ('qpos','qvel','ctrl','mocap_pos','mocap_quat')}), 'LAST_DURABLE_STATE_CHANGED'
    return dict(complete_prefix_native=len(rows),durable_request_source_content_verified=True,
                allocator_recomputed=False,fullstate_replay_performed=False,
                post_bridge_coverage_qualified=False)

class CaptureRefusal(RuntimeError):
    def __init__(self,first,proof,secondary):
        super().__init__(first);self.proof=proof;self.secondary=secondary

def fullstate(v):
    return dict(time=float(v.d.time),**{k:getattr(v.d,k).tolist()for k in ('qpos','qvel','ctrl','mocap_pos','mocap_quat')})

def capture(native,wire,*,run_id,prepared_sources,causal_source,request,output,setup,save_proof,prepared_history=None,clock=time.monotonic):
    """Caller supplies already qualified causal-source provenance, not truth.

    This source draft deliberately issues no methodinput, eventcertificate,
    response controls or admission. Its result can only feed a later explicitly
    registered current-domain binder. No synthetic source timestamps.
    """
    proof=dict(passed=False,source_only=True,current_domain_qualified=False,
        numerical_permission=False,physical_permission=False,first_error=None,
        complete_actual_capture_runtime_qualified=False,checks={})
    first=None;answer=None
    try:
        def check(name,value):
            proof['checks'][name]=bool(value);assert value,name
        check('exact_native_definition',Path(type(native).packet.__code__.co_filename).resolve()==R/NATIVE)
        check('native_source_SHA',hashlib.sha256((R/NATIVE).read_bytes()).hexdigest()==prepared_sources[NATIVE])
        check('canonical_run',native.run_id==run_id and not native.in_step)
        v=native.vehicle;tick=v.count;before=fullstate(v);modes=native.mode_memory.snapshot(tick)
        gear=dict(gear=native.gear.gear,last_tick=native.gear.last_tick,brake_start=native.gear.brake_start)
        proof.update(before_native=tick,before_fullstate=copy.deepcopy(before),before_fullstate_sha256=digest(before),
            current_mode=copy.deepcopy(modes),current_gear=copy.deepcopy(gear))
        check('root_counts_complete',type(tick)is int and tick==native.applied==len(v.rows)==len(native.events)==v.audit.native_count and len(v.contacts)==tick+1 and v.bad==0)
        check('gear_clock_complete',gear['last_tick']==tick-1)
        check('exact_projection_source',hashlib.sha256((R/'experiments/v1528_fixed_we_evaluation_contract/origin_binding.py').read_bytes()).hexdigest()==prepared_sources['experiments/v1528_fixed_we_evaluation_contract/origin_binding.py'])
        check('canonical_fixed_clock',abs(float(v.d.time)-.01*tick)<=1e-8)
        check('current_wire_identity',type(wire['sequence'])is int and native.sent[wire['sequence']]==wire and wire['run_id']==run_id)
        check('wire_native_hold',type(wire['native_tick'])is int and 0<=tick-wire['native_tick']<5)
        check('wire_age_before_capture',0<=clock()-wire['sampled_at']<=.2)
        # packet() reads only body, wheel, allocator and existing source. No
        # current()/framecache/scan operation is used in this acquisition.
        packet=native.packet(wire)
        coordinates=projection.compare(before,packet,setup)
        proof['fullstate_projection']=coordinates
        check('complete_fullstate_coordinates',coordinates['passed'])
        check('body_encoder_source_time',packet['native_tick']==tick and packet['steering']['native_tick']==tick and packet['body_measured_at']==packet['steering']['measured_at'])
        check('mode_matches_owner',all(packet[k]==modes[k]for k in ('coupled_episode','steering_motion_active','parked_target')))
        check('control_memory_matches_owner',packet['controller_memory']['last_ctrl']==v.adapter.last.tolist()and packet['controller_memory']['integral']==float(v.adapter.integral))
        check('scan_provenance_separate',packet['scan_provenance']==dict(sequence=wire['sequence'],native_tick=wire['native_tick'],sampled_at=wire['sampled_at'],wire_sha256=digest(wire)))
        assert prepared_history is not None and prepared_history.native is native,'STOPPED_HISTORY_NOT_PREPARED'
        prepared_history.same_stopped_state()
        proof['canonical_receipt_content']=copy.deepcopy(prepared_history.proof['complete_applied_history'])
        proof['historical_preparation_sha256']=prepared_history.proof_sha256
        check('same_event_fullstate',request['actual']['evidence_state_sha256']==digest(before))
        check('same_event_wire',request['actual']['wire']==wire)
        feedback=request['actual']['feedback']
        check('same_event_memory_mode_gear',feedback['last_ctrl']==packet['controller_memory']['last_ctrl']and feedback['integral']==packet['controller_memory']['integral']and feedback['parked_target']==modes['parked_target']and feedback['steering_motion_active']==modes['steering_motion_active']and feedback['gear_memory']==gear)
        origin=copy.deepcopy(causal_source)
        proof['causal_content']=prepared_history.extended_causal_content(origin,wire,request)
        proof.update(current_packet=copy.deepcopy(packet),current_packet_sha256=digest(packet),causal_source=origin,
            frozen_source_manifest_sha256=digest(prepared_sources))
        check('state_unchanged_by_capture',fullstate(v)==before and native.mode_memory.snapshot(tick)==modes and gear==dict(gear=native.gear.gear,last_tick=native.gear.last_tick,brake_start=native.gear.brake_start))
        proof['capture_checked_monotonic']=clock()
        proof['capture_source_age_s']=proof['capture_checked_monotonic']-wire['sampled_at']
        check('wire_age_after_capture',0<=proof['capture_source_age_s']<=.2)
        check('durable_capture_age_sample',0<=proof['capture_source_age_s']<=.2)
        proof['passed']=True
        answer=dict(role='CAPTURED_SOURCE_ONLY_NOT_METHOD_INPUT',packet=copy.deepcopy(packet),fullstate=before,
            gear_memory=gear,mode_memory=modes,causal_source=origin,physical_permission=False,numerical_permission=False)
    except BaseException as error:
        first='CANONICAL_CURRENT_CAPTURE_REFUSED:'+repr(error);proof.update(passed=False,first_error=first)
    secondary=None
    try:save_proof(proof)
    except BaseException as error:secondary=repr(error)
    if first or secondary:raise CaptureRefusal(first or 'CANONICAL_CURRENT_CAPTURE_SAVE_REFUSED',proof,secondary)
    return answer
