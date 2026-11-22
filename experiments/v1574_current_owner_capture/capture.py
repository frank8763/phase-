"""Acquire canonical owner source once; no method/model/live permission."""
import copy
import hashlib
import json
import math
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2]
NATIVE='experiments/v1567_epoch_scope_target/native_step.py'
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

class CaptureRefusal(RuntimeError):
    def __init__(self,first,proof,secondary):
        super().__init__(first);self.proof=proof;self.secondary=secondary

def fullstate(v):
    return dict(time=float(v.d.time),**{k:getattr(v.d,k).tolist()for k in ('qpos','qvel','ctrl','mocap_pos','mocap_quat')})

def capture(native,wire,*,run_id,prepared_sources,causal_source,save_proof,clock=time.monotonic):
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
        check('canonical_fixed_clock',abs(float(v.d.time)-.01*tick)<=1e-8)
        check('current_wire_identity',type(wire['sequence'])is int and native.sent[wire['sequence']]==wire and wire['run_id']==run_id)
        check('wire_native_hold',type(wire['native_tick'])is int and 0<=tick-wire['native_tick']<5)
        check('wire_age_before_capture',0<=clock()-wire['sampled_at']<=.2)
        # packet() reads only body, wheel, allocator and existing source. No
        # current()/framecache/scan operation is used in this acquisition.
        packet=native.packet(wire)
        check('body_encoder_source_time',packet['native_tick']==tick and packet['steering']['native_tick']==tick and packet['body_measured_at']==packet['steering']['measured_at'])
        check('mode_matches_owner',all(packet[k]==modes[k]for k in ('coupled_episode','steering_motion_active','parked_target')))
        check('control_memory_matches_owner',packet['controller_memory']['last_ctrl']==v.adapter.last.tolist()and packet['controller_memory']['integral']==float(v.adapter.integral))
        check('scan_provenance_separate',packet['scan_provenance']==dict(sequence=wire['sequence'],native_tick=wire['native_tick'],sampled_at=wire['sampled_at'],wire_sha256=digest(wire)))
        # Bound source+snapshot identity, never accept a plain arbitrary set of
        # coefficients as having been observed. Qualifiedtrackerreceipt and
        # complete sensing coverage still require an actual provider.
        origin=copy.deepcopy(causal_source)
        check('causal_provider_role',origin['role']=='CURRENT_CANONICAL_OBSERVATION_CAUSAL_SOURCE')
        check('causal_provider_current',origin['run_id']==run_id and origin['covered_native']==tick and origin['observation_wire_sha256']==digest(wire))
        check('causal_snapshot_SHA',digest(origin['snapshot'])==origin['snapshot_sha256'])
        check('causal_receipt_present',isinstance(origin['source_receipt_sha256'],str)and len(origin['source_receipt_sha256'])==64)
        proof.update(current_packet=copy.deepcopy(packet),current_packet_sha256=digest(packet),causal_source=origin,
            frozen_source_manifest_sha256=digest(prepared_sources))
        check('state_unchanged_by_capture',fullstate(v)==before and native.mode_memory.snapshot(tick)==modes and gear==dict(gear=native.gear.gear,last_tick=native.gear.last_tick,brake_start=native.gear.brake_start))
        check('wire_age_after_capture',0<=clock()-wire['sampled_at']<=.2)
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
