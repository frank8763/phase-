"""Package only closed physical evidence and necessary runtime; verify every member SHA."""
import fcntl,hashlib,json,os,stat,subprocess,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v856_nav2_foundation';OUT=ROOT/'cloud';OUT.mkdir(exist_ok=True);REC=R/'records/nav2_v856_20261107';CHUNK=32*1024**2

def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def walk(base):
 for current,dirs,files in os.walk(base,followlinks=False):
  dirs[:]=[d for d in dirs if not(Path(current)/d).is_symlink()]
  for name in files:
   p=Path(current)/name
   if stat.S_ISREG(p.lstat().st_mode):yield p

def archive(group,files):
 target=OUT/(group+'.tar.zst');assert not target.exists()
 records=[]
 for p in sorted(set(files)):
  if p.is_symlink():records.append(dict(path=str(p.relative_to(R)),type='symlink',link=os.readlink(p),bytes=0))
  else:records.append(dict(path=str(p.relative_to(R)),type='file',bytes=p.stat().st_size,sha256=sha(p)))
 inventory={x['path']:x for x in records}
 with target.open('wb')as out:
  encoder=subprocess.Popen(['zstd','-q','-3','-T1','-c'],stdin=subprocess.PIPE,stdout=out)
  try:
   with tarfile.open(fileobj=encoder.stdin,mode='w|')as t:
    for item in records:t.add(R/item['path'],arcname=item['path'],recursive=False)
   encoder.stdin.close();assert encoder.wait(timeout=120)==0
  finally:
   if encoder.poll()is None:encoder.kill();encoder.wait()
 # Independent decompressed-content readback, every saved path exactly once.
 seen=set();reader=subprocess.Popen(['zstd','-q','-dc',str(target)],stdout=subprocess.PIPE)
 with tarfile.open(fileobj=reader.stdout,mode='r|')as t:
  for member in t:
   assert member.name in inventory and member.name not in seen;seen.add(member.name);row=inventory[member.name]
   if row['type']=='symlink':assert member.issym()and member.linkname==row['link']
   else:
    assert member.isfile()and member.size==row['bytes'];stream=t.extractfile(member);h=hashlib.sha256()
    for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    assert h.hexdigest()==row['sha256']
 assert reader.wait(timeout=30)==0 and seen==set(inventory)
 digest=sha(target);parts=[];reassembled=hashlib.sha256()
 with target.open('rb')as f:
  i=0
  while True:
   block=f.read(CHUNK)
   if not block:break
   part=OUT/(group+f'.tar.zst.part{i:03d}');part.write_bytes(block);parts.append(dict(name=part.name,bytes=len(block),sha256=sha(part)));reassembled.update(part.read_bytes());i+=1
 assert reassembled.hexdigest()==digest
 record=dict(group=group,source_files=len(records),raw_bytes=sum(x['bytes']for x in records),archive_bytes=target.stat().st_size,archive_sha256=digest,parts=parts,source_sha_and_decompressed_member_sha_verified=True,part_reassembly_sha_verified=True,files=records)
 (OUT/(group+'.INVENTORY.json')).write_text(json.dumps(record,indent=2)+'\n');target.unlink() # exact verified parts preserve the same archive, avoiding a duplicate.
 print(json.dumps({k:v for k,v in record.items()if k!='files'}),flush=True);return record

def main():
 assert json.loads((ROOT/'closed_analysis/FINAL_INDEPENDENT_AUDIT.json').read_text())['passed']
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 records=[]
 for p in walk(ROOT):
  rel=p.relative_to(ROOT)
  if rel.parts[0]in ['rootfs','cloud','apt']:continue
  records.append(p)
 for name in ['ros.key','ros.gpg','InRelease.verified','SIGNATURE.console','Packages.gz','sources.list','SIMULATION.console','DOWNLOAD_URIS.console']:
  p=ROOT/'apt'/name
  if p.exists():records.append(p)
 # Embedded release metadata is a closed snapshot, not a self-referential live log.
 evidence=archive('v856-evidence',records)
 selected=json.loads((ROOT/'RUNTIME_SELECTED.json').read_text());runtime=archive('v856-ros-runtime',[R/x['path']for x in selected['files']])
 index=dict(format_version=1,repository='frank8763/phase-',release_tag='phase-nav2-v856-20261107',release_url='https://github.com/frank8763/phase-/releases/tag/phase-nav2-v856-20261107',created_unix=time.time(),archives=[{k:v for k,v in a.items()if k!='files'}for a in [evidence,runtime]],runtime_requires='Compatible Ubuntu24.04 amd64 and system Python3.12 plus host system libraries listed in RUNTIME_SELECTED.json',status='LOCAL_SOURCE_DECOMPRESSION_AND_PART_SHA_VERIFIED_REMOTE_UPLOAD_PENDING',scientific_outcome='SOFTWARE_INTERFACE_PASSED_NATIVE_SPEED_QUALIFICATION_FAILED_NO_NAVIGATION')
 (REC/'RECORD_INDEX.json').write_text(json.dumps(index,indent=2)+'\n');(OUT/'RECORD_INDEX.json').write_text(json.dumps(index,indent=2)+'\n')
 print('PACKAGING_DONE',flush=True)
if __name__=='__main__':main()
