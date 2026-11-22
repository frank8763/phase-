"""Pure proposal selection. These functions never grant model/actual authority."""
import math


def select_time(records, variant):
    assert variant in {'full', 'no_time'}
    assert len(records) == 40
    assert [r['wait_native'] for r in records] == list(range(0, 2000, 50))
    for row in records:
        assert type(row['passed']) is bool
        assert type(row['selection_slack_m']) in (float, int)
        assert math.isfinite(row['selection_slack_m'])
    good = [r for r in records if r['passed'] and
            (variant == 'full' or r['wait_native'] == 0)]
    selected = min(good, key=lambda r: (-r['selection_slack_m'], r['wait_native'])) if good else None
    return dict(selected=selected, variant=variant, examined=40,
                intervention='EW_fallback_wait_selection_only',
                proposal_only=True, physical_authorized=False)


def select_refuge(candidates, variant):
    assert variant in {'full', 'no_onward'}
    # Original caller supplies candidates in fixed guide-score order. Reordering
    # here by an onward result would leak the removed mechanism into the ablation.
    selected = None
    for row in candidates:
        assert type(row['guide_score']) in (float, int) and math.isfinite(row['guide_score'])
        assert type(row['safe_prefix']) is bool
        assert type(row['prefix_feedback_stop_passed']) is bool
        assert type(row['onward_passed']) is bool
    assert [r['guide_score'] for r in candidates] == sorted(r['guide_score'] for r in candidates)
    for row in candidates[:8]:
        if not row['safe_prefix'] or not row['prefix_feedback_stop_passed']:
            continue
        if variant == 'full' and not row['onward_passed']:
            continue
        selected = row
        break
    return dict(selected=selected, variant=variant,
                intervention='WE_preexecution_onward_preview_only',
                measured_handoff_replan_still_required=True,
                proposal_only=True, physical_authorized=False)
