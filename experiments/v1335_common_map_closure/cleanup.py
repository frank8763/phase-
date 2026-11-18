"""Only remote-verified closed raw and duplicate transport/cache deletion."""
import subprocess
import time
from package import *


def main():
    assert not (D/'CLEANUP_RESULT.json').exists(),'ONE_CLEANUP'
    proof=read(D/'FULL_REMOTE_VERIFIED.json'); assert proof['passed'] and proof['published'] and proof['every_decompressed_member_SHA']
    assert read(R/'CURRENT_EXPERIMENT.json')['status']=='REVIEW_PENDING'
    assert (R/'REVIEW_PENDING').read_bytes()==(R/'runs/v1333_rpp_exit_handoff/REVIEW_PENDING.before').read_bytes()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    inv=read(D/'SOURCE_INVENTORY.json'); frozen=set(read(R/'experiments/v1333_rpp_exit_handoff/SOURCE_FREEZE.json')['files'])
    tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0')); selected=[]
    for item in inv['files']+inv['excluded_caches']:
        path=R/item['path']; assert item['path'] not in tracked and item['path'] not in frozen
        assert (path.is_relative_to(R/'runs/v858_nav2_verified/v1332/mppi_main') or path.is_relative_to(R/'runs/v858_nav2_verified/v1333/rpp_main')) and not any(p.is_symlink() for p in path.parents)
        if item.get('kind')=='symlink': assert path.is_symlink() and str(path.readlink())==item['target']
        else: assert path.is_file() and not path.is_symlink() and sha(path)==item['sha256']
        selected.append(dict(item,reason='remote verified raw' if 'reason' not in item else item['reason']))
    for folder in [O/'transport',O/'readback']:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                assert not path.is_symlink() and not any(p.is_symlink() for p in path.parents)
                selected.append(dict(path=str(path.relative_to(R)),bytes=path.stat().st_size,sha256=sha(path),reason='duplicate remotely verified transport'))
    dump(D/'CLEANUP_MANIFEST.json',dict(files=selected,models=0))
    for item in selected: (R/item['path']).unlink()
    result=dict(passed=True,files_removed=len(selected),logical_bytes_removed=sum(x['bytes'] for x in selected),frozen_dependencies_deleted=0,unique_evidence_lost=False,restore_index=str((D/'RECORD_INDEX.json').relative_to(R)),models=0,completed_unix=time.time())
    dump(D/'CLEANUP_RESULT.json',result); print(json.dumps(result))


if __name__=='__main__': main()
