"""Archive closure records and preserved entry failures without loading models."""
import gzip
import hashlib
import json
import shutil
import signal
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
root = repo / 'runs/tracked_norm_20261105'
dest = repo / 'evidence/rpccr_tracked_norm_closure_20261105'
assert not dest.exists(), 'EXISTING_ARCHIVE_MUST_NOT_BE_OVERWRITTEN'
assert json.loads((root / 'CLOSURE_CHECKS.json').read_text())['automation_deleted']
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('300S_CLOSURE_ARCHIVE')))
signal.alarm(300)
snapshot = root / 'closure_snapshot'
assert not snapshot.exists()
snapshot.mkdir()
for name in ['CURRENT_EXPERIMENT.json', 'RPCCR_TRACKED_NORM_AUTHORIZATION_20261105.json',
             'RPCCR_TRACKED_NORM_LEDGER_20261105.json', 'RESEARCH_STATUS.md', 'REVIEW_PENDING',
             'docs/RPCCR_TRACKED_NORM_V820_REPORT.md', 'docs/RPCCR_TRACKED_NORM_20261105_DIAGNOSIS.md']:
    source = repo / name
    shutil.copyfile(source, snapshot / source.name)
(root / 'AUTOMATION_STOP.json').write_text(json.dumps(dict(
    automation_id='phase-v820', deleted=True, delete_status='deleted',
    tool='mcp__codex_app__automation_update', reason='Registered task and complete repeat independently verified; no further simulations.'), indent=2) + '\n')

files = set()
for directory in [root, Path(__file__).parent, repo / 'experiments/v818_tracked_norm_native_probe',
                  repo / 'runs/v820_zero_model_interfaces', repo / 'runs/v820_zero_model_interfaces_02']:
    files.update(p for p in directory.rglob('*') if p.is_file() and p.suffix not in ['.lock', '.pyc']
                 and '__pycache__' not in p.parts)
for pattern in ['v817*console', 'v818*', 'v819*console', 'v820*console']:
    files.update(p for p in (repo / 'runs').glob(pattern) if p.is_file())
for name in ['v817_tracked_norm_qualification', 'v819_tracked_norm_native_entry', 'v820_tracked_norm_global']:
    directory = repo / 'runs' / name
    files.update(p for p in directory.glob('*.json') if p.is_file())
    if (directory / 'ARCHIVE_VERIFIED.json').exists():
        files.add(directory / 'ARCHIVE_VERIFIED.json')

dest.mkdir()
(dest / 'blobs').mkdir()
inventory = []
sha = lambda data: hashlib.sha256(data).hexdigest()
for p in sorted(files):
    raw = p.read_bytes()
    digest = sha(raw)
    blob = dest / 'blobs' / (digest + '.gz')
    compressed = gzip.compress(raw, mtime=0)
    if blob.exists():
        assert blob.read_bytes() == compressed
    else:
        blob.write_bytes(compressed)
    inventory.append(dict(path=str(p.relative_to(repo)), bytes=len(raw), sha256=digest,
                          blob=str(blob.relative_to(dest))))
(dest / 'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory, indent=2).encode(), mtime=0))
for item in inventory:
    raw = gzip.decompress((dest / item['blob']).read_bytes())
    assert len(raw) == item['bytes'] and sha(raw) == item['sha256']
    assert sha((repo / item['path']).read_bytes()) == item['sha256']
manifest = [dict(path=str(p.relative_to(dest)), bytes=p.stat().st_size, sha256=sha(p.read_bytes()))
            for p in sorted(dest.rglob('*')) if p.is_file()]
(dest / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
for item in manifest:
    assert sha((dest / item['path']).read_bytes()) == item['sha256']
result = dict(status='CLOSURE_AND_ORIGINAL_ENTRY_FAILURES_ALL_SOURCE_SHA_VERIFIED',
              sources=len(inventory), raw_bytes=sum(x['bytes'] for x in inventory),
              manifest_entries=len(manifest), archive=str(dest.relative_to(repo)),
              mutable_operational_metadata_frozen_in_snapshot=True, new_models=0, new_integrations=0,
              original_raw_deleted=False, network_attempts_this_archive=0)
(root / 'CLOSURE_ARCHIVE_VERIFIED.json').write_text(json.dumps(result, indent=2) + '\n')
signal.alarm(0)
print(json.dumps(result))
