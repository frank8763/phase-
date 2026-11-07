"""Three bounded parallel transfers, each requiring remote digest and downloaded SHA."""
import concurrent.futures,fcntl,hashlib,json,subprocess,threading,time
from pathlib import Path
from plan import R,OUT,dump
GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-';TAG='phase-essential-records-20261107';mutex=threading.Lock()

def gh(args,**kwargs):return subprocess.run([str(GH),*args],cwd=R,check=True,**kwargs)
def api(path):return json.loads(gh(['api',path],capture_output=True,text=True,timeout=90).stdout)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def main():
    lock=(OUT/'upload.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    source=json.loads((OUT/'SOURCE_REMOTE_VERIFIED.json').read_text());assert source['passed'];index=json.loads((OUT/'RECORD_INDEX.json').read_text());index.update(source_commit=source['commit'],release_url=f'https://github.com/{REPO}/releases/tag/{TAG}');dump(OUT/'RECORD_INDEX.json',index)
    releases=api(f'repos/{REPO}/releases?per_page=100');release=next(x for x in releases if x['tag_name']==TAG);assert release['draft']
    notes=OUT/'RELEASE_NOTES.md';notes.write_text('Essential Phase research records through2026-11-07.\n\nSource/reports: '+source['commit']+'\n\nPreserves static acceptance, the verified three-route development milestone, latest V855 actual states/sensors/controls and terminal failure witnesses, selected reproduction inputs, and failed confirmation actual trajectories. Original failed outcomes remain failed. Unselected earlier candidate pools and duplicate archives are intentionally omitted by user request; these selected archives do not claim to reproduce every old rejected candidate audit.\n\nRECORD_INDEX.json records archive and part SHA256. Every asset has been verified by streamed download before local essential data is removed. Restore only one group on demand with tools/phase_storage_20261107/restore.py.\n')
    items=[dict(x,path=OUT/'assets'/x['name'])for group in index['archives']for x in group['parts']]
    for name in ['RECORD_INDEX.json','PLAN_SUMMARY.json','DELETE_PLAN.jsonl.gz']:
        p=OUT/name;items.append(dict(name=name,path=p,bytes=p.stat().st_size,sha256=sha(p)))
    existing={x['name']:x for x in api(f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100')};done=json.loads((OUT/'ASSET_REMOTE_VERIFICATION.json').read_text())if(OUT/'ASSET_REMOTE_VERIFICATION.json').exists()else[];byname={x['name']:x for x in done};progress={};started=time.time()
    def status(item,stage,**kwargs):
        with mutex:
            progress[item['name']]=dict(stage=stage,bytes=item['bytes'],**kwargs);dump(OUT/'UPLOAD_PARALLEL_PROGRESS.json',dict(verified=len(byname),total=len(items),verified_bytes=sum(x['bytes']for x in byname.values()),elapsed_s=time.time()-started,active=progress.copy(),workers=3))
    def transfer(item):
        old=byname.get(item['name'])
        if old is not None:
            assert old['sha256']==item['sha256']and old['bytes']==item['bytes']and old['streamed_download_verified'];return old
        status(item,'UPLOADING');asset=existing.get(item['name'])
        if asset is not None:assert asset['state']=='uploaded'and asset['size']==item['bytes'],'INCOMPLETE_REMOTE_ASSET_NEEDS_DIAGNOSIS'
        else:
            with(OUT/(item['name']+'.parallel_upload.console')).open('wb')as f:gh(['release','upload',TAG,str(item['path']),'--repo',REPO],stdout=f,stderr=subprocess.STDOUT,timeout=1800)
            asset=next(x for x in api(f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100')if x['name']==item['name'])
        assert asset['size']==item['bytes']and asset['state']=='uploaded';remote=asset.get('digest')
        if remote is not None:assert remote=='sha256:'+item['sha256']
        status(item,'DOWNLOADING_AND_HASHING');h=hashlib.sha256();size=0
        with(OUT/(item['name']+'.parallel_download.console')).open('wb')as error:
            p=subprocess.Popen([str(GH),'release','download',TAG,'--repo',REPO,'--pattern',item['name'],'--output','-'],cwd=R,stdout=subprocess.PIPE,stderr=error)
            try:
                for block in iter(lambda:p.stdout.read(1048576),b''):
                    size+=len(block);h.update(block)
                    if size%(32*1024**2)==0:status(item,'DOWNLOADING_AND_HASHING',downloaded_bytes=size)
                assert p.wait(timeout=30)==0
            finally:
                if p.poll()is None:p.terminate();p.wait(timeout=5)
        assert size==item['bytes']and h.hexdigest()==item['sha256']
        record=dict(name=item['name'],asset_id=asset['id'],bytes=size,sha256=h.hexdigest(),server_digest=remote,url=asset['browser_download_url'],streamed_download_verified=True)
        with mutex:
            byname[item['name']]=record;progress.pop(item['name'],None);dump(OUT/'ASSET_REMOTE_VERIFICATION.json',list(byname.values()));print(json.dumps(dict(event='ASSET_VERIFIED',asset=item['name'],verified=len(byname),total=len(items))),flush=True)
        return record
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
            futures=[pool.submit(transfer,item)for item in items]
            for future in concurrent.futures.as_completed(futures):future.result()
        assert len(byname)==len(items)
        gh(['release','edit',TAG,'--repo',REPO,'--target',source['commit'],'--notes-file',str(notes),'--draft=false','--latest=false'],timeout=90)
        final=api(f'repos/{REPO}/releases/{release["id"]}');assert not final['draft'];proof=dict(passed=True,repository=REPO,release_url=final['html_url'],source_commit=source['commit'],release_id=final['id'],assets=len(byname),bytes=sum(x['bytes']for x in byname.values()),every_asset_streamed_download_sha_verified=True,public_history_rewritten=False,verified_unix=time.time());dump(OUT/'FULL_REMOTE_VERIFIED.json',proof);print(json.dumps(proof),flush=True)
    except BaseException as e:dump(OUT/'TRANSFER_ERROR.json',dict(type=type(e).__name__,message=str(e),verified=len(byname),local_essential_files_retained=True));raise
if __name__=='__main__':main()
