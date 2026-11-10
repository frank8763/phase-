"""Declared V961 dependency, source-frozen before models."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v963_packet_contract',ROOT/'experiments/v961_steering_continuity/packet_contract.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def policy_packet(run_id,vehicle,snapshot,snapshot_at,now,phase):
    packet=module.policy_packet(run_id,vehicle,snapshot,snapshot_at,now,phase)
    packet['controller_memory']=dict(last_ctrl=vehicle.adapter.last.tolist(),integral=float(vehicle.adapter.integral))
    packet['profile_status']=getattr(vehicle,'profile_status',dict(active=False,completed_id=None))
    return packet
