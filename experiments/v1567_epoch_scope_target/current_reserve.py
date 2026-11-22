"""Draft full2200 reserve from CURRENT measured origin and carried method state.

No construction/import of numerical modules without a separately qualified
current-reserve Guard. V1563 private Guard has no such capability and is refused.
The original entry epoch is never reset at a later callback.
"""
import copy
import hashlib
import importlib.util
from pathlib import Path
import traceback

R=Path(__file__).resolve().parents[2]

def exact(name,relative,guard):
    guard.check()
    path=R/relative
    assert hashlib.sha256(path.read_bytes()).hexdigest()==guard.source[relative]
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

class CurrentStopTrajectory:
    stage='CURRENT_RESERVE'

    def __init__(self,*,defs,setup,packet,method_memory,gear_memory,method,guard):
        guard.require_current_reserve(method,packet,method_memory,gear_memory,native_cap=2200)
        assert Path(defs['model'].Predictor.__init__.__code__.co_filename).resolve()==R/'experiments/v1159_bounded_steering_load/model.py'
        assert Path(defs['runtime'].initial.__code__.co_filename).resolve()==R/'experiments/v1118_coupled_live_qualification/runtime.py'
        self.guard=guard
        base=method['base_method']
        self.base_native=base['fixed_origin_native'];self.base_time=base['fixed_origin_sim_time']
        self.native=packet['native_tick']
        assert abs(packet['sim_time']-(self.base_time+.01*(self.native-self.base_native)))<=1e-8
        assert method_memory['epoch_native']==self.base_native
        assert method_memory['covered_native']==self.native
        assert method_memory['actual_sensor_claim']is False
        assert type(method_memory['steering_load_episode'])is bool
        assert method_memory['response_method_sha256']==method['response_method_sha256']
        assert type(method_memory['chain_sha256'])is str and len(method_memory['chain_sha256'])==64
        assert gear_memory['last_tick']==self.native-1
        gear=exact('v1566_original_current_gear','experiments/v1396_rpp_rpc_retirement/gear_handoff.py',guard)
        self.gear=gear.GearHandoff()
        for key in ('gear','last_tick','brake_start'):setattr(self.gear,key,gear_memory[key])
        self.feedback=exact('v1566_original_current_feedback','experiments/v1409_scalar_steering_feedback/feedback.py',guard)
        origin=defs['runtime'].initial(copy.deepcopy(packet))
        # Current carried method state, never a default/reset False.
        origin['steering_load_episode']=method_memory['steering_load_episode']
        guard.save_current_origin_before_construction(origin,packet,method_memory,gear_memory)
        guard.begin(self.stage,'Predictor')
        self.p=defs['model'].Predictor(setup,origin)
        guard.completed(self.stage,'Predictor')
        p=self.p;p.adapter.encoders=lambda:self.feedback.current(p)
        p.adapter.parked_target=packet['parked_target']
        assert p.coupled_episode==packet['coupled_episode']
        assert bool(getattr(p.adapter,'_steering_motion_active',False))==packet['steering_motion_active']
        assert list(self.feedback.current(p))==[*packet['steering']['position'],*packet['steering']['velocity']]

    def snapshot(self):
        p=self.p
        assert p.high_speed_episode is False
        return dict(state=p.state.copy(),memory=[*p.adapter.last,float(p.adapter.integral)],
            modes=[int(p.coupled_episode),int(getattr(p.adapter,'_steering_motion_active',False)),int(p.steering_load_episode)],
            parked_target=getattr(p.adapter,'parked_target',None),encoders=list(self.feedback.current(p)),
            gear=[self.gear.gear,self.gear.last_tick,-1 if self.gear.brake_start is None else self.gear.brake_start],
            native=self.native,sim_time=self.base_time+.01*(self.native-self.base_native))

    def advance(self,raw):
        self.guard.check();assert raw==(0.,0.,0)
        before=self.snapshot();candidate=copy.deepcopy(self.gear);s=before['state']
        v,w,proof=candidate.select(0.,0.,native_tick=self.native,body=[*s[:4],s[5]],last_ctrl=before['memory'][:4],encoders=before['encoders'])
        self.p.adapter.parked_target=None
        self.gear=candidate
        self.guard.begin(self.stage,'native')
        state,control=self.p.step(v,w,False)
        self.guard.completed(self.stage,'native');self.native+=1
        return dict(before=before,after=self.snapshot(),raw=raw,requested=(0.,0.),applied=(v,w),gear_proof=proof,ctrl=control.copy())

class CurrentReserve:
    def __init__(self,*,method,setup,defs,guard,current_method_memory,current_gear,save_complete,save_partial):
        guard.require_current_reserve_components(method,complete_native=2200)
        self.method=copy.deepcopy(method);self.setup=copy.deepcopy(setup);self.defs=defs;self.guard=guard
        self.current_method_memory=current_method_memory;self.current_gear=current_gear
        self.save_complete=save_complete;self.save_partial=save_partial
        self.snapshot_sha256=method['causal_snapshot_sha256']
        self.evidence=exact('v1566_full_current_schema','experiments/v1552_complete_canonical_witness/evidence.py',guard)
        self.gates=exact('v1566_unchanged_2200_gates','experiments/v1552_complete_canonical_witness/gates.py',guard)
        self.geometry,self.forecast=self.gates.geometry(method,setup,guard)

    def __call__(self,packet,modes):
        import json
        digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        self.guard.check()
        assert modes['covered_native']==packet['native_tick']
        assert all(packet[k]==modes[k]for k in ('coupled_episode','steering_motion_active','parked_target'))
        identity=digest(packet);memory=copy.deepcopy(self.current_method_memory())
        trajectory=None;branch=None;attempted=False
        try:
            trajectory=CurrentStopTrajectory(defs=self.defs,setup=self.setup,packet=packet,method_memory=memory,
                gear_memory=copy.deepcopy(self.current_gear()),method=self.method,guard=self.guard)
            branch=self.evidence.Branch(trajectory)
            for _ in range(2200):branch.advance(trajectory,(0.,0.,0))
            arrays=branch.arrays()
            # Complete13arrays must be durable before evaluating geometry or
            # caps. Save callbacks may not retry a failed large-array write.
            attempted=True
            saved=self.save_complete(arrays,dict(source_packet_sha256=identity,current_method_memory=memory,
                response_method_sha256=self.method['response_method_sha256'],model_counts=self.guard.counts(),
                complete_native=2200,stored_before_gate=True))
            assert saved['all13arrays_durable']is True
            proof=self.gates.evaluate(arrays,self.method,self.setup,self.geometry,expected_native=2200,zero_suffix=2200,raw_current_only=True)
            assert digest(packet)==identity
            answer=dict(passed=proof['passed'],before_native=packet['native_tick'],complete_native=2200,
                source_packet_sha256=identity,causal_snapshot_sha256=self.snapshot_sha256,
                causal_tube_lower_m=proof['causal_tube_lower_m'],full_checks=proof['checks'],
                model_variant='V1159_BOUNDED_STEERING_LOAD_OVER_V1114',model_feedback='CURRENT_BRANCH_SCALAR_AFTER_MEASURED_ORIGIN',
                minimum200_preserved=True,all_arrays_saved_before_gate=True,
                method_memory_epoch_native=memory['epoch_native'],method_memory_covered_native=memory['covered_native'],
                response_method_sha256=self.method['response_method_sha256'])
            self.guard.save_after_gate(answer,saved)
            return answer,arrays['states'],arrays['ctrl']
        except BaseException as error:
            failure=dict(first_error=repr(error),traceback=traceback.format_exc(),source_packet=copy.deepcopy(packet),
                current_method_memory=memory,model_counts=self.guard.counts(),complete_certificate=False,
                large_array_save_already_attempted=attempted)
            try:self.save_partial(failure,None if branch is None or attempted else branch.arrays())
            except BaseException as secondary:
                failure['secondary_save_error']=repr(secondary)
                self.guard.save_secondary_failure(failure)
            raise
