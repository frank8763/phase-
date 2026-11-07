"""All-source lossless immutable stage archive, no models or integration."""
import gzip,hashlib,json,os,subprocess,sys
from pathlib import Path
from evidence_rules import dump,read,sha

def archive(repo,phase,own,report,freezepath,name):
 target=repo/name;assert not target.exists(),'NO_ARCHIVE_OVERWRITE';target.mkdir();(target/'blobs').mkdir();files={repo/n for n in read(freezepath)['files']}
 directories=[phase,own]
 for relative in read(phase/'ARCHIVE_EXTRA_PATHS.json'):
  p=repo/relative
  if p.is_dir():directories.append(p)
  elif p.is_file():files.add(p)
 for directory in directories:files.update(p for p in directory.rglob('*')if p.is_file()and p.suffix not in['.lock','.pyc']and '__pycache__'not in p.parts and p.name not in['finalize.console','transport.console'])
 files.add(report);inventory=[];previous=repo/'evidence/rpccr_v842_pilot90_20261106/blobs'
 for p in sorted(files):
  data=p.read_bytes();h=hashlib.sha256(data).hexdigest();encoding='identity'if p.suffix=='.gz'else'gzip';blob=target/'blobs'/(h+('.raw'if encoding=='identity'else'.gz'))
  if not blob.exists():
   old=previous/blob.name
   if old.exists()and old!=blob:os.link(old,blob)
   else:blob.write_bytes(data if encoding=='identity'else gzip.compress(data,mtime=0))
  inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(data),sha256=h,blob=str(blob.relative_to(target)),encoding=encoding))
 (target/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0));verified={}
 for x in inventory:
  if x['blob']not in verified:
   b=(target/x['blob']).read_bytes();data=b if x['encoding']=='identity'else gzip.decompress(b);verified[x['blob']]=(len(data),hashlib.sha256(data).hexdigest())
  assert verified[x['blob']]==(x['bytes'],x['sha256'])and sha(repo/x['path'])==x['sha256']
 manifest=[dict(path=str(p.relative_to(target)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(target.rglob('*'))if p.is_file()];dump(target/'MANIFEST.json',manifest)
 transport=None
 if any(x['bytes']>90*1024**2 for x in manifest):
  transport=name+'_transport';p=subprocess.run([sys.executable,'-B',str(repo/'experiments/global_day_20261104_analysis/transport_archive.py'),str(target),str(repo/transport)],cwd=repo,capture_output=True,text=True,timeout=605);(phase/'transport.console').write_text(p.stdout+p.stderr);assert p.returncode==0,'LOSSLESS_REASSEMBLY_FAILED'
 return dict(archive=name,transport=transport,source_and_decompressed_sha_verified=True,raw_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),raw_deleted=False)
