"""Exact current-origin conversion, proof and original eight bytes before gate."""
import copy
import hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2]


def prepare(method,defs,guard,save_proof):
    proof=dict(passed=False,first_error=None,response_method_sha256=method['response_method_sha256'],
        origin=None,models_constructed=0,numerical_native=0,method_epoch_not_sensor=True)
    first=None;answer=None
    try:
        guard.check();guard.require_current_event_input(method)
        base=method['base_method'];packet=base['physical_source']['packet']
        assert base['scientific_integration_revision']==11
        assert base['method_memory']['steering_load_episode']is False
        assert base['method_memory']['actual_sensor_claim']is False
        assert Path(defs['runtime'].initial.__code__.co_filename).resolve()==R/'experiments/v1118_coupled_live_qualification/runtime.py'
        answer=defs['runtime'].initial(copy.deepcopy(packet))
        answer['steering_load_episode']=False
        import numpy as np
        view=np.asarray(answer['state'],dtype=np.float64).view();view.setflags(write=False)
        proof['origin']={k:v.tolist()if hasattr(v,'tolist')else copy.deepcopy(v)for k,v in answer.items()}
        proof['initial_state_bytes']=dict(dtype=str(view.dtype),shape=list(view.shape),hex=view.tobytes().hex(),sha256=hashlib.sha256(view.tobytes()).hexdigest())
        close=lambda a,b:float(np.max(abs(np.asarray(a)-np.asarray(b))))<=1e-8
        proof['checks']=dict(state8=view.shape==(8,)and bool(np.isfinite(view).all()),
            body=close(view[[0,1,2,3,5]],packet['body']),lateral=abs(float(view[4])-packet['body_lateral'])<=1e-8,
            last_control=close(answer['last_ctrl'],packet['controller_memory']['last_ctrl']),
            integral=answer['integral']==packet['controller_memory']['integral'],
            encoders=close([*answer['front_position'],*answer['front_velocity']],
                           [*packet['steering']['position'],*packet['steering']['velocity']]),
            coupled_unchanged=answer['coupled_episode']==packet['coupled_episode'],
            active_unchanged=answer['steering_motion_active']==packet['steering_motion_active'],
            declared_method_epoch_false=answer['steering_load_episode']is False)
        proof['passed']=all(proof['checks'].values())
        if not proof['passed']:first='CURRENT_EVENT_ORIGIN_PROJECTION_REFUSED';proof['first_error']=first
    except BaseException as error:first=repr(error);proof['first_error']=first
    secondary=None
    try:save_proof(proof)
    except BaseException as error:secondary=repr(error)
    if first or secondary:
        error=AssertionError(first or 'CURRENT_EVENT_ORIGIN_SAVE_REFUSED');error.proof=proof;error.secondary=secondary;raise error
    return answer
