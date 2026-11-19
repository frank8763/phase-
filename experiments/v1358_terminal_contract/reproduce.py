"""Two deterministic saved-tail contract red signals; zero physical models."""
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sys.path.insert(0,str(R/'experiments/v1357_expiry_evidence_relay'))
from recovery_guard import check


def main():
    O.mkdir(exist_ok=True);known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    root=R/'runs/v858_nav2_verified/v1357'
    plans=json.loads((root/'periodic_mode0_dynamic_main/CAUSAL_ROUTE_RECORDS.json').read_text())
    plan=next(p for p in plans if p['index']==10);path=np.asarray(plan['rear_path_with_gears']);last=path[-1]
    body=last[:2]+.3*np.array([math.cos(last[2]),math.sin(last[2])]);goal=np.array([4.,-2.]);distance=float(np.linalg.norm(body-goal))
    assert plan['report']['status']=='GLOBAL_GOAL_PATH' and distance>.45
    reserves=json.loads((root/'periodic_mode0_dynamic_main/RECOVERY_RESERVE_RECORDS.json').read_text())
    event=next(e for e in reserves if e['native_tick']==19650)
    allowed,proof=check(known,event['body'],*event['requested'])
    assert not allowed and proof['command_geometry_terminal_m']>proof['current_known_clearance_m']
    result=dict(reproduced=True,wrong_goal_label=dict(index=10,reported=plan['report']['status'],actual_nominal_body_goal_distance_m=distance,required_goal_radius_m=.45),
        recoverable_escape_refused=dict(native_tick=event['native_tick'],body=event['body'],requested=event['requested'],proof=proof),
        minimum_inputs=['terminal_pose_goal','current_body_requested_twist_known_geometry'],models=0,physical_native=0)
    (O/'ORIGINAL_REPRODUCTION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
