"""One Release backup of the closed checkpoint; verify bytes and every member."""
from pathlib import Path
import hashlib,json,os,subprocess,tarfile,time,io,signal,fcntl
R=Path(__file__).resolve().parents[2];O=R/'runs/v1230_fixed24_resume';D=R/'records/nav2_v1228_checkpoint_20261116';P=R/'runs/v1228_terminal_reserve_confirmation';GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-';TAG='phase-v1228-fixed24-checkpoint-20261116'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def dump(p,v):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def gh(args,timeout=90,**kw):return subprocess.run([str(GH),*args],cwd=R,check=True,timeout=timeout,**kw)
def api(path):return json.loads(gh(['api',path+('&'if'?'in path else'?')+'phase_read='+str(time.time_ns())],capture_output=True,text=True).stdout)
class ReadHash:
 def __init__(self,stream):self.stream=stream;self.h=hashlib.sha256();self.size=0
 def read(self,n=-1):
  b=self.stream.read(n);self.h.update(b);self.size+=len(b);return b

def main():
 assert not(D/'REMOTE_VERIFIED.json').exists()
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert read(P/'COMPLETION.json')['stop_reason']=='INSUFFICIENT_REMAINING_FOR_COMPLETE_TASK_AUDIT'
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 cloud=O/'cloud';cloud.mkdir(exist_ok=True);inventory=D/'INVENTORY.json';archive=cloud/'v1228-checkpoint-and-source-v2.tar.gz'
 if not inventory.exists():
  files={n:dict(v)for n,v in read(P/'LOCAL_MANIFEST.json')['files'].items()}
  for n,h in read(R/'experiments/v1228_terminal_reserve_confirmation/SOURCE_FREEZE.json')['files'].items():
   assert sha(R/n)==h;files[n]=dict(sha256=h,bytes=(R/n).stat().st_size)
  for folder in [R/'experiments/v1229_fixed24_resume_preparation',R/'runs/v1229_fixed24_resume_preparation']:
   for p in folder.rglob('*'):
    if p.is_file()and '__pycache__'not in p.parts:files[str(p.relative_to(R))]=dict(sha256=sha(p),bytes=p.stat().st_size)
  for n in ['LOCAL_MANIFEST.json','FINALIZED.json','campaign.console','watchdog.console','finalize.console','HANDOFF.md']:
   p=P/n
   if p.exists():files[str(p.relative_to(R))]=dict(sha256=sha(p),bytes=p.stat().st_size)
  dump(inventory,dict(files=files,raw_bytes=sum(v['bytes']for v in files.values()),models=0,new_mujoco_native=0))
 else:files=read(inventory)['files']
 if not archive.exists():
  assert not(archive.with_suffix('.partial')).exists(),'PRESERVE_INTERRUPTED_ARCHIVE'
  tmp=archive.with_suffix('.partial')
  with tarfile.open(tmp,'w:gz',compresslevel=1,dereference=True)as tf:
   for n,v in sorted(files.items()):
    p=R/n;assert p.resolve().is_relative_to(R)and sha(p)==v['sha256'];tf.add(p,arcname=n,recursive=False)
  tmp.replace(archive)
  with tarfile.open(archive,'r:gz')as tf:
   seen=set()
   for m in tf:
    assert m.isfile()and m.name in files and m.name not in seen
    h=hashlib.sha256();size=0
    # Read each member once, without extracting it to disk.
    f=tf.extractfile(m)
    for b in iter(lambda:f.read(1048576),b''):h.update(b);size+=len(b)
    assert size==files[m.name]['bytes']and h.hexdigest()==files[m.name]['sha256'];seen.add(m.name)
   assert seen==set(files)
  dump(D/'LOCAL_ARCHIVE_VERIFIED.json',dict(passed=True,sha256=sha(archive),bytes=archive.stat().st_size,members=len(files),all_member_sha_verified=True))
 info=read(D/'LOCAL_ARCHIVE_VERIFIED.json');assert sha(archive)==info['sha256']
 print(json.dumps(dict(stage='archive_verified',**info)),flush=True)
 # Release assets are not Git blobs. Existing same-name assets are only verified.
 rel=api(f'repos/{REPO}/releases/tags/{TAG}')
 found=[rel]
 assert len(found)==1;rel=found[0]
 items=[(archive,info['sha256']), (inventory,sha(inventory))];receipts=[]
 for path,digest in items:
  assets=api(f'repos/{REPO}/releases/{rel["id"]}/assets?per_page=100');asset=next((a for a in assets if a['name']==path.name),None)
  claim=D/(path.name+'.UPLOAD_CLAIM.json')
  if asset is None:
   assert not claim.exists(),'NO_ASSET_UPLOAD_RETRY'
   dump(claim,dict(at=time.time(),name=path.name,sha256=digest))
   with (O/(path.name+'.upload.console')).open('x')as f:gh(['release','upload',TAG,str(path),'--repo',REPO],timeout=600,stdout=f,stderr=subprocess.STDOUT)
   asset=next(a for a in api(f'repos/{REPO}/releases/{rel["id"]}/assets?per_page=100')if a['name']==path.name)
  assert asset['state']=='uploaded'and asset['size']==path.stat().st_size and asset.get('digest')=='sha256:'+digest,'SERVER_DIGEST_MISMATCH'
  with (O/(path.name+'.readback.console')).open('x')as err:
   proc=subprocess.Popen([str(GH),'release','download',TAG,'--repo',REPO,'--pattern',path.name,'--output','-'],cwd=R,stdout=subprocess.PIPE,stderr=err)
   reader=ReadHash(proc.stdout);seen=set()
   try:
    if path==archive:
     with tarfile.open(fileobj=reader,mode='r|gz')as tf:
      for m in tf:
       assert m.isfile()and m.name in files and m.name not in seen
       h=hashlib.sha256();size=0;f=tf.extractfile(m)
       for b in iter(lambda:f.read(1048576),b''):h.update(b);size+=len(b)
       assert size==files[m.name]['bytes']and h.hexdigest()==files[m.name]['sha256'],'REMOTE_MEMBER_SHA_MISMATCH';seen.add(m.name)
     assert seen==set(files)
    for b in iter(lambda:reader.read(1048576),b''):pass
    assert proc.wait(timeout=10)==0 and reader.size==path.stat().st_size and reader.h.hexdigest()==digest,'REMOTE_ARCHIVE_SHA_MISMATCH'
   finally:
    if proc.poll()is None:proc.kill();proc.wait(timeout=5)
  receipts.append(dict(name=path.name,asset_id=asset['id'],bytes=reader.size,sha256=digest,url=asset['browser_download_url'],streamed_download_sha_verified=True,all_decompressed_member_sha_verified=path==archive,members=len(seen)))
  dump(D/'ASSET_READBACKS.json',receipts);print(json.dumps(dict(stage='asset_verified',name=path.name,bytes=reader.size,members=len(seen))),flush=True)
 dump(D/'REMOTE_VERIFIED.json',dict(passed=True,release_url=rel['html_url'],release_tag=TAG,assets=receipts,all_bytes_and_sha_and_decompressed_members_verified=True,models=0,new_mujoco_native=0,verified_unix=time.time()))
 print(json.dumps(dict(stage='remote_verified',release=rel['html_url'])),flush=True)
if __name__=='__main__':
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('ARCHIVE_TRANSPORT_BOUND')));signal.alarm(1800)
 try:main()
 except BaseException as e:dump(D/'TRANSPORT03_ERROR.json',dict(error=repr(e),models=0,new_mujoco_native=0));raise
