"""One source sync; source/runtime archives and combined exact remote barriers."""
import base64,datetime,gzip,hashlib,io,json,os,subprocess,tarfile,time,fcntl
from context import R,C,S,PARENT,read,sha,files
from budget import check
GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-';TAG='phase-v2185-fixed-raw-original-response-20261128'
CAP=4*1024**2

def put(p,v):
    raw=json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(raw)<=32*1024
    with p.open('xb')as f:f.write(raw)
def events():return [json.loads(v)for v in(S/'OPERATIONS.jsonl').read_bytes().splitlines()]if(S/'OPERATIONS.jsonl').exists()else[]
def journal(value):
    p=S/'OPERATIONS.jsonl';raw=json.dumps(dict(unix=time.time(),**value),sort_keys=True,separators=(',',':')).encode()+b'\n'
    assert (p.stat().st_size if p.exists()else 0)+len(raw)<=16*1024
    with p.open('ab')as f:f.write(raw);f.flush();os.fsync(f.fileno())
def once(op):
    assert not any(e.get('op')==op and e['event']=='claim'for e in events()),'ALREADY_ATTEMPTED_NO_RETRY:'+op
    journal(dict(event='claim',op=op))
def command(args,timeout=30,op=None):
    assert time.time()<datetime.datetime(2026,11,29,9,tzinfo=datetime.timezone(datetime.timedelta(hours=8))).timestamp()
    if str(args[0])==str(GH):assert sha(GH)==read(S/'SOURCE_READY.json')['installed_IO_GH_SHA256']
    if op:once(op)
    try:
        p=subprocess.run(args,cwd=R,env=dict(os.environ,GODEBUG='http2client=0'),capture_output=True,timeout=timeout)
        assert len(p.stdout)<=CAP and len(p.stderr)<=16*1024
        if op:journal(dict(event='return',op=op,returncode=p.returncode,stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr).hexdigest()))
        return p
    except BaseException as e:
        if op:journal(dict(event='unknown_or_failure',op=op,error=repr(e)))
        raise
def gh(args,timeout=30,op=None):
    p=command([str(GH),*args],timeout,op);assert p.returncode==0,p.stderr.decode(errors='replace')[-400:];return p.stdout

def source_sync():
    assert read(S/'SOURCE_QUALIFICATION.json')['passed']and not(S/'SOURCE_SYNC.json').exists()
    assert not any(e.get('op')in {'source_push','source_ref'}for e in events())
    source=files();assert all(sha(R/n)==h for n,h in source.items())
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();assert head!=read(PARENT/'SOURCE_SYNC_RESULT.json')['head']
    needed=read(S/'SOURCE_QUALIFICATION.json')['git_source_files']
    for n in needed:assert subprocess.check_output(['git','show',head+':'+n],cwd=R)==(R/n).read_bytes()
    value=dict(head=head,push_attempted=True,push_returned=False,ref_verified=False,actual_remote_Git_members_SHA256={})
    try:
        p=command(['git','push','origin','HEAD:main'],30,'source_push');value.update(push_returned=True,push_returncode=p.returncode)
    except BaseException as e:value['push_error']=repr(e)
    try:
        p=command([str(GH),'api','repos/'+REPO+'/git/ref/heads/main'],5,'source_ref');value['ref_verified']=p.returncode==0 and json.loads(p.stdout)['object']['sha']==head
        if value['ref_verified']:
            for n in needed:
                oid=subprocess.check_output(['git','rev-parse',head+':'+n],cwd=R,text=True).strip()
                response=json.loads(gh(['api','repos/'+REPO+'/git/blobs/'+oid]));assert response['sha']==oid and response['encoding']=='base64'
                raw=base64.b64decode(response['content']);assert raw==(R/n).read_bytes()and hashlib.sha256(raw).hexdigest()==source[n]
                value['actual_remote_Git_members_SHA256'][n]=source[n]
    except BaseException as e:value['readback_error']=repr(e)
    value['passed']=value['ref_verified']and set(value['actual_remote_Git_members_SHA256'])==set(needed)
    put(S/'SOURCE_SYNC.json',value);assert value['passed'],'SOURCE_REF_OR_GIT_BYTES_NOT_VERIFIED_NO_MODEL';return value

def inventory(paths):
    rows=[]
    for p in sorted(set(paths)):
        assert p.is_file()and not p.is_symlink()and p.resolve().is_relative_to(R)
        rows.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
    return rows

def packed(rows):
    out=io.BytesIO()
    with gzip.GzipFile(fileobj=out,mode='wb',compresslevel=9,mtime=0)as z,tarfile.open(fileobj=z,mode='w|')as t:
        for row in rows:
            p=R/row['path'];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'];m=tarfile.TarInfo(row['path']);m.size=row['bytes'];m.mode=0o600;m.mtime=0
            with p.open('rb')as f:t.addfile(m,f)
    return out.getvalue()

def verify(raw,index):
    assert len(raw)==index['archive_bytes']and hashlib.sha256(raw).hexdigest()==index['archive_sha256'];wanted={r['path']:r for r in index['files']};seen=set()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz')as t:
        for m in t:
            assert m.isfile()and m.name in wanted and m.name not in seen;row=wanted[m.name];assert m.size==row['bytes']and hashlib.sha256(t.extractfile(m).read()).hexdigest()==row['sha256'];seen.add(m.name)
    assert seen==set(wanted)

def source_paths():
    sync=read(S/'SOURCE_SYNC.json');assert sync['passed'];git=set(sync['actual_remote_Git_members_SHA256'])
    paths=[R/n for n in read(S/'SOURCE_FREEZE.json')['files']if n not in git]
    paths += [S/n for n in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_READY.json','SOURCE_ONCE.json','SOURCE_SYNC.json','STORAGE_PRECHARGE.json','PRE_SOURCE_SCOPE_AMENDMENT.json','REQUIRED_ARRAY_FORMAT_PREFLIGHT.json','ARRAY_FORMAT_PREFLIGHT.json']]
    return paths

def archive(kind):
    assert kind in {'source','runtime'};check('source'if kind=='source'else'runtime')
    source=files();assert all(sha(R/n)==h for n,h in source.items())
    if kind=='source':paths=source_paths()
    else:
        assert read(S/'COMPLETION.json')['closed']
        paths=[p for p in(S/'RUNTIME').rglob('*')if p.is_file()]+[S/n for n in ['COMPLETION.json','RUNTIME_ONCE.json','ROUND_WINDOW.json','OWNED_CHILD.json','NUMERICAL_ADMISSION.json','SOURCE_REMOTE_CLOSURE.json','SOURCE_FREEZE.json','SOURCE_SYNC.json']]
    rows=inventory(paths);raw=packed(rows);assert len(raw)<=CAP
    once(kind+'_archive');folder=S/(kind.upper()+'_TRANSPORT');folder.mkdir()
    name='sha256-'+hashlib.sha256(raw).hexdigest()+'-v2185-'+kind+'.tar.gz.part000';p=folder/name
    with p.open('xb')as f:f.write(raw)
    value=dict(kind=kind,files=rows,archive_bytes=len(raw),archive_sha256=hashlib.sha256(raw).hexdigest(),part=dict(name=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),source_commit=read(S/'SOURCE_SYNC.json')['head'],scientific_navigation_passed=None)
    verify(p.read_bytes(),value);put(S/(kind.upper()+'_INDEX.json'),value);check('source'if kind=='source'else'closed');return value

def release():
    p=command([str(GH),'api','repos/'+REPO+'/releases/tags/'+TAG])
    if p.returncode==0:x=json.loads(p.stdout)
    else:
        assert b'404'in p.stderr or b'404'in p.stdout
        x=json.loads(gh(['api','--method','POST','repos/'+REPO+'/releases','-f','tag_name='+TAG,'-f','target_commitish='+read(S/'SOURCE_SYNC.json')['head'],'-f','name=Phase fixed raw-command original response mathematics','-f','body=Fixed original10shadow and5admission response predictions. No physical plant, formal navigation or mechanism gain is inferred.','-F','draft=false','-F','prerelease=false','-f','make_latest=false'],op='release_create'))
    assert x['target_commitish']==read(S/'SOURCE_SYNC.json')['head']and x['tag_name']==TAG
    return dict(id=x['id'],url=x['html_url'],source_commit=x['target_commitish'],tag=TAG)

def deliver(kind):
    assert kind in {'source','runtime'};runtime=kind=='runtime';check('closed'if runtime else'source')
    locks=[]
    for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
        f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    if runtime:
        from owner import same
        assert read(S/'COMPLETION.json')['closed']and not same(read(S/'OWNED_CHILD.json'))
    index_path=S/(kind.upper()+'_INDEX.json');index=read(index_path);folder=S/(kind.upper()+'_TRANSPORT');r=read(S/'RELEASE.json')if runtime else release()
    if not runtime:put(S/'RELEASE.json',r)
    assert r['source_commit']==read(S/'SOURCE_SYNC.json')['head']
    for path in [folder/index['part']['name'],index_path]:
        assets=json.loads(gh(['api','repos/'+REPO+'/releases/'+str(r['id'])+'/assets?per_page=100']));assert not any(a['name']==path.name for a in assets),'EXISTING_ASSET_NO_SECOND_UPLOAD'
        gh(['release','upload',TAG,str(path),'--repo',REPO],60,'upload_'+kind+'_'+path.name)
    assets=json.loads(gh(['api','repos/'+REPO+'/releases/'+str(r['id'])+'/assets?per_page=100']));lookup={a['name']:a for a in assets}
    for path in [folder/index['part']['name'],index_path]:assert lookup[path.name]['size']==path.stat().st_size
    raw=gh(['api','-H','Accept: application/octet-stream','repos/'+REPO+'/releases/assets/'+str(lookup[index['part']['name']]['id'])],60);verify(raw,index)
    downloaded=folder/'actual_remote_readback.tar.gz'
    with downloaded.open('xb')as f:f.write(raw)
    ri=gh(['api','-H','Accept: application/octet-stream','repos/'+REPO+'/releases/assets/'+str(lookup[index_path.name]['id'])],60);assert hashlib.sha256(ri).hexdigest()==sha(index_path)
    entries=[]
    for p in [folder/index['part']['name'],downloaded]:
        st=p.lstat();assert not p.is_symlink();entries.append(dict(path=str(p.relative_to(R)),bytes=st.st_size,sha256=sha(p),mtime_ns=st.st_mtime_ns,device=st.st_dev,inode=st.st_ino))
    journal(dict(event='actual_remote_all_SHA_and_eligible_cleanup_manifest',kind=kind,index_sha256=sha(index_path),entries=entries))
    for row in entries:
        p=R/row['path'];st=p.lstat();assert not p.is_symlink()and(st.st_size,st.st_mtime_ns,st.st_dev,st.st_ino)==(row['bytes'],row['mtime_ns'],row['device'],row['inode'])and sha(p)==row['sha256'];p.unlink()
    value=dict(passed=True,kind=kind,actual_remote_every_block_member_whole_index_SHA=True,index_path=str(index_path.relative_to(R)),index_sha256=sha(index_path),archive_sha256=index['archive_sha256'],archive_bytes=len(raw),members=len(index['files']),source_commit=r['source_commit'],source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'),release=r,exact_transport_cleanup_completed=True,removed_transport_paths=[v['path']for v in entries],exact_cleanup_manifest=entries,raw_currentinputs_anchors_retained=True,scientific_navigation_passed=None)
    if not runtime:
        sync=read(S/'SOURCE_SYNC.json');new=read(S/'SOURCE_FREEZE.json')['files'];archived={v['path']for v in index['files']};git=sync['actual_remote_Git_members_SHA256'];assert set(new)<=archived|set(git)
        assert all(new[n]==h for n,h in git.items())and read(PARENT/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
        value.update(all_frozen_members_actual_remote_covered=True,inherited_freeze_sha256=sha(PARENT/'SOURCE_FREEZE.json'),inherited_recovery_sha256=sha(PARENT/'CURRENT_SOURCE_REMOTE_RECOVERY.json'),actual_remote_Git_members_SHA256=git)
    else:value.update(scientific_math_result_sha256=sha(S/'RUNTIME/RESULT.json')if(S/'RUNTIME/RESULT.json').exists()else None,canonical_post_runtime_barrier=True,original_physical_or_formal_executed=0)
    put(S/('RUNTIME_REMOTE_CLOSURE.json'if runtime else'SOURCE_REMOTE_CLOSURE.json'),value);check('closed');return value
