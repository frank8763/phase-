"""Immutable all-source lossless evidence archive; zero models/integrations."""
import gzip,hashlib,json,subprocess,sys
from pathlib import Path
from evidence_rules import dump,read,sha
def archive(repo,stage,own,report,freezepath,name):
 target=repo/name;assert not target.exists();target.mkdir();(target/'blobs').mkdir();files={repo/n for n in read(freezepath)['files']}
 for directory in[stage,own]:files.update(p for p in directory.rglob('*')if p.is_file()and p.suffix not in['.lock','.pyc']and '__pycache__'not in p.parts and p.name not in['finalize.console','transport.console'])
 files.add(report);inventory=[]
 for p in sorted(files):
  raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();encoding='identity'if p.suffix=='.gz'else'gzip';blob=target/'blobs'/(h+('.raw'if encoding=='identity'else'.gz'))
  if not blob.exists():blob.write_bytes(raw if encoding=='identity'else gzip.compress(raw,mtime=0))
  inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=str(blob.relative_to(target)),encoding=encoding))
 (target/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0));verified={}
 for x in inventory:
  if x['blob']not in verified:
   data=(target/x['blob']).read_bytes();raw=data if x['encoding']=='identity'else gzip.decompress(data);verified[x['blob']]=(len(raw),hashlib.sha256(raw).hexdigest())
  assert verified[x['blob']]==(x['bytes'],x['sha256'])and sha(repo/x['path'])==x['sha256']
 manifest=[dict(path=str(p.relative_to(target)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(target.rglob('*'))if p.is_file()];dump(target/'MANIFEST.json',manifest)
 transport=None
 if any(x['bytes']>90*1024**2 for x in manifest):
  transport=name+'_transport';p=subprocess.run([sys.executable,'-B',str(repo/'experiments/global_day_20261104_analysis/transport_archive.py'),str(target),str(repo/transport)],cwd=repo,capture_output=True,text=True,timeout=605);(stage/'transport.console').write_text(p.stdout+p.stderr);assert p.returncode==0,'LOSSLESS_TRANSPORT_FAILED'
 return dict(archive=name,transport=transport,raw_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),source_and_decompressed_sha_verified=True,raw_deleted=False)
