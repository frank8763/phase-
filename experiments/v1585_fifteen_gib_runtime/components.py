"""Same-current private evidence -> installed strict actual consumer.

Only a separately admitted actual experiment can enter. Source qualification
is recorded separately from actual runtime outcome, which remains unknown.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def exact(name,path,source):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source[str(path.relative_to(R))]
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class Components:
    def __init__(self,*,context,native,actual_admission,output,writer,boundary,scope,source,check_budget):
        self.method=context['method'];self.proposal=context['proposal'];self.native=native;self.check_budget=check_budget
        self.generation_reader=context['generation_reader']
        self.memory_module=exact('v1585_same_durable_epoch',R/'experiments/v1567_epoch_scope_target/method_memory.py',source)
        live=exact('v1585_actual_current_capability',C/'live_guard.py',source)
        store=exact('v1585_complete_current_actual_sink',C/'actual_sink.py',source)
        reserve=exact('v1585_current_CPP2200',C/'current_reserve.py',source)
        physical=exact('v1585_complete_actual_guard',C/'physical_guard.py',source)
        fixed=exact('v1585_variable_fixed_response',C/'reference.py',source)
        tracker=exact('v1585_goal_tracker_actual',C/'tracker.py',source)
        self.execution_module=exact('v1585_strict_actual_execution',C/'execution.py',source)
        self.guard=live.LiveGuard(private_guard=context['guard'],native=native,actual_admission=actual_admission,
            transaction_result_path=context['result_path'],geometry=context['geometry'],maximum_calls=8200)
        self.sink=store.ActualSink(folder=output,writer=writer,boundary=boundary,scope=scope,source=source,method=self.method,native=native)
        self.memory=self.memory_module.MethodMemory(self.method,save_receipt=self.save_method_receipt)
        self.reserve=reserve.CurrentReserve(method=self.method,setup=context['setup'],defs=context['defs'],guard=self.guard,
            current_method_memory=self.memory.current,current_gear=lambda:dict(gear=native.gear.gear,last_tick=native.gear.last_tick,brake_start=native.gear.brake_start),
            save_origin=self.sink.origin,save_complete=self.sink.complete,save_partial=self.sink.partial,
            save_after_gate=self.sink.after_gate,save_raw_bytes=self.sink.raw_bytes,save_raw_proof=self.sink.raw_proof)
        self.physical=physical.PhysicalGuard(vehicle=native.vehicle,native=native,method=self.method,geometry=context['geometry'])
        arrays=context['generation_reader'].arrays('nominal');states=arrays['states']
        self.reference=fixed.FixedResponse(states=states.tolist(),origin_native=native.applied,
            origin_sim_time=self.method['base_method']['fixed_origin_sim_time'],
            expected_state_bytes_sha256=hashlib.sha256(states.tobytes()).hexdigest(),
            method_sha256=self.method['response_method_sha256'],nominal_native=self.proposal['nominal_native'])
        self.tracker=tracker.SegmentTracker(self.method['actual_next_segment'],origin_body=list(native.vehicle.body()),
            origin_native=native.applied,origin_sim_time=float(native.vehicle.d.time))
        self.installed=False

    def save_method_receipt(self,value):
        with self.sink.scope.activate():
            self.sink.journal.write(self.sink.codec.encoded(dict(kind='METHOD_MEMORY',receipt=value)).decode()+'\n')
            self.sink.journal.flush();self.sink.codec.sync_readonly(self.sink.folder/'APPLIED_JOURNAL.jsonl')

    def authorize_goal_bound_execution(self,*,native,method,proposal):
        self.guard.check();assert native is self.native and method==self.method and proposal==self.proposal
        q=json.loads((R/self.guard.authority['source_qualification_path']).read_text())
        assert q['passed']and q['closed']and q['models']==0 and q['physical_native']==0
        assert all(q['source_gates'][k]for k in ('goal_bound_policy','variable_complete_witness','current_source_runtime_binding',
            'current_CPP2200_API','actual_durable_policy_and_reference','actual_lifecycle_and_replay_source_pipeline'))
        return dict(actual_source_content_verified=True,same_current_input_complete_witness_qualified=True,
            current_CPP2200_same_model_branch_and_source_qualified=True,actual_policy_source_qualified=True,
            fixed_reference_source_qualified=True,source_control_coverage_fullstate_replay_pair_source_qualified=True,
            actual_runtime_qualified=False,whole_route_passed=False)

    def install(self):
        assert not self.installed;self.guard.check();n=self.native
        n.reserve=self.reserve;n.physical_guard=self.physical;n.sink=self.sink;n.bridge_started=True
        n.before_native_budget=self.native_budget
        self.execution=self.execution_module.Execution(native=n,tracker=self.tracker,proposal=self.proposal,
            reference=self.reference,components=self,method_memory=self.memory,method=self.method)
        self.installed=True;return self.execution

    def native_budget(self,stage,count):
        # The registered2200 nominal tail is part of normal method execution,
        # not an extra120s error-tail window. Its original zero request and
        # current2200 safety checks remain in NativeStep unchanged.
        if stage=='ACTUAL_STOP_TAIL':
            offset=self.native.applied-self.tracker.origin
            assert self.proposal['motion_native']<=offset<self.proposal['nominal_native']
            assert self.execution.inflight and not self.execution.closed
            return self.check_budget('ACTUAL_NATIVE',count)
        return self.check_budget(stage,count)

    def check_before_native(self,*,method,native,count):
        self.guard.check();assert method==self.method and native is self.native and count==1
        self.check_budget('ACTUAL_NATIVE',1)
        assert self.memory.current()['covered_native']==native.applied

    def durable_applied_receipt(self,native,*,decision,tail):
        assert native is self.native
        value=copy.deepcopy(self.sink.last_applied_receipt)
        assert value['after_native']==native.applied and value['row']['before_native']==native.applied-1
        assert value['row']==native.events[-1]
        clean=copy.deepcopy(value);identity=clean.pop('durable_receipt_sha256');assert digest(clean)==identity
        return value

    def method_transition(self,memory,row,receipt,*,decision):
        assert row['before_native']==memory['covered_native']and receipt['after_native']==row['before_native']+1
        v,w=row['request'][:2]
        value=dict(before_native=row['before_native'],after_native=receipt['after_native'],epoch_native=memory['epoch_native'],
            response_method_sha256=self.method['response_method_sha256'],actual_sensor_claim=False,
            load_before=memory['steering_load_episode'],load_after=self.memory_module.next_load(memory['steering_load_episode'],v,row['parked_target']),
            applied_body=[v,w],parked_target=row['parked_target'],previous_chain_sha256=memory['chain_sha256'],
            decision_sha256=digest(dict(kind='FROZEN_ORIGINAL_FINAL2200_TAIL'))if decision is None else decision['decision_sha256'],
            source_packet_sha256=row['source_packet_sha256'],source_full_state_sha256=row['source_full_state_sha256'],
            after_full_state_sha256=receipt['after_full_state_sha256'],actual_receipt_sha256=receipt['durable_receipt_sha256'])
        value['chain_sha256']=digest(value);return value

    def close(self):self.sink.close(self.guard.counts())
