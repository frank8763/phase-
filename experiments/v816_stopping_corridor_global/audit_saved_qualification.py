"""Independent geometry, soft costs, 657 coverage and registered progress gates."""
import hashlib
import json
from pathlib import Path
import numpy as np
from exact_footprint import pose_values
from independent_soft_reference import field,soft_values
from union_belief import future_cells

repo=Path(__file__).resolve().parents[2];root=repo/'runs/v816_stopping_corridor_global/pre_navigation'
read=lambda p:json.loads(p.read_text())
rows=read(root/'RESULTS.json');protocol=read(repo/'runs/v809_time_reference_global/main_slot01/paired/STATIC_PROTOCOL.json')
records=[];coverage=0
for r in rows:
    state=r['causal_state'];f=field(protocol,state)
    checks=dict(source=hashlib.sha256((repo/r['input_file']).read_bytes()).hexdigest()==r['input_sha256'],
        no_hidden=r['metadata']['hidden_world_geometry_used']is False and state['hidden_world_geometry_used']is False,
        hard_map=r['causal_world']['rectangles']==[*protocol['known_rectangles'],state['current_outer_rectangle']],
        no_execution_guarantee=r['metadata']['reference_is_not_dynamic_execution_certificate']and r['metadata']['all_actual_328_native_admission_unchanged'],
        current_hard_future_soft=r['metadata']['future_cost_is_soft']and r['metadata']['reference_has_no_execution_arrival_clock'])
    if r['path']is None:
        checks['has_forward_progress_reference']=False
    else:
        z=np.load(root/f'step{r["step"]:04d}.npz');geometry=pose_values(f,z['dense']);heat=soft_values(f,state,z['dense']);p=z['path']
        geometry_error=float(np.max(abs(geometry-z['current_values'])));heat_error=float(np.max(abs(heat-z['heat'])))
        checks.update(geometry_exact=geometry_error<=1e-10,heat_exact=heat_error<=1e-10,
            hard_floor=bool(geometry.min()>=r['stats']['guard_m']-1e-8),forward_only=bool(np.all(p[:,3]==1)),
            horizon_discontinuity_removed=r['horizon_jump_m']<=1e-12,
            meaningful_forward_reference=r['endpoint_goal_m']<=.28 or r['start_goal_m']-r['endpoint_goal_m']>=.5,
            curvature=bool(np.all(abs((np.diff(p[:,2])+np.pi)%(2*np.pi)-np.pi)/.04<=np.tan(.42722137342572125)/.6+1e-8)))
        if r['step']==303:checks['first_post_stop_full_goal_reference']=r['stats']['status']=='GLOBAL_GOAL_PATH'and r['endpoint_goal_m']<=.28
    t=np.arange(657)*.01;tt=t[:,None]
    pl=np.asarray(state['position_lower']);pu=np.asarray(state['position_upper']);vl=np.asarray(state['velocity_lower']);vu=np.asarray(state['velocity_upper'])
    lo=np.maximum(pl+tt*vl-.02*tt*tt,pl-.12*tt)-1e-5;hi=np.minimum(pu+tt*vu+.02*tt*tt,pu+.12*tt)+1e-5
    cl,ch=future_cells(state['outer_state_cells'],t)
    checks['original657_cells_still_contained']=bool(np.max(lo[:,None,:]-cl)<=1e-7 and np.max(ch-hi[:,None,:])<=1e-7)
    coverage+=657
    records.append(dict(step=r['step'],checks={k:bool(v)for k,v in checks.items()},passed=bool(all(checks.values()))))
checks=dict(exact_initial_static=read(root/'INITIAL_STATIC_ROUTE.json')['status']=='EXACT_ORIGINAL_INITIAL_SPATIAL_PATH',
    fixed_four=[r['step']for r in rows]==[303,363,649,1183],all_fixed_registered_gates=all(x['passed']for x in records))
out=dict(status='SOFT_REFERENCE_INDEPENDENT_QUALIFICATION_PASS'if all(checks.values())else'SOFT_REFERENCE_QUALIFICATION_NOT_PASSED',
    checks=checks,records=records,original_657_future_coverage_queries=coverage,new_models=0,integrations=0,
    scope='Spatial proposal, current occupancy and soft future cost only; physical dynamic safety and final arrival remain untested.')
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert all(checks.values())
