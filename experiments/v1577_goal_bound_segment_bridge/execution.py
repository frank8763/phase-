"""Own measured-output fixed tracker -> strict NativeStep, no model controls.

The live resolver remains a required distinct capability. No callable in this
draft can grant it or substitute private PASS for actual qualification.
"""
import hashlib
import json
import math
import time
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


class Execution:
    def __init__(self,*,native,tracker,proposal,reference,components,method_memory,method):
        live=components.authorize_goal_bound_execution(native=native,method=method,proposal=proposal)
        assert all(live[k]for k in ('actual_source_content_verified','same_current_input_complete_witness_qualified',
            'current_CPP2200_same_model_branch_and_source_qualified','actual_policy_source_qualified','fixed_reference_source_qualified',
            'source_control_coverage_fullstate_replay_pair_source_qualified'))
        assert native.applied==native.vehicle.count==tracker.origin==reference.origin
        assert reference.method_sha256==method['response_method_sha256']
        assert proposal['motion_native']+2200==proposal['nominal_native']
        self.native=native;self.tracker=tracker;self.proposal=proposal;self.reference=reference
        self.components=components;self.memory=method_memory;self.method=method
        self.origin=native.applied;self.closed=False;self.failed=False;self.inflight=False

    def block(self,delivery):
        assert not self.closed and not self.failed and not self.inflight
        n=self.native;offset=n.applied-self.origin
        assert offset%5==0 and 0<=offset<self.proposal['nominal_native']
        self.failed=True;self.inflight=True;receipts=[];decision=None
        # The stopped preparation obtains its fresh actual wire outside this
        # block. NativeStep checks that wire again AFTER each2200certificate.
        wire=n.sent[delivery['observation_sequence']]
        assert delivery['source_kind']=='ACTUAL_FRAME'and delivery['run_id']==n.run_id
        assert wire['native_tick']==n.applied and 0<=time.monotonic()-wire['sampled_at']<=.2
        tail=offset>=self.proposal['motion_native']
        if tail:v=w=0.
        else:
            packet=n.packet(wire)
            decision=self.tracker.select(packet['body'],native_tick=n.applied,sim_time=packet['sim_time'])
            assert not decision['terminal_requested'],'ACTUAL_FIXED_STOP_TIMING_REACHED_EARLY'
            v,w=decision['body_request']
        for _ in range(5):
            before=n.applied
            self.components.check_before_native(method=self.method,native=n,count=1)
            # One canonical gear/filter operation belongs to NativeStep. No
            # direct qpos/qvel/time/control-memory writes occur in this layer.
            n.apply(v,w,phase='GOAL_BOUND_FINAL2200_TAIL'if tail else'GOAL_BOUND_SIGNED_SEGMENT',
                control_owner='APPLIED_STOP_TAIL'if tail else'DISCLOSED_SHARED_EXECUTION_BRIDGE',
                delivery=delivery,parked_target=None,monitor=self.reference,stop_tail=tail)
            assert n.applied==n.vehicle.count==before+1
            receipt=self.components.durable_applied_receipt(n,decision=decision,tail=tail)
            # Carried public method observer is advanced from the ACTUAL
            # filtered request only after its fullstate/action receipt exists.
            transition=self.components.method_transition(self.memory.current(),n.events[-1],receipt,decision=decision)
            self.memory.applied(transition);receipts.append(receipt)
        if decision is not None:self.tracker.commit(decision,applied_native=5,applied_request_receipts_sha256=digest(receipts))
        self.inflight=False;self.failed=False
        if n.applied-self.origin==self.proposal['nominal_native']:
            assert n.last_zero_count>=2200
            body=n.vehicle.body();target=self.tracker.poses[-1]
            rear=(body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]))
            assert math.dist(rear,target[:2])<=.12+1e-8
            assert abs(math.atan2(math.sin(body[2]-target[2]),math.cos(body[2]-target[2])))<=.20+1e-8
            self.closed=True
        return dict(complete=self.closed,covered_native=n.applied,whole_route_passed=False)
