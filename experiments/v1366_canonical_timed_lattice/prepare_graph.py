"""One original saved input plus fixed entry-to-canonical polynomial witnesses."""
import importlib.util
import json
import math
import os
from pathlib import Path
import time
import numpy as np
from build_primitives import make_edge

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'GRAPH_INPUT.json';assert not target.exists()
    library=json.loads((O/'PRIMITIVES.json').read_text());edges=library['edges']
    assert len(edges)==128 and sum(e['start_heading']!=e['end_heading'] for e in edges)==64,'HEADING_LIBRARY_DISCONNECTED'
    req=json.loads((R/'runs/v1362_terminal_route_diagnosis/ORIGINAL_REQUEST03.json').read_text())
    journal=json.loads((R/'runs/v858_nav2_verified/v1361/sweep_terminal_dynamic_main/APPLIED_JOURNAL.json').read_text());event=journal[req['native_tick']]
    assert max(abs(a-b) for a,b in zip(event['body'],req['body']))<1e-8
    k=[math.tan(a)/(.6+side*.27*math.tan(a)) for a,side in zip(event['last_ctrl'][:2],[1,-1])]
    assert abs(k[0]-k[1])<1e-8
    entries=[]
    for edge in edges:
        if edge['start_heading']!=0:continue
        entry=make_edge(0,edge['end_heading'],edge['offset'],edge['gear'],sum(k)/2)
        if entry is not None:entry['start_heading']=16;entries.append(entry)
    assert entries and any(e['gear']<0 for e in entries) and any(e['gear']>0 for e in entries)
    edges=edges+entries
    # Retain the original coefficient source and timing table unchanged.
    saved=json.loads((R/'runs/v1364_space_time_vehicle/KINODYNAMIC_RESULT.json').read_text())
    assert saved['source_tick']==req['native_tick']
    result=dict(request=req,headings=library['headings'],grid_step_m=.2,edges=edges,
        center_rectangle_table=saved['forecast_center_rectangle_table'],entry_edge_count=len(entries),
        initial_center_steering_rad=math.atan(.6*sum(k)/2),initial_gear=event['gear_handoff']['prior_gear'],
        actual_initial_memory=event['last_ctrl'],source_tick=saved['source_tick'],
        no_pose_snap=True,models=0,physical_native=0,wall_s=time.monotonic()-begin)
    target.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps(dict(edges=len(edges),entry_edges=len(entries),initial_gear=result['initial_gear'],wall_s=result['wall_s'],models=0)))


if __name__=='__main__':main()
