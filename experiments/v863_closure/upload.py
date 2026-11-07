"""One bounded publish attempt per asset, followed by remote digest/download SHA verification."""
import concurrent.futures,hashlib,json,subprocess,threading,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v862_v863_closure';OUT=ROOT/'cloud';REC=R/'records/nav2_v863_execution_20261107';GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-';TAG='phase-nav2-v862-v863-20261107';mutex=threading.Lock()
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
  notes=OUT/'RELEASE_NOTES.md';notes.write_text('V862 genuine Nav2 MPPI static WE failed at180s; V863 single explicitly approved official RPP1.3.13 candidate, same physical model/map/Adapter/hard gates, passed one static WE in45.69s simulation, goal error0.241048108m, minclearance0.272050220m, badcontacts0,4569actual+4569complete own-control replay with error0. No dynamic actor/navigation, no route repeats or new24, no training/real robot. Original failures and inherited22:33:58 deadline unchanged. Necessary full native/ROS evidence and signed plugin provenance preserved; base ROS runtime reused from V856 Release. Finite development evidence only, not a general controller superiority or RP-CCR innovation claim.')
  head=api(f'repos/{REPO}/git/ref/heads/main')['object']['sha'];gh(['release','create',TAG,'--repo',REPO,'--target',head,'--draft','--title','Phase V862 MPPI failure and V863 RPP static route success','--notes-file',str(notes)],timeout=90);found=[x for x in api(f'repos/{REPO}/releases?per_page=100')if x['tag_name']==TAG]
 assert len(found)==1;release=found[0];assets={x['name']:x for x in api(f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100')};items=[]
 for a in index['archives']:
  for part in a['parts']:items.append(dict(part,path=OUT/part['name']))
 for name in ['RECORD_INDEX.json','v862-v863-evidence.INVENTORY.json']:
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
