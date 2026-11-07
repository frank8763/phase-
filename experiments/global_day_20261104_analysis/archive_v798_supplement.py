"""One immutable archive of V798 saved interpretation and operation metadata."""
import gzip, hashlib, json
from pathlib import Path
repo = Path(__file__).resolve().parents[2]
dest = repo / 'evidence/rpccr_legacy_tracking_v798_20261104_supplement'
assert not dest.exists()
assert (repo / 'REVIEW_PENDING').exists()
read = lambda p: json.loads(p.read_text())
assert read(repo / 'runs/v798_legacy_tracking_transplant/FINALIZED.json')['source_unchanged']
assert read(repo/'runs/v798_supplemental_saved_audit/RESULT.json')['status']=='ALL_LEGACY_PROPOSER_SAVED_EVIDENCE_VERIFIED'
files = set(p for p in (repo / 'runs/v798_saved_causal_diagnosis').rglob('*') if p.is_file())
for name in [
    'experiments/global_day_20261104_analysis/audit_v798_supplemental_saved.py',
    'experiments/global_day_20261104_analysis/analyze_v798_supplemental_saved.py',
    'experiments/global_day_20261104_analysis/summarize_v798_saved.py',
    'experiments/global_day_20261104_analysis/archive_v798_supplement.py',
    'docs/RPCCR_LEGACY_TRACKING_V798_ANALYSIS.md',
    'docs/RPCCR_LEGACY_TRACKING_V798_REPORT.md',
    'RPCCR_LEGACY_TRACKING_AUTHORIZATION_20261104.json',
    'RPCCR_LEGACY_TRACKING_LEDGER_20261104.json', 'CURRENT_EXPERIMENT.json',
    'AGENTS.md', 'RESEARCH_STATUS.md',
    'runs/v798_legacy_tracking_transplant/FINALIZED.json',
    'runs/v798_legacy_tracking_transplant/CLOSURE_HANDOFF.md',
    'runs/v798_saved_audit_error_preserved.json',
    'runs/v798_supplemental_saved_audit/RESULT.json',
    'runs/v798_supplemental_saved_audit.console',
    'runs/v798_causal_recheck.console',
    'runs/v798_qualification_attempt02.console',
    'runs/v798_driver.console', 'runs/v798_probe.console',
    'runs/v798_saved_audit.console', 'runs/v798_analysis.console',
 'runs/v798_finalize.console',
    'runs/v798_driver_launch.json', 'runs/v798_launch.json',
    'runs/v798_review_guard.before',
]:
    files.add(repo / name)
dest.mkdir(); (dest / 'blobs').mkdir()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
inventory = []
for p in sorted(files):
    raw = p.read_bytes(); h = sha(raw); blob = dest / 'blobs' / (h+'.gz')
    packed = gzip.compress(raw, mtime=0)
    if blob.exists(): assert blob.read_bytes() == packed
    else: blob.write_bytes(packed)
    inventory.append(dict(path=str(p.relative_to(repo)), bytes=len(raw), sha256=h,
                          blob=str(blob.relative_to(dest))))
(dest / 'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for row in inventory:
    raw = gzip.decompress((dest / row['blob']).read_bytes())
    assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
    assert sha((repo / row['path']).read_bytes())==row['sha256']
manifest=[dict(path=str(p.relative_to(dest)), bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
          for p in sorted(dest.rglob('*')) if p.is_file()]
(dest / 'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert all(sha((dest / r['path']).read_bytes())==r['sha256'] for r in manifest)
summary=dict(status='SUPPLEMENT_SOURCE_AND_DECOMPRESSED_BYTES_VERIFIED',
    source_files=len(inventory),raw_bytes=sum(r['bytes'] for r in inventory),
    manifest_entries=len(manifest),model_initializations=0,integrations=0,raw_deleted=False)
(repo / 'runs/v798_supplement_archive_result.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
