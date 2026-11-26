from pathlib import Path
import json
R=Path(__file__).resolve().parents[2];S=R/'runs/v2052_svg_registered_causal_solver'
def admission():
 b=json.loads((S/'PREPARATION_RESERVATION.json').read_text());assert b['passed']and b['existing_preparation_allocated_bound_bytes']<=8*1024**2 and b['new_subset_peak_bytes']==8*1024**2 and b['whole_preparation_cap_bytes']==16*1024**2;assert b['joint_peak_bytes']==16095019008<16106127360;return dict(passed=True,joint_peak_bytes=b['joint_peak_bytes'],no_new_plant=True,unchanged_original_preparation_cap=True)
def transport_current_upper():return admission()['joint_peak_bytes']-(2+512)*1024**2
