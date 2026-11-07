"""Independent complete finite ordinary-input ordering audit; saved JSON only."""
import argparse
import json
from pathlib import Path
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('pair', type=Path)
a = ap.parse_args()
cell = a.pair / 'geometry_memory'
lines = lambda p: [json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []
decisions = lines(cell / 'control_decisions.jsonl')
admissions = {r['step']: r for r in lines(cell / 'model_admission.jsonl')}
execution = lines(cell / 'v648_execution.jsonl')
ids = json.loads((cell / 'ACTUATOR_COMMAND_CONTRACT.json').read_text())['ids']
records = []
for nominal in [r for r in decisions if r['candidate_role'] == 'ORDINARY' and r['stage'] == 'NOMINAL']:
    step = nominal['step']
    safe = sorted([c for c in nominal.get('candidates', []) if c['reason'] is None],
                  key=lambda c: c['score'], reverse=True)
    unique, seen = [], set()
    for candidate in safe:
        key = tuple(candidate['first_command'])
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    tested = [r for r in decisions if r['step'] == step and r['candidate_role'] == 'ORDINARY'
              and r['stage'] == 'BACKUP_APPEND']
    selected = admissions.get(step)
    ordinary_selected = bool(selected and selected['status'] == 'MODEL_SAFE_COMMAND'
                             and not selected.get('certified_backup_handover'))
    if not unique:
        passed = len(tested) == 1 and tested[0]['detail']['status'] == 'SKIPPED_NO_NOMINAL'
        records.append(dict(step=step, unique=0, tested=0, selected_rank=None, passed=passed))
        continue
    rank = selected['joint_admission_distinct_command_rank'] if ordinary_selected else None
    expected = rank + 1 if rank is not None else len(unique)
    checks = [0 < len(unique) <= 25, len(tested) == expected]
    for i, r in enumerate(tested):
        checks += [r['distinct_command_rank'] == i,
                   np.array_equal(r['first_command'], unique[i]['first_command']),
                   abs(r['ordinary_score'] - unique[i]['score']) <= 1e-10,
                   r['unexamined_distinct_safe_commands'] == len(unique) - i - 1,
                   r['detail']['status'] == 'APPENDABLE_BACKUP_FOUND' if i == rank else
                   r['detail']['status'] in ['NO_APPENDABLE_BACKUP', 'PREFIX_SELF_DOMAIN_REJECTED']]
    if rank is not None:
        checks += [selected['joint_admission_maximum_commands'] == len(unique),
                   abs(selected['score'] - unique[rank]['score']) <= 1e-10,
                   np.max(abs(np.asarray(execution[step]['ctrl'])[ids] - unique[rank]['first_command'])) <= 1e-12]
    records.append(dict(step=step, unique=len(unique), tested=len(tested), selected_rank=rank,
                        passed=bool(all(checks))))
passed = bool(records and all(r['passed'] for r in records))
result = dict(status='COMPLETE_FINITE_JOINT_SELECTION_VERIFIED' if passed else 'FAIL',
              records=records, selected_beyond_original_top3=sum(r['selected_rank'] is not None
                                                               and r['selected_rank'] >= 3 for r in records),
              new_models=0, new_integrations=0)
(a.pair / 'COMPLETE_JOINT_SELECTION_AUDIT.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'records'}))
assert passed
