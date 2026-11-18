"""Bounded GitHub Release upload and full downloaded/decompressed SHA audit."""
from pathlib import Path
import concurrent.futures,hashlib,importlib.util,json,os,subprocess,threading,time,urllib.request
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name;D=R/'records/v1281_backup_20261118'
GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-';mutex=threading.Lock()
def dump(p,x):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def gh(args,timeout=90):
    p=subprocess.run([str(GH),*args],cwd=R,capture_output=True,text=True,timeout=timeout)
    assert p.returncode==0,'GITHUB_CLI_FAILED '+str(args[:3])+': '+p.stderr[-600:]
    return p.stdout
def api(path):return json.loads(gh(['api',path]))
def main():
    os.sched_setaffinity(0,{2,3,4,5});os.nice(19)
    assert not(D/'DELIVERY_CLAIM.json').exists(),'NO_DUPLICATE_NEW_RELEASE'
    source=read(D/'GIT_SYNC_RESULT.json');assert source['push_succeeded']and source['remote_head_verified']
    head=source['head'];index=read(D/'RECORD_INDEX.json');tag=index['release_tag']
    dump(D/'DELIVERY_CLAIM.json',dict(head=head,tag=tag,started_unix=time.time(),scope='new V1281 backup, not retry of historical sync'))
    request=O/'CREATE_RELEASE.json';dump(request,dict(tag_name=tag,target_commitish=head,name='V1281 dynamic fixed24: 24/24 and three exact repeats',body=(D/'RELEASE_NOTES.md').read_text(),draft=True,prerelease=False,make_latest='false'))
    release=json.loads(gh(['api','--method','POST',f'repos/{REPO}/releases','--input',str(request)]));rid=release['id'];dump(D/'RELEASE_CREATED.json',dict(id=rid,tag=tag,url=release['html_url'],draft=True,source_commit=head))
    items=[]
    for group in index['archives']:
        for part in group['parts']:items.append(dict(part,path=O/'transport'/group['group']/part['name']))
    for name in ['RECORD_INDEX.json','SOURCE_INVENTORY.json','FINAL_SUMMARY.json','INTERNAL_SYMLINKS.json','GIT_SYNC_RESULT.json','README.md']:
        p=D/name;items.append(dict(name=p.name,path=p,bytes=p.stat().st_size,sha256=sha(p)))
    progress={};uploaded=[];begin=time.monotonic()
    def transfer(item):
        assert item['path'].stat().st_size==item['bytes']and sha(item['path'])==item['sha256']
        gh(['release','upload',tag,str(item['path']),'--repo',REPO],timeout=300)
        with mutex:
            uploaded.append(item['name']);dump(D/'UPLOAD_PROGRESS.json',dict(uploaded=len(uploaded),total=len(items),last_asset=item['name'],elapsed_s=time.monotonic()-begin))
            print(json.dumps(dict(event='UPLOADED',asset=item['name'],complete=len(uploaded),total=len(items))),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        for f in concurrent.futures.as_completed([pool.submit(transfer,item)for item in items]):f.result()
    assets=api(f'repos/{REPO}/releases/{rid}/assets?per_page=100');byname={x['name']:x for x in assets}
    assert len(byname)==len(items),'ASSET_COUNT'
    for item in items:
        a=byname[item['name']];assert a['state']=='uploaded'and a['size']==item['bytes']
        if a.get('digest'):assert a['digest']=='sha256:'+item['sha256'],'SERVER_DIGEST '+item['name']
    spec=importlib.util.spec_from_file_location('phase_archive_readback',C/'archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
    all_members=read(D/'SOURCE_INVENTORY.json')['files'];download=O/'readback';download.mkdir();verified=[]
    def fetch(item):
        destination=download/item['name']
        with destination.open('xb')as out:
            p=subprocess.run([str(GH),'release','download',tag,'--repo',REPO,'--pattern',item['name'],'--output','-'],cwd=R,stdout=out,stderr=subprocess.PIPE,timeout=300)
        assert p.returncode==0,'DOWNLOAD_FAILED '+item['name']
        assert destination.stat().st_size==item['bytes']and sha(destination)==item['sha256'],'DOWNLOADED_SHA '+item['name']
        return destination
    def verify_group(group):
        # Inventory membership is bound to exact archive paths by its local
        # per-group inventory produced before Git/release publication.
        members=read(O/'transport'/group['group']/(group['group']+'.INVENTORY.json'))['files']
        arc.verify(group,members,lambda part:(fetch(part),True))
        result=dict(group=group['group'],files=len(members),raw_bytes=group['raw_bytes'],parts=len(group['parts']),all_downloaded_parts_and_decompressed_member_SHA_verified=True)
        with mutex:
            verified.append(result);dump(D/'REMOTE_ARCHIVE_READBACK.json',dict(groups=verified,complete=len(verified),total=len(index['archives'])))
            print(json.dumps(dict(event='DECOMPRESSED_REMOTE_SHA_VERIFIED',group=group['group'],complete=len(verified),total=len(index['archives']))),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        for f in concurrent.futures.as_completed([pool.submit(verify_group,g)for g in index['archives']]):f.result()
    partnames={p['name']for g in index['archives']for p in g['parts']}
    for item in items:
        if item['name']not in partnames:fetch(item).unlink()
    assert sum(g['files']for g in verified)==index['source_files']==len(all_members)
    pre=dict(passed=True,release_id=rid,release_url=release['html_url'],source_commit=head,files=index['source_files'],raw_bytes=index['raw_bytes'],
        archive_bytes=index['archive_bytes'],groups=len(verified),every_asset_download_SHA_verified=True,every_decompressed_member_SHA_verified=True,
        all_server_digests_verified=True,draft_at_readback=True,models=0,physical_native=0)
    dump(D/'REMOTE_READBACK_PREPUBLISH.json',pre)
    gh(['release','upload',tag,str(D/'REMOTE_READBACK_PREPUBLISH.json'),'--repo',REPO])
    gh(['release','edit',tag,'--repo',REPO,'--draft=false','--latest=false'])
    final=api(f'repos/{REPO}/releases/{rid}');assert not final['draft']and final['tag_name']==tag
    ref=api(f'repos/{REPO}/git/ref/tags/{tag}');assert ref['object']['sha']==head,'RELEASE_TAG_SOURCE_HEAD'
    finalassets={a['name']:a for a in api(f'repos/{REPO}/releases/{rid}/assets?per_page=100')}
    assert all(finalassets[n]['id']==a['id']for n,a in byname.items()),'ASSET_IDENTITY_CHANGED_AFTER_READBACK'
    # Public unauthenticated index read proves the published restore URL works.
    url=f'https://github.com/{REPO}/releases/download/{tag}/RECORD_INDEX.json'
    with urllib.request.urlopen(url,timeout=60)as src:public=src.read()
    assert hashlib.sha256(public).hexdigest()==sha(D/'RECORD_INDEX.json'),'PUBLIC_INDEX_READBACK'
    complete=dict(pre,published=True,draft_at_readback=True,public_index_download_SHA_verified=True,tag_commit_verified=True,asset_identities_unchanged=True,verified_unix=time.time(),local_raw_cleanup_not_yet_done=True)
    dump(D/'FULL_REMOTE_VERIFIED.json',complete)
    gh(['release','upload',tag,str(D/'FULL_REMOTE_VERIFIED.json'),'--repo',REPO])
    finalproof=dict(name='FULL_REMOTE_VERIFIED.json',bytes=(D/'FULL_REMOTE_VERIFIED.json').stat().st_size,sha256=sha(D/'FULL_REMOTE_VERIFIED.json'))
    fetch(finalproof).unlink()
    print(json.dumps(complete),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as e:
        dump(D/'DELIVERY_ERROR.json',dict(error=repr(e),all_unverified_local_evidence_retained=True,models=0,physical_native=0));raise
