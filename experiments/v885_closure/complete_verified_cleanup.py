"""Finish zero-model cleanup after verified delivery; preserve the original link assertion."""
import gzip,json,os,pathlib,shutil,stat,time
from deliver_once import R,O,REC,CLOUD,TAG,REPO,closed_lock,read,dump,sha,gh
def main():
    lock=closed_lock()
    original=read(REC/'DELIVERY_RESULT.json')
    assert original['status']=='DELIVERY_INCOMPLETE_NO_RETRY' and not original['raw_deleted']
    assert 'meshes_fixed' in original['error']
    proof=read(REC/'REMOTE_VERIFIED.json');assert proof['passed'] and proof['actual_members_restored']==266
    assert read(REC/'GIT_SYNC_RESULT.json')['remote_head_verified']
    with(O/'CLEANUP_COMPLETION_CLAIM.json').open('x')as f:
        json.dump(dict(models=0,integrations=0,source_push_retried=False,asset_delivery_retried=False,at=time.time()),f)
    cache=O/'remote_restore';index=read(CLOUD/'RECORD_INDEX.json');expected={}
    for asset in proof['assets']:
        for base in [CLOUD,cache]:
            p=base/asset['name'];assert p.stat().st_size==asset['bytes'] and sha(p)==asset['sha256']
    for group in index['archives']:
        inv=read(cache/(group['group']+'.INVENTORY.json'))
        expected.update({row['path']:row for row in inv['files']})
    raw=R/'runs/v858_nav2_verified/v885';entries=[]
    for base in [raw,CLOUD,cache]:
        assert base.is_dir() and not base.is_symlink() and base.resolve().is_relative_to(R/'runs')
        for current,dirs,files in os.walk(base,followlinks=False):
            for name in dirs+files:
                p=pathlib.Path(current)/name;s=p.lstat();rel=str(p.relative_to(R))
                if stat.S_ISLNK(s.st_mode):
                    assert base==raw and p.name=='meshes_fixed'
                    entries.append(dict(path=rel,type='symlink',link=os.readlink(p),bytes=s.st_size))
                elif stat.S_ISREG(s.st_mode):
                    digest=sha(p)
                    if base==raw:assert rel in expected and expected[rel]['sha256']==digest
                    entries.append(dict(path=rel,type='file',bytes=s.st_size,sha256=digest))
                else:assert stat.S_ISDIR(s.st_mode),rel
    assert sum(x['type']=='symlink' for x in entries)==4
    manifest=REC/'CLEANUP_FILES.jsonl.gz'
    manifest.write_bytes(gzip.compress(('\n'.join(json.dumps(x)for x in entries)+'\n').encode(),mtime=0))
    for row in entries:
        p=R/row['path']
        if row['type']=='symlink':assert p.is_symlink() and os.readlink(p)==row['link']
        else:assert not p.is_symlink() and sha(p)==row['sha256']
    # Unlink recorded directory entries only; never traverse or read a resource-link target.
    for row in entries:(R/row['path']).unlink()
    for base in [raw,CLOUD,cache]:
        for current,dirs,files in os.walk(base,topdown=False,followlinks=False):
            assert not files and all(not(pathlib.Path(current)/n).exists()for n in dirs)
            pathlib.Path(current).rmdir()
    result=dict(status='REMOTE_SOURCE_AND_266_MEMBER_RESTORE_VERIFIED_V885_TEMPORARY_CACHE_CLEANED',models=0,integrations=0,remote_verified=True,raw_deleted=True,removed_bytes=sum(x['bytes']for x in entries),resource_links_unlinked=4,resource_link_targets_accessed=False,old_failure_receipt_preserved='records/nav2_v885_20261108/DELIVERY_RESULT.json',source_push_retried=False,asset_delivery_retried=False,source_commit=original['source_commit'],release_url=proof['release_url'],cleanup_manifest_sha256=sha(manifest),at=time.time())
    dump(REC/'CLEANUP_COMPLETION.json',result);dump(O/'CLEANUP_COMPLETION.json',result)
    receipts=[REC/n for n in ['REMOTE_VERIFIED.json','DELIVERY_RESULT.json','CLEANUP_FILES.jsonl.gz','GIT_SYNC_RESULT.json','CLEANUP_COMPLETION.json']]
    receipts.append(pathlib.Path(__file__).resolve())
    gh(['release','upload',TAG,*map(str,receipts),'--repo',REPO],30)
    receipt_cache=O/'receipt_restore';receipt_cache.mkdir(exist_ok=False)
    for p in receipts:
        gh(['release','download',TAG,'--repo',REPO,'--pattern',p.name,'--dir',str(receipt_cache)],15)
        assert sha(receipt_cache/p.name)==sha(p),p.name
    shutil.rmtree(receipt_cache)
    dump(REC/'RECEIPTS_REMOTE_VERIFIED.json',dict(passed=True,files=[dict(name=p.name,sha256=sha(p))for p in receipts],at=time.time(),no_second_push=True))
    print(json.dumps(result),flush=True)
if __name__=='__main__':main()
