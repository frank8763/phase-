"""Losslessly split oversized evidence blobs; never change original archives."""
import argparse
import hashlib
import json
import signal
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser()
ap.add_argument('archive', type=Path)
ap.add_argument('destination', type=Path)
args = ap.parse_args()
archive, dest = args.archive.resolve(), args.destination.resolve()
assert archive.is_relative_to(repo / 'evidence') and dest.is_relative_to(repo / 'evidence')
assert not dest.exists()
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('600S_TRANSPORT_LIMIT')))
signal.alarm(600)
dest.mkdir()
entries = []
for row in json.loads((archive / 'MANIFEST.json').read_text()):
    if row['bytes'] <= 90 * 1024**2:
        continue
    source = archive / row['path']
    digest, chunks = hashlib.sha256(), []
    with source.open('rb') as stream:
        while data := stream.read(32 * 1024**2):
            digest.update(data)
            part = dest / f"{row['sha256']}.part{len(chunks):03d}"
            part.write_bytes(data)
            h = hashlib.sha256(data).hexdigest()
            assert hashlib.sha256(part.read_bytes()).hexdigest() == h
            chunks.append(dict(path=str(part.relative_to(repo)), bytes=len(data), sha256=h))
    assert digest.hexdigest() == row['sha256']
    assert sum(x['bytes'] for x in chunks) == row['bytes']
    joined = hashlib.sha256()
    for item in chunks:
        joined.update((repo / item['path']).read_bytes())
    assert joined.hexdigest() == row['sha256']
    entries.append(dict(original_blob=str(source.relative_to(repo)), sha256=row['sha256'],
                        bytes=row['bytes'], chunks=chunks, original_preserved=True,
                        chunk_reassembly_verified=True))
assert entries
(dest / 'TRANSPORT_MANIFEST.json').write_text(json.dumps(dict(
    status='LOSSLESS_CHUNK_TRANSPORT_VERIFIED', source_archive=str(archive.relative_to(repo)),
    entries=entries, original_deleted=False, new_integrations=0), indent=2) + '\n')
(dest / 'README.md').write_text(
    '# Exact archive transport\n\n'
    'Original oversized compressed blobs remain locally unchanged and are excluded only from Git transfer. '
    'The 32MiB chunks reconstruct their exact original compressed bytes and SHA256. '
    'Run `python3 experiments/global_day_20261104_analysis/reconstruct_transport.py '
    + str((dest / 'TRANSPORT_MANIFEST.json').relative_to(repo)) + '` from the repository root. '
    'A conflicting existing original is never overwritten. Verify the original archive MANIFEST afterward. '
    'Local verification does not imply remote synchronization.\n')
signal.alarm(0)
print(json.dumps(dict(large_blobs=len(entries), chunks=sum(len(x['chunks']) for x in entries),
                      bytes=sum(x['bytes'] for x in entries), all_reassembly_verified=True)))
