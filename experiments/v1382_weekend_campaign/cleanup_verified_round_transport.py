"""Remove only duplicate archive transports after complete remote recovery."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

R=Path(__file__).resolve().parents[2];O=R/'runs/v1383_exact_timed_handoff';REC=R/'runs/v1391_handoff_archive_recovery'
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    return h.hexdigest()
def dump(p,v):
    temporary=p.with_suffix('.tmp');temporary.write_text(json.dumps(v,indent=2)+'\n');temporary.replace(p)
def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert not (O/'TRANSPORT_CLEANUP_CLAIM.json').exists()
    proof=read(O/'FULL_REMOTE_VERIFIED.json');index=read(O/'ARCHIVE_INDEX.json')
    assert proof['passed'] and proof['every_asset_download_SHA_verified'] and proof['every_decompressed_member_SHA_verified'] and proof['recovery_index_download_SHA_verified']
    assert proof['source_members']==len(index['files']) and proof['source_commit']==read(O/'SYNC_RESULT.json')['head']
    assert read(R/'runs/v1392_handoff_remote_delivery/FINALIZED.json')['passed']
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
        assert read(R/'runs/v1382_weekend_campaign/LEDGER.json')['active_round'] is None
        tracked=set(subprocess.run(['git','ls-files','-z'],cwd=R,capture_output=True,check=True).stdout.decode().split('\0'))
        files=[]
        for row in index['parts']:
            assert Path(row['name']).name==row['name']
            for root in [O/'archive',REC/'archive']:
                p=root/row['name'];assert not p.is_symlink() and p.is_file() and str(p.relative_to(R)) not in tracked
                s=p.stat();assert s.st_size==row['bytes'] and sha(p)==row['sha256']
                files.append(dict(path=str(p.relative_to(R)),device=s.st_dev,inode=s.st_ino,mtime_ns=s.st_mtime_ns,bytes=s.st_size,sha256=row['sha256']))
        dump(O/'TRANSPORT_CLEANUP_CLAIM.json',dict(files=files,source_sha256=sha(Path(__file__)),remote_proof_sha256=sha(O/'FULL_REMOTE_VERIFIED.json'),models=0))
        for row in files:
            p=R/row['path'];s=p.stat();assert (s.st_dev,s.st_ino,s.st_mtime_ns,s.st_size)==(row['device'],row['inode'],row['mtime_ns'],row['bytes'])
        for row in files:(R/row['path']).unlink()
        dump(O/'TRANSPORT_CLEANUP.json',dict(passed=True,duplicate_paths_removed=len(files),unique_archive_logical_bytes=index['archive_bytes'],all_removed_bytes_remote_restored_and_SHA_verified=True,physical_raw_deleted=False,physical_raw_main_and_repeat_retained=True,models=0,closed_unix=time.time()))
        print(json.dumps(read(O/'TRANSPORT_CLEANUP.json')))
if __name__=='__main__':main()
