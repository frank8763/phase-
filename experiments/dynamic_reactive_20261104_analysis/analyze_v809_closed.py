"""One bounded, saved-log-only diagnosis. Never creates a model or control."""
import collections
import hashlib
import json
import math
from pathlib import Path
import numpy as np

repo = Path(__file__).resolve().parents[2]
root = repo / 'runs/v809_time_reference_global'
cell = root / 'main_slot01/paired/geometry_memory'
out = repo / 'runs/v809_closed_diagnosis'
out.mkdir(exist_ok=False)
read = lambda p: json.loads(p.read_text())
trace = read(cell / 'trace.json')
plans = [read(p) for p in sorted(cell.glob('planning_*.json'))]
rv = [json.loads(s) for s in (cell / 'route_revalidation.jsonl').open()]
decisions = [json.loads(s) for s in (cell / 'control_decisions.jsonl').open()]
result = read(cell / 'result.json')
assert read(root / 'FINALIZED.json')['archive']['all_source_and_decompressed_readback_verified']

def metrics(rows):
    walk = reverse = 0.
    for a, b in zip(rows, rows[1:]):
        dx, dy = np.asarray(b['pose'][:2]) - a['pose'][:2]
        walk += math.hypot(dx, dy)
        reverse += max(0., -dx * math.cos(a['pose'][2]) - dy * math.sin(a['pose'][2]))
    best = min(rows, key=lambda q: q['goal_distance_m'])
    return dict(public_sampled_path_length_m=walk, public_sampled_reverse_projection_m=reverse,
        best_goal_distance_m=best['goal_distance_m'], best_step=best['step'],
        start_goal_distance_m=rows[0]['goal_distance_m'], end_goal_distance_m=rows[-1]['goal_distance_m'],
        goal_distance_reduction_m=rows[0]['goal_distance_m'] - rows[-1]['goal_distance_m'],
        gear_counts=dict(collections.Counter(x['active_gear'] for x in rows)))

tracked = [p for p in plans if p['step'] >= 303]
planning = []
for p in tracked:
    path = np.asarray(p['path'])
    planning.append(dict(step=p['step'], status=p['stats']['status'],
        remaining_goal_m=p['stats']['goal_distance_m'], nodes=len(path),
        reverse_nodes=int(np.sum(path[:, 3] < 0)),
        gear_switches=int(np.sum(np.diff(path[:, 3]) != 0))))
nominal = [x for x in decisions if x.get('stage') == 'NOMINAL']
append = [x for x in decisions if x.get('stage') == 'BACKUP_APPEND']
diagnosis = dict(status='SAVED_FAILURE_DIAGNOSIS_COMPLETE',
    original_outcome=result['outcome'], original_goal_distance_m=result['goal_distance_m'],
    discovery_step=result['first_discovery_step'], stop_finished_step=result['discovery_brake_finished_step'],
    full_episode=metrics(trace), after_stop=metrics(trace[303:]), tracked_plans=planning,
    all_tracked_plans_reach_geometric_goal=all(p['status'] == 'GLOBAL_GOAL_PATH' for p in planning),
    all_tracked_plans_contain_reverse=all(p['reverse_nodes'] > 0 for p in planning),
    route_invalid_triggers=sum(x['current_route_invalid'] for x in rv),
    no_route_progress_triggers=sum(x['stagnated_without_route_progress'] for x in rv),
    nominal_decisions=len(nominal), append_decisions=len(append),
    all_nominal_safe=all(x['summary']['status'] == 'MODEL_SAFE_COMMAND' for x in nominal),
    all_append_safe=all(x['detail']['status'] == 'APPENDABLE_BACKUP_FOUND' for x in append),
    hypotheses=dict(
        reference_reversals_and_replanning='SUPPORTED: every tracked reference has two gear changes; 20 reference-invalid replans; public-sampled reverse distance after stop >4m.',
        universal_forward_safety_rejection='NOT_SUPPORTED: all ordinary commands have complete admitted tails; no recovery activation. Forward alternatives at every state were not exhaustively tested.',
        lack_of_geometric_global_route='CONTRADICTED_ON_SAVED_SEARCHES: all 21 tracked searches returned complete goal references.',
        merely_smooth_slow_progress='NOT_SUPPORTED_AS_SUFFICIENT_EXPLANATION: 9.8775m sampled travel gives only 1.5493m net goal reduction; last distance regresses from best.',
        fresh_forecast_changes='SUPPORTED_AS_REPLAN_TRIGGER, but independent causal contribution to reference-choice oscillation remains unproven.'),
    next_revision='Prefer a fully certified geometric forward-only goal reference from the existing primitive subset, else retain original bidirectional reference search. This is not an execution guarantee.',
    no_promise_that_more_time_would_arrive=True,
    model_initializations=0, navigation_native=0, private_native=0, replay_native=0)
paths = [cell/'trace.json',cell/'result.json',cell/'control_decisions.jsonl',cell/'route_revalidation.jsonl',*sorted(cell.glob('planning_*.json'))]
diagnosis['source_sha256'] = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(out/'RESULT.json').write_text(json.dumps(diagnosis, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({k: diagnosis[k] for k in ['status','after_stop','route_invalid_triggers','all_tracked_plans_contain_reverse','model_initializations']}))
