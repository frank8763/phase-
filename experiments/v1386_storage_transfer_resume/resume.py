"""Bounded I/O continuation of the preserved storage plan, with no models."""
import concurrent.futures
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tarfile
import threading
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
W=R/'runs/v1382_weekend_campaign/storage';END=1795395600;TARGET=8*1024**3;LIMIT=10*1024**3
spec=importlib.util.spec_from_file_location('preserved_storage_primitives',R/'experiments/v1382_weekend_campaign/storage_preserve.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
read=base.read;dump=base.dump;sha=base.sha
progress_lock=threading.Lock()

def assets(release):
    result={}
    for page in range(1,21):
        rows=json.loads(base.gh(['api',f'repos/{base.REPO}/releases/{release["id"]}/assets?per_page=100&page={page}']))
        for row in rows:
            assert row['name'] not in result,'DUPLICATE_REMOTE_ASSET';result[row['name']]=row
        if len(rows)<100:return result
    raise AssertionError('BOUNDED_ASSET_LIST_LIMIT')

def ensure_uploaded(path,known):
    row=known.get(path.name)
    if row is not None:
        assert row['size']==path.stat().st_size and row.get('digest')=='sha256:'+sha(path),'REMOTE_ASSET_CONFLICT'
        return
    base.gh(['release','upload',base.TAG,str(path),'--repo',base.REPO],timeout=300)

def download(path,row):
    assert time.time()<END and not path.is_symlink()
    if path.exists() and path.stat().st_size==row['size']:
        assert 'sha256:'+sha(path)==row['digest'],'EXISTING_DOWNLOAD_SHA_MISMATCH';return
    assert not path.exists() or path.stat().st_size<row['size'],'OVERSIZED_PARTIAL_DOWNLOAD'
    before=path.stat().st_size if path.exists() else 0
    # curl refuses a server that cannot honor the existing byte range. There is
    # one attempt per asset in this continuation; no retry loop or overwrite.
    command=['curl','--fail','--location','--silent','--show-error','--connect-timeout','30','--max-time','900','--continue-at','-','--output',str(path),'--write-out','%{http_code}',row['browser_download_url']]
    p=subprocess.run(command,capture_output=True,text=True,timeout=910)
    assert p.returncode==0 and p.stdout.strip() in ('200','206'),'BOUNDED_DOWNLOAD_FAILED_'+str(p.returncode)
    assert path.stat().st_size==row['size'] and 'sha256:'+sha(path)==row['digest'],'DOWNLOADED_SIZE_OR_SHA_MISMATCH'
    with progress_lock:dump(O/'TRANSFER.json',dict(last_asset=row['name'],resumed_bytes=before,verified_bytes=row['size'],http_status=p.stdout.strip(),verified_unix=time.time(),models=0))

def preserve(group,release):
    folder=W/group['id'];folder.mkdir(exist_ok=True);index_path=folder/(group['id']+'.INDEX.json')
    if index_path.exists():
        index=read(index_path);assert index['files']==group['files'],'EXISTING_INDEX_PLAN_MISMATCH'
    else:
        assert not any(folder.glob('*.tar.gz.part*')),'INCOMPLETE_PACKAGE_REQUIRES_DIAGNOSIS'
        dump(folder/'SOURCE_INVENTORY.json',group);writer=base.Parts(folder,group['id'])
        import gzip
        with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=1,mtime=0) as compressor,tarfile.open(fileobj=compressor,mode='w|') as archive:
            for row in group['files']:
                p=R/row['path'];assert not p.is_symlink() and p.is_file() and p.stat().st_size==row['bytes']
                info=tarfile.TarInfo(row['path']);info.size=row['bytes'];info.mode=0o600
                with p.open('rb') as stream:archive.addfile(info,stream)
        writer.finish();index=dict(id=group['id'],parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),files=group['files'],release_url=release['url'],models=0);dump(index_path,index)
    known=assets(release)
    for row in index['parts']:
        p=folder/row['name'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'];ensure_uploaded(p,known)
    ensure_uploaded(index_path,known);known=assets(release)
    destination=folder/'download';destination.mkdir(exist_ok=True)
    paths=[destination/row['name'] for row in index['parts']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(download,path,known[path.name]) for path in paths]
        for future in concurrent.futures.as_completed(futures):future.result()
    digest=hashlib.sha256()
    for p in paths:
        with p.open('rb') as stream:
            for b in iter(lambda:stream.read(1024**2),b''):digest.update(b)
    assert digest.hexdigest()==index['archive_sha256']
    wanted={row['path']:row for row in group['files']};seen=set()
    with tarfile.open(fileobj=base.Reader(paths),mode='r|gz') as archive:
        for member in archive:
            assert member.isfile() and member.name in wanted and member.name not in seen
            row=wanted[member.name];assert member.size==row['bytes'];h=hashlib.sha256();stream=archive.extractfile(member)
            for b in iter(lambda:stream.read(1024**2),b''):h.update(b)
            assert h.hexdigest()==row['sha256'];seen.add(member.name)
    assert seen==set(wanted)
    recovered=destination/index_path.name;download(recovered,known[index_path.name]);assert sha(recovered)==sha(index_path)
    proof=dict(passed=True,every_asset_actual_download_SHA_verified=True,every_decompressed_member_SHA_verified=True,recovery_index_download_SHA_verified=True,release_url=release['url'],group=group['id'],source_files=len(seen),source_bytes=sum(x['bytes'] for x in group['files']),archive_bytes=index['archive_bytes'],verified_unix=time.time(),continuation=str(C.relative_to(R)),models=0)
    assert not (folder/'FULL_REMOTE_VERIFIED.json').exists();dump(folder/'FULL_REMOTE_VERIFIED.json',proof)
    named=folder/(group['id']+'.REMOTE_VERIFIED.json');dump(named,proof);ensure_uploaded(named,assets(release))
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert (R/'REVIEW_PENDING').exists() and read(R/'CURRENT_EXPERIMENT.json')['active_run'] is None
        for freeze in [O/'SOURCE_FREEZE.json',R/'experiments/v1383_exact_timed_handoff/SOURCE_FREEZE.json']:
            assert all(sha(R/name)==h for name,h in read(freeze)['files'].items()),'SOURCE_CHANGED'
        tracked=set(subprocess.run(['git','ls-files','-z'],cwd=R,capture_output=True,check=True).stdout.decode().split('\0'))
        for row in group['files']:
            p=R/row['path'];assert row['path'] not in tracked and not p.is_symlink() and p.resolve().is_relative_to(R/'runs/v858_nav2_verified')
            s=p.stat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(row['device'],row['inode'],row['bytes'],row['mtime_ns']) and sha(p)==row['sha256']
        for row in group['files']:(R/row['path']).unlink()
    for p in [*paths,recovered]:p.unlink()
    destination.rmdir()
    for row in index['parts']:(folder/row['name']).unlink()
    dump(folder/'CLEANUP_RESULT.json',dict(passed=True,files=len(seen),raw_logical_bytes=proof['source_bytes'],raw_only_deleted_after_full_remote_readback=True,remaining_runs_allocated_bytes=base.usage(),models=0))
    return proof

def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert read(W/'ERROR.json')['unverified_originals_retained'] is True
    assert not (O/'CLAIM.json').exists();dump(O/'CLAIM.json',dict(pid=os.getpid(),started_unix=time.time(),maximum_download_attempts_per_asset=1,download_limit_s=900,parallel_downloads=3,models=0))
    try:
        plan=read(W/'PLAN.json');release=read(W/'RELEASE.json');verified=[]
        for group in plan['groups']:
            if base.usage()<=TARGET:break
            folder=W/group['id']
            if (folder/'CLEANUP_RESULT.json').exists():verified.append(read(folder/'FULL_REMOTE_VERIFIED.json'));continue
            verified.append(preserve(group,release));dump(O/'PROGRESS.json',dict(completed_groups=len(verified),last_group=group['id'],remaining_runs_allocated_bytes=base.usage(),models=0))
        remaining=base.usage();assert remaining<LIMIT-512*1024**2
        final=dict(passed=True,remaining_runs_allocated_bytes=remaining,limit_bytes=LIMIT,verified_groups=verified,source_protected=True,continuation=str(C.relative_to(R)),original_error_retained=True,models=0)
        assert not (W/'FINALIZED.json').exists();dump(W/'FINALIZED.json',final);dump(O/'FINALIZED.json',final)
        p=R/'runs/v1382_weekend_campaign/LEDGER.json';ledger=read(p);ledger.update(status='STORAGE_READY_FOR_FIRST_ROUND',models_now_authorized=False,storage_ready=True,storage_allocated_bytes=remaining,storage_proof=str((W/'FINALIZED.json').relative_to(R)));dump(p,ledger)
    except BaseException as exc:
        import traceback
        dump(O/'ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),unverified_originals_retained=True,models=0));raise

if __name__=='__main__':main()
