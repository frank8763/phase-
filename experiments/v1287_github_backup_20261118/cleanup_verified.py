"""Delete only the preregistered, remotely read-back closed raw caches."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,time
C=Path(__file__).resolve().parent;R=C.parents[1];D=R/'records/v1281_backup_20261118';O=R/'runs'/C.name
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    assert not(D/'CLEANUP_RESULT.json').exists(),'ONE_SELECTED_CLEANUP'
    proof=read(D/'FULL_REMOTE_VERIFIED.json');assert proof['passed']and proof['published']and proof['every_asset_download_SHA_verified']and proof['every_decompressed_member_SHA_verified']and proof['tag_commit_verified']
    plan=read(D/'CLEANUP_PLAN_PENDING.json');inventory={x['path']:x for x in read(D/'SOURCE_INVENTORY.json')['files']}
    assert read(R/'CURRENT_EXPERIMENT.json')['active_run']is None and(R/'REVIEW_PENDING').exists()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    frozen=set(read(R/'experiments/v1281_partial_reconnection_fixed24/SOURCE_FREEZE.json')['files'])
    # Validate the entire deletion list before the first unlink.
    for x in plan['files']:
        n=x['path'];p=R/n;assert n in inventory and n not in frozen and x==inventory[n]
        assert any(n.startswith(prefix)for prefix in plan['raw_roots'])and p.is_file()and not p.is_symlink()and p.resolve().is_relative_to(R)
        assert p.stat().st_size==x['bytes']and sha(p)==x['sha256'],'CHANGED_OR_UNVERIFIED_RAW '+n
    removed=0;size=0
    for x in plan['files']:(R/x['path']).unlink();removed+=1;size+=x['bytes']
    for root in plan['raw_roots']:
        p=R/root
        for sub in sorted((x for x in p.rglob('*')if x.is_dir()and not x.is_symlink()),key=lambda x:len(x.parts),reverse=True):
            try:sub.rmdir()
            except OSError:pass
        try:p.rmdir()
        except OSError:pass
    # Duplicate compressed transport is now recoverable from the verified
    # Release. Its catalog remains in Git and on the Release.
    transport=O/'transport';transport_bytes=sum(p.stat().st_size for p in transport.rglob('*')if p.is_file())
    assert transport.is_dir()and not transport.is_symlink();shutil.rmtree(transport)
    result=dict(closed=True,passed=True,source_raw_files_removed=removed,source_raw_logical_bytes_removed=size,
        duplicate_transport_logical_bytes_removed=transport_bytes,total_logical_bytes_removed=size+transport_bytes,
        runtime_source_and_frozen_dependency_files_deleted=0,all_removed_source_members_preverified_locally_and_remotely=True,
        restore_index='records/v1281_backup_20261118/RECORD_INDEX.json',release_url=proof['release_url'],stage_accessed=False,
        models=0,physical_native=0,completed_unix=time.time())
    (D/'CLEANUP_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
