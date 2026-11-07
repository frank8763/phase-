"""Finalize the passed saved qualification; no models/integrations."""
import gzip,hashlib,json,pathlib
repo=pathlib.Path(__file__).resolve().parents[2];own=repo/'experiments/v808_timed_reference_qualification';root=repo/'runs/v808_timed_reference_qualification';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(root/'COMPLETION.json')['status']=='SAVED_REFERENCE_SEARCH_COMPLETE'and read(root/'FINAL_INDEPENDENT_AUDIT.json')['status']=='TIME_REFERENCE_QUALIFICATION_PASS';assert not(root/'FINALIZED.json').exists()
assert all(sha(repo/p)==h for p,h in read(own/'CANDIDATE_FREEZE.json')['files'].items())
dest=repo/'evidence/rpccr_time_reference_qualification_v808_20261104';assert not dest.exists();dest.mkdir();(dest/'blobs').mkdir();inventory=[]
for folder in [own,root]:
 for p in sorted(folder.rglob('*')):
  if not p.is_file()or'__pycache__'in p.parts:continue
  raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();data=gzip.compress(raw,mtime=0);blob=dest/'blobs'/(h+'.gz')
  if blob.exists():assert blob.read_bytes()==data
  else:blob.write_bytes(data)
  inventory.append(dict(path=str(p.relative_to(repo)),sha256=h,bytes=len(raw),blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for x in inventory:
 raw=gzip.decompress((dest/x['blob']).read_bytes());assert len(raw)==x['bytes']and hashlib.sha256(raw).hexdigest()==x['sha256']==sha(repo/x['path'])
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(dest.rglob('*'))if p.is_file()];(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
(root/'FINALIZED.json').write_text(json.dumps(dict(status='TIME_REFERENCE_QUALIFICATION_PASS',source_decompressed_sha_verified=True,archive=str(dest.relative_to(repo)),sources=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),models=0,integrations=0),indent=2)+'\n')
print(json.dumps({'qualified':True,'sources':len(inventory),'archive':str(dest.relative_to(repo)),'models':0,'integrations':0}))

