#!/usr/bin/env python3
"""Verify the curated bundle and its read-only dependency isolation."""
import ast
import csv
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    rows = json.loads((REPO / 'manifests/source_provenance.json').read_text())
    for row in rows:
        path = REPO / row['destination']
        assert path.is_file(), str(path)
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], str(path)
    for directory in ('runtime', 'current', 'tools'):
        for path in (REPO / directory).rglob('*.py'):
            ast.parse(path.read_text(), filename=str(path))
    assert not list((REPO / 'runtime').rglob('*stage_td3*'))
    assert not list((REPO / 'runtime').rglob('*e2e_phase10*'))
    # Validate the complete historical paired denominator, retaining its old evaluation rule.
    with (REPO / 'evidence/phase22_formal/Final300/paired_rows.csv').open() as stream:
        pairs = list(csv.DictReader(stream))
    assert len(pairs) == 300
    assert {int(r['seed']) for r in pairs} == set(range(22800, 23100))
    old_totals = {label: sum(int(r[label + '_safe']) for r in pairs)
                  for label in ('phase21_v11', 'phase22_v1')}
    assert old_totals == {'phase21_v11': 165, 'phase22_v1': 214}, old_totals
    stats = json.loads((REPO / 'evidence/phase22_formal/Final300/summary.json').read_text())
    assert stats['conclusion']['confirmatory_accuracy_safety_gate_pass'] is False
    assert stats['conclusion']['real_time_gate_phase22_v1_pass'] is False
    contact_logs = 0
    for label in ('best_verified_rescue', 'harm_counterexample', 'current_v647'):
        for branch in ('frozen_original', 'rpccr_online'):
            root = REPO / 'evidence' / label / branch
            result = json.loads((root / 'result.json').read_text())
            with gzip.open(root / 'contacts.jsonl.gz', 'rb') as stream:
                digest = hashlib.sha256()
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(block)
            assert digest.hexdigest() == result['contacts']['contact_log_content_sha256']
            contact_logs += 1
    probe = subprocess.run([sys.executable, str(REPO / 'tools/isolate.py'), '--probe'],
                           capture_output=True, text=True, check=True)
    isolated = json.loads(probe.stdout)
    assert isolated['simulation_steps'] == isolated['training_updates'] == 0
    assert isolated['stage_visible'] is False
    assert isolated['original_phase_runs_visible'] is False
    assert isolated['model_sha256'] == '4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f'
    result = {'status': 'READY_PAUSED', 'preserved_original_files_verified': len(rows),
              'contact_logs_verified': contact_logs, 'Final300_pairs': len(pairs),
              'historical_safe_totals': old_totals, 'isolated_probe': isolated,
              'experiment_authorization': 'PAUSED_PENDING_USER_REVIEW' if (REPO / 'REVIEW_PENDING').exists() else 'REVIEW_MARKER_ABSENT'}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
