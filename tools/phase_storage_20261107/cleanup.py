"""Delete only planned Phase outputs after selected evidence has remote SHA/readback proof."""
import fcntl,gzip,hashlib,json,os,shutil,time
from pathlib import Path
from plan import R,OUT,dump

def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def main():
    assert R==Path('/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-')
    proof=json.loads((OUT/'FULL_REMOTE_VERIFIED.json').read_text());assert proof['passed']and proof['every_asset_streamed_download_sha_verified']
    source=json.loads((OUT/'SOURCE_SNAPSHOT.json').read_text());assert source['commit']==proof['source_commit'];assert all(sha(R/p)==h for p,h in source['sha256'].items()),'NEEDED_LOCAL_SOURCE_CHANGED'
    assert(R/'REVIEW_PENDING').is_file();lock=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for pid in [496878,497260]:assert not Path(f'/proc/{pid}/cmdline').exists(),'KNOWN_PHASE_RUN_STILL_EXISTS'
    plan=json.loads((OUT/'PLAN.json').read_text());protected=set(plan['core_git_files']);before=shutil.disk_usage(R);count=0;logical=0;missing=0;started=time.time()
    dump(OUT/'CLEANUP_STARTED.json',dict(started_unix=started,free_bytes_before=before.free,remote_source=proof['source_commit'],release=proof['release_url']))
    with gzip.open(OUT/'DELETE_PLAN.jsonl.gz','rt')as stream:
        for line in stream:
            row=json.loads(line);relative=Path(row['path']);assert not relative.is_absolute()and '..'not in relative.parts and relative.parts[0]in ['runs','evidence'];assert row['path']not in protected
            p=R/relative;assert not p.is_relative_to(OUT)
            try:s=p.lstat()
            except FileNotFoundError:missing+=1;continue
            assert(s.st_ino,s.st_dev,s.st_size,s.st_mtime_ns)==(row['inode'],row['device'],row['bytes'],row['mtime_ns']),('DELETE_INPUT_CHANGED',row['path'])
            p.unlink();count+=1;logical+=s.st_size
            if count%10000==0:dump(OUT/'CLEANUP_PROGRESS.json',dict(deleted_files=count,logical_bytes=logical,elapsed_s=time.time()-started,free_bytes=shutil.disk_usage(R).free))
            if count%200000==0:print(json.dumps(dict(event='DELETING',files=count,logical_GiB=logical/1024**3)),flush=True)
    for base in [R/'runs',R/'evidence']:
        for folder,dirs,files in os.walk(base,topdown=False,followlinks=False):
            directory=Path(folder)
            if directory==base or directory.is_relative_to(OUT):continue
            try:directory.rmdir()
            except OSError:pass
    assert all((R/p).exists()for p in protected),'REQUIRED_LOCAL_FILE_REMOVED'
    for p in(OUT/'assets').glob('*'):p.unlink()
    for p in(R/'tools/phase_storage_20261107/vendor').glob('*.tar.gz'):p.unlink()
    after=shutil.disk_usage(R);result=dict(passed=True,deleted_files=count,already_missing=missing,deleted_logical_bytes=logical,free_bytes_before=before.free,free_bytes_after=after.free,actual_filesystem_bytes_freed=after.free-before.free,elapsed_s=time.time()-started,source_and_models_preserved=True,essential_records_remote_verified=True,stage_accessed=False,models=0,integrations=0)
    dump(OUT/'CLEANUP_RESULT.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
