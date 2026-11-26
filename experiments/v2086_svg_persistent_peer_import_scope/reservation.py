"""Carve 56.25 MiB from completed RPP archive space, retain its 224 MiB bank."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2];O=R/'runs/v2086_svg_persistent_peer_import_scope';S=R/'runs/v2045_remaining_parallel_source'
def admission():
 prior=R/'runs/v2055_svg_vehicle_stop_component';assert not(prior/'PILOT_ONCE_CLAIM.json').exists()and not(prior/'actual').exists(),'PRIOR_COMPONENT_MUST_REMAIN_UNEXECUTED'
 x=json.loads((O/'RESERVATION.json').read_text());b=json.loads((S/'QUIESCENT_BASELINE.json').read_text());assert x['passed']and x['joint_peak_bytes']==b['joint_peak_bytes']==16095019008<16106127360
 assert x['component_peak_bytes']==(56*1024**2+256*1024)and x['from_completed_RPP_archive_bytes']==240*1024**2 and x['component_peak_bytes']<=x['from_completed_RPP_archive_bytes']
 assert x['RPP_224MiB_retention_bank_untouched']and x['no_concurrent_Phase_actual_model_permission']
 for i in range(10,13):assert json.loads((S/'rounds'/f'common_{i:02d}__RPP'/'POST_ROUND_STORAGE_BARRIER.json').read_text())['passed']
 assert x['combined_RPP_archive_subgrants_bytes']==2*(34*1024**2+256*1024)+16*1024**2+(56*1024**2+256*1024)<x['from_completed_RPP_archive_bytes']
 assert json.loads((R/'runs/v2073_svg_parameter_inheritance_scope/POST_COMPONENT_STORAGE_BARRIER.json').read_text())['passed']
 return x
def transport_current_upper():return admission()['joint_peak_bytes']-(16+512)*1024**2
