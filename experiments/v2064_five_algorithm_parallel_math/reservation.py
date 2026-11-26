from pathlib import Path
import json
R=Path(__file__).resolve().parents[2];S=R/'runs/v2064_five_algorithm_parallel_math'
def admission():
 x=json.loads((S/'RESERVATION.json').read_text());assert x['passed']and x['joint_peak_bytes']==16095019008<16106127360 and x['new_math_peak_bytes']==16*1024**2
 assert x['existing_unexecuted_SVG_component_peak_bytes']==34*1024**2+256*1024 and x['new_math_peak_bytes']+x['existing_unexecuted_SVG_component_peak_bytes']<=240*1024**2 and x['RPP224MiB_retention_bank_untouched']
 assert not(R/'runs/v2055_svg_vehicle_stop_component/PILOT_ONCE_CLAIM.json').exists()and not(R/'runs/v2059_svg_recovered_queue_prerequisite/PILOT_ONCE_CLAIM.json').exists()
 for i in range(10,13):assert json.loads((R/'runs/v2045_remaining_parallel_source/rounds'/f'common_{i:02d}__RPP/POST_ROUND_STORAGE_BARRIER.json').read_text())['passed']
 return x
def transport_current_upper():return admission()['joint_peak_bytes']-(4+512)*1024**2
