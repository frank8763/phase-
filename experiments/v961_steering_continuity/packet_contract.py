"""Same causal physical packet plus actual steering at the same native tick."""
import importlib.util
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v961_base_packet',ROOT/'experiments/v945_rpccr_observation_liveness/packet_contract.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)


def policy_packet(run_id,vehicle,snapshot,snapshot_at,now,phase):
    packet=base.policy_packet(run_id,vehicle,snapshot,snapshot_at,now,phase)
    ids=np.asarray(vehicle.adapter.commands.ids[:2]);joints=vehicle.m.actuator_trnid[ids,0]
    q=vehicle.m.jnt_qposadr[joints];v=vehicle.m.jnt_dofadr[joints]
    packet['steering']=dict(native_tick=vehicle.count,measured_at=packet['body_measured_at'],
        position=vehicle.d.qpos[q].tolist(),velocity=vehicle.d.qvel[v].tolist())
    return packet
