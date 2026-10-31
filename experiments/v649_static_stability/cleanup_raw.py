"""Remove only this completed round's raw runtime copies after archive verification.
Plan captures every original file hash. Cleanup requires a recorded remote commit
and byte-identical remote MANIFEST; selected compressed artifacts are verified
against raw bytes first. Unselected large logs are intentionally not backed up.
"""
import argparse,gzip,hashlib,json,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');a=p.parse_args();repo=Path(__file__).resolve().parents[2];root=repo/'runs/v649_static_stability';e=repo/'evidence/static_stability_20261031';plan=e/'RAW_CLEANUP_PLAN.json.gz'
def sha(b):return hashlib.sha256(b).hexdigest()
manifest=json.loads((e/'MANIFEST.json').read_text())
for entry in manifest:assert sha((e/entry['path']).read_bytes())==entry['sha256'],entry['path']
if not a.execute:
 assert root.is_dir() and not plan.exists()
 files=[{'path':str(f.relative_to(repo)),'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in sorted(root.rglob('*'))if f.is_file()and not f.is_symlink()]
 links=[{'path':str(f.relative_to(repo)),'target':os.readlink(f)}for f in sorted(root.rglob('*'))if f.is_symlink()]
 with gzip.GzipFile(str(plan),'wb',mtime=0)as stream:stream.write(json.dumps({'scope':'only runs/v649_static_stability; selected full evidence and all-attempt metadata retained; unselected raw logs intentionally not backed up','files':files,'symlinks':links},indent=2).encode())
 print(json.dumps({'planned_files':len(files),'planned_bytes':sum(x['bytes']for x in files)}));raise SystemExit
remote=e/'REMOTE_VERIFICATION.json';proof=json.loads(remote.read_text());assert proof['remote_head']==proof['local_head']and proof['manifest_byte_identical']and proof['package_files_verified']
# Manifest at verification is preserved as its SHA, independent of later cleanup metadata.
assert sha((e/'MANIFEST.json').read_bytes())==proof['manifest_sha256']
for run in (e/'selected').iterdir():
 for f in run.rglob('*'):
  if not f.is_file():continue
  raw=root/run.name/'paired'/f.relative_to(run)
  if f.name.endswith(('.json.gz','.jsonl.gz','.mjb.gz')):
   raw=Path(str(raw)[:-3]);b=gzip.decompress(f.read_bytes())
  else:b=f.read_bytes()
  assert raw.is_file()and sha(raw.read_bytes())==sha(b),str(raw)
with gzip.open(plan,'rt')as stream:payload=json.load(stream);files=payload['files'];links=payload['symlinks']
expected={repo/x['path']for x in files};actual={f for f in root.rglob('*')if f.is_file()and not f.is_symlink()};assert expected==actual,'Raw files changed since plan'
for row in files:
 f=repo/row['path'];assert f.is_relative_to(root)and not f.is_symlink()and f.stat().st_size==row['bytes']and sha(f.read_bytes())==row['sha256'],row['path']
assert {repo/x['path']for x in links}=={f for f in root.rglob('*')if f.is_symlink()}
for row in links:
 f=repo/row['path'];assert f.is_relative_to(root)and f.is_symlink()and os.readlink(f)==row['target']
for row in links:(repo/row['path']).unlink()
for row in files:(repo/row['path']).unlink()
for d in sorted((x for x in root.rglob('*')if x.is_dir()and not x.is_symlink()),key=lambda p:len(p.parts),reverse=True):d.rmdir()
root.rmdir()
(e/'RAW_CLEANUP_RESULT.json').write_text(json.dumps({'status':'COMPLETE','deleted_files':len(files),'deleted_local_symlinks':len(links),'deleted_bytes':sum(x['bytes']for x in files),'scope':'runs/v649_static_stability only; frozen sources, models, other rounds and Stage untouched','remote_archive_commit':proof['remote_head'],'selected_archive_bytes_verified_against_raw':True,'unselected_raw_logs_backed_up':False},indent=2));print((e/'RAW_CLEANUP_RESULT.json').read_text())
