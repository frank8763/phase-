"""One same-repository Release, all part and decompressed-member remote SHA."""
import concurrent.futures,subprocess,time
from package import *
GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-'


def gh(args,timeout=120):
    p=subprocess.run([str(GH),*args],cwd=R,capture_output=True,text=True,timeout=timeout);assert p.returncode==0,'GH_FAILED '+str(args[:3])+': '+p.stderr[-400:];return p.stdout


def main():
    assert not(D/'DELIVERY_CLAIM.json').exists(),'ONE_NEW_DELIVERY';sync=read(D/'GIT_SYNC_RESULT.json');assert sync['push_succeeded']and sync['remote_head_verified'];index=read(D/'RECORD_INDEX.json');tag=index['release_tag'];head=sync['head']
    dump(D/'DELIVERY_CLAIM.json',dict(tag=tag,source_commit=head,started_unix=time.time(),models=0))
    request=O/'CREATE_RELEASE.json';dump(request,dict(tag_name=tag,target_commitish=head,name='Static tracking pilot and 8-state temporal mechanism ablation',body='Closed development evidence. Same-reference static pilot: RPP main/repeat passed; adapted MPPI first main violated15cm actual-clearance gate and stopped, repeat unexecuted. Temporal saved-state study:8 exact reconstructions,320timings, selected8/8 vswait0 5/8 source admission; not physical success-rate/generalization. Source reports,CSV and figure in Git; compact saved inputs avoid full-history recovery. 4MiB chunks and SHA index.',draft=True,make_latest='false'))
    release=json.loads(gh(['api','--method','POST',f'repos/{REPO}/releases','--input',str(request)],60));rid=release['id'];dump(D/'RELEASE_CREATED.json',dict(id=rid,url=release['html_url'],head=head,draft=True))
    items=[]
    for g in index['archives']:
        for part in g['parts']:items.append(dict(part,path=O/'transport'/g['group']/part['name']))
    for name in ['RECORD_INDEX.json','SOURCE_INVENTORY.json','RESULT_SUMMARY.json']:
        p=D/name;items.append(dict(name=name,path=p,bytes=p.stat().st_size,sha256=sha(p)))
    def upload(item):
        assert sha(item['path'])==item['sha256'];gh(['release','upload',tag,str(item['path']),'--repo',REPO]);print(json.dumps(dict(uploaded=item['name'])),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        for f in pool.map(upload,items):pass
    assets=json.loads(gh(['api',f'repos/{REPO}/releases/{rid}/assets?per_page=100'],60));byname={x['name']:x for x in assets};assert len(byname)==len(items)
    readback=O/'readback';readback.mkdir()
    def download(item):
        a=byname[item['name']];assert a['size']==item['bytes']and a['state']=='uploaded'
        if a.get('digest'):assert a['digest']=='sha256:'+item['sha256']
        dest=readback/item['name']
        with dest.open('xb')as stream:p=subprocess.run([str(GH),'release','download',tag,'--repo',REPO,'--pattern',item['name'],'--output','-'],cwd=R,stdout=stream,stderr=subprocess.PIPE,timeout=120)
        assert p.returncode==0 and dest.stat().st_size==item['bytes']and sha(dest)==item['sha256'],'REMOTE_PART_SHA';return dest
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for _ in pool.map(download,items):pass
    allitems=read(D/'SOURCE_INVENTORY.json')['files'];groups=[]
    for g in index['archives']:
        archive=readback/(g['group']+'.tar.gz')
        with archive.open('xb')as stream:
            for part in g['parts']:stream.write((readback/part['name']).read_bytes())
        assert sha(archive)==g['archive_sha256'];n=verify(archive,[x for x in allitems if x['group']==g['group']]);groups.append(dict(group=g['group'],members=n,member_sha_verified=True));print(json.dumps(dict(remote_group_verified=g['group'],members=n)),flush=True)
    gh(['release','edit',tag,'--repo',REPO,'--draft=false','--latest=false'],60);final=json.loads(gh(['api',f'repos/{REPO}/releases/{rid}'],60));ref=json.loads(gh(['api',f'repos/{REPO}/git/ref/tags/{tag}'],60));assert not final['draft']and ref['object']['sha']==head
    proof=dict(passed=True,published=True,release_url=final['html_url'],release_id=rid,source_commit=head,all_parts_downloaded_SHA_verified=True,every_decompressed_member_SHA_verified=True,groups=groups,verified_members=sum(g['members']for g in groups),raw_bytes=index['raw_bytes'],tag_commit_verified=True,models=0,physical_native=0,completed_unix=time.time());dump(D/'FULL_REMOTE_VERIFIED.json',proof);print(json.dumps(proof),flush=True)


if __name__=='__main__':main()
