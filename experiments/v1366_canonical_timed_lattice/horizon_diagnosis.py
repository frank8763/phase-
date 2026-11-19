"""One120s same-prefix nominal-time diagnostic with original1.5s online cap."""
import copy
import json
import os
import time
import numpy as np
from planner import R,C,O
from horizon_planner import solve_horizon
from build_polygons import clipped
from all_returns import module


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'HORIZON120_RESULT.json';assert not target.exists()
    graph=json.loads((O/'GRAPH_INPUT.json').read_text());stamp=graph['request']['sim_time']
    old=json.loads((R/'runs/v1362_terminal_route_diagnosis/CONNECTIVITY_AND_SHAPE.json').read_text());vertices=old['coefficient_snapshot']['vertices']
    support_module=module('same_causal_interval_120s',R/'experiments/v1020_terminal_two_route_development/periodic_support.py')
    normal=np.c_[np.cos(np.arange(16)*np.pi/8),np.sin(np.arange(16)*np.pi/8)];polygons=[];boxes=[]
    for tick in range(601):
        bounds=support_module.swept_bounds(vertices,stamp+tick*.2-.2,stamp+(tick+1)*.2+.2)
        lo=-bounds[[8,12]];hi=bounds[[0,4]];boxes.append([*((lo+hi)/2),*((hi-lo)/2)])
        polygons.append(clipped(normal,bounds+.1).tolist())
    graph['center_rectangle_table']=boxes;prepared=time.monotonic();result=solve_horizon(graph,polygons=polygons,adaptive=True)
    result.update(nominal_horizon_s=120,forecast_preprocessing_s=prepared-begin,original_operational_speed_cap_m_s=.1,
        same_source_tick=old['coefficient_source_tick'],same_total_rest_wait_cap_s=40.,forecast_polygons=polygons,
        models=0,physical_native=0,actual_timing_response_qualified=False,physical_window_still_closed=True)
    target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['path','forecast_polygons']}))


if __name__=='__main__':main()
