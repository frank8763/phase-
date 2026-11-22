"""Concrete actual NativeStep consumer; components are not yet qualified.

No model, vehicle, scan, process or numerical definitions are imported here.
The live authority resolver must refuse saved-only V1563 certificates before
this constructor. A caller flag cannot grant current capture or model validity.
"""
import copy
import time

class CanonicalExecution:
    def __init__(self,*,native,cursor,reference,components,authority,save_method_receipt):
        # This resolver is a missing production prerequisite, not a boolean
        # manufactured from the saved model PASS. No implementation supplied
        # in this draft or in V1563 can grant it.
        live=components.authorize_live_execution(native=native,cursor=cursor,authority=authority)
        assert live['current_origin_capture_qualified']and live['same_current_input_witness_qualified']
        assert live['current_reserve_variant']=='V1159_BOUNDED_LOAD_CURRENT_SCALAR'
        assert live['current_reserve_stop_native']==2200 and live['minimum200_preserved']
        assert live['fixed_response_error_qualified']and live['actual_policy_qualified']
        assert live['fullstate_replay_pair_pipeline_qualified']
        assert native.applied==native.vehicle.count==cursor.origin
        assert native.gear.last_tick==cursor.origin-1 and cursor.offset==0
        assert reference.origin==cursor.origin and reference.method_sha256==cursor.method_sha256
        self.native=native;self.cursor=cursor;self.reference=reference
        self.components=components;self.live=copy.deepcopy(live);self.authority=copy.deepcopy(authority)
        self.save_method_receipt=save_method_receipt;self.inflight=False;self.closed=False

    def advance(self,delivery):
        assert not self.closed and not self.inflight and not self.cursor.closed
        n=self.native;tick=n.vehicle.count
        # Exact model/current origin, current method memory, CPU2/lock/dual
        # clocks, bytes and remaining actual/private work checked BEFORE step.
        self.components.check_before_native(self.authority,self.live,tick,1)
        assert n.applied==tick and n.gear.last_tick==tick-1
        wire=n.sent[delivery['observation_sequence']]
        assert delivery['source_kind']=='ACTUAL_FRAME'and delivery['run_id']==n.run_id
        assert 0<=tick-wire['native_tick']<5 and 0<=time.monotonic()-wire['sampled_at']<=.2
        packet=n.packet(wire)
        feedback=dict(native_tick=tick,sim_time=packet['sim_time'],body=packet['body'],
            encoders=[*packet['steering']['position'],*packet['steering']['velocity']],
            last_ctrl=packet['controller_memory']['last_ctrl'],integral=packet['controller_memory']['integral'],
            gear_memory=dict(gear=n.gear.gear,brake_start=n.gear.brake_start,last_tick=n.gear.last_tick),
            mode_history=n.mode_memory.snapshot(tick))
        decision=self.cursor.select(feedback)
        tail=decision['final_original2200_tail']
        self.inflight=True
        # NativeStep owns one gear select, current source-bound reserve,
        # post-certificate200ms checks, original allocator, physical guard,
        # before/applied receipts and monotonic fixed reference assessment.
        # A V1415/plain-V1114/200reserve owner is rejected by components above.
        self.components.apply_current_native(n,decision=decision,delivery=delivery,
            phase='CANONICAL_FINAL2200_TAIL'if tail else'CANONICAL_ORIGINAL_CATALOGUE0',
            monitor=self.reference)
        assert n.applied==n.vehicle.count==tick+1
        row=n.events[-1]
        receipt=self.components.durable_applied_receipt(n,decision)
        memory=self.cursor.commit(row,durable_receipt=receipt)
        self.save_method_receipt(memory)
        self.inflight=False
        if self.cursor.closed:
            assert n.last_zero_count>=2200
            self.closed=True
        return dict(before_native=tick,after_native=tick+1,schedule_complete=self.closed,
            whole_route_passed=False,actual_navigation_goal_not_inferred=True)
