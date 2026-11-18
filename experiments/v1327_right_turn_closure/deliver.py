"""Upload once, download all <=1MiB parts, archive/member SHA before publish."""
import concurrent.futures
import subprocess
import time
from package import *
GH=R/'tools/phase_storage_20261107/vendor/gh'; REPO='frank8763/phase-'


def gh(args,seconds=60):
    p=subprocess.run([str(GH),*args],cwd=R,capture_output=True,text=True,timeout=seconds)
    assert p.returncode==0,'GH_FAILED '+str(args[:2])+': '+p.stderr[-300:]
    return p.stdout


def main():
    assert not (D/'DELIVERY_CLAIM.json').exists(),'ONE_NEW_DELIVERY'
    sync=read(D/'GIT_SYNC_RESULT.json'); assert sync['push_succeeded'] and sync['remote_head_verified']
    index=read(D/'RECORD_INDEX.json'); head=sync['head']; tag=index['release_tag']
    assert index['source_files']>=72 and index['raw_bytes']>1024**2,'EMPTY_EVIDENCE_NOT_DELIVERABLE'
    dump(D/'DELIVERY_CLAIM.json',dict(started_unix=time.time(),source_commit=head,tag=tag,models=0))
    release_body=O/'CREATE_RELEASE.json'
    dump(release_body,dict(tag_name=tag,target_commitish=head,name='V1326 coherent MPPI right-turn component main and exact repeat passed',body='Static right component only: both1875 actual+1875 own replay; independent audits passed. Goal0.072459m, headingerror0.000275rad, rear-radialerror0.009895m, minimumactualclearance0.327206m, badcontacts0; completepair states/ctrl error0. Registered EW-origin right component. Original WE/NS nominal geometry rejections preserved. V1325 missing ROS entry and killed-worker unknown counts retained. Not whole-route/dynamic qualification or canonicalMPPI superiority. Full source-member evidence, <=1MiBchunks and SHA index.',draft=True,make_latest='false'))
    release=json.loads(gh(['api','--method','POST',f'repos/{REPO}/releases','--input',str(release_body)])); rid=release['id']
    dump(D/'RELEASE_CREATED.json',dict(release_id=rid,source_commit=head,draft=True,tag=tag))
    items=[dict(p,path=O/'transport'/p['name']) for p in index['parts']]
    for name in ['RECORD_INDEX.json','SOURCE_INVENTORY.json','RESULT_SUMMARY.json']:
        path=D/name; items.append(dict(name=name,path=path,bytes=path.stat().st_size,sha256=sha(path)))
    def upload(item):
        assert sha(item['path'])==item['sha256']
        gh(['release','upload',tag,str(item['path']),'--repo',REPO])
        print(json.dumps(dict(uploaded=item['name'])),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for _ in pool.map(upload,items): pass
    assets={a['name']:a for a in json.loads(gh(['api',f'repos/{REPO}/releases/{rid}/assets?per_page=100']))}
    assert len(assets)==len(items)
    output=O/'readback'; output.mkdir()
    results=[]; errors=[]
    def download(item):
        a=assets[item['name']]; assert a['size']==item['bytes'] and a['state']=='uploaded'
        if a.get('digest'): assert a['digest']=='sha256:'+item['sha256']
        dest=output/item['name']
        with dest.open('xb') as stream:
            p=subprocess.run([str(GH),'release','download',tag,'--repo',REPO,'--pattern',item['name'],'--output','-'],cwd=R,stdout=stream,stderr=subprocess.PIPE,timeout=60)
        assert p.returncode==0 and dest.stat().st_size==item['bytes'] and sha(dest)==item['sha256'],'REMOTE_PART_SHA'
        print(json.dumps(dict(verified=item['name'])),flush=True)
        return dict(name=item['name'],sha256=item['sha256'],bytes=item['bytes'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(download,item):item['name'] for item in items}
        for future in concurrent.futures.as_completed(futures):
            try: results.append(future.result())
            except Exception as error: errors.append(dict(name=futures[future],error_type=type(error).__name__,reason=str(error) if isinstance(error,AssertionError) else 'TRANSPORT_ERROR_NO_RAW_URL'))
    dump(D/'READBACK_RESULT.json',dict(passed=not errors,verified=results,errors=errors,models=0))
    assert not errors,'REMOTE_READBACK_INCOMPLETE_KEEP_RAW'
    archive=output/index['archive_name']
    with archive.open('xb') as stream:
        for part in index['parts']: stream.write((output/part['name']).read_bytes())
    assert archive.stat().st_size==index['archive_bytes'] and sha(archive)==index['archive_sha256']
    count=verify(archive,read(D/'SOURCE_INVENTORY.json')['files'])
    gh(['release','edit',tag,'--repo',REPO,'--draft=false','--latest=false'])
    final=json.loads(gh(['api',f'repos/{REPO}/releases/{rid}'])); ref=json.loads(gh(['api',f'repos/{REPO}/git/ref/tags/{tag}']))
    assert not final['draft'] and ref['object']['sha']==head
    proof=dict(passed=True,published=True,release_url=final['html_url'],source_commit=head,verified_members=count,all_parts_download_SHA=True,every_decompressed_member_SHA=True,tag_commit_verified=True,raw_bytes=index['raw_bytes'],models=0,physical_native=0,completed_unix=time.time())
    dump(D/'FULL_REMOTE_VERIFIED.json',proof); print(json.dumps(proof),flush=True)


if __name__=='__main__': main()
