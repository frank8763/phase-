"""Restore exact archive blobs from a committed transport manifest, without overwrite."""
import argparse
import hashlib
import json
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser()
ap.add_argument('manifest', type=Path)
args = ap.parse_args()
manifest = args.manifest.resolve()
assert manifest.is_relative_to(repo / 'evidence')


def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        while data := stream.read(1024**2):
            h.update(data)
    return h.hexdigest()


for row in json.loads(manifest.read_text())['entries']:
    target = (repo / row['original_blob']).resolve()
    assert target.is_relative_to(repo / 'evidence')
    if target.exists():
        assert target.stat().st_size == row['bytes'] and digest(target) == row['sha256']
        continue
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + '.reconstructing')
    h, size = hashlib.sha256(), 0
    with tmp.open('xb') as stream:
        for chunk in row['chunks']:
            part = (repo / chunk['path']).resolve()
            assert part.is_relative_to(repo / 'evidence')
            assert part.stat().st_size == chunk['bytes'] and digest(part) == chunk['sha256']
            with part.open('rb') as source:
                while data := source.read(1024**2):
                    h.update(data)
                    size += len(data)
                    stream.write(data)
    assert size == row['bytes'] and h.hexdigest() == row['sha256']
    assert not target.exists()
    tmp.rename(target)
print('All originals match their exact compressed bytes and SHA256.')
