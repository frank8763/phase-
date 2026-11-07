"""Independently audit spatial proposal semantics; execution gates are separate."""
import argparse
import json
from pathlib import Path
import numpy as np
from exact_footprint import pose_values
from independent_soft_reference import field,soft_values,dense_path

ap=argparse.ArgumentParser();ap.add_argument('pair',type=Path);a=ap.parse_args()
root=a.pair/'geometry_memory';read=lambda p:json.loads(p.read_text())
protocol=read(a.pair/'STATIC_PROTOCOL.json')
states={x['step']:x for x in map(json.loads,(root/'motion_estimate.jsonl').open())}
records=[]
for source in sorted(root.glob('planning_*.json')):
    r=read(source);state=states[r['step']]
    if state['center']is None:continue
    md=r['route_projection_metadata'];world=r['causal_route_input']
    checks=dict(current_only_hard_map=world['rectangles']==[*protocol['known_rectangles'],state['current_outer_rectangle']]and world['circles']==protocol['known_circles'],
        no_truth=md['hidden_world_geometry_used']is False and state['hidden_world_geometry_used']is False,
        no_reference_control_certificate=md['reference_is_not_dynamic_execution_certificate']and md['all_actual_328_native_admission_unchanged']and md['all_original_657_coverage_unchanged'],
        parameters=md['status']=='CURRENT_OCCUPANCY_WITH_SOFT_REACHABILITY'and md['soft_heat_samples']==7 and md['horizon_s']==6.56 and md['heat_decay_s']==3.28 and md['heat_clearance_m']==.30 and md['heat_scale_m']==1. and md['heat_edge_weight']==1.)
    minimum=error=None
    if r['path']is not None:
        path=np.asarray(r['path']);f=field(protocol,state);minimum=float(pose_values(f,dense_path(path)).min())
        heat=soft_values(f,state,path[:,:3]);error=float(np.max(abs(heat-np.asarray(r['stats']['soft_heat_at_path_nodes']))))
        policy=r['stats']['spatial_soft_reference'];selected=policy['forward_reference_selected']
        checks.update(hard_current_floor=minimum>=r['stats']['guard_m']-1e-8 and abs(minimum-r['stats']['minimum_clearance_m'])<=1e-8,
            soft_values_exact=error<=1e-10,soft_cost_bounded=bool(np.all((heat>=0)&(heat<=1))),
            selected_forward_or_fallback=(not selected)or bool(np.all(path[:,3]==1)),
            no_virtual_arrival_clock=policy['no_virtual_arrival_clock']and policy['future_cost_is_soft']and policy['does_not_authorize_execution'],
            fallback_account=(policy['original_bidirectional_fallback_called']==r['stats']['goal_first_policy']['bidirectional_called'])if 'goal_first_policy'in r['stats']else(policy['original_bidirectional_fallback_called']==(not selected)),
            fixed_search_work=policy['preferred_expanded']<=16000 and policy['total_expanded']<=32000)
    records.append(dict(step=r['step'],checks={k:bool(v)for k,v in checks.items()},passed=bool(all(checks.values())),
        minimum_current_reference_m=minimum,maximum_soft_heat_error=error))
out=dict(status='SPATIAL_PROPOSAL_SEPARATION_AUDIT_PASS'if all(x['passed']for x in records)else'FAIL',
    records=records,models=0,integrations=0,scope='Current hard reference geometry and soft forecast reconstruction only. Original native dynamic control and complete tail audited separately; future reference paths are not execution guarantees.')
(a.pair/'PROPOSAL_SEPARATION_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(status=out['status'],tracked_plans=len(records))));assert all(x['passed']for x in records)
