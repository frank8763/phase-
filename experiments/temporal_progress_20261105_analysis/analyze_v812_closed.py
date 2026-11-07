"""Bounded saved-log failure decomposition; no models, new controls or search."""
import collections
import hashlib
import json
import math
from pathlib import Path
import signal
import numpy as np

repo=Path(__file__).resolve().parents[2]
root=repo/'runs/v812_soft_global_reference'
cell=root/'main_slot01/paired/geometry_memory'
out=repo/'runs/v812_closed_diagnosis';out.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text())
assert read(root/'ROUND_WINDOW.json')['round_closed']
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('300S_SAVED_ANALYSIS')))
signal.alarm(300)
trace=read(cell/'trace.json');result=read(cell/'result.json')
def motion(rows):
    walk=reverse=0.
    for a,b in zip(rows,rows[1:]):
        dx,dy=np.asarray(b['pose'][:2])-a['pose'][:2]
        walk+=math.hypot(dx,dy)
        reverse+=max(0.,-dx*math.cos(a['pose'][2])-dy*math.sin(a['pose'][2]))
    best=min(rows,key=lambda x:x['goal_distance_m'])
    return dict(public_sampled_path_m=walk,public_sampled_reverse_projection_m=reverse,
        start_goal_m=rows[0]['goal_distance_m'],end_goal_m=rows[-1]['goal_distance_m'],
        best_goal_m=best['goal_distance_m'],best_step=best['step'],
        net_goal_distance_reduction_m=rows[0]['goal_distance_m']-rows[-1]['goal_distance_m'],
        active_gears=dict(collections.Counter(str(x['active_gear'])for x in rows)))
plans=[]
for p in sorted(cell.glob('planning_*.json')):
    x=read(p);path=np.asarray(x['path'])if x['path']is not None else None
    plans.append(dict(step=x['step'],status=x['stats']['status'],
        goal_remaining_m=x['stats'].get('goal_distance_m'),nodes=0 if path is None else len(path),
        reverse_nodes=0 if path is None else int(np.sum(path[:,3]<0)),
        expanded=x['stats'].get('expanded'),
        policy=x['stats'].get('spatial_soft_reference'),wall_s=x['stats'].get('wall_s')))
route_rows=[json.loads(s)for s in(cell/'route_revalidation.jsonl').open()]
stages=collections.Counter();nominal=collections.Counter();append=collections.Counter();reject_reasons=collections.Counter();first_failed=None;nominal_reasons=collections.Counter()
for line in(cell/'control_decisions.jsonl').open():
    x=json.loads(line);stages[(x.get('candidate_role'),x.get('stage'))]+=1
    if x.get('stage')=='NOMINAL':
        nominal[x['summary']['status']]+=1
        for candidate in x.get('candidates',[]):nominal_reasons[str(candidate.get('reason'))]+=1
    if x.get('stage')=='BACKUP_APPEND':
        detail=x['detail'];append[detail['status']]+=1
        if detail['status']!='APPENDABLE_BACKUP_FOUND' and first_failed is None:
            first_failed=dict(step=x['step'],detail_keys=list(detail),status=detail['status'],
                distinct_command_rank=x.get('distinct_command_rank'),
                scalar_detail={k:v for k,v in detail.items()if not isinstance(v,(dict,list))})
        for item in detail.get('attempts',[]):reject_reasons[str(item.get('reason'))]+=1
summary=dict(status='V812_SAVED_FAILURE_DECOMPOSITION_COMPLETE',result=result,
    full_episode=motion(trace),after_stop=motion(trace[303:]),plans=plans,
    tracked_plan_count=sum(x['step']>=303 for x in plans),
    tracked_plans_with_reverse=sum(x['step']>=303 and x['reverse_nodes']>0 for x in plans),
    invalid_reference_triggers=sum(x['current_route_invalid']for x in route_rows),
    stagnant_reference_triggers=sum(x['stagnated_without_route_progress']for x in route_rows),
    nominal_statuses=dict(nominal),nominal_candidate_reasons=dict(nominal_reasons),
    append_statuses=dict(append),append_reasons_if_recorded=dict(reject_reasons),
    first_failed_append=first_failed,remaining_ordinary_alternatives_not_proven_globally_infeasible=True,
    new_models=0,new_navigation_native=0,new_private_native=0,new_replay_native=0)
sources=[cell/'trace.json',cell/'result.json',cell/'control_decisions.jsonl',cell/'route_revalidation.jsonl',*sorted(cell.glob('planning_*.json'))]
summary['source_sha256']={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sources}
(out/'RESULT.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
signal.alarm(0)
print(json.dumps({k:v for k,v in summary.items()if k not in ['result','plans','source_sha256']},ensure_ascii=False))
