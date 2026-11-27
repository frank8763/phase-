"""One source push; immutable once archives and actual remote member readback."""
import base64,datetime,gzip,hashlib,io,json,os,subprocess,tarfile,time
from pathlib import Path
from context import R,C,S,read,sha,put,source_files
from budget import check
GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-'
TAG='phase-v2184-fair-raw-controller-math-20261128'
def journal(event):
    p=S/'OPERATIONS.jsonl';raw=json.dumps(dict(unix=time.time(),**event),sort_keys=True,separators=(',',':')).encode()+b'\n'
    assert p.stat().st_size+len(raw)<=16*1024 if p.exists()else len(raw)<=16*1024
    with p.open('ab')as f:f.write(raw);f.flush();os.fsync(f.fileno())
def events():return [json.loads(x)for x in(S/'OPERATIONS.jsonl').read_bytes().splitlines()]if(S/'OPERATIONS.jsonl').exists()else[]
def once(op):
    assert not any(e.get('op')==op and e['event']=='claim'for e in events()),'OPERATION_ALREADY_CLAIMED_NO_AUTOMATIC_RETRY:'+op
    journal(dict(event='claim',op=op))
def command(args,*,timeout=30,mutation=None):
    assert time.time()<datetime.datetime(2026,11,29,9,tzinfo=datetime.timezone(datetime.timedelta(hours=8))).timestamp(),'WEEKEND_IO_CLOSED_AFTER09'
    if args and str(args[0])==str(GH):
        pin=read(S/'SOURCE_READY_PREFLIGHT.json')['IO_tool'];assert sha(GH)==pin['sha256']and GH.stat().st_size==pin['bytes'],'INSTALLED_IO_TOOL_CHANGED'
    if mutation:once(mutation)
    try:
        p=subprocess.run(args,cwd=R,env=dict(os.environ,GODEBUG='http2client=0'),capture_output=True,timeout=timeout)
        assert len(p.stdout)<=2*1024**2 and len(p.stderr)<=16*1024,'TRANSFER_RESPONSE_CAP'
        if mutation:journal(dict(event='return',op=mutation,returncode=p.returncode,stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr).hexdigest()))
        return p
    except BaseException as e:
        if mutation:journal(dict(event='unknown_or_failed',op=mutation,error=repr(e)))
        raise
def gh(args,*,timeout=30,mutation=None):
    p=command([str(GH),*args],timeout=timeout,mutation=mutation)
    assert p.returncode==0,'GITHUB_OPERATION_FAILED:'+p.stderr.decode(errors='replace')[-400:]
    return p.stdout
def source_sync():
    assert read(S/'SOURCE_QUALIFICATION.json')['passed']and not(S/'SOURCE_SYNC_RESULT.json').exists()
    assert not any(e.get('op')in {'unique_source_push','unique_source_ref'}for e in events()),'SOURCE_SYNC_ALREADY_ATTEMPTED_NO_SECOND_PUSH_OR_REF'
    files=source_files();assert all(sha(R/n)==h for n,h in files.items())
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
    assert head!=read(R/'runs/v2180_fresh_projection_component/CURRENT_SOURCE_REMOTE_RECOVERY.json')['source_commit']
    for n in read(S/'SOURCE_QUALIFICATION.json')['git_source_files']:
        assert subprocess.check_output(['git','show',head+':'+n],cwd=R)==(R/n).read_bytes(),'COMMITTED_NEW_SOURCE_BYTES_MISMATCH'
    result=dict(head=head,remote_verified=False,push_attempted=False,push_returned=False,source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'))
    try:
        result['push_attempted']=True
        p=command(['git','push','origin','HEAD:main'],timeout=30,mutation='unique_source_push')
        result.update(push_returned=True,push_returncode=p.returncode)
    except BaseException as e:result['push_first_error']=repr(e)
    try:
        p=command([str(GH),'api','repos/'+REPO+'/git/ref/heads/main'],timeout=5,mutation='unique_source_ref')
        result.update(ref_returncode=p.returncode,ref_stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),remote_verified=p.returncode==0 and json.loads(p.stdout)['object']['sha']==head)
    except BaseException as e:result['ref_first_error']=repr(e)
    if result['remote_verified']:
        result['actual_remote_Git_members_SHA256']={}
        try:
            for n in read(S/'SOURCE_QUALIFICATION.json')['git_source_files']:
                object_id=subprocess.check_output(['git','rev-parse',head+':'+n],cwd=R,text=True).strip()
                response=json.loads(gh(['api','repos/'+REPO+'/git/blobs/'+object_id]))
                assert response['sha']==object_id and response['encoding']=='base64'
                remote=base64.b64decode(response['content']);assert hashlib.sha256(remote).hexdigest()==files[n]and remote==(R/n).read_bytes(),'ACTUAL_REMOTE_GIT_MEMBER_BYTES_CHANGED'
                result['actual_remote_Git_members_SHA256'][n]=files[n]
        except BaseException as e:result['member_readback_first_error']=repr(e)
        result['all_Git_members_actual_remote_SHA']=set(result['actual_remote_Git_members_SHA256'])==set(read(S/'SOURCE_QUALIFICATION.json')['git_source_files'])
    put(S/'SOURCE_SYNC_RESULT.json',result);assert result['remote_verified']and result.get('all_Git_members_actual_remote_SHA')is True,'UNVERIFIED_SOURCE_REF_OR_MEMBER_NO_NUMERICS'
    return result
def inventory(paths):
    rows=[]
    for p in sorted(set(paths)):
        assert p.is_file()and not p.is_symlink()and p.resolve().is_relative_to(R)
        rows.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
    return rows
def packed(rows):
    out=io.BytesIO()
    with gzip.GzipFile(fileobj=out,mode='wb',compresslevel=9,mtime=0)as z,tarfile.open(fileobj=z,mode='w|')as tar:
        for row in rows:
            p=R/row['path'];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']
            info=tarfile.TarInfo(row['path']);info.size=row['bytes'];info.mode=0o600;info.mtime=0
            with p.open('rb')as f:tar.addfile(info,f)
    return out.getvalue()
def verify_members(raw,index):
    assert len(raw)==index['archive_bytes']and hashlib.sha256(raw).hexdigest()==index['archive_sha256']
    wanted={r['path']:r for r in index['files']};seen=set()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz')as tar:
        for m in tar:
            assert m.isfile()and m.name in wanted and m.name not in seen
            r=wanted[m.name];assert m.size==r['bytes']
            assert hashlib.sha256(tar.extractfile(m).read()).hexdigest()==r['sha256'];seen.add(m.name)
    assert seen==set(wanted)
def archive(kind):
    assert kind in {'source','runtime'};runtime=kind=='runtime';check('runtime'if runtime else'source')
    assert all(sha(R/n)==h for n,h in source_files().items())
    paths=[]
    if runtime:
        assert read(S/'COMPLETION.json')['closed']
        paths=list((S/'RUNTIME').rglob('*'))
        paths=[p for p in paths if p.is_file()]
        paths += [S/n for n in ['COMPLETION.json','RUNTIME_ONCE.json','ROUND_WINDOW.json','OWNED_CHILD.json','NUMERICAL_ADMISSION.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','POST_SOURCE_STORAGE_BARRIER.json']]
    else:
        assert read(S/'SOURCE_QUALIFICATION.json')['passed']and read(S/'SOURCE_SYNC_RESULT.json')['remote_verified']
        sync=read(S/'SOURCE_SYNC_RESULT.json');git_members=sync['actual_remote_Git_members_SHA256']
        assert sync['all_Git_members_actual_remote_SHA']and all(source_files()[n]==h for n,h in git_members.items())
        paths=[R/n for n in read(S/'SOURCE_FREEZE.json')['files']if n not in git_members]
        paths += [S/n for n in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_INHERITED_CHAINS.json','SOURCE_SYNC_RESULT.json','SOURCE_READY_PREFLIGHT.json','STORAGE_PRECHARGE.json','INNER_STAGE_ALLOCATION_AMENDMENT.json','SOURCE_ONCE.json','SOURCE_OUTER_CLOSED.json','READINESS_ARCHIVE_CAPACITY_FAILURE.json','SOURCE_READY_PREFLIGHT_01_SUPERSEDED_BY_REVIEW.json']]
    rows=inventory(paths);raw=packed(rows);limit=(64 if runtime else 96)*1024
    assert len(raw)<=limit,'EXACT_ARCHIVE_SIZE_EXCEEDS_PREDECLARED_CAP_BEFORE_CLAIM'
    once(kind+'_archive');folder=S/('RUNTIME_TRANSPORT'if runtime else'SOURCE_TRANSPORT');folder.mkdir(exist_ok=False)
    name='sha256-'+hashlib.sha256(raw).hexdigest()+'-v2184-'+kind+'.tar.gz.part000'
    p=folder/name
    with p.open('xb')as f:f.write(raw)
    index=dict(schema=1,kind=kind,files=rows,parts=[dict(name=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())],archive_bytes=len(raw),archive_sha256=hashlib.sha256(raw).hexdigest(),source_commit=read(S/'SOURCE_SYNC_RESULT.json')['head'],scientific_navigation_passed=None,new_controller_or_model_calls=0)
    verify_members(p.read_bytes(),index);put(S/('v2184-'+kind+'.INDEX.json'),index);check('closed'if runtime else'source')
    return index
def ensure_release():
    q=command([str(GH),'api','repos/'+REPO+'/releases/tags/'+TAG])
    if q.returncode==0:release=json.loads(q.stdout)
    else:
        assert b'404'in q.stderr or b'404'in q.stdout,'UNKNOWN_RELEASE_LOOKUP_FAILURE_NO_POST'
        head=read(S/'SOURCE_SYNC_RESULT.json')['head']
        release=json.loads(gh(['api','--method','POST','repos/'+REPO+'/releases','-f','tag_name='+TAG,'-f','target_commitish='+head,'-f','name=Phase fixed raw controller mathematical interfaces','-f','body=New DWA/RPP raw-output interface mathematics on an exposed saved causal input. No physical plant, navigation, mechanism benefit or formal comparison result is inferred from transport.','-F','draft=false','-F','prerelease=false','-f','make_latest=false'],mutation='create_release_once'))
    assert release['tag_name']==TAG and release['target_commitish']==read(S/'SOURCE_SYNC_RESULT.json')['head'],'RELEASE_SOURCE_CONFLICT'
    return dict(id=release['id'],url=release['html_url'],tag=TAG,source_commit=release['target_commitish'])
def deliver(kind):
    runtime=kind=='runtime';assert kind in {'source','runtime'}
    check('closed'if runtime else'source');index_path=S/('v2184-'+kind+'.INDEX.json');index=read(index_path)
    folder=S/('RUNTIME_TRANSPORT'if runtime else'SOURCE_TRANSPORT');release=read(S/'RELEASE.json')if runtime else ensure_release()
    if not runtime:put(S/'RELEASE.json',release)
    # Runtime reuses the original source commit; no second push/ref operation.
    assert release['source_commit']==read(S/'SOURCE_SYNC_RESULT.json')['head']
    for path in [folder/index['parts'][0]['name'],index_path]:
        assets=json.loads(gh(['api','repos/'+REPO+'/releases/'+str(release['id'])+'/assets?per_page=100']))
        same=[a for a in assets if a['name']==path.name]
        if not same:gh(['release','upload',TAG,str(path),'--repo',REPO],timeout=60,mutation='upload_'+kind+'_'+path.name)
        else:assert len(same)==1 and same[0]['size']==path.stat().st_size,'EXISTING_ASSET_CONFLICT'
    assets=json.loads(gh(['api','repos/'+REPO+'/releases/'+str(release['id'])+'/assets?per_page=100']))
    selected={a['name']:a for a in assets};part=index['parts'][0]
    assert selected[part['name']]['size']==part['bytes']and selected[index_path.name]['size']==index_path.stat().st_size
    raw=gh(['api','-H','Accept: application/octet-stream','repos/'+REPO+'/releases/assets/'+str(selected[part['name']]['id'])],timeout=60)
    assert len(raw)<=(64 if runtime else 96)*1024
    downloaded=folder/'actual_remote_readback.tar.gz'
    with downloaded.open('xb')as f:f.write(raw)
    verify_members(downloaded.read_bytes(),index)
    remote_index=gh(['api','-H','Accept: application/octet-stream','repos/'+REPO+'/releases/assets/'+str(selected[index_path.name]['id'])],timeout=60)
    assert hashlib.sha256(remote_index).hexdigest()==sha(index_path),'ACTUAL_REMOTE_INDEX_SHA_MISMATCH'
    proof=dict(passed=True,kind=kind,release=release,index_path=str(index_path.relative_to(R)),index_sha256=sha(index_path),every_block_member_whole_index_actual_remote_SHA=True,members=len(index['files']),archive_bytes=len(raw),source_commit=release['source_commit'],no_new_numerical_calls=True,scientific_navigation_passed=None,verified_unix=time.time())
    put(S/(kind.upper()+'_FULL_REMOTE_VERIFIED.json'),proof)
    entries=[]
    for p in [folder/part['name'],downloaded]:
        st=p.stat();entries.append(dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=st.st_size,mtime_ns=st.st_mtime_ns,device=st.st_dev,inode=st.st_ino))
    put(S/(kind.upper()+'_CLEANUP_MANIFEST.json'),dict(remote_proof_sha256=sha(S/(kind.upper()+'_FULL_REMOTE_VERIFIED.json')),entries=entries))
    for e in entries:
        p=R/e['path'];st=p.stat();assert(st.st_size,st.st_mtime_ns,st.st_dev,st.st_ino)==(e['bytes'],e['mtime_ns'],e['device'],e['inode'])and sha(p)==e['sha256'];p.unlink()
    put(S/(kind.upper()+'_TRANSPORT_CLEANUP.json'),dict(passed=True,exact_SHA_size_mtime_device_inode=True,removed=[e['path']for e in entries],all_raw_currentinputs_anchors_retained=True))
    if not runtime:
        files=source_files();parent=read(S/'SOURCE_INHERITED_CHAINS.json')['inherited'][0]
        assert read(R/parent['recovery_path'])['all_frozen_members_remote_chain_covered']
        git_members=read(S/'SOURCE_SYNC_RESULT.json')['actual_remote_Git_members_SHA256']
        assert set(read(S/'SOURCE_FREEZE.json')['files'])==set(git_members)|{r['path']for r in index['files']if r['path']in read(S/'SOURCE_FREEZE.json')['files']}
        assert all(files[n]==h for n,h in git_members.items())
        put(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json',dict(passed=True,all_frozen_members_remote_chain_covered=True,source_members=len(files),source_commit=release['source_commit'],source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'),remote_proof_sha256=sha(S/'SOURCE_FULL_REMOTE_VERIFIED.json'),actual_remote_Git_members_SHA256=git_members,Git_readback_proof_sha256=sha(S/'SOURCE_SYNC_RESULT.json'),inherited=parent))
        put(S/'POST_SOURCE_STORAGE_BARRIER.json',dict(passed=True,actual_remote_all_SHA=True,exact_transport_cleanup_completed=True,removed_transport_paths=[e['path']for e in entries],recovery_sha256=sha(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json'),numerics_authorized=False))
    else:put(S/'POST_RUNTIME_STORAGE_BARRIER.json',dict(passed=True,actual_remote_all_SHA=True,exact_transport_cleanup_completed=True,source_commit=release['source_commit'],scientific_result_path=str((S/'RUNTIME/RESULT.json').relative_to(R)),scientific_result_sha256=sha(S/'RUNTIME/RESULT.json')if(S/'RUNTIME/RESULT.json').exists()else None,physical_navigation_passed=False))
    check('closed')
