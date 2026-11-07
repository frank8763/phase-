"""Restore exact oversized archive blobs from verified committed chunks; never overwrite."""
import hashlib,json
from pathlib import Path
repo=Path(__file__).resolve().parents[2];base=repo/'evidence';manifest=json.loads((base/'global_dynamic_overnight_20261103_transport/TRANSPORT_MANIFEST.json').read_text())
def digest(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  while data:=f.read(1024*1024):h.update(data)
 return h.hexdigest()
for row in manifest['entries']:
 target=(repo/row['original_blob']).resolve();assert target.is_relative_to(base.resolve())
 if target.exists():assert target.stat().st_size==row['bytes']and digest(target)==row['sha256'];continue
 target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_suffix(target.suffix+'.reconstructing');h=hashlib.sha256();size=0
 with tmp.open('xb')as output:
  for chunk in row['chunks']:
   part=(repo/chunk['path']).resolve();assert part.is_relative_to(base.resolve())and part.stat().st_size==chunk['bytes']and digest(part)==chunk['sha256']
   with part.open('rb')as f:
    while data:=f.read(1024*1024):h.update(data);size+=len(data);output.write(data)
 assert h.hexdigest()==row['sha256']and size==row['bytes'];assert not target.exists();tmp.rename(target)
print('All oversized archive blobs match original bytes and SHA256.')
