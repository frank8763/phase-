"""Same declared M8 projection under the new explicit response capability."""
import copy
from pathlib import Path

R=Path(__file__).resolve().parents[2]


def prepare(method,defs,guard,save_proof):
    proof=dict(passed=False,models_constructed=0,numerical_native=0,
               response_method_sha256=method['response_method_sha256'],origin=None)
    first=None
    answer=None
    try:
        guard.check()
        base=method['base_method']
        assert method['response_method_sha256']==guard.input_sha
        assert base['method_input_sha256']==method['base_method_semantic_sha256']
        assert base['scientific_integration_revision']==8
        assert base['method_memory']['steering_load_episode'] is False
        assert base['method_memory']['actual_sensor_claim'] is False
        packet=base['physical_source']['packet']
        assert packet['coupled_episode'] is False and packet['steering_motion_active'] is False
        assert packet['parked_target'] is None
        assert Path(defs['runtime'].initial.__code__.co_filename).resolve()==R/'experiments/v1118_coupled_live_qualification/runtime.py'
        answer=defs['runtime'].initial(copy.deepcopy(packet))
        answer['steering_load_episode']=False
        import numpy as np
        close=lambda a,b:float(np.max(abs(np.asarray(a)-np.asarray(b))))<=1e-8
        proof['origin']={key:value.tolist() if hasattr(value,'tolist')else copy.deepcopy(value)for key,value in answer.items()}
        proof['initial_state_bytes']=dict(dtype=str(answer['state'].dtype),shape=list(answer['state'].shape),hex=answer['state'].tobytes().hex())
        proof['checks']=dict(state8=answer['state'].shape==(8,)and bool(np.isfinite(answer['state']).all()),
                body=close(answer['state'][[0,1,2,3,5]],packet['body']),
                lateral=abs(float(answer['state'][4])-packet['body_lateral'])<=1e-8,
                last_control=close(answer['last_ctrl'],packet['controller_memory']['last_ctrl']),
                integral=answer['integral']==packet['controller_memory']['integral'],
                encoders=close([*answer['front_position'],*answer['front_velocity']],[*packet['steering']['position'],*packet['steering']['velocity']]),
                coupled_unchanged=answer['coupled_episode'] is False,
                active_unchanged=answer['steering_motion_active'] is False,
                explicit_epoch_false=answer['steering_load_episode'] is False)
        proof['passed']=all(proof['checks'].values())
        if not proof['passed']:
            first='NEW_RESPONSE_CURRENT_ORIGIN_PROJECTION_REFUSED'
            proof['first_error']=first
    except BaseException as error:
        first=repr(error)
        proof['first_error']=first
    secondary=None
    try:
        save_proof(proof)
    except BaseException as error:
        secondary=repr(error)
    if first or secondary:
        error=AssertionError(first or 'NEW_RESPONSE_ORIGIN_PROOF_SAVE_REFUSED')
        error.secondary=secondary
        error.proof=proof
        raise error
    return answer
