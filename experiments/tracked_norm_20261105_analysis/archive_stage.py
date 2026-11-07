"""One immutable stage archive. Final stdout is deliberately not a source."""
import argparse,gzip,hashlib,json,signal
from pathlib import Path
repo=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['qualification','component']);a=ap.parse_args()
if a.stage=='qualification':name='v817_tracked_norm_qualification';freeze_name='CANDIDATE_FREEZE.json';audit_name='DECLARED_NORM_FIXED_CONTRACTS_INDEPENDENT_PASS'
else:name='v819_tracked_norm_native_entry';freeze_name='INPUT_FREEZE.json';audit_name='DECLARED_NORM_NATIVE_COMPONENT_EVIDENCE_PASS'
root=repo/'runs'/name;own=repo/'experiments'/name
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(root/'ROUND_WINDOW.json')['round_closed']
assert read(root/'FINAL_INDEPENDENT_AUDIT.json')['status']==audit_name
assert not(root/'ARCHIVE_VERIFIED.json').exists()
freeze=read(own/freeze_name);assert all(sha(repo/n)==h for n,h in freeze['files'].items())
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('600S_STAGE_ARCHIVE')));signal.alarm(600)
dest=repo/'evidence'/f'rpccr_tracked_norm_{a.stage}_20261105';assert not dest.exists();dest.mkdir();(dest/'blobs').mkdir()
files=set(repo/n for n in freeze['files'])
for d in [own,root]:files.update(p for p in d.rglob('*')if p.is_file()and p.suffix not in['.pyc','.lock']and '__pycache__'not in p.parts)
inventory=[]
for p in sorted(files):
    raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();blob=dest/'blobs'/(h+'.gz')
    if not blob.exists():blob.write_bytes(gzip.compress(raw,mtime=0))
    inventory.append(dict(path=str(p.relative_to(repo)),sha256=h,bytes=len(raw),blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for x in inventory:
    data=gzip.decompress((dest/x['blob']).read_bytes());assert len(data)==x['bytes']and hashlib.sha256(data).hexdigest()==x['sha256']and sha(repo/x['path'])==x['sha256']
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(dest.rglob('*'))if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for x in manifest:assert sha(dest/x['path'])==x['sha256']
result=dict(status='ALL_STAGE_SOURCES_AND_DECOMPRESSED_SHA_VERIFIED',stage=a.stage,archive=str(dest.relative_to(repo)),sources=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),raw_deleted=False,new_models=0,new_integrations=0)
(root/'ARCHIVE_VERIFIED.json').write_text(json.dumps(result,indent=2)+'\n');signal.alarm(0);print(json.dumps(result))
