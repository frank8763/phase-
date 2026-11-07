"""Upload selected Release assets and verify every byte by streaming them back."""
import fcntl,hashlib,json,subprocess,time
from pathlib import Path
from plan import R,OUT,dump
GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-';TAG='phase-essential-records-20261107'

def gh(args,**kwargs):return subprocess.run([str(GH),*args],cwd=R,check=True,**kwargs)
def api(path):return json.loads(gh(['api',path],capture_output=True,text=True,timeout=90).stdout)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def main():
    lock=(OUT/'upload.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    source=json.loads((OUT/'SOURCE_REMOTE_VERIFIED.json').read_text());assert source['passed'];index=json.loads((OUT/'RECORD_INDEX.json').read_text());index['source_commit']=source['commit'];index['release_url']=f'https://github.com/{REPO}/releases/tag/{TAG}';dump(OUT/'RECORD_INDEX.json',index)
    releases=api(f'repos/{REPO}/releases?per_page=100');found=[x for x in releases if x['tag_name']==TAG]
    if not found:
        notes=OUT/'RELEASE_NOTES.md';notes.write_text('Essential Phase research records through2026-11-07.\n\nSelected static acceptance, verified three-route development milestone, latest V855 actual evidence and terminal rejection witnesses and reproduction inputs, and the failed fresh-confirmation actual trajectories are retained. Original failed outcomes remain failed. Superseded intermediate candidate pools and duplicate archives are intentionally omitted by user request.\n\nSource and reports: '+source['commit']+'\n\nEvery asset has SHA256 in RECORD_INDEX.json; the upload was verified by streamed download. Restore only the required archive using tools/phase_storage_20261107/restore.py.\n')
        gh(['release','create',TAG,'--repo',REPO,'--target',source['commit'],'--draft','--title','Phase essential research records ·2026-11-07','--notes-file',str(notes)],timeout=90)
        found=[x for x in api(f'repos/{REPO}/releases?per_page=100')if x['tag_name']==TAG]
    release=found[0];items=[]
    for group in index['archives']:
        items.extend(dict(x,path=OUT/'assets'/x['name'])for x in group['parts'])
    for name in ['RECORD_INDEX.json','PLAN_SUMMARY.json','DELETE_PLAN.jsonl.gz']:
        p=OUT/name;items.append(dict(name=name,path=p,bytes=p.stat().st_size,sha256=sha(p)))
    done_file=OUT/'ASSET_REMOTE_VERIFICATION.json';done=json.loads(done_file.read_text())if done_file.exists()else[];byname={x['name']:x for x in done}
    for item in items:
        previous=byname.get(item['name'])
        if previous is not None:
            assert previous['sha256']==item['sha256']and previous['bytes']==item['bytes']and previous['streamed_download_verified'];continue
        dump(OUT/'UPLOAD_PROGRESS.json',dict(stage='UPLOADING',asset=item['name'],bytes=item['bytes'],verified_assets=len(done),total_assets=len(items),started_unix=time.time()))
        assets=api(f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100');matching=[x for x in assets if x['name']==item['name']]
        if not matching:
            with(OUT/(item['name']+'.upload.console')).open('wb')as f:gh(['release','upload',TAG,str(item['path']),'--repo',REPO],stdout=f,stderr=subprocess.STDOUT,timeout=1800)
            matching=[x for x in api(f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100')if x['name']==item['name']]
        assert len(matching)==1;asset=matching[0];assert asset['size']==item['bytes']and asset['state']=='uploaded';remote_digest=asset.get('digest')
        if remote_digest is not None:assert remote_digest=='sha256:'+item['sha256'],'REMOTE_ASSET_DIGEST_MISMATCH'
        dump(OUT/'UPLOAD_PROGRESS.json',dict(stage='STREAMING_DOWNLOAD_VERIFY',asset=item['name'],bytes=item['bytes'],verified_assets=len(done),total_assets=len(items)))
        h=hashlib.sha256();size=0
        with(OUT/(item['name']+'.download.console')).open('wb')as err:
            p=subprocess.Popen([str(GH),'release','download',TAG,'--repo',REPO,'--pattern',item['name'],'--output','-'],cwd=R,stdout=subprocess.PIPE,stderr=err)
            try:
                for block in iter(lambda:p.stdout.read(1048576),b''):
                    size+=len(block);h.update(block)
                    if size%(32*1024**2)==0:dump(OUT/'UPLOAD_PROGRESS.json',dict(stage='STREAMING_DOWNLOAD_VERIFY',asset=item['name'],downloaded_bytes=size,total_bytes=item['bytes'],verified_assets=len(done),total_assets=len(items)))
                assert p.wait(timeout=30)==0
            finally:
                if p.poll()is None:p.terminate();p.wait(timeout=5)
        assert size==item['bytes']and h.hexdigest()==item['sha256'],'REMOTE_DOWNLOAD_SHA_MISMATCH'
        record=dict(name=item['name'],asset_id=asset['id'],bytes=size,sha256=h.hexdigest(),server_digest=remote_digest,url=asset['browser_download_url'],streamed_download_verified=True);done.append(record);byname[record['name']]=record;dump(done_file,done);print(json.dumps(dict(event='ASSET_VERIFIED',asset=item['name'],bytes=size,verified=len(done),total=len(items))),flush=True)
    assert len(done)==len(items)
    gh(['release','edit',TAG,'--repo',REPO,'--draft=false','--latest=false'],timeout=90)
    final=api(f'repos/{REPO}/releases/{release["id"]}');assert not final['draft'];dump(OUT/'FULL_REMOTE_VERIFIED.json',dict(passed=True,repository=REPO,release_url=final['html_url'],source_commit=source['commit'],release_id=final['id'],assets=len(done),bytes=sum(x['bytes']for x in done),every_asset_streamed_download_sha_verified=True,public_history_rewritten=False,verified_unix=time.time()));print(json.dumps(json.loads((OUT/'FULL_REMOTE_VERIFIED.json').read_text())),flush=True)
if __name__=='__main__':main()
