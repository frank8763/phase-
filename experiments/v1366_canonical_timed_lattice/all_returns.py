"""Causal all-novel-ray support on exactly the original received packet prefix."""
import gzip
import importlib.util
import json
import math
import os
from pathlib import Path
import time
import numpy as np
from build_polygons import clipped

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'ALL_RETURN_FORECAST.json';assert not target.exists()
    raw=R/'runs/v858_nav2_verified/v1361/sweep_terminal_dynamic_main';graph=json.loads((O/'GRAPH_INPUT.json').read_text());req=graph['request'];tick=req['native_tick']
    original=json.loads((raw/'CAUSAL_OBSERVATIONS.json').read_text());original=[z for z in original if z['native_tick']<=tick]
    with gzip.open(raw/'physics/SENSORS.json.gz','rt') as stream:packets={z['native_tick']:z for z in json.load(stream)}
    journal=json.loads((raw/'APPLIED_JOURNAL.json').read_text())
    legacy=module('unchanged_raw_ray_selector',R/'experiments/v1354_fast_stamped_pipeline/causal_occupancy.py')
    periodic=module('unchanged_periodic_coefficients',R/'experiments/v1037_periodic_norm_source/periodic_norm.py');tracker=periodic.PeriodicSupport()
    support_module=module('unchanged_periodic_interval',R/'experiments/v1020_terminal_two_route_development/periodic_support.py')
    normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)];records=[];first_error=0.
    for selected in original:
        t=selected['native_tick'];packet=packets[t];body=journal[t]['body'];ranges=np.asarray(packet['ranges'])
        assert np.max(abs(np.asarray(body[:2])-packet['xy']))<=1e-8
        expected,directions=legacy.static_ranges(np.asarray(body[:2]),body[2],req['known'])
        ids=np.flatnonzero((ranges<2.94)&(ranges+.12<expected))
        assert len(ids) and int(ids[0])==selected['ray']
        points=np.asarray(body[:2])+ranges[ids,None]*directions[ids]
        first_error=max(first_error,float(np.max(abs(points[0]-selected['point']))));assert first_error<1e-6
        support=np.min(points@normals.T+.24,axis=0)
        updated=tracker.update(selected['sim_time'],t,support.tolist())
        records.append(dict(native_tick=t,sim_time=selected['sim_time'],rays=ids.tolist(),points=points.tolist(),support=support.tolist(),coefficient_update=updated))
    polygons=[];supports=[];boxes=[]
    for i in range(401):
        bounds=support_module.swept_bounds([p.v for p in tracker.polytopes],req['sim_time']+i*.2-.2,req['sim_time']+(i+1)*.2+.2)+.1
        polygon=clipped(normals,bounds);polygons.append(polygon.tolist());supports.append(bounds.tolist())
        low=-bounds[[8,12]]+.1;high=bounds[[0,4]]-.1;boxes.append([*((low+high)/2),*((high-low)/2)])
    result=dict(records=records,polygons=polygons,supports=supports,normals=normals.tolist(),center_rectangle_table=boxes,
        coefficient_snapshot=tracker.snapshot(),coefficient_source_tick=tracker.source_tick,source_tick_limit=tick,
        original_received_novel_packets=len(original),all_novel_returns=sum(len(z['rays']) for z in records),
        multiple_return_packets=sum(len(z['rays'])>1 for z in records),original_first_selected_point_error_m=first_error,
        original_point_error_radius_unchanged_m=.24,extra_sensor_frames=0,future_observations=0,online_truth=False,
        models=0,physical_native=0,wall_s=time.monotonic()-begin)
    assert tracker.source_tick<=tick
    target.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['records','polygons','supports','normals','center_rectangle_table','coefficient_snapshot']}))


if __name__=='__main__':main()
