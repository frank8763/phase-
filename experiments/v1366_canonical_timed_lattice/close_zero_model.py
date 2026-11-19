"""One zero-model selected archive, complete member SHA and transport readback."""
import fcntl
import hashlib
import json
from pathlib import Path
import tarfile
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for piece in iter(lambda:stream.read(1048576),b''):h.update(piece)
    return h.hexdigest()


def dump(path,x):path.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')


def main():
    assert not (O/'FINALIZED.json').exists(),'ALREADY_CLOSED'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());assert state['status']=='REVIEW_PENDING' and state.get('active_run') is None
    completion=json.loads((O/'COMPLETION.json').read_text());assert completion['closed'] and completion['models']==completion['actual_native']==0
    files=json.loads((C/'SOURCE_FREEZE.json').read_text())['files'];assert all(sha(R/p)==h for p,h in files.items())
    archive_dir=O/'archive';archive_dir.mkdir(exist_ok=False);items=[]
    for folder in [C,O]:
        for p in sorted(folder.rglob('*')):
            if archive_dir in p.parents or p==archive_dir:continue
            assert not p.is_symlink()
            if p.is_file():items.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
    report=R/'docs/CANONICAL_SHARED_CONTROLLERS_V1366_REPORT.md';items.append(dict(path=str(report.relative_to(R)),bytes=report.stat().st_size,sha256=sha(report)))
    assert len({x['path'] for x in items})==len(items)
    archive=archive_dir/'evidence.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=3) as stream:
        for item in items:stream.add(R/item['path'],arcname=item['path'],recursive=False)
    wanted={x['path']:x for x in items};seen=set()
    with tarfile.open(archive,'r:gz') as stream:
        for member in stream:
            assert member.isfile() and member.name in wanted and member.name not in seen
            seen.add(member.name);h=hashlib.sha256();content=stream.extractfile(member)
            for piece in iter(lambda:content.read(1048576),b''):h.update(piece)
            assert h.hexdigest()==wanted[member.name]['sha256']
    assert seen==set(wanted)
    parts=[]
    with archive.open('rb') as stream:
        for index in range(1000):
            piece=stream.read(32*1024**2)
            if not piece:break
            p=archive_dir/('evidence.tar.gz.part%03d'%index);p.write_bytes(piece)
            parts.append(dict(name=p.name,bytes=len(piece),sha256=sha(p)))
    rebuilt=hashlib.sha256()
    for part in parts:
        p=archive_dir/part['name'];assert sha(p)==part['sha256']
        with p.open('rb') as stream:
            for piece in iter(lambda:stream.read(1048576),b''):rebuilt.update(piece)
    assert rebuilt.hexdigest()==sha(archive)
    dump(O/'ARCHIVE_INDEX.json',dict(files=items,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,parts=parts,
        all_members_and_reassembled_parts_SHA_verified=True,remote_download_restore_verified=False,raw_deleted=False,models=0))
    total=sum(p.stat().st_size for root in [C,O] for p in root.rglob('*') if p.is_file())
    assert total<64*1024**2,'PREPARATION_STORAGE_CAP_EXCEEDED'
    dump(O/'FINALIZED.json',dict(passed=True,scientific_full_dynamic_route_passed=False,
        scope='zero-model local source/software-evidence closure, not physical acceptance',
        source_unchanged=True,local_memberSHA_and_reassembly_verified=True,raw_deleted=False,
        remote_download_restore_verified=False,total_bytes=total,models=0,physical_native=0,finished_unix=time.time()))
    print(json.dumps(dict(finalized=True,members=len(items),parts=len(parts),archive_bytes=archive.stat().st_size,total_bytes=total,models=0)))


if __name__=='__main__':main()
