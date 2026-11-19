"""Independent original NumPy polygon geometry and evaluator-only coverage."""
import ast
import ctypes
import json
import math
import os
from pathlib import Path
import time
import numpy as np
from planner import _array,R,C,O


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'INDEPENDENT_POLYGON_AUDIT.json';assert not target.exists()
    original=R/'experiments/v934_rpccr_certified_recovery/polygon_geometry.py'
    function=next(n for n in ast.parse(original.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='distances')
    namespace=dict(np=np,math=math);exec(compile(ast.Module(body=[function],type_ignores=[]),str(original),'exec'),namespace)
    data=json.loads((O/'FORECAST_POLYGONS.json').read_text());polygons=data['polygons'];normals=np.array(data['normals']);supports=np.array(data['supports'])
    library=ctypes.CDLL(str(O/'libgraph_polygon.so'));probe=library.polygon_values_probe
    probe.argtypes=[_array,ctypes.c_int,_array,ctypes.c_int,ctypes.c_double,_array]
    rng=np.random.default_rng(1366);error=0.;reviewed=0
    for index in [0,23,101,203,400]:
        polygon=np.array(polygons[index]);rear=np.c_[rng.uniform(-4.,4.,600),rng.uniform(-4.,4.,600),rng.uniform(-math.pi,math.pi,600)]
        body=rear.copy();body[:,:2]+=.3*np.c_[np.cos(rear[:,2]),np.sin(rear[:,2])]
        reference=namespace['distances'](body,polygon);packed=np.zeros((16,2));packed[:len(polygon)]=polygon
        actual=np.empty(len(rear));probe(np.ascontiguousarray(rear),len(rear),packed,len(polygon),1e100,actual)
        error=max(error,float(np.max(abs(actual-reference))));assert np.max(abs(actual-reference))<1e-8
        probe(np.ascontiguousarray(rear),len(rear),packed,len(polygon),.274,actual)
        assert (actual<=reference+1e-8).all() and np.array_equal(actual>=.274,reference>=.274)
        reviewed+=len(rear)
    # No truth is an input to graph generation/forecast construction.
    actor=json.loads((R/'runs/v858_nav2_verified/v1361/sweep_terminal_dynamic_main/physics/SETUP.json').read_text())['actor']
    graph=json.loads((O/'GRAPH_INPUT.json').read_text());origin=graph['request']['sim_time'];maximum=-math.inf;future_samples=0
    for index,polygon in enumerate(polygons):
        q=np.array(polygon);assert (q@normals.T<=supports[index]+1e-8).all()
        stamps=np.linspace(origin+index*.2-.2,origin+(index+1)*.2+.2,61)
        centers=np.asarray(actor['anchor_xy'])+.25*np.sin(stamps*.32+actor['phase_rad'])[:,None]*np.asarray(actor['axis_xy'])
        maximum=max(maximum,float(np.max(centers@normals.T+.1-supports[index])));future_samples+=len(stamps)
    assert maximum<=1e-8
    result=dict(passed=True,geometry_cases=reviewed,maximum_original_numpy_distance_error_m=error,
        conservative_shortcut_preserves274mm_classification=True,forecast_rows=len(polygons),
        offline_future_actor_disk_samples=future_samples,maximum_actor_disk_support_excess_m=maximum,
        actual_actor_truth_only_in_evaluator=True,source_tick=15105,models=0,physical_native=0,
        original_dynamic_complete_route_qualified=False,wall_s=time.monotonic()-begin)
    target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
