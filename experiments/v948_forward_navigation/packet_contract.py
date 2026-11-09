"""Native mechanical encoders, measured coherently with the existing body packet."""
import importlib.util
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v945_packet_frozen',ROOT/'experiments/v945_rpccr_observation_liveness/packet_contract.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)


def policy_packet(run_id,vehicle,snapshot,snapshot_at,now,phase):
    packet=old.policy_packet(run_id,vehicle,snapshot,snapshot_at,now,phase)
    # Encoder addresses come from the two actual steering actuator transmissions.
    # Root/actor/general model state is never added to the online packet.
    joints=vehicle.m.actuator_trnid[np.asarray(vehicle.adapter.commands.ids[:2]),0]
    q=vehicle.m.jnt_qposadr[joints];v=vehicle.m.jnt_dofadr[joints]
    assert len(set(joints))==2 and np.all(q>=7) and np.all(v>=6),'INVALID_STEERING_ENCODER_MAPPING'
    position=vehicle.d.qpos[q];velocity=vehicle.d.qvel[v]
    assert np.isfinite([*position,*velocity]).all(),'NONFINITE_STEERING_ENCODERS'
    packet['steering']=dict(position=position.tolist(),velocity=velocity.tolist(),
                            native_tick=vehicle.count,measured_at=now)
    return packet
