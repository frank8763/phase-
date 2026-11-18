"""One bounded direct asset upload per file; full SHA readback before publish."""
import concurrent.futures
import subprocess
import time
from package import *

GH=R/'tools/phase_storage_20261107/vendor/gh'; REPO='frank8763/phase-'


def api(arguments,limit=60):
    result=subprocess.run([str(GH),'api',*arguments],cwd=R,capture_output=True,text=True,timeout=limit)
    if result.returncode:raise RuntimeError('GITHUB_API_FAILED_RETURN_'+str(result.returncode))
    return json.loads(result.stdout)


def main():
    assert not (D/'DELIVERY_CLAIM.json').exists(),'ONE_DELIVERY'
    sync=read(D/'GIT_SYNC_RESULT.json');assert sync['push_succeeded'] and sync['remote_head_verified']
    index=read(D/'RECORD_INDEX.json');head=sync['head'];tag=index['release_tag']
    dump(D/'DELIVERY_CLAIM.json',dict(source_commit=head,started_unix=time.time(),one_upload_per_asset=True,models=0))
    payload=O/'CREATE_RELEASE.json'
    dump(payload,dict(tag_name=tag,target_commitish=head,name='V1332/V1333 common-map static development: failures and exact evidence',body='MPPI functional NoValidControl followed by original supervisor interruption; final packet5495actual, no full trace. RPP3460actual+3460own replay, exacterror0 and all physical checks pass, but no goal. Both repeats unexecuted. Frozen source and full saved failure evidence, not successful navigation or algorithm superiority.',draft=True,make_latest='false'))
    release=api(['--method','POST',f'repos/{REPO}/releases','--input',str(payload)])
    rid=release['id'];dump(D/'RELEASE_CREATED.json',dict(release_id=rid,source_commit=head,draft=True,tag=tag))
    items=[dict(item,path=O/'transport'/item['name']) for item in index['parts']]
    for name in ['RECORD_INDEX.json','SOURCE_INVENTORY.json','RESULT_SUMMARY.json']:
        path=D/name;items.append(dict(name=name,path=path,bytes=path.stat().st_size,sha256=sha(path)))
    def upload(item):
        assert sha(item['path'])==item['sha256']
        asset=api(['--method','POST','-H','Content-Type: application/octet-stream','--input',str(item['path']),f'https://uploads.github.com/repos/{REPO}/releases/{rid}/assets?name={item["name"]}'])
        assert asset['name']==item['name'] and asset['size']==item['bytes'] and asset['state']=='uploaded'
        if asset.get('digest'):assert asset['digest']=='sha256:'+item['sha256']
        print(json.dumps(dict(uploaded=item['name'])),flush=True)
        return dict(name=item['name'],asset_id=asset['id'],sha256=item['sha256'],bytes=item['bytes'])
    uploaded=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(upload,item):item['name'] for item in items}
        for future in concurrent.futures.as_completed(futures):
            try:uploaded.append(future.result())
            except Exception as error:errors.append(dict(name=futures[future],error_type=type(error).__name__,reason='UPLOAD_FAILED_NO_RETRY'))
    dump(D/'UPLOAD_RESULT.json',dict(passed=not errors,uploaded=uploaded,errors=errors,models=0))
    assert not errors,'UPLOAD_INCOMPLETE_KEEP_RAW'
    output=O/'readback';output.mkdir();verified=[];errors=[]
    def download(item):
        destination=output/item['name']
        with destination.open('xb') as stream:
            result=subprocess.run([str(GH),'api',f'repos/{REPO}/releases/assets/{item["asset_id"]}','-H','Accept: application/octet-stream'],cwd=R,stdout=stream,stderr=subprocess.PIPE,timeout=60)
        assert result.returncode==0 and destination.stat().st_size==item['bytes'] and sha(destination)==item['sha256']
        print(json.dumps(dict(verified=item['name'])),flush=True)
        return item
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(download,item):item['name'] for item in uploaded}
        for future in concurrent.futures.as_completed(futures):
            try:verified.append(future.result())
            except Exception as error:errors.append(dict(name=futures[future],error_type=type(error).__name__,reason='READBACK_FAILED_NO_RAW_URL'))
    dump(D/'READBACK_RESULT.json',dict(passed=not errors,verified=verified,errors=errors,models=0))
    assert not errors,'READBACK_INCOMPLETE_KEEP_RAW'
    archive=output/index['archive_name']
    with archive.open('xb') as stream:
        for item in index['parts']:stream.write((output/item['name']).read_bytes())
    assert archive.stat().st_size==index['archive_bytes'] and sha(archive)==index['archive_sha256']
    count=verify(archive,read(D/'SOURCE_INVENTORY.json')['files'])
    patch=O/'PUBLISH_RELEASE.json';dump(patch,dict(draft=False,make_latest='false'))
    final=api(['--method','PATCH',f'repos/{REPO}/releases/{rid}','--input',str(patch)])
    ref=api([f'repos/{REPO}/git/ref/tags/{tag}']);assert not final['draft'] and ref['object']['sha']==head
    proof=dict(passed=True,published=True,release_url=final['html_url'],source_commit=head,verified_members=count,all_parts_download_SHA=True,every_decompressed_member_SHA=True,tag_commit_verified=True,raw_bytes=index['raw_bytes'],models=0,physical_native=0,completed_unix=time.time())
    dump(D/'FULL_REMOTE_VERIFIED.json',proof);print(json.dumps(proof),flush=True)


if __name__=='__main__':main()
