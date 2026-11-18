"""Zero-model closed right-turn evidence, <=1MiB transport assets."""
import fcntl
import hashlib
import json
from pathlib import Path
import tarfile
import time

R=Path(__file__).resolve().parents[2]; C=Path(__file__).resolve().parent
O=R/'runs/v1335_common_map_closure'; D=R/'records/v1332_common_map_20261118'


def read(p): return json.loads(Path(p).read_text())
def dump(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify(archive,items):
    wanted={x['path']:x for x in items}; seen=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            assert member.name in wanted and member.name not in seen
            item=wanted[member.name]
            if item.get('kind')=='symlink': assert member.issym() and member.linkname==item['target']
            else:
                assert member.isfile() and member.size==item['bytes']
                h=hashlib.sha256(); source=tar.extractfile(member)
                for chunk in iter(lambda:source.read(1048576),b''): h.update(chunk)
                assert h.hexdigest()==item['sha256']
            seen.add(member.name)
    assert seen==set(wanted); return len(seen)


def main():
    assert not (D/'RECORD_INDEX.json').exists(),'ONE_PACKAGE'
    assert read(R/'runs/v1333_rpp_exit_handoff/COMPLETION.json')['closed'] and not read(R/'runs/v1333_rpp_exit_handoff/COMPLETION.json')['passed']
    assert read(D/'RESULT_SUMMARY.json')['rpp_full_safe_stop_replay_passed']
    assert (R/'REVIEW_PENDING').read_bytes()==(R/'runs/v1333_rpp_exit_handoff/REVIEW_PENDING.before').read_bytes()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    O.mkdir(exist_ok=True); D.mkdir(exist_ok=True); items=[]; caches=[]
    roots=[R/'runs/v858_nav2_verified/v1332/mppi_main',R/'runs/v858_nav2_verified/v1333/rpp_main']
    for root in roots:
        assert root.is_dir(),'MISSING_SOURCE_ROOT'
        assert (root/'FINAL_PACKET.json').stat().st_size>0
        if root.parent.name=='v1333': assert read(root/'RESULT.json')['replay']['passed'] and (root/'physics/NATIVE_TRACE.npz').stat().st_size>0
        for path in sorted(root.rglob('*')):
            relative=str(path.relative_to(R))
            if path.is_symlink():
                target=str(path.readlink()); assert path.name=='meshes_fixed' and target=='/home/linghu/catkin_ws/src/mk-mini/training/assets/mkmini_real/meshes_fixed'
                items.append(dict(path=relative,kind='symlink',target=target,bytes=len(target.encode()),sha256=hashlib.sha256(target.encode()).hexdigest())); continue
            if not path.is_file(): continue
            item=dict(path=relative,bytes=path.stat().st_size,sha256=sha(path))
            if 'cache' in path.parts: caches.append(dict(item,reason='reconstructible Mesa cache')); continue
            items.append(item)
    assert len(items)>=30 and sum(x['bytes'] for x in items)>1024**2,'EMPTY_OR_INCOMPLETE_EVIDENCE'
    transport=O/'transport'; transport.mkdir(); archive=transport/'common-map-static-witness.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=6,dereference=False) as tar:
        for item in items: tar.add(R/item['path'],arcname=item['path'],recursive=False)
    count=verify(archive,items); parts=[]
    with archive.open('rb') as stream:
        while True:
            data=stream.read(1024**2)
            if not data: break
            path=transport/(archive.name+f'.part{len(parts):03}'); path.write_bytes(data)
            parts.append(dict(name=path.name,bytes=len(data),sha256=sha(path)))
    tag='phase-common-map-static-v1332-v1333-20261118'
    dump(D/'SOURCE_INVENTORY.json',dict(files=items,excluded_caches=caches))
    index=dict(release_tag=tag,release_url=f'https://github.com/frank8763/phase-/releases/tag/{tag}',archive_name=archive.name,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,parts=parts,raw_bytes=sum(x['bytes'] for x in items),source_files=count,max_part_bytes=1024**2,models=0)
    dump(D/'RECORD_INDEX.json',index); print(json.dumps(index))


if __name__=='__main__': main()
