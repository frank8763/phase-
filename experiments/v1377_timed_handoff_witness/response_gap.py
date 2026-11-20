"""Re-read actual prior steering preparation, zero models and no state replay."""
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R,O,read,sha,json

def main():
    frozen=read(O/'RESPONSE_GAP_SOURCE_FREEZE.json');assert all(sha(R/p)==h for p,h in frozen['files'].items())
    rows=read(R/'runs/v858_nav2_verified/v1376/capture_main/APPLIED_JOURNAL.json');prep=[x for x in rows if x['phase']=='PREPARE_FORWARD']
    start=prep[0]['before_native'];end=prep[-1]['before_native']+1;origin=prep[0]['body'];following=rows[end]['body']
    measured=dict(actual_duration_s=(end-start)*.01,
        max_center_translation_m=max(math.dist(x['body'][:2],origin[:2]) for x in prep+[rows[end]]),
        max_abs_yaw_change_rad=max(abs(math.atan2(math.sin(x['body'][2]-origin[2]),math.cos(x['body'][2]-origin[2]))) for x in prep+[rows[end]]),
        maximum_body_speed_m_s=max(abs(x['body'][3]) for x in prep),maximum_abs_yaw_rate_rad_s=max(abs(x['body'][4]) for x in prep))
    saved=read(O/'ACTUAL_PREPARATION_RESPONSE_GAP.json');assert saved['before_native']==start and saved['after_native']==end
    assert saved['source_case_only'] is True and saved['not_a_state_general_response_envelope'] is True
    assert all(abs(saved[k]-v)<=1e-12 for k,v in measured.items())
    proof=dict(passed=True,source_case_only=True,metrics=measured,no_new_vehicle_or_replay=True,models=0,physical_native=0,replay_native=0)
    p=O/'RESPONSE_GAP_READBACK.json';assert not p.exists();p.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
    assert all(sha(R/p)==h for p,h in frozen['files'].items())
if __name__=='__main__':main()
