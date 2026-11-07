"""Archive the closed V793 supplemental saved-log analysis with exact readback."""
import gzip
import hashlib
import json
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
dest = repo / 'evidence/rpccr_complete_joint_navigation_v793_20261104_supplement'
assert not dest.exists()
dest.mkdir()
(dest / 'blobs').mkdir()
files = set()
for name in ['experiments/global_day_20261104_analysis', 'runs/v793_saved_diagnosis']:
    files.update(p for p in (repo / name).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for name in [
    'RPCCR_GLOBAL_METHOD_REVIEW_AUTHORIZATION_20261104.json',
    'RPCCR_GLOBAL_METHOD_REVIEW_LEDGER_20261104.json', 'CURRENT_EXPERIMENT.json',
    'docs/RPCCR_COMPLETE_JOINT_V793_REPORT.md', 'docs/RPCCR_COMPLETE_JOINT_V792_REPORT.md',
    'docs/RPCCR_METHOD_REVIEW_LATEST_20261104.md',
    'runs/v793_saved_diagnosis.console', 'runs/v793_finalize.console',
    'runs/v793_transport.console', 'runs/v793_finalize_started.json',
    'runs/v793_complete_joint_navigation/CLOSURE_HANDOFF.md',
    'runs/v793_complete_joint_navigation/FINALIZED.json',
    'runs/v793_complete_joint_navigation/FINAL_INDEPENDENT_AUDIT.json',
]:
    files.add(repo / name)
inventory = []
for p in sorted(files):
    raw = p.read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    blob = dest / 'blobs' / (h + '.gz')
    data = gzip.compress(raw, mtime=0)
    if blob.exists():
        assert blob.read_bytes() == data
    else:
        blob.write_bytes(data)
    inventory.append(dict(path=str(p.relative_to(repo)), bytes=len(raw), sha256=h,
                          blob=str(blob.relative_to(dest))))
(dest / 'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory, indent=2).encode(), mtime=0))
for row in inventory:
    raw = gzip.decompress((dest / row['blob']).read_bytes())
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    assert hashlib.sha256((repo / row['path']).read_bytes()).hexdigest() == row['sha256']
manifest = [dict(path=str(p.relative_to(dest)), bytes=p.stat().st_size,
                 sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            for p in sorted(dest.rglob('*')) if p.is_file()]
(dest / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
for row in manifest:
    assert hashlib.sha256((dest / row['path']).read_bytes()).hexdigest() == row['sha256']
summary = dict(status='SUPPLEMENT_SOURCE_AND_DECOMPRESSED_BYTES_VERIFIED',
               source_files=len(inventory), raw_bytes=sum(x['bytes'] for x in inventory),
               manifest_entries=len(manifest), new_models=0, new_integrations=0, raw_deleted=False)
(repo / 'runs/v793_supplement_archive_result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary))
