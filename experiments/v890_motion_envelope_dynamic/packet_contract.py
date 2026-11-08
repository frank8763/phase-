"""Add measured scan pose only; never actor or evaluator labels."""
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import policy_packet as original_packet
def policy_packet(run_id,vehicle,snapshot,snapshot_at,now,phase):
    packet=original_packet(run_id,vehicle,snapshot,snapshot_at,now,phase)
    packet['scan']['xy']=list(snapshot['xy']);packet['scan']['yaw']=float(snapshot['yaw'])
    return packet
