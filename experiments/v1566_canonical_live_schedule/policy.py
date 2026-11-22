"""Raw request cursor, never an actuator-array replay or a gear filter."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

R=Path(__file__).resolve().parents[2]
SCHEDULE='experiments/v1550_canonical_observer_policy/schedule.py'

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def vector(value,n):
    assert isinstance(value,(list,tuple)) and len(value)==n
    assert all(type(v)in(int,float)and math.isfinite(v)for v in value)

class CanonicalSchedule:
    """Proposes raw requests; commit consumes an already applied owner receipt.

    No plant access, no model/Allocator imports, no actual permission. A failed
    commit leaves the original pending request and cursor intact for closure;
    the enclosing actual owner must close and must not retry an applied action.
    """
    def __init__(self,method,*,prepared_sources):
        clean=copy.deepcopy(method);identity=clean.pop('response_method_sha256')
        assert digest(clean)==identity
        assert method['scientific_integration_revision']==10
        assert method['geometry_kind']=='FULL_PERIOD_DISK'
        path=R/SCHEDULE
        assert hashlib.sha256(path.read_bytes()).hexdigest()==prepared_sources[SCHEDULE]
        spec=importlib.util.spec_from_file_location('v1566_original_raw_schedule',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.rows=module.raw_rows(prepared_sources)
        self.cuts=module.boundaries(self.rows)
        assert self.cuts==tuple(tuple(row)for row in method['fixed_boundaries'])
        self.at=module.at;self.body_request=module.body_request
        self.method_sha256=identity
        self.base=copy.deepcopy(method['base_method'])
        self.origin=self.base['fixed_origin_native']
        self.sim_origin=self.base['fixed_origin_sim_time']
        assert self.base['method_memory']['steering_load_episode']is False
        assert self.base['method_memory']['actual_sensor_claim']is False
        self.load_episode=False
        self.offset=0;self.pending=None;self.prepared_feedback=None;self.closed=False
        self.method_memory_chain='0'*64

    def select(self,feedback):
        assert not self.closed and self.pending is None and 0<=self.offset<13600
        native=feedback['native_tick']
        assert type(native)is int and native==self.origin+self.offset
        assert abs(feedback['sim_time']-(self.sim_origin+.01*self.offset))<=1e-8
        vector(feedback['body'],5);vector(feedback['encoders'],4);vector(feedback['last_ctrl'],4)
        assert math.isfinite(feedback['integral'])
        assert feedback['gear_memory']['last_tick']==native-1
        assert feedback['mode_history']['covered_native']==native
        raw=self.at(self.rows,self.offset);v,w=self.body_request(raw)
        decision=dict(before_native=native,offset=self.offset,sim_time=feedback['sim_time'],
            response_method_sha256=self.method_sha256,raw_row=list(raw),upstream_request=[v,w,False],
            parked_target=raw[0]if raw[2]else None,
            final_original2200_tail=self.offset>=11400,
            method_load_before=self.load_episode,
            feedback_sha256=digest(feedback),control_owner='DISCLOSED_SHARED_EXECUTION_BRIDGE',
            no_saved_actuator_control=True,gear_filter_owner='CANONICAL_NATIVE_STEP_ONCE')
        decision['decision_sha256']=digest(decision)
        self.prepared_feedback=copy.deepcopy(feedback)
        self.pending=copy.deepcopy(decision)
        return copy.deepcopy(decision)

    def commit(self,row,*,durable_receipt):
        assert not self.closed and self.pending is not None
        pending=self.pending
        feedback=self.prepared_feedback
        assert digest(feedback)==pending['feedback_sha256']
        assert row['body']==feedback['body']and row['encoders']==feedback['encoders']
        assert row['last_ctrl']==feedback['last_ctrl']and row['integral']==feedback['integral']
        assert row['mode_history']==feedback['mode_history']
        assert row['applied']is True and row['before_native']==pending['before_native']
        assert row['raw_request']==pending['upstream_request']
        assert row['parked_target']==pending['parked_target']
        assert row['body']==durable_receipt['body_before']
        assert row['encoders']==durable_receipt['encoders_before']
        assert row['last_ctrl']==durable_receipt['last_ctrl_before']
        assert row['integral']==durable_receipt['integral_before']
        assert row['source_full_state_sha256']==durable_receipt['source_full_state_sha256']
        assert durable_receipt['before_native']==row['before_native']
        assert durable_receipt['after_native']==row['before_native']+1
        assert durable_receipt['applied_receipt_saved']is True
        assert durable_receipt['source_checked_after_certificate']is True
        assert durable_receipt['source_packet_sha256']==row['source_packet_sha256']
        assert durable_receipt['decision_sha256']==pending['decision_sha256']
        assert durable_receipt['gear_handoff']==row['gear_handoff']
        assert durable_receipt['gear_last_tick']==row['before_native']
        assert durable_receipt['mode_covered_native']==row['before_native']+1
        actual_v,actual_w,stale=row['request'];assert stale is False
        target=row['parked_target']
        load=self.load_episode
        if target is not None or actual_v<=-.005:load=False
        elif actual_v>=.005:load=True
        memory=dict(before_native=row['before_native'],after_native=row['before_native']+1,
            epoch_native=self.origin,load_before=self.load_episode,load_after=load,
            applied_body=[actual_v,actual_w],parked_target=target,
            actual_sensor_claim=False,decision_sha256=pending['decision_sha256'],
            previous_chain_sha256=self.method_memory_chain)
        chain=digest(memory)
        self.offset+=1;self.load_episode=load;self.method_memory_chain=chain;self.pending=None;self.prepared_feedback=None
        if self.offset==13600:self.closed=True
        return dict(memory,chain_sha256=chain)
