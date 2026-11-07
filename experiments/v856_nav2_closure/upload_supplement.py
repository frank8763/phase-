"""Add license notices/final index once, retaining original uploaded index unchanged."""
import hashlib,json,subprocess,time
from pathlib import Path
from upload_records import R,ROOT,OUT,REC,GH,REPO,TAG,api,sha,dump,gh

def main():
 base=json.loads((OUT/'FULL_REMOTE_VERIFIED.json').read_text());assert base['passed'];index=json.loads((REC/'RECORD_INDEX.json').read_text());index['status']='LOCAL_ALL_ARCHIVE_MEMBER_AND_PART_SHA_VERIFIED_SEE_REMOTE_RECEIPTS';(REC/'RECORD_INDEX.json').write_text(json.dumps(index,indent=2)+'\n');(OUT/'FINAL_RECORD_INDEX.json').write_text(json.dumps(index,indent=2)+'\n');group=index['archives'][-1];assert group['group']=='v856-third-party-licenses'
 files=[OUT/r['name']for r in group['parts']]+[OUT/'v856-third-party-licenses.INVENTORY.json',OUT/'FINAL_RECORD_INDEX.json'];assets={a['name']:a for a in api(f'repos/{REPO}/releases/{base["release_id"]}/assets?per_page=100')};done=json.loads((OUT/'ASSET_REMOTE_VERIFICATION.json').read_text())
 for p in files:
  digest=sha(p);size=p.stat().st_size;asset=assets.get(p.name)
  if asset is None:
   with(OUT/(p.name+'.upload.console')).open('w')as f:gh(['release','upload',TAG,str(p),'--repo',REPO],stdout=f,stderr=subprocess.STDOUT,timeout=180)
   asset=next(a for a in api(f'repos/{REPO}/releases/{base["release_id"]}/assets?per_page=100')if a['name']==p.name)
  assert asset['size']==size and asset['digest']=='sha256:'+digest
  h=hashlib.sha256();read=0
  with(OUT/(p.name+'.download.console')).open('w')as err:
   proc=subprocess.Popen([str(GH),'release','download',TAG,'--repo',REPO,'--pattern',p.name,'--output','-'],cwd=R,stdout=subprocess.PIPE,stderr=err)
   for b in iter(lambda:proc.stdout.read(1048576),b''):h.update(b);read+=len(b)
   assert proc.wait(timeout=10)==0
  assert read==size and h.hexdigest()==digest
  old=next((a for a in done if a['name']==p.name),None)
  if old:assert old['sha256']==digest
  else:done.append(dict(name=p.name,asset_id=asset['id'],bytes=size,sha256=digest,server_digest=asset['digest'],url=asset['browser_download_url'],streamed_download_sha_verified=True))
  dump(OUT/'ASSET_REMOTE_VERIFICATION.json',done);print(json.dumps(dict(asset=p.name,verified=True)),flush=True)
 base.update(assets=len(done),asset_bytes=sum(a['bytes']for a in done),all_server_digests_matched=True,all_streamed_download_sha_verified=True,final_index_asset='FINAL_RECORD_INDEX.json',release_url=index['release_url'],verified_unix=time.time());dump(OUT/'FULL_REMOTE_VERIFIED.json',base);dump(REC/'FULL_REMOTE_VERIFIED.json',base);dump(REC/'ASSET_REMOTE_VERIFICATION.json',done)
if __name__=='__main__':main()
