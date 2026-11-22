"""New integrated schema: original prefix plus strict goal-bound receipts.

No legacy event CURRENT_INPUT/TRANSACTION_CLOSED/200-array index assumptions.
Only durable AFTER rows count; missing/duplicate/inflight rows refuse success.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]


def collect(output,*,source):
    p=R/'experiments/v1423_integrated_route_audit/recorded.py'
    assert hashlib.sha256(p.read_bytes()).hexdigest()==source[str(p.relative_to(R))]
    s=importlib.util.spec_from_file_location('v1609_original_receipt_normalizer',p)
    original=importlib.util.module_from_spec(s);s.loader.exec_module(original)
    output=Path(output);root=original.lines(output/'ACTUAL_OWNER_JOURNAL.jsonl')
    rows=original.receipts(root,before_kind='BEFORE_ORIGINAL_PREFIX_NATIVE',after_kind='AFTER_ORIGINAL_PREFIX_NATIVE',bound_hash=False)
    actual=output/'goal_bound_actual';events=[]
    if actual.exists():
        closed=json.loads((actual/'CURRENT_CLOSED.json').read_text());assert closed['closed']and closed['pending_actual_row']is None
        journal=actual/'APPLIED_JOURNAL.jsonl'
        assert hashlib.sha256(journal.read_bytes()).hexdigest()==closed['journal_sha256']
        events=original.lines(journal)
        applied=original.receipts(events,before_kind='BEFORE_NATIVE',after_kind='AFTER_NATIVE',bound_hash=True)
        assert len(applied)==closed['applied_receipts'];rows.extend(applied)
    rows.sort(key=lambda row:row['before_native'])
    assert [row['before_native']for row in rows]==list(range(len(rows))),'GOAL_BOUND_NATIVE_GAP_OR_DUPLICATE'
    return rows,events,root
