"""Exact-call-shape draft: batch ONLY identically zero tail after one old step.

No numerical import or construction on import. No expected arrays are inputs.
The new batch-capable Guard is deliberately absent from this preparation.
"""
import copy
import hashlib
import importlib.util
from pathlib import Path

R=Path(__file__).resolve().parents[2]
TRAJECTORY='experiments/v1550_canonical_observer_policy/trajectory.py'

def original_module(guard):
    guard.check()
    p=R/TRAJECTORY
    assert hashlib.sha256(p.read_bytes()).hexdigest()==guard.source[TRAJECTORY]
    spec=importlib.util.spec_from_file_location('v1569_exact_original_cpp_carrier',p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

class BatchCarrier:
    stage='CPP_AUDIT'

    def __init__(self,original):
        self.original=original

    @classmethod
    def create(cls,defs,setup,coefficients,origin,gear_memory,method,guard):
        # No numerical execution is licensed by the already closed old Guard.
        guard.require_exact_zero_tail_batch_capability(method,native_tail=2200)
        old=original_module(guard)
        return cls(old.CPPTrajectory.create(defs,setup,coefficients,origin,gear_memory,method,guard))

    @property
    def native(self):return self.original.native

    def snapshot(self):return self.original.snapshot()

    def fork(self):return type(self)(self.original.fork())

    def advance(self,raw):return self.original.advance(raw)

    def fill_complete_stop(self,branch):
        owner=self.original;guard=owner.guard
        guard.require_exact_zero_tail_batch_capability(None,native_tail=2200)
        # First measured-origin step and original mode transition unchanged.
        # Branch.advance invokes this wrapper's exact old advance once.
        branch.advance(self,(0.,0.,0))
        first=owner.snapshot();start_native=owner.native;n=2199
        assert owner.steps>=1
        assert first['parked_target']is None and first['modes'][1]==0
        engine_before=owner.engine.native
        origin=copy.deepcopy(owner.origin)
        guard.begin_batch(self.stage,'native',n)
        states,controls,memory=owner.engine.simulate(origin,[(0.,0.,n,0)])
        assert owner.engine.native-engine_before==n and owner.engine.in_call is False
        assert states.shape==(n+1,8)and controls.shape==(n,4)and memory.shape==(n+1,5)
        # Completion follows the successful FFI's own exact work, not the
        # later Python evidence reconstruction or file-save result.
        guard.completed_batch(self.stage,'native',n)
        assert states[0].tolist()==first['state'].tolist()
        assert memory[0].tolist()==list(first['memory'])
        gear=copy.deepcopy(owner.gear)
        before=first
        pending=[]
        for index in range(n):
            tick=start_native+index
            v,w,proof=gear.select(0.,0.,native_tick=tick,
                body=[*before['state'][:4],before['state'][5]],
                last_ctrl=before['memory'][:4],encoders=before['encoders'])
            assert v==w==0.,'ZERO_TAIL_GEAR_CHANGED_NUMERICAL_INPUT'
            after=dict(state=states[index+1].copy(),memory=memory[index+1].tolist(),
                modes=list(first['modes']),parked_target=None,
                encoders=list(owner.feedback.from_state(states[index+1])),
                gear=[gear.gear,gear.last_tick,-1 if gear.brake_start is None else gear.brake_start],
                native=tick+1,sim_time=owner.base_time+.01*(tick+1-owner.base_native))
            pending.append(dict(before=before,after=after,raw=(0.,0.,0),requested=(0.,0.),
                applied=(v,w),gear_proof=proof,ctrl=controls[index].copy()))
            before=after
        # Publish one complete numerical result and its reconstructed receipts.
        # No predicted state was supplied as a later FFI step's initial state.
        owner.origin.update(state=states[-1].copy(),last_ctrl=memory[-1,:4].copy(),integral=float(memory[-1,4]),
            coupled_episode=bool(first['modes'][0]),steering_motion_active=False,
            steering_load_episode=bool(first['modes'][2]))
        owner.gear=gear;owner.native+=n;owner.steps+=n;owner.parked_target=None
        assert owner.native==start_native+n
        assert before['state'].tolist()==owner.snapshot()['state'].tolist()
        branch.rows.extend(pending)
        return dict(complete_stop_native=2200,old_first_step_native=1,batch_native=n,
            FFI_calls=2,no_expected_arrays_as_numerical_input=True,physical_native=0,
            native_work_not_FFI_call_count=True,qualification_not_inferred=True)
