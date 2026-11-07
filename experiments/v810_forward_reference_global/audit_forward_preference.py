"""Independent policy/metadata audit of saved route proposals; no models."""
import argparse
import json
from pathlib import Path
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('pair', type=Path)
a = ap.parse_args()
root = a.pair / 'geometry_memory'
states = {x['step']: x for x in map(json.loads, (root / 'motion_estimate.jsonl').open())}
records = []
for source in sorted(root.glob('planning_*.json')):
    row = json.loads(source.read_text())
    if states[row['step']]['center'] is None:
        continue
    stats = row['stats']
    policy = stats['forward_reference_preference']
    selected = policy['selected_forward_goal_reference']
    preferred_expanded = policy['preferred_expanded']
    total = policy['total_expanded']
    checks = dict(reference_only=policy['actual_reverse_control_and_recovery_unchanged'],
        original_fallback_iff_no_selected_forward=policy['original_bidirectional_fallback_called'] == (not selected),
        work_accounted=0 <= preferred_expanded <= 16000 and preferred_expanded <= total <= 32000)
    if selected:
        path = np.asarray(row['path'])
        checks.update(selected_complete_goal=stats['status'] == policy['preferred_status'] == 'GLOBAL_GOAL_PATH',
            forward_only=bool(np.all(path[:, 3] == 1)),
            goal_endpoint=float(np.linalg.norm(path[-1, :2] - row['causal_input']['goal'])) < .28 + 1e-8,
            selected_work_exact=total == preferred_expanded == stats['expanded'])
    else:
        checks.update(fallback_requires_failed_forward_goal=policy['preferred_status'] != 'GLOBAL_GOAL_PATH',
            fallback_work_exact=total == preferred_expanded + stats.get('expanded', 0))
    records.append(dict(step=row['step'], selected_forward=selected,
        checks={k: bool(v) for k, v in checks.items()}, passed=bool(all(checks.values()))))
result = dict(status='FORWARD_PREFERENCE_POLICY_PASS' if all(x['passed'] for x in records) else 'FAIL',
    records=records, models=0, integrations=0,
    scope='Reference preference only. Actual reverse controls and emergency tail unchanged; no whole-route execution guarantee.')
(a.pair / 'FORWARD_PREFERENCE_AUDIT.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(status=result['status'], tracked_plans=len(records))))
assert all(x['passed'] for x in records)
