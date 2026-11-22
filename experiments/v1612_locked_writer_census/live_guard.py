"""Actual current CPP2200 authority, distinct from private model admission.

This wrapper cannot create root authority. A real actual-scope admission,
completed same-input private transaction and canonical receipts are required.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


class LiveGuard:
    active_phase='CURRENT_CPP_RESERVE'
    def __init__(self,*,private_guard,native,actual_admission,transaction_result_path,geometry,maximum_calls):
        self.private=private_guard;self.native=native;self.source=private_guard.source;self.lock=private_guard.lock
        self.method=copy.deepcopy(private_guard.method);self.input_sha=private_guard.input_sha;self.geometry=geometry
        self.path=Path(actual_admission);self.identity=sha(self.path);self.authority=read(self.path)
        a=self.authority
        assert a['scope']=='REVISION12_FIRST_GOAL_BOUND_SEGMENT_ACTUAL_RUNTIME'
        assert a['scientific_revision']==12 and a['physical_authorized']is True and a['whole_route_admission']is False
        assert a['models_authorized']and a['optimizer_authorized']is False
        assert a['round_id']==private_guard.authority['round_id']
        assert a['source_freeze_sha256']==private_guard.authority['source_freeze_sha256']
        assert a['maximum_current_reserve_calls']==maximum_calls and type(maximum_calls)is int and 1<=maximum_calls<=8400
        result=read(transaction_result_path)
        assert result['passed']and result['closed']and result['first_error']is None and result['secondary_errors']==[]
        assert result['complete_model_reference']['generation_result_sha256']==private_guard.generation_result_sha256
        assert private_guard.phases_started==['CPP_PROPOSAL','CPP_GENERATION','PYTHON_AUDIT']and private_guard.active_phase is None
        private_guard.ledgers['CPP_GENERATION'].complete();private_guard.ledgers['PYTHON_AUDIT'].complete()
        private_guard.require_current_event_input(self.method)
        self.transaction_sha=sha(transaction_result_path);self.maximum_calls=maximum_calls;self.calls=0;self.live_dependency=True
        self.ledger=private_guard.Work(native=2200*maximum_calls,nominal=0,witness=2200*maximum_calls,
            copies=0,engine=1,predictor=0,batch_calls=maximum_calls)
        self.ledger.bucket('witness');self.call_start_native=None;self.check()

    def check(self):
        self.private.check();assert sha(self.path)==self.identity
        a=self.authority
        assert time.time()<a['execution_deadline_unix']<=a['absolute_deadline_unix']<=1795395600
        assert time.monotonic()<a['execution_deadline_monotonic']<=a['hard_stop_monotonic']

    def require_live_component(self,name,method):
        self.check();assert name=='CURRENT_CPP_RESERVE'and method==self.method and self.live_dependency

    def require_current_reserve_source(self,packet,memory,gear):
        self.check();n=self.native;v=n.vehicle;tick=packet['native_tick'];base=self.method['base_method']
        self.ledger.idle();assert n.applied==v.count==tick and not n.in_step
        assert self.calls<self.maximum_calls
        assert memory['epoch_native']==base['fixed_origin_native']and memory['covered_native']==tick
        assert memory['response_method_sha256']==self.input_sha and memory['actual_sensor_claim']is False
        assert type(memory['steering_load_episode'])is bool and memory['complete_applied_receipt_coverage']is True
        assert gear==dict(gear=n.gear.gear,last_tick=n.gear.last_tick,brake_start=n.gear.brake_start)
        assert gear['last_tick']==tick-1
        modes=n.mode_memory.snapshot(tick)
        assert all(packet[k]==modes[k]for k in ('coupled_episode','steering_motion_active','parked_target'))
        assert list(v.body())==packet['body']
        assert v.steering_sample().tolist()==[*packet['steering']['position'],*packet['steering']['velocity']]
        assert v.adapter.last.tolist()==packet['controller_memory']['last_ctrl']and float(v.adapter.integral)==packet['controller_memory']['integral']
        assert packet['steering']['native_tick']==tick and packet['body_measured_at']==packet['steering']['measured_at']
        assert abs(packet['sim_time']-(base['fixed_origin_sim_time']+.01*(tick-base['fixed_origin_native'])))<=1e-8
        assert len(v.rows)==v.audit.native_count==len(v.commands)==tick and len(v.contacts)==tick+1 and v.bad==0
        self.geometry.check_range(tick,2201)
        self.call_start_native=self.ledger.value['native'];self.calls+=1

    def begin(self,stage,kind):
        self.check();assert stage==self.active_phase
        if kind=='native':
            assert self.call_start_native is not None and self.ledger.value['native']-self.call_start_native<2200
            self.ledger.claim(1)
        else:self.ledger.construct(kind)

    def completed(self,stage,kind):
        assert stage==self.active_phase
        if kind=='native':self.ledger.acknowledge(1)
        else:self.ledger.constructed(kind)

    def require_exact_zero_tail_batch_capability(self,method,*,native_tail):
        self.check();assert native_tail==2200 and(method is None or method==self.method)
        assert self.call_start_native is not None and self.ledger.value['native']-self.call_start_native==0

    def begin_batch(self,stage,kind,count):
        self.check();assert stage==self.active_phase and kind=='native'and count==2199
        assert self.ledger.value['native']-self.call_start_native==1
        self.ledger.claim(count,batch=True)

    def completed_batch(self,stage,kind,count):
        assert stage==self.active_phase and kind=='native';self.ledger.acknowledge(count,batch=True)

    def counts(self):
        return dict(private=self.private.counts(),current_reserve=self.ledger.counts(),current_calls=self.calls,
            internal_Allocator_constructors=None,physical=self.native.exact_accounting(),replay_native=0,optimizer_calls=0)
