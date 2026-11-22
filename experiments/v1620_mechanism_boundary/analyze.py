"""Complete denominators, paired benefit/harm, and phase limits; no models."""
from collections import Counter
from spec import VARIANTS

INVALID = {'operation_error', 'source_error', 'evidence_error', 'model_error',
           'control_contract_error', 'safety_error'}
FUNCTIONAL = {'arrival', 'algorithm_refusal', 'timeout', 'deadlock'}


def summarize(manifest, outcomes):
    assigned = {a['assignment_id']: (t, a) for t in manifest['tasks']
                for a in t['assignments']}
    assert len(assigned) == manifest['assignment_count']
    assert len(outcomes) == len({r['assignment_id'] for r in outcomes}), 'DUPLICATE_OUTCOME'
    measured = {}
    counts = {v: Counter() for v in VARIANTS}
    for row in outcomes:
        key = row['assignment_id']
        assert key in assigned, 'UNREGISTERED_OUTCOME'
        _, assignment = assigned[key]
        assert row['variant'] == assignment['variant']
        assert row['outcome'] in INVALID | FUNCTIONAL
        assert type(row['whole_passed']) is bool
        if row['whole_passed']:
            assert row['outcome'] == 'arrival'
            assert row['whole_audit_verified'] is True and row['own_replay_verified'] is True
            assert row['source_coverage_verified'] is True and row['complete_applied_tail'] is True
        else:
            assert row['outcome'] != 'arrival', 'ARRIVAL_WITHOUT_FULL_GATE'
        measured[key] = row
        counts[row['variant']][row['outcome']] += 1
    paired = []
    for task in manifest['tasks']:
        if len(task['assignments']) != 2:
            continue
        ids = {a['variant']:a['assignment_id'] for a in task['assignments']}
        ablation = next(v for v in ids if v != 'full')
        left = measured.get(ids['full']); right = measured.get(ids[ablation])
        state = 'unexecuted_or_incomplete'
        if left is not None and right is not None:
            if left['outcome'] in INVALID or right['outcome'] in INVALID:
                state = 'interface_or_evidence_invalid_pair'
            else:
                state = ('rescue' if left['whole_passed'] and not right['whole_passed'] else
                         'harm' if right['whole_passed'] and not left['whole_passed'] else 'tie')
        paired.append(dict(task_id=task['task']['task_id'], ablation=ablation, state=state))
    return dict(planned_tasks=manifest['task_count'], planned_assignments=len(assigned),
                executed_assignments=len(measured),
                unexecuted_assignments=sorted(set(assigned)-set(measured)),
                all_attempt_outcomes={v:dict(c) for v,c in counts.items()},
                paired_results=paired, paired_counts=dict(Counter(p['state'] for p in paired)),
                whole_successes=sum(r['whole_passed'] for r in outcomes),
                no_pooled_heterogeneous_denominator=True,
                no_new_map_or_motion_class_claim=True,
                statistical_superiority_established=False,
                numerical_or_physical_permission=False)
