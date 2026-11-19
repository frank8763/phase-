"""Finite speed/time feasibility counterfactual, never changes old Twist limit."""
import json
import os
from pathlib import Path
import time
from planner import solve,R,C,O
from retime import retime


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'TIMING_DIAGNOSIS.json';assert not target.exists()
    guard=(R/'REVIEW_PENDING').read_bytes();pointer=(R/'CURRENT_EXPERIMENT.json').read_bytes()
    graph=json.loads((O/'GRAPH_INPUT.json').read_text());polygons=json.loads((O/'FORECAST_POLYGONS.json').read_text())['polygons'];cases=[]
    selected=None
    for cap in [.1,.15,.2]:
        prep=time.monotonic();candidate=retime(graph,cap);preprocessing=time.monotonic()-prep
        result=solve(candidate,polygons=polygons,adaptive=True)
        result.update(diagnostic_speed_cap_m_s=cap,retiming_preprocessing_s=preprocessing,
                      original_operational_contract_compatible=cap==.1,actual_controls_qualified=False)
        cases.append(result);print(json.dumps({k:v for k,v in result.items() if k!='path'}),flush=True)
        if result['code']==0:
            selected=cap;(O/'SELECTED_NOMINAL_GRAPH.json').write_text(json.dumps(candidate,separators=(',',':'))+'\n');break
    proof=dict(cases=cases,first_nominal_positive_speed=selected,speed_caps_preregistered=[.1,.15,.2],higher_caps_not_applied=True,
        operational_speed_contract_unchanged_m_s=.1,models=0,physical_native=0,physical_launch_allowed=False,
        wall_s=time.monotonic()-begin,review_pending_unchanged=(R/'REVIEW_PENDING').read_bytes()==guard,current_pointer_unchanged=(R/'CURRENT_EXPERIMENT.json').read_bytes()==pointer)
    assert proof['review_pending_unchanged'] and proof['current_pointer_unchanged']
    target.write_text(json.dumps(proof,indent=2)+'\n')


if __name__=='__main__':main()
