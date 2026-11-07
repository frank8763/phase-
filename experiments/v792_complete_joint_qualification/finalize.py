"""Zero-model qualification closure and exact source/decompressed archive readback."""
import gzip
import hashlib
import json
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
own = Path(__file__).parent
root = repo / 'runs/v792_complete_joint_qualification'
audit = repo / 'runs/v792_complete_joint_saved_audit'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert (repo / 'REVIEW_PENDING').exists() and not (root / 'FINALIZED.json').exists()
assert read(root / 'ROUND_WINDOW.json')['round_closed']
source_ok = all(sha(repo / n) == h for n, h in read(own / 'INPUT_FREEZE.json')['files'].items())
assert source_ok
raw = read(root / 'RESULT.json') if (root / 'RESULT.json').exists() else None
saved = read(audit / 'RESULT.json') if (audit / 'RESULT.json').exists() else None
verified = bool(raw and saved and saved['status'] == 'ALL_FIXED_JOINT_RETURN_EVIDENCE_VERIFIED')
missed = None if not verified else raw['missed_qualified_returns']['248']
result = dict(status='FIXED_JOINT_EVIDENCE_VERIFIED' if verified else 'DIAGNOSTIC_NOT_VERIFIED',
              evidence_complete=verified, source_unchanged=source_ok,
              missed_positive_joint_inputs=missed,
              original_replay_steps=read(root / 'COMPLETION.json')['original_replay_steps'],
              private_integrations=read(root / 'COMPLETION.json')['private_integrations'],
              scene_validation_integrations=read(root / 'COMPLETION.json')['scene_validation_integrations'],
              new_navigation=0, new_confirmation=0, new_integrations_finalizer=0,
              training_updates=0, stage_access=0, real_robot=0)
(root / 'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(result, indent=2) + '\n')
dest = repo / 'evidence/rpccr_complete_joint_v792_20261104'
assert not dest.exists()
dest.mkdir()
(dest / 'blobs').mkdir()
files = [p for directory in [own, root, audit] if directory.exists()
         for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts
         and p.suffix not in ['.lock', '.pyc']]
files += [repo / 'docs/RPCCR_METHOD_REVIEW_20261104.md',
          repo / 'RPCCR_GLOBAL_METHOD_REVIEW_AUTHORIZATION_20261104.json']
inventory = []
for p in sorted(set(files)):
    data = p.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    blob = dest / 'blobs' / (h + '.gz')
    packed = gzip.compress(data, mtime=0)
    if blob.exists():
        assert blob.read_bytes() == packed
    else:
        blob.write_bytes(packed)
    inventory.append(dict(path=str(p.relative_to(repo)), bytes=len(data), sha256=h,
                          blob=str(blob.relative_to(dest))))
(dest / 'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory, indent=2).encode(), mtime=0))
for row in inventory:
    data = gzip.decompress((dest / row['blob']).read_bytes())
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
    assert sha(repo / row['path']) == row['sha256']
manifest = [dict(path=str(p.relative_to(dest)), bytes=p.stat().st_size, sha256=sha(p))
            for p in sorted(dest.rglob('*')) if p.is_file()]
(dest / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
for row in manifest:
    assert sha(dest / row['path']) == row['sha256']
summary = dict(source_files=len(inventory), raw_bytes=sum(r['bytes'] for r in inventory),
               all_source_and_decompressed_readback_verified=True, raw_deleted=False)
(root / 'FINALIZED.json').write_text(json.dumps(dict(**result, archive=str(dest.relative_to(repo)),
                                                   archive_summary=summary), indent=2) + '\n')
print(json.dumps(dict(**result, archive_summary=summary), indent=2))
