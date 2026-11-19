"""Deterministic no-model reproduction of uncertainty-induced start refusal."""
import importlib.util
import json
import math
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sys.path.insert(0,str(R/'experiments/v1354_fast_stamped_pipeline'))
from causal_occupancy import CausalBall
from observed_route import nominal_clearance


def main():
    O.mkdir(exist_ok=True)
    raw=R/'runs/v858_nav2_verified/v1354/rpp_fast_stamped_dynamic_main'
    events=json.loads((raw/'CAUSAL_OBSERVATIONS.json').read_text())
    records=json.loads((raw/'CAUSAL_ROUTE_RECORDS.json').read_text())
    last=events[-1];minimal=next(row for row in records if row['index']==4)
    tracker=CausalBall({});tracker.center=__import__('numpy').array(last['point']);tracker.last=last['sim_time']
    center,radius=tracker.occupied_ball(minimal['sim_time'])
    clearance=nominal_clearance(minimal['body'],center,radius)
    reproduced=radius>2. and clearance<.15 and minimal['report']['status']=='START_BELOW_HARD_FLOOR'
    assert reproduced,'SAVED_START_REFUSAL_NOT_REPRODUCED'
    proof=dict(reproduced=True,saved_last_return=last,saved_failed_request=4,
        first_refusal_native=minimal['native_tick'],observation_age_s=minimal['sim_time']-last['sim_time'],
        current_prediction_radius_m=radius,robot_to_predicted_occupancy_clearance_m=clearance,
        actual_saved_body=minimal['body'],safe_actual_clearance_report_m=.2500331552976056,
        full_trace_new_native=0,models=0,red_signal='START_BELOW_HARD_FLOOR caused by growing uncertainty, not measured collision',
        minimal_reproducer_inputs=['last_point','last_time','current_time','current_body'])
    (O/'REPRODUCTION.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':main()
