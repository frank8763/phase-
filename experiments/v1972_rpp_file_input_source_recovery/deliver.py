"""One archive upload/readback/cleanup; source Release shared by runtime."""
import fcntl,hashlib,importlib.util,json,os,signal,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];S=R/'runs/v1971_rpp_file_input_component';D0=R/'runs/v1972_rpp_file_input_source_recovery'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');t.replace(p)
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(runtime=False):
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    rid=os.environ.get('PHASE_EVENING_ASSIGNMENT','')
    D=S/'runtime_archives'/rid if runtime else D0
    if '--source-sync'in sys.argv:
        assert runtime and not(D/'SOURCE_SYNC_RESULT.json').exists()
        recovery=read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json');p=R/recovery['source_sync_result_path']
        assert sha(p)==recovery['source_sync_result_sha256'];prior=read(p);assert prior['remote_verified']and prior['head']==recovery['source_commit']
        put(D/'SOURCE_SYNC_RESULT.json',dict(head=prior['head'],remote_verified=True,push_executed=False,ref_executed=False,reused_exact_original_source_sync=True,original_source_proof_path=str(p.relative_to(R)),original_source_proof_sha256=sha(p),models=0));return 0
    O=D/'remote_delivery';assert not O.exists()and not(D/'FULL_REMOTE_VERIFIED.json').exists()
    index=read(D/'ARCHIVE_INDEX.json');sync=read(D/'SOURCE_SYNC_RESULT.json');assert sync['remote_verified']and read(D/'FINALIZED.json')['passed']
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    O.mkdir();start=time.time();mono=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    auth=read(S/'AUTHORIZATION.json')
    end=start+600
    def guard(*_):assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<end and time.monotonic()<mono+(end-start),'IO_OR_NIGHT_DUAL_CLOCK_STOP'
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FINITE_ARCHIVE_IO_STOP')));signal.setitimer(signal.ITIMER_REAL,end-start)
    put(O/'CLAIM.json',dict(pid=os.getpid(),boot_id=boot,started_unix=start,scope='RUNTIME'if runtime else'SOURCE',source_index_sha256=sha(D/'ARCHIVE_INDEX.json'),no_model=True))
    h=load('v1914_exact_transfer',R/'experiments/v1389_idempotent_storage_transfer/resume.py');h.O=O;h.W=O;h.END=end;h.base.ROOT_END=end
    receipts=O/'http_receipts';receipts.mkdir();counter=[0]
    def receipt(value):
        counter[0]+=1;put(receipts/(str(counter[0])+'.json'),value)
    http=load('v1920_repaired_http',R/'experiments/v1940_content_addressed_runtime_recovery/net.py').Client(R,guard,receipt);h.base.gh=http.gh
    pending=load('v1949_pending_digest',R/'experiments/v1940_content_addressed_runtime_recovery/pending_asset.py');original_check=h.check_asset
    h.check_asset=lambda path,row:pending.check_asset(path,row,original_check,lambda:http.request('GET','https://api.github.com/repos/frank8763/phase-/releases/assets/'+str(row['id'])),guard,receipt)
    Reader=load('v1914_exact_reader',R/'experiments/v1382_weekend_campaign/deliver_full9390_preparation.py').RemoteReader
    verify=load('v1914_exact_verifier',R/'experiments/v1400_archive_link_schema/resume.py').verify_stream
    result=dict(closed=False,passed=False,physical_native=0,models=0,new_push=False,new_ref=False)
    try:
        assert h.base.usage()+(32+512)*1024**2<15*1024**3
        for row in index['parts']:
            p=D/'archive'/row['name'];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']
        if runtime:
            assert rid in [f'common_{i:02d}__DWA'for i in range(6,13)]
            prior=read(D0/'remote_delivery/RELEASE.json');release=http.request('GET','https://api.github.com/repos/frank8763/phase-/releases/'+str(prior['id']))
        else:
            tag='phase-v1971-rpp-file-input-source-20261125'
            release=http.request('GET','https://api.github.com/repos/frank8763/phase-/releases/tags/'+tag,missing_ok=True)
            if release is None:
                put(O/'CREATE_ONCE_CLAIM.json',dict(tag=tag,source_commit=sync['head'],never_repeat_uncertain_POST=True))
                payload=dict(tag_name=tag,target_commitish=sync['head'],name='Phase RPP quota-bound readonly file-input current vehicle component',body='Exact24actual-observed ROS constructor dependencies pinned. Original RPP binary/controller/parameters/fixture unchanged. New one synthetic straight control-output component only after source chain; zero DLL/model/constructor/solve in source software check. Prior technical refusal preserved, no formal trial or navigation qualification. Execution lock held for entire CPU2 native child. No training or hardware.',draft=False,prerelease=False,make_latest='false')
                try:release=http.request('POST','https://api.github.com/repos/frank8763/phase-/releases',data=json.dumps(payload).encode())
                except BaseException:
                    release=http.request('GET','https://api.github.com/repos/frank8763/phase-/releases/tags/'+tag,missing_ok=True)
                    assert release is not None,'UNCERTAIN_CREATE_NO_REPEAT'
        assert release['target_commitish']==sync['head']
        http.release_id=release['id'];h.base.TAG=release['tag_name'];put(O/'RELEASE.json',dict(id=release['id'],url=release['html_url']))
        alias=D/((rid if runtime else'v1971_source')+'.ARCHIVE_INDEX.json');assert not alias.exists();alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())
        for row in index['parts']:h.ensure_uploaded(D/'archive'/row['name'],h.assets(read(O/'RELEASE.json')))
        h.ensure_uploaded(alias,h.assets(read(O/'RELEASE.json')));known=h.assets(read(O/'RELEASE.json'))
        folder=O/'readback';folder.mkdir();reader=Reader(index['parts'],known,folder,h.download);count=verify(reader,index)
        assert len(reader.verified)==len(index['parts'])
        recovered=folder/'ARCHIVE_INDEX.json';h.download(recovered,known[alias.name]);assert sha(recovered)==sha(D/'ARCHIVE_INDEX.json')
        proof=dict(passed=True,source_commit=sync['head'],release_url=release['html_url'],release_id=release['id'],assignment_id=rid if runtime else None,every_asset_actual_download_SHA=True,every_member_SHA_and_link_text=True,whole_archive_SHA=True,recovery_index_download_SHA=True,members=count,archive_bytes=index['archive_bytes'],models=0,physical_admission=False,verified_unix=time.time(),remote_index_asset_name=alias.name,new_push=False,new_ref=False)
        put(D/'FULL_REMOTE_VERIFIED.json',proof);entries=[]
        for p,hsh in [(D/'archive'/r['name'],r['sha256'])for r in index['parts']]+[(alias,sha(D/'ARCHIVE_INDEX.json'))]:
            st=p.lstat();assert p.is_file()and not p.is_symlink()and sha(p)==hsh
            entries.append(dict(path=str(p.relative_to(R)),sha256=hsh,bytes=st.st_size,device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns))
        put(D/'TRANSPORT_CLEANUP_MANIFEST.json',dict(verified_remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),entries=entries))
        for row in entries:
            p=R/row['path'];st=p.lstat();assert(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(row['device'],row['inode'],row['bytes'],row['mtime_ns'])and sha(p)==row['sha256'];p.unlink()
        recovered.unlink();folder.rmdir()
        put(D/'TRANSPORT_CLEANUP.json',dict(passed=True,only_remote_verified_duplicate_transport_removed=True,exact_SHA_size_mtime_device_inode_manifest=True,all_originals_retained=True,models=0))
        put(O/'FINALIZED.json',proof);result.update(passed=True,proof=proof)
    except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'ERROR.json',result)
    finally:result.update(closed=True,wall_s=time.monotonic()-mono);put(O/'RESULT.json',result)
    print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
