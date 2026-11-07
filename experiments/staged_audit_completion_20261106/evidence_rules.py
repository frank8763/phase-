"""Finite acceptance gates; no model construction or integration."""
import hashlib
import json
from pathlib import Path

AUDITS = [
    ('audit_run.py', 'INDEPENDENT_CANONICAL_AUDIT.json', 120),
    ('audit_forward_controller.py', 'FORWARD_GUIDANCE_AUDIT.json', 60),
    ('audit_route_commitment.py', 'ROUTE_COMMITMENT_AUDIT.json', 240),
    ('audit_projection_learning.py', 'PROJECTION_LEARNING_AUDIT.json', 60),
    ('audit_all_tail_geometry.py', 'SAVED_TAIL_GEOMETRY_AUDIT.json', 150),
    ('audit_shadow_mode.py', 'SHADOW_MODE_AUDIT.json', 60),
    ('audit_reentry.py', 'REENTRY_INDEPENDENT_AUDIT.json', 240),
    ('audit_complete_joint.py', 'COMPLETE_JOINT_SELECTION_AUDIT.json', 60),
    ('audit_nominal_layers.py', 'NOMINAL_LAYER_AUDIT.json', 240),
    ('audit_reactive.py', 'REACTIVE_POLICY_AUDIT.json', 300),
    ('audit_proposal_separation.py', 'PROPOSAL_SEPARATION_AUDIT.json', 300),
    ('audit_tracked_norm.py', 'TRACKED_NORM_INDEPENDENT_AUDIT.json', 300),
]
AUDITS.append(('audit_goal_renewal.py', 'GOAL_REFERENCE_RENEWAL_AUDIT.json', 180))
AUDITS.append(('audit_ranked_return.py', 'RANKED_RETURN_AUDIT.json', 180))
AUDITS.append(('audit_forward_escape.py', 'FORWARD_ESCAPE_AUDIT.json', 180))
FUNCTIONAL_CHECKS = {'moving_before_discovery', 'new_causal_route_after_stop',
                     'actually_continued_after_replanning', 'strict_arrival'}


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    temporary.replace(path)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024**2), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main_gate(tasks, records, confirmation):
    mains = [x for x in records if x['role'] == 'MAIN']
    successful = [x for x in mains if x.get('physical_passed') and x.get('functional_passed')]
    routes = {case: sum(x['task']['case_id'] == case for x in successful)
              for case in {x['case_id'] for x in tasks}}
    directions = {direction: sum(x['task']['initial_axis_motion_direction'] == direction for x in successful)
                  for direction in {x['initial_axis_motion_direction'] for x in tasks}}
    complete = len(mains) == len(tasks) and [x['task'] for x in mains] == tasks
    if confirmation:
        passed = complete and len(tasks) == 24 and len(successful) >= 23 and min(routes.values()) >= 7 and min(directions.values()) >= 11
    else:
        passed = complete and len(successful) == len(tasks) == 1
    return dict(passed=passed, main_attempts=len(mains), main_successes=len(successful),
                planned_main=len(tasks), unexecuted_main=len(tasks)-len(mains),
                success_rate=(len(successful)/len(tasks) if complete else None),
                route_successes=routes, direction_successes=directions)


def repeat_check(base, pair, base_result, result, contact_compare):
    import numpy as np
    def rows(path):
        return [json.loads(s) for s in (path/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
    aa, bb = rows(base), rows(pair)
    errors = {k: float(np.max(abs(np.asarray([x[k] for x in aa])-np.asarray([x[k] for x in bb]))))
              if len(aa) == len(bb) and aa else None for k in ['qpos_full','qvel_full','ctrl','mocap_pos']}
    contacts = contact_compare(base, pair)
    da, db = base/'geometry_memory/FIRST_DISCOVERY.json', pair/'geometry_memory/FIRST_DISCOVERY.json'
    checks = dict(state_ctrl=all(v is not None and v <= 1e-8 for v in errors.values()),
                  model=sha(base/'scene_model.mjb') == sha(pair/'scene_model.mjb'),
                  initial=base_result['normalized_initial_state_hash'] == result['normalized_initial_state_hash'],
                  contacts=contacts['passed'], discovery=da.exists() == db.exists() and (not da.exists() or read(da) == read(db)),
                  same_outcome=base_result['outcome'] == result['outcome'],
                  same_length=base_result['public_steps'] == result['public_steps'])
    return dict(passed=all(checks.values()), checks=checks, errors=errors, contact_comparison=contacts)

AUDITS.append(('audit_reference_recovery.py', 'REFERENCE_RECOVERY_AUDIT.json', 300))

AUDITS.append(('audit_early_joint.py','EARLY_JOINT_AUDIT.json',600))
