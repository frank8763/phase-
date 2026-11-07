"""Independent stopping-sweep corridor and unchanged future soft-cost audit."""
import argparse,json
from pathlib import Path
import numpy as np
from exact_footprint import pose_values
from independent_corridor import independent_field,containment
from independent_soft_reference import soft_values,dense_path
ap=argparse.ArgumentParser();ap.add_argument('pair',type=Path);a=ap.parse_args()
read=lambda p:json.loads(p.read_text());cell=a.pair/'geometry_memory';protocol=read(a.pair/'STATIC_PROTOCOL.json')
states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').open())};records=[]
for source in sorted(cell.glob('planning_*.json')):
 r=read(source);state=states[r['step']]
 if state['center']is None:continue
 md=r['route_projection_metadata'];w=r['causal_route_input'];excess,samples=containment(state,w,len(protocol['known_rectangles']))
 checks=dict(original_current_retained=w['rectangles'][:11]==[*protocol['known_rectangles'],state['current_outer_rectangle']]and w['circles']==protocol['known_circles'],
  causal=state['hidden_world_geometry_used']is False and md['hidden_world_geometry_used']is False,
  stopping_horizon=md['status']=='STOPPING_HORIZON_REACHABLE_UNION_REFERENCE'and md['horizon_s']==3.28 and r['route_projection_horizon_s']==3.28,
  original_cells_covered=excess<=1e-10,no_virtual_clock=md['reference_has_no_execution_arrival_clock'],
  execution_separate=md['reference_is_not_dynamic_execution_certificate']and md['all_actual_328_native_admission_unchanged']and md['all_original_657_coverage_unchanged'])
 minimum=heat_error=None
 if r['path']is not None:
  p=np.asarray(r['path']);f=independent_field(protocol,state);minimum=float(pose_values(f,dense_path(p)).min())
  heat=soft_values(f,state,p[:,:3]);heat_error=float(np.max(abs(heat-np.asarray(r['stats']['soft_heat_at_path_nodes']))))
  policy=r['stats']['spatial_soft_reference']
  checks.update(stopping_room_floor=minimum>=max(.155,r['stats']['guard_m'])-1e-8 and abs(minimum-r['stats']['minimum_clearance_m'])<=1e-8,
   soft_cost_exact=heat_error<=1e-10,forward_or_explicit_fallback=(not policy['forward_reference_selected'])or bool(np.all(p[:,3]>0)),
   finite_search=policy['total_expanded']<=32000 and policy['preferred_expanded']<=16000)
 records.append(dict(step=r['step'],checks={k:bool(v)for k,v in checks.items()},passed=bool(all(checks.values())),minimum_stopping_corridor_m=minimum,maximum_soft_heat_error=heat_error,containment_excess_m=excess,containment_samples=samples))
out=dict(status='STOPPING_CORRIDOR_PROPOSAL_AUDIT_PASS'if all(x['passed']for x in records)else'FAIL',records=records,models=0,integrations=0,
 scope='Spatial room over the current belief stopping horizon; no assertion of later-arrival or native approach safety. Full physical control and braking certificates audited separately.')
(a.pair/'PROPOSAL_SEPARATION_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(status=out['status'],tracked_plans=len(records))));assert all(x['passed']for x in records)
