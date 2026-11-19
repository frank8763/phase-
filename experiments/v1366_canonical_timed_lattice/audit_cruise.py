"""Nominal boundary-continuity/clock/slew readback, no vehicle integration."""
import json
import math
import os
from pathlib import Path
import time
import numpy as np
from planner import R,C,O


def review(edge):
    p=np.asarray(edge['samples']);assert np.isfinite(p).all() and np.max(abs(np.diff(p[:,3])-.05))<1e-8
    assert abs(p[0,4]-.1*edge['gear']*edge['incoming_speed_state'])<1e-8
    assert abs(p[-1,4]-.1*edge['gear']*edge['outgoing_speed_state'])<1e-8
    assert abs(p[-1,5])<1e-8 and abs(p[:,4]).max()<=.10000001
    assert np.max(abs(np.diff(p[:,4]))/.05)<=.10000001
    assert np.max(abs(np.diff(p[:,5]))/.05)<=.600001
    assert np.max(abs(p[-1,:2]-.2*np.array(edge['offset'])))<1e-8
    if edge['outgoing_speed_state']==0:assert abs(p[-40:,4]).max()<1e-8
    return True


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'INDEPENDENT_CRUISE_AUDIT.json';assert not target.exists()
    graph=json.loads((O/'CRUISE_GRAPH.json').read_text());assert all(review(edge) for edge in graph['edges'])
    copies={}
    for edge in graph['edges']:
        p=np.asarray(edge['samples']);key=(edge['start_heading'],edge['end_heading'],tuple(edge['offset']),edge['gear'])
        copies.setdefault(key,[]).append(edge)
    for edges in copies.values():
        first=np.array(edges[0]['coefficient'])
        assert all(np.max(abs(np.array(edge['coefficient'])-first))<1e-10 for edge in edges)
    negatives=[]
    for kind in ['nonzero_stop','incoming_speed','instant_steering','clock','endpoint_snap']:
        edge=json.loads(json.dumps(graph['edges'][0]))
        if kind=='nonzero_stop':edge['samples'][-1][4]=.01
        elif kind=='incoming_speed':edge['samples'][0][4]=.1
        elif kind=='instant_steering':edge['samples'][1][5]+=.2
        elif kind=='clock':edge['samples'][4][3]=-.1
        else:edge['samples'][-1][0]+=.01
        try:review(edge)
        except AssertionError:negatives.append(kind)
        else:raise AssertionError('INVALID_BOUNDARY_ACCEPTED '+kind)
    proof=dict(passed=True,temporal_variants=len(graph['edges']),underlying_spatial_edges=len(copies),
        boundary_speed_states=[0.,.1],speed_limit_unchanged=True,negative_cases=negatives,
        original_dynamic_full_route_qualified=False,actual_response_or_control_qualified=False,
        models=0,physical_native=0,wall_s=time.monotonic()-begin)
    target.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))


if __name__=='__main__':main()
