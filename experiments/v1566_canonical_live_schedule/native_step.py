"""Canonical V1159 complete2200 current-reserve consumer, draft/unqualified.

Explicit fork of V1423; original source/physical/control gates unchanged.

The registered outer owner supplies independently qualified reserve/physical
guards and the evidence sink. No standalone launch or physical permission.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

R=Path(__file__).resolve().parents[2]


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


frames=exact('v1411_native_original_frames',R/'experiments/v1396_rpp_rpc_retirement/frames.py')
stamped=exact('v1411_native_original_time_gate',R/'experiments/v1396_rpp_rpc_retirement/stamped_contract.py')
mode=exact('v1411_native_exact_mode_book',R/'experiments/v1398_current_event_witness/mode_memory.py')
gear_module=exact('v1411_native_original_gear_gate',R/'experiments/v1396_rpp_rpc_retirement/gear_handoff.py')


def state_digest(vehicle):
    value={key:getattr(vehicle.d,key).tolist()for key in ('qpos','qvel','ctrl','mocap_pos','mocap_quat')};value['time']=float(vehicle.d.time)
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


class NativeStep:
    def __init__(self,vehicle,*,run_id,reserve,physical_guard,evidence_sink):
        assert vehicle.count==0 and float(vehicle.d.time)==0., 'SHARED_NATIVE_REQUIRES_CANONICAL_T0'
        self.vehicle=vehicle;self.run_id=run_id;self.reserve=reserve;self.physical_guard=physical_guard;self.sink=evidence_sink
        self.gear=gear_module.GearHandoff();self.mode_memory=mode.ModeMemory(canonical_native=0,coupled_episode=False,steering_motion_active=False)
        self.sampler=frames.SampleCache();self.sequence=0;self.applied=0;self.in_step=False;self.events=[];self.last_zero_count=0
        self.bridge_started=False
        self.plugin_native=0;self.bridge_native=0;self.stop_native=0;self.sent={}

    def observe_original_prefix(self,row,*,control_owner):
        # An observer of the original normal-route execution from canonical t0;
        # never a function that applies a command or authorizes a bridge step.
        v=self.vehicle
        assert not self.bridge_started and not self.in_step and v.count==self.applied+1
        assert row['applied'] is True and row['before_native']==self.applied
        assert control_owner in {'ORIGINAL_RPP','DISCLOSED_SHARED_EXECUTION_BRIDGE','APPLIED_STOP_TAIL'}
        assert len(v.rows)==v.count and len(v.contacts)==v.count+1 and v.audit.native_count==v.count and v.bad==0
        assert bool(getattr(v.adapter,'_steering_motion_active',False))==(row['parked_target'] is not None)
        candidate=copy.deepcopy(self.gear)
        vr,wr,proof=candidate.select(*row['upstream_request'][:2],native_tick=row['before_native'],body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders'])
        assert [vr,wr,False]==row['request'] and proof==row['gear_handoff'],'ORIGINAL_PREFIX_GEAR_ACCOUNT_CHANGED'
        self.mode_memory.applied(before_native=row['before_native'],v=vr,w=wr,parked_target=row['parked_target'],steering_motion_active_after=bool(getattr(v.adapter,'_steering_motion_active',False)))
        self.gear=candidate;self.applied+=1
        self.plugin_native+=control_owner=='ORIGINAL_RPP';self.bridge_native+=control_owner=='DISCLOSED_SHARED_EXECUTION_BRIDGE';self.stop_native+=control_owner=='APPLIED_STOP_TAIL'
        self.last_zero_count=self.last_zero_count+1 if control_owner=='APPLIED_STOP_TAIL'else 0
        self.events.append(copy.deepcopy(dict(row,control_owner=control_owner,original_normal_route_prefix_observation=True)))

    def packet(self,scan_wire):
        # Body/encoder samples are current actual measurements. Scan provenance
        # is separate and never relabeled as a current acquisition.
        v=self.vehicle;enc=v.steering_sample().tolist();modes=self.mode_memory.snapshot(v.count)
        assert modes['steering_motion_active']==bool(getattr(v.adapter,'_steering_motion_active',False))and modes['parked_target']==getattr(v.adapter,'parked_target',None), 'ACTUAL_NATIVE_MODE_HISTORY_CHANGED'
        now=time.monotonic();body=list(v.body());lateral=float(-v.d.qvel[0]*__import__('math').sin(body[2])+v.d.qvel[1]*__import__('math').cos(body[2]))
        return dict(body=body,body_lateral=lateral,native_tick=v.count,sim_time=float(v.d.time),body_measured_at=now,sent_at=now,
                    steering=dict(position=enc[:2],velocity=enc[2:],native_tick=v.count,measured_at=now),
                    controller_memory=dict(last_ctrl=v.adapter.last.tolist(),integral=float(v.adapter.integral)),
                    coupled_episode=modes['coupled_episode'],steering_motion_active=modes['steering_motion_active'],parked_target=modes['parked_target'],
                    scan_provenance=None if scan_wire is None else dict(sequence=scan_wire['sequence'],native_tick=scan_wire['native_tick'],sampled_at=scan_wire['sampled_at'],wire_sha256=hashlib.sha256(json.dumps(scan_wire,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()))

    def current(self):
        # The original outer producer calls only at its 5native publication
        # cadence or a stopped event. apply() never acquires an extra scan.
        v=self.vehicle;wire=frames.wire_packet(self.sampler,v,self.run_id,self.sequence);self.sequence+=1
        self.sent[wire['sequence']]=copy.deepcopy(wire);frames.validate_wire(wire)
        return wire,self.packet(wire)

    def apply(self,v_request,w_request,*,phase,control_owner,delivery,parked_target=None,monitor=None,stop_tail=False):
        v=self.vehicle;assert v.count==self.applied and not self.in_step
        self.before_native_budget('ACTUAL_STOP_TAIL' if stop_tail else 'ACTUAL_NATIVE',1)
        assert control_owner in {'ORIGINAL_RPP','DISCLOSED_SHARED_EXECUTION_BRIDGE','APPLIED_STOP_TAIL'}
        if not stop_tail:
            assert delivery is not None and delivery['source_kind']=='ACTUAL_FRAME', 'MODELED_PACKET_CANNOT_DRIVE_PLANT'
        wire=None if stop_tail else self.sent[delivery['observation_sequence']]
        packet=self.packet(wire);before=state_digest(v);source_modes=self.mode_memory.snapshot(v.count)
        packet_sha256=hashlib.sha256(json.dumps(packet,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        if stop_tail:
            assert v_request==w_request==0. and parked_target is None and control_owner=='APPLIED_STOP_TAIL'
        else:
            assert delivery['source_kind']=='ACTUAL_FRAME', 'MODELED_PACKET_CANNOT_DRIVE_PLANT'
            frames.validate_binding(delivery,self.sent)
            assert delivery['run_id']==self.run_id and 0<=v.count-delivery['observation_native_tick']<5, 'ACTUAL_SOURCE_STATE_HOLD_EXCEEDED'
            v_request,w_request,expiry=stamped.before_step(v_request,w_request,delivery,time.monotonic());assert expiry['fresh'], 'ACTUAL_NATIVE_COMMAND_EXPIRED'
        # This callback must use this complete measured packet, current causal
        # field and the registered private model budget on the same CPU2 lock.
        proof,branch_states,branch_ctrl=self.reserve(packet,source_modes)
        assert state_digest(v)==before and self.mode_memory.snapshot(v.count)==source_modes, 'PRIVATE_CERTIFICATE_MUTATED_ACTUAL_OWNER'
        assert v.adapter.last.tolist()==packet['controller_memory']['last_ctrl']and float(v.adapter.integral)==packet['controller_memory']['integral'], 'PRIVATE_CERTIFICATE_MUTATED_ACTUAL_ALLOCATOR'
        assert hashlib.sha256(json.dumps(packet,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==packet_sha256, 'PRIVATE_CERTIFICATE_MUTATED_SOURCE_PACKET'
        assert proof['before_native']==v.count and proof['complete_native']==2200 and proof['passed']is True, 'CURRENT_ACTUAL_COMPLETE_BRAKING_REFUSED'
        assert proof['source_packet_sha256']==packet_sha256, 'PRIVATE_BRAKING_ORIGIN_CHANGED'
        assert proof['causal_tube_lower_m']>=.22-1e-8
        assert proof['model_variant']=='V1159_BOUNDED_STEERING_LOAD_OVER_V1114'
        assert proof['model_feedback']=='CURRENT_BRANCH_SCALAR_AFTER_MEASURED_ORIGIN'
        assert proof['minimum200_preserved']is True and proof['all_arrays_saved_before_gate']is True
        assert proof['method_memory_epoch_native']<=v.count
        assert proof['method_memory_covered_native']==v.count
        assert branch_states.shape==(2201,8) and branch_ctrl.shape==(2200,4), 'INCOMPLETE_CURRENT_BRAKING_EVIDENCE'
        if not stop_tail:
            assert stamped.before_step(v_request,w_request,delivery,time.monotonic())[2]['fresh'], 'ACTUAL_COMMAND_EXPIRED_DURING_CERTIFICATE'
            assert 0<=time.monotonic()-wire['sampled_at']<=.2, 'ACTUAL_SCAN_EXPIRED_DURING_CERTIFICATE'
        source_checked_monotonic=time.monotonic()
        candidate=copy.deepcopy(self.gear)
        vr,wr,gear_proof=candidate.select(v_request,w_request,native_tick=v.count,body=packet['body'],last_ctrl=v.adapter.last,encoders=[*packet['steering']['position'],*packet['steering']['velocity']])
        row=dict(before_native=v.count,phase=phase,control_owner=control_owner,raw_request=[v_request,w_request,False],request=[vr,wr,False],parked_target=parked_target,
                 body=packet['body'],encoders=[*packet['steering']['position'],*packet['steering']['velocity']],last_ctrl=packet['controller_memory']['last_ctrl'],integral=packet['controller_memory']['integral'],
                 source_packet_sha256=packet_sha256,source_packet=copy.deepcopy(packet),source_full_state_sha256=before,source_checked_monotonic=source_checked_monotonic,mode_history=source_modes,steering_motion_active_before=source_modes['steering_motion_active'],gear_handoff=gear_proof,delivery=delivery,applied=False)
        self.events.append(row);self.sink.before(row,proof,branch_states,branch_ctrl)
        v.adapter.parked_target=parked_target;self.gear=candidate;self.in_step=True
        v.step(vr,wr,False)
        self.in_step=False;row['applied']=True;self.applied+=1
        self.last_zero_count=self.last_zero_count+1 if stop_tail else 0
        self.plugin_native+=control_owner=='ORIGINAL_RPP';self.bridge_native+=control_owner=='DISCLOSED_SHARED_EXECUTION_BRIDGE';self.stop_native+=control_owner=='APPLIED_STOP_TAIL'
        self.mode_memory.applied(before_native=row['before_native'],v=vr,w=wr,parked_target=parked_target,steering_motion_active_after=bool(getattr(v.adapter,'_steering_motion_active',False)))
        row['physical_guard']=self.physical_guard(v)
        if monitor is not None:row['response_membership']=monitor.assess(list(v.body()),v.count)
        self.sink.after(row)
        return gear_proof

    def exact_accounting(self):
        return dict(actual_native=None if self.in_step else self.applied,actual_inflight_unknown=self.in_step,
                    original_RPP_native=None if self.in_step else self.plugin_native,shared_bridge_native=None if self.in_step else self.bridge_native,applied_stop_tail_native=None if self.in_step else self.stop_native,
                    completed_original_RPP_native_lower_bound=self.plugin_native,completed_shared_bridge_native_lower_bound=self.bridge_native,completed_stop_tail_native_lower_bound=self.stop_native,
                    complete200_applied_zero_tail=self.last_zero_count>=200)
