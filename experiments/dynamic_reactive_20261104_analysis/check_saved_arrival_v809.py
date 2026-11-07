"""Zero-model symptom check on the already executed, immutable V809 episode.

This catches the failed end-to-end outcome, not a controller regression seam.
Repeating physical navigation for diagnosis would consume the remaining quota.
"""
import argparse
import hashlib
import json
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--assert-arrival', action='store_true')
args = parser.parse_args()
root = repo / 'runs/v809_time_reference_global/main_slot01/paired/geometry_memory'
result = json.loads((root / 'result.json').read_text())
trace = json.loads((root / 'trace.json').read_text())
assert len(trace) == result['public_steps'] == 1200
assert abs(trace[-1]['goal_distance_m'] - result['goal_distance_m']) < 1e-12
assert result['first_discovery_step'] == 262
assert result['discovery_brake_finished_step'] == 302
report = dict(
    status='ARRIVAL_PASS' if result['strict_safe_arrival'] else 'ARRIVAL_FAIL',
    outcome=result['outcome'],
    public_steps=len(trace),
    remaining_goal_m=result['goal_distance_m'],
    tolerance_m=.45,
    new_models=0,
    new_integrations=0,
    is_controller_regression_test=False,
    source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in [root / 'result.json', root / 'trace.json']},
)
print(json.dumps(report, indent=2))
if args.assert_arrival:
    assert result['strict_safe_arrival'] and result['goal_distance_m'] <= .45, report['status']
