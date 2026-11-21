"""Current origin projection with complete diagnostics saved before refusal."""
import copy
import fcntl
import hashlib
import json
import math
import os
import time
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
class OriginRefusal(AssertionError):
    def __init__(self,message,proof,secondary=None):super().__init__(message);self.proof=proof;self.secondary=secondary
def prepare(method,*,runtime,save_proof,scope,authority,lock):
    """Pure original initial() only. Predictors/Engine are never constructed here.

    Source qualification may execute this coordinate conversion under a
    no-constructor profile. The numerical owner separately admits model work.
    """
    proof=dict(passed=False,scope=scope,stage='binding',origin=None,initial_state=None,
               initial_memory=None,method_epoch_qualified=False,models_constructed=0,
               numerical_integrations=0,physical_permission=False)
    first=None;value=None
    try:
        assert scope in {'SOURCE_ORIGIN_ONLY','ADMITTED_STOP_COMPONENT_ORIGIN'}
        assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(R)
        assert Path('/proc/self/fd/'+str(lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock'
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert authority['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        assert time.time()<authority['absolute_deadline_unix']<=1795395600 and time.monotonic()<authority['hard_stop_monotonic']
        parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
        if scope=='SOURCE_ORIGIN_ONLY':
            assert authority['scope']=='SOURCE_ORIGIN_ONLY'and authority['models_authorized']is False
            assert parent['active_round']is None and not parent['models_now_authorized']
        else:
            assert authority['scope']=='CURRENT_ORIGIN_COMPLETE_STOP_COMPONENT'and authority['models_authorized']is True
            assert parent['active_round']==authority['round_id']=='v1536_review_precharge_source'and parent['models_now_authorized']
        clean=copy.deepcopy(method);identity=clean.pop('method_input_sha256');assert digest(clean)==identity==authority['current_input_sha256']
        assert method['scientific_integration_revision']==8 and method['model_variant']=='V1159_BOUNDED_STEERING_LOAD_OVER_V1114'
        assert method['not_fresh_wire']and not method['physical_permission']
        physical=method['physical_source'];body=physical['packet'];original=dict(physical);physical_id=original.pop('input_sha256')
        assert digest(original)==physical_id==method['physical_source_input_sha256']
        memory=method['method_memory'];assert memory['steering_load_episode']is False and memory['actual_sensor_claim']is False
        assert memory['epoch_policy']=='ORIGINAL_OBSERVER_ENTRY_LOAD_FALSE_ONLY_AT_DECLARED_EVENT'
        assert memory['epoch_native']==method['fixed_origin_native']==body['native_tick']
        assert memory['epoch_sim_time']==method['fixed_origin_sim_time']==body['sim_time']
        assert body['coupled_episode']is False and body['steering_motion_active']is False and body['parked_target']is None
        assert Path(runtime.initial.__code__.co_filename).resolve()==R/'experiments/v1118_coupled_live_qualification/runtime.py'
        proof['stage']='original_numeric_projection'
        value=runtime.initial(copy.deepcopy(body));value['steering_load_episode']=False
        # Retain raw coordinate bytes and JSON diagnostics before value gates.
        def diagnostic(v):
            if hasattr(v,'tolist'):return diagnostic(v.tolist())
            if type(v)is float and not math.isfinite(v):return dict(nonfinite_repr=repr(v))
            if isinstance(v,list):return [diagnostic(x)for x in v]
            if isinstance(v,dict):return {k:diagnostic(x)for k,x in v.items()}
            return v
        proof['origin']=diagnostic(value)
        import numpy as np
        state=np.asarray(value['state']);last=np.asarray(value['last_ctrl'])
        proof['initial_state_bytes']=dict(dtype=str(state.dtype),shape=list(state.shape),hex=state.tobytes().hex())
        proof['initial_last_ctrl_bytes']=dict(dtype=str(last.dtype),shape=list(last.shape),hex=last.tobytes().hex())
        proof.update(initial_state=diagnostic(state),initial_memory=diagnostic([*value['last_ctrl'],value['integral']]),
                     method_input_sha256=identity,physical_source_input_sha256=physical_id,
                     fixed_origin_native=method['fixed_origin_native'],fixed_origin_sim_time=method['fixed_origin_sim_time'],
                     explicit_method_epoch=copy.deepcopy(memory),stage='projection_checks')
        close=lambda a,b:float(np.max(np.abs(np.asarray(a)-np.asarray(b))))<=1e-8
        checks=dict(state8=state.shape==(8,)and bool(np.isfinite(state).all()),
                    memory4=last.shape==(4,)and bool(np.isfinite(last).all())and math.isfinite(float(value['integral'])),
                    body=close(state[[0,1,2,3,5]],body['body']),
                    lateral=abs(float(state[4])-body['body_lateral'])<=1e-8,
                    last_ctrl=close(last,body['controller_memory']['last_ctrl']),
                    integral=value['integral']==body['controller_memory']['integral'],
                    front_position=value['front_position']==body['steering']['position'],
                    front_velocity=value['front_velocity']==body['steering']['velocity'],
                    unchanged_mode=value['coupled_episode']is body['coupled_episode']and value['steering_motion_active']is body['steering_motion_active'],
                    separate_explicit_load=value['steering_load_episode']is False and 'steering_load_episode'not in body)
        proof['checks']=checks
        if all(checks.values()):proof.update(passed=True,stage='converted_saved_before_gate',source_metadata_not_model_sensor_timestamp=True)
        else:
            first='CURRENT_ORIGIN_CONVERSION_REFUSED:CURRENT_ORIGIN_PROJECTION_MISMATCH'
            proof.update(first_error=first,failed_stage=proof['stage'])
    except BaseException as error:
        first='CURRENT_ORIGIN_CONVERSION_REFUSED:'+repr(error);proof.update(first_error=first,failed_stage=proof['stage'])
    secondary=None
    try:save_proof(proof)
    except BaseException as error:secondary=repr(error)
    if first is not None or secondary is not None:raise OriginRefusal(first or'CURRENT_ORIGIN_PROOF_SAVE_FAILED',proof,secondary)
    return value
