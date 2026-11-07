"""Saved route revalidation and gear-switch journals, no simulator/predictor imports."""
import collections,hashlib,json,signal,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];cell=repo/'runs/v790_persistent_body_global/main_slot01/paired/geometry_memory';dest=repo/'runs/global_dynamic_overnight_20261103/route_trigger_analysis';dest.mkdir(exist_ok=False)
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('ROUTE_LOG_ANALYSIS_120S_CAP')));signal.alarm(120)
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]
assert(repo/'runs/v790_persistent_body_global/FINALIZED.json').exists()
source=[cell/'route_revalidation.jsonl',cell/'gear_transitions.jsonl',cell/'model_admission.jsonl'];hashes={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest()for p in source};route=lines(source[0]);gears=lines(source[1]);ad=lines(source[2]);plans=[read(p)for p in sorted(cell.glob('planning_*.json'))];rmap={x['step']:x for x in route}
first_reverse=next(p['step']for p in plans if any(x[3]<0 for x in p['path']));details=[]
for step in range(max(0,first_reverse-7),first_reverse+8):
 row=rmap.get(step);plan=next((p for p in plans if p['step']==step),None);admission=next((a for a in ad if a['step']==step),None)
 details.append(dict(step=step,old_reference=None if row is None else{k:v for k,v in row.items()if k!='reference_path'},new_plan=None if plan is None else dict(status=plan['stats']['status'],reverse_nodes=sum(x[3]<0 for x in plan['path']),first_gear=plan['path'][0][3],points=len(plan['path']),projection_horizon_s=plan['route_projection_horizon_s']),actual_admission=None if admission is None else{key:admission.get(key)for key in['status','active_gear','certified_backup_handover','hidden_world_geometry_used']}))
flags=collections.Counter()
for row in route:
 for key in ['current_route_invalid','old_net_motion_stagnant','stagnated_without_route_progress']:
  flags[key]+=bool(row.get(key))
zero_index=sum(x['index']==0 for x in route);same_step_replans=sum(p['step']in rmap and rmap[p['step']]['current_route_invalid']for p in plans)
out=dict(status='SAVED_ROUTE_TRIGGER_DIAGNOSIS_COMPLETE',new_models=0,new_integrations=0,new_predictions=0,source_hashes=hashes,route_revalidation_rows=len(route),flag_true_counts=dict(flags),path_index_zero_rows=zero_index,plans=len(plans),plans_immediately_after_invalid_old_route=same_step_replans,first_reverse_plan_step=first_reverse,first_reverse_window=details,gear_transition_count=len(gears),gear_transition_status_counts=dict(collections.Counter(x['status']for x in gears)),interpretation='Stored route validation repeatedly rejects the old projected reference and resets path progress through replanning. First reverse plan follows this invalidation, not an absence of GLOBAL_GOAL_PATH. These logs do not prove a new controller will pass or that horizon shortening is safe.')
(dest/'RESULT.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');signal.alarm(0);assert all(hashlib.sha256((repo/p).read_bytes()).hexdigest()==h for p,h in hashes.items());print(json.dumps({k:out[k]for k in ['status','route_revalidation_rows','flag_true_counts','path_index_zero_rows','plans','plans_immediately_after_invalid_old_route','first_reverse_plan_step']}))
