"""Delete explicitly unselected intermediates; selected essential originals remain."""
import fcntl,gzip,json,shutil,time
from pathlib import Path
from plan import R,OUT,dump
from cleanup import sha

def main():
    assert R==Path('/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-')
    lock=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert(R/'REVIEW_PENDING').exists()
    for pid in [496878,497260]:assert not Path(f'/proc/{pid}/cmdline').exists()
    source=json.loads((OUT/'SOURCE_SNAPSHOT.json').read_text());assert json.loads((OUT/'SOURCE_REMOTE_VERIFIED.json').read_text())['commit']==source['commit'];assert all(sha(R/p)==h for p,h in source['sha256'].items())
    plan=json.loads((OUT/'PLAN.json').read_text());protected=set(plan['core_git_files']);essential={p for g in plan['groups'].values()for p in g['files']};protected_all=protected|essential;assert all((R/p).exists()for p in essential)
    before=shutil.disk_usage(R).free;count=0;logical=0;missing=0;start=time.time();original_start=OUT/'TRASH_CLEANUP_STARTED.json'
    if original_start.exists():before=json.loads(original_start.read_text())['free_bytes_before']
    else:dump(original_start,dict(free_bytes_before=before,started_unix=start,necessary_local_originals_kept_until_remote_verified=True))
    with gzip.open(OUT/'DELETE_PLAN.jsonl.gz','rt')as stream:
        for raw in stream:
            row=json.loads(raw)
            if row['role']!='UNSELECTED_INTERMEDIATE_OR_DUPLICATE':continue
            rel=Path(row['path']);assert not rel.is_absolute()and '..'not in rel.parts and rel.parts[0]in ['runs','evidence'];assert row['path']not in protected_all;p=R/rel;assert not p.is_relative_to(OUT)
            try:s=p.lstat()
            except FileNotFoundError:missing+=1;continue
            assert(s.st_ino,s.st_dev,s.st_size,s.st_mtime_ns)==(row['inode'],row['device'],row['bytes'],row['mtime_ns']),('TRASH_INPUT_CHANGED',row['path'])
            p.unlink();count+=1;logical+=s.st_size
            if count%100000==0:dump(OUT/'TRASH_CLEANUP_PROGRESS.json',dict(files=count,logical_bytes=logical,elapsed_s=time.time()-start,free_bytes=shutil.disk_usage(R).free));print(json.dumps(dict(event='TRASH_REMOVED',files=count)),flush=True)
    assert all((R/p).exists()for p in protected|essential)
    result=dict(passed=True,deleted_files=count,already_missing=missing,logical_bytes=logical,actual_filesystem_bytes_freed=shutil.disk_usage(R).free-before,elapsed_s=time.time()-start,all_selected_essential_originals_still_present=True,only_user_authorized_unselected_intermediates_deleted=True,stage_accessed=False,models=0)
    dump(OUT/'TRASH_CLEANUP_RESULT.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
