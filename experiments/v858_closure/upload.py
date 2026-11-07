"""One bounded publish attempt per asset, followed by remote digest/download SHA verification."""
import concurrent.futures,hashlib,json,subprocess,threading,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v858_nav2_verified';OUT=ROOT/'cloud';REC=R/'records/nav2_v858_v859_20261107';GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-';TAG='phase-nav2-v858-v860-20261107';mutex=threading.Lock()
def gh(args,**kwargs):return subprocess.run([str(GH),*args],cwd=R,check=True,**kwargs)
def api(path):
 path+=('&'if'?'in path else'?')+'phase_read='+str(time.time_ns())
 return json.loads(gh(['api',path],capture_output=True,text=True,timeout=60).stdout)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def dump(p,v):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2)+'\n');t.replace(p)
def main():
 index=json.loads((OUT/'RECORD_INDEX.json').read_text());assert index['release_tag']==TAG
 releases=api(f'repos/{REPO}/releases?per_page=100');found=[x for x in releases if x['tag_name']==TAG]
 if not found:
  notes=OUT/'RELEASE_NOTES.md';notes.write_text('Phase V858-V860 engineering development, 2026-11-07. NOT DYNAMIC ACCEPTANCE. V858 assembly/controller qualification passed; static Nav2 tracking failed. V859 fixed-response steering candidate failed. V860 lifecycle entry failed before policy commands. New dynamic/24 confirmation never started. All actual state/control/contact traces and frozen science source retained. Archive source members and 32MiB transport parts independently SHA-verified; streamed remote download receipts accompany records. Existing V856 Release supplies original qualification inputs and selected ROS runtime; no duplicate SDK. Final transport stdout is a separate asset; the original empty in-progress member is preserved as its snapshot. Training and real robot zero.')
  head=subprocess.run(['git','rev-parse','HEAD'],cwd=R,check=True,capture_output=True,text=True).stdout.strip();gh(['release','create',TAG,'--repo',REPO,'--target',head,'--draft','--title','Phase V858-V860 model and Nav2 development evidence','--notes-file',str(notes)],timeout=90);found=[x for x in api(f'repos/{REPO}/releases?per_page=100')if x['tag_name']==TAG]
 assert len(found)==1;release=found[0];assets={x['name']:x for x in api(f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100')};items=[]
 for a in index['archives']:
  for part in a['parts']:items.append(dict(part,path=OUT/part['name']))
 for name in ['RECORD_INDEX.json','v858-v860-evidence.INVENTORY.json','package.final.console','TRANSPORT_LOG_NOTE.json']:
  p=OUT/name;items.append(dict(name=name,path=p,bytes=p.stat().st_size,sha256=sha(p)))
 receipt=OUT/'ASSET_REMOTE_VERIFICATION.json';done=json.loads(receipt.read_text())if receipt.exists()else[];doneby={x['name']:x for x in done}
 def transfer(item):
  if item['name']in doneby:
   old=doneby[item['name']];assert old['sha256']==item['sha256']and old['streamed_download_sha_verified'];return
  asset=assets.get(item['name'])
  if asset is None:
   with (OUT/(item['name']+'.upload.console')).open('w')as f:gh(['release','upload',TAG,str(item['path']),'--repo',REPO],stdout=f,stderr=subprocess.STDOUT,timeout=300)
   asset=next(x for x in api(f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100')if x['name']==item['name'])
  assert asset['size']==item['bytes']and asset['state']=='uploaded';assert asset.get('digest')=='sha256:'+item['sha256'],'SERVER_DIGEST_NOT_MATCHED'
  h=hashlib.sha256();size=0;start=time.monotonic()
  with (OUT/(item['name']+'.download.console')).open('w')as err:
   p=subprocess.Popen([str(GH),'release','download',TAG,'--repo',REPO,'--pattern',item['name'],'--output','-'],cwd=R,stdout=subprocess.PIPE,stderr=err)
   try:
    for b in iter(lambda:p.stdout.read(1048576),b''):
     size+=len(b);h.update(b)
     if time.monotonic()-start>300:raise TimeoutError('BOUNDED_DOWNLOAD')
    assert p.wait(timeout=10)==0
   finally:
    if p.poll()is None:p.terminate();p.wait(timeout=5)
  assert size==item['bytes']and h.hexdigest()==item['sha256'],'REMOTE_DOWNLOAD_SHA_MISMATCH'
  row=dict(name=item['name'],asset_id=asset['id'],bytes=size,sha256=h.hexdigest(),server_digest=asset['digest'],url=asset['browser_download_url'],streamed_download_sha_verified=True)
  with mutex:done.append(row);dump(receipt,done);print(json.dumps(dict(asset=item['name'],verified=len(done),total=len(items))),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
  fs=[pool.submit(transfer,item)for item in items]
  for f in concurrent.futures.as_completed(fs):f.result()
 assert len(done)==len(items)
 verification=dict(passed=True,release_id=release['id'],release_url=release['html_url'],assets=len(done),asset_bytes=sum(x['bytes']for x in done),all_server_digests_matched=True,all_streamed_download_sha_verified=True,verified_unix=time.time(),status='VERIFIED_DRAFT_PENDING_SOURCE_COMMIT_AND_PUBLICATION')
 dump(OUT/'FULL_REMOTE_VERIFIED.json',verification);dump(REC/'ASSET_REMOTE_VERIFICATION.json',done);dump(REC/'FULL_REMOTE_VERIFIED.json',verification);print(json.dumps(verification),flush=True)
if __name__=='__main__':main()
