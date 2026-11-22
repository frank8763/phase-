"""Current measured source + carried epoch -> full CPP2200 before actual action.

The Engine is constructed once during stopped preparation, before a fresh
command. Each call supplies only its actual current origin; subsequent states
are this branch's own outputs. No numerical operation on import.
"""
import copy
import hashlib
import importlib.util
from pathlib import Path
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent


def exact(name,path,guard):
    guard.check();assert hashlib.sha256(path.read_bytes()).hexdigest()==guard.source[str(path.relative_to(R))]
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def current_carrier(defs,engine,origin,packet,gear_memory,method,guard):
    old=exact('v1588_current_exact_cpp_advance',R/'experiments/v1550_canonical_observer_policy/trajectory.py',guard)
    batch=exact('v1588_current_exact_zero_batch',R/'experiments/v1571_complete_batch_comparison/batch_backend.py',guard)
    class CurrentTrajectory(old.CPPTrajectory):
        stage='CURRENT_CPP_RESERVE'
        def __init__(self):
            # The original constructor describes an event-origin trajectory.
            # Current callbacks retain that event CLOCK but use the present
            # origin, measured front encoders, mode and exact current gear.
            base=method['base_method'];self.guard=guard;self.engine=engine
            self.origin=copy.deepcopy(origin);self.base_native=base['fixed_origin_native']
            self.base_time=base['fixed_origin_sim_time'];self.native=packet['native_tick'];self.steps=0
            self.front_origin=[*origin['front_position'],*origin['front_velocity']]
            self.gear=old.new_gear(copy.deepcopy(gear_memory),guard)
            self.feedback=old.exact('v1588_current_branch_feedback',old.FEEDBACK,guard)
            self.parked_target=packet['parked_target']
            assert self.gear.last_tick==self.native-1
    class CurrentBatch(batch.BatchCarrier):stage='CURRENT_CPP_RESERVE'
    return CurrentBatch(CurrentTrajectory())


class CurrentReserve:
    def __init__(self,*,method,setup,defs,guard,current_method_memory,current_gear,
                 save_origin,save_complete,save_partial,save_after_gate,save_raw_bytes,save_raw_proof):
        guard.check();guard.require_live_component('CURRENT_CPP_RESERVE',method)
        assert guard.active_phase=='CURRENT_CPP_RESERVE'and guard.live_dependency
        self.method=copy.deepcopy(method);self.setup=copy.deepcopy(setup);self.defs=defs;self.guard=guard
        self.memory=current_method_memory;self.gear=current_gear
        self.save_origin=save_origin;self.save_complete=save_complete;self.save_partial=save_partial
        self.save_after_gate=save_after_gate;self.save_raw_bytes=save_raw_bytes;self.save_raw_proof=save_raw_proof
        self.failed=False;self.in_call=False
        self.evidence=exact('v1588_same_complete13array_schema',R/'experiments/v1552_complete_canonical_witness/evidence.py',guard)
        self.gates=exact('v1588_current_complete_gates',C/'gates.py',guard)
        self.geometry=guard.geometry
        assert self.geometry is not None and method['geometry_kind']=='ORIGINAL_CAUSAL_TIME_POLYGONS'
        self.failure=exact('v1588_same_raw_return_save',R/'experiments/v1571_complete_batch_comparison/batch_failure.py',guard)
        params=exact('v1588_current_json_io',C/'current_input.py',guard)
        import json
        parameters_path=R/'experiments/v1159_bounded_steering_load/PARAMETERS.json'
        assert hashlib.sha256(parameters_path.read_bytes()).hexdigest()==guard.source[str(parameters_path.relative_to(R))]
        parameters=json.loads(parameters_path.read_text())
        assert Path(defs['engine'].Engine.__init__.__code__.co_filename).resolve()==R/'experiments/v1159_bounded_steering_load/engine.py'
        guard.begin('CURRENT_CPP_RESERVE','Engine')
        self.engine=defs['engine'].Engine(setup,parameters['coefficients'])
        guard.completed('CURRENT_CPP_RESERVE','Engine')
        self.digest=params.digest

    def __call__(self,packet,modes):
        assert not self.failed and not self.in_call,'CURRENT_RESERVE_NOT_RETRIED_AFTER_FAILURE'
        self.failed=True;self.in_call=True;started=time.monotonic()
        memory=None;gear=None
        carrier=None;branch=None;attempted=False;origin_saved=False;first=None
        source_identity=None
        try:
            source_identity=self.digest(packet)
            memory=copy.deepcopy(self.memory());gear=copy.deepcopy(self.gear())
            assert all(packet[k]==modes[k]for k in ('coupled_episode','steering_motion_active','parked_target'))
            self.guard.require_current_reserve_source(packet,memory,gear)
            assert Path(self.defs['runtime'].initial.__code__.co_filename).resolve()==R/'experiments/v1118_coupled_live_qualification/runtime.py'
            origin=self.defs['runtime'].initial(copy.deepcopy(packet))
            origin['steering_load_episode']=memory['steering_load_episode']
            # This durable record precedes any native or FFI call and retains
            # the current measured metadata without inventing model timestamps.
            self.save_origin(dict(source_packet=copy.deepcopy(packet),source_packet_sha256=source_identity,
                method_memory=memory,gear_memory=gear,origin={k:v.tolist()if hasattr(v,'tolist')else copy.deepcopy(v)for k,v in origin.items()},
                model_counts=self.guard.counts(),stored_before_any_native=True))
            origin_saved=True
            carrier=current_carrier(self.defs,self.engine,origin,packet,gear,self.method,self.guard)
            branch=self.evidence.Branch(carrier);carrier.fill_complete_stop(branch)
            arrays=branch.arrays();attempted=True
            saved=self.save_complete(arrays,dict(source_packet_sha256=source_identity,method_memory=memory,
                response_method_sha256=self.method['response_method_sha256'],complete_native=2200,
                model_counts=self.guard.counts(),stored_before_gate=True))
            assert saved['all13arrays_durable']is True
            proof=self.gates.evaluate(arrays,self.method,self.setup,self.geometry,
                expected_native=2200,zero_suffix=2200,raw_current_only=True)
            answer=dict(passed=proof['passed'],before_native=packet['native_tick'],complete_native=2200,
                source_packet_sha256=source_identity,causal_snapshot_sha256=self.method['causal_snapshot_sha256'],
                causal_tube_lower_m=proof['causal_tube_lower_m'],full_checks=proof['checks'],
                model_variant='V1159_BOUNDED_STEERING_LOAD_OVER_V1114',
                model_feedback='CURRENT_BRANCH_SCALAR_AFTER_MEASURED_ORIGIN',
                minimum200_preserved=True,all_arrays_saved_before_gate=True,
                method_memory_epoch_native=memory['epoch_native'],method_memory_covered_native=memory['covered_native'],
                response_method_sha256=self.method['response_method_sha256'],
                callback_wall_s=time.monotonic()-started,timing_is_single_observation=True,
                timing_qualification_inferred=False)
            self.save_after_gate(answer,saved)
            assert self.digest(packet)==source_identity,'CURRENT_RESERVE_PACKET_MUTATED'
            assert proof['passed'],'CURRENT_COMPLETE2200_RESERVE_REFUSED'
            self.failed=False
            return answer,arrays['states'],arrays['ctrl']
        except BaseException as error:
            first=repr(error)
            failure=dict(first_error=first,traceback=traceback.format_exc(),source_packet=copy.deepcopy(packet),
                current_method_memory=memory,current_gear=gear,model_counts=self.guard.counts(),
                complete_certificate=False,origin_saved=origin_saved,large_array_save_already_attempted=attempted,
                callback_wall_s=time.monotonic()-started)
            if carrier is not None and carrier.batch_return is not None:
                try:failure['raw_return_preservation']=self.failure.preserve(carrier,save_bytes=self.save_raw_bytes,
                    save_proof=self.save_raw_proof,accounting=self.guard.counts())
                except BaseException as secondary:failure['secondary_raw_save_error']=repr(secondary)
            try:self.save_partial(failure,None if branch is None or attempted else branch.arrays())
            except BaseException as secondary:
                # Caller preserves original error even when its evidence sink
                # fails. Do not reserialize or rerun the large branch.
                error.secondary_current_save=repr(secondary)
            raise
        finally:self.in_call=False
