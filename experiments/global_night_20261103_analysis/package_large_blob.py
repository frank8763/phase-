"""Lossless Git transport for immutable archive blobs over GitHub's single-file cap."""
import hashlib,json,signal,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];archive=repo/'evidence/rpccr_persistent_body_global_v790_20261103';dest=repo/'evidence/global_dynamic_overnight_20261103_transport';dest.mkdir(exist_ok=False)
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('TRANSPORT_600S_CAP')));signal.alarm(600)
manifest=json.loads((archive/'MANIFEST.json').read_text());entries=[];chunk_size=32*1024*1024
for row in manifest:
 if row['bytes']<=90*1024*1024:continue
 source=archive/row['path'];digest=hashlib.sha256();chunks=[]
 with source.open('rb')as f:
  index=0
  while True:
   data=f.read(chunk_size)
   if not data:break
   digest.update(data);part=dest/f"{row['sha256']}.part{index:03d}";part.write_bytes(data);h=hashlib.sha256(data).hexdigest();assert hashlib.sha256(part.read_bytes()).hexdigest()==h;chunks.append(dict(path=str(part.relative_to(repo)),sha256=h,bytes=len(data)));index+=1
 assert digest.hexdigest()==row['sha256'] and sum(x['bytes']for x in chunks)==row['bytes'];verify=hashlib.sha256()
 for c in chunks:verify.update((repo/c['path']).read_bytes())
 assert verify.hexdigest()==row['sha256'];entries.append(dict(original_blob=str(source.relative_to(repo)),sha256=row['sha256'],bytes=row['bytes'],chunks=chunks,original_preserved=True,chunk_reassembly_verified=True))
assert entries
(dest/'TRANSPORT_MANIFEST.json').write_text(json.dumps(dict(status='LOSSLESS_CHUNK_TRANSPORT_VERIFIED',source_archive=str(archive.relative_to(repo)),chunk_size=chunk_size,entries=entries,new_integrations=0,original_deleted=False),indent=2)+'\n')
(dest/'README.md').write_text('# Lossless archive transport\n\nThe immutable V790 archive contains a compressed raw-evidence blob larger than100MB. Its original remains local unchanged; only this one original large blob is omitted from Git transport. All chunks here are32MiB maximum and reconstruct its exact compressed bytes/SHA. Other archive files and original manifests are transported normally. Run `python3 experiments/global_night_20261103_analysis/reconstruct_large_blobs.py` from the Phase repository after checkout, then verify the original archive MANIFEST. Reconstruction never overwrites a conflicting original. Remote synchronization is not implied by local chunk verification.\n')
signal.alarm(0);print(json.dumps(dict(status='LOSSLESS_CHUNK_TRANSPORT_VERIFIED',large_blobs=len(entries),chunks=sum(len(x['chunks'])for x in entries),total_bytes=sum(x['bytes']for x in entries))))
