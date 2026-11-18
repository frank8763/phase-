"""Zero-model selected closed evidence pack with full member SHA readback."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tarfile
import time

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name
D = R / 'records/v1296_backup_20261118'
TAG = 'phase-rpp-turn-v1296-20261118'
ROOTS = ['runs/v858_nav2_verified/v1296']


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def read(p):
    return json.loads(p.read_text())


def dump(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')


def verify(archive, inventory):
    wanted = {x['path']: x for x in inventory}
    seen = set()
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            assert member.name in wanted and member.name not in seen, 'UNEXPECTED_MEMBER'
            if wanted[member.name].get('kind') == 'symlink':
                assert member.issym() and member.linkname == wanted[member.name]['link_target'], 'SYMLINK_TARGET'
                assert hashlib.sha256(member.linkname.encode()).hexdigest() == wanted[member.name]['sha256']
                seen.add(member.name)
                continue
            assert member.isfile() and member.size == wanted[member.name]['bytes'], 'MEMBER_TYPE_OR_SIZE'
            stream = tar.extractfile(member); h = hashlib.sha256()
            for b in iter(lambda: stream.read(1048576), b''):
                h.update(b)
            assert h.hexdigest() == wanted[member.name]['sha256'], 'MEMBER_SHA'
            seen.add(member.name)
    assert seen == set(wanted), 'MISSING_MEMBER'
    return len(seen)


def main():
    O.mkdir(exist_ok=True)
    assert not (D / 'RECORD_INDEX.json').exists(), 'ARCHIVE_ALREADY_FINALIZED'
    D.mkdir(exist_ok=True)
    os.sched_setaffinity(0, {2, 3, 4, 5}); os.nice(19)
    assert read(R / 'runs/v1296_rpp_turn_brake/COMPLETION.json')['closed'] is True
    assert read(R / 'CURRENT_EXPERIMENT.json')['active_run'] is None and (R / 'REVIEW_PENDING').exists()
    lock = (R / 'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    inventory, excluded = [], []
    for root in ROOTS:
        for p in sorted((R / root).rglob('*')):
            if p.is_symlink():
                target = str(p.readlink())
                assert p.name == 'meshes_fixed' and target == '/home/linghu/catkin_ws/src/mk-mini/training/assets/mkmini_real/meshes_fixed', 'UNREVIEWED_SYMLINK_TARGET'
                inventory.append(dict(path=str(p.relative_to(R)), kind='symlink', link_target=target,
                                      canonical_repository_target='runtime/mk-mini/training/assets/mkmini_real/meshes_fixed',
                                      bytes=len(target.encode()), sha256=hashlib.sha256(target.encode()).hexdigest()))
                continue
            if not p.is_file():
                continue
            if 'cache' in p.relative_to(R / root).parts:
                excluded.append(dict(path=str(p.relative_to(R)), bytes=p.stat().st_size, sha256=sha(p), reason='reconstructible Mesa shader cache'))
                continue
            inventory.append(dict(path=str(p.relative_to(R)), bytes=p.stat().st_size, sha256=sha(p)))
    archive = O / 'v1296-left-turn-failure-evidence.tar.gz'
    with tarfile.open(archive, 'w:gz', compresslevel=6, dereference=False) as tar:
        for item in inventory:
            p = R / item['path']
            assert (hashlib.sha256(str(p.readlink()).encode()).hexdigest() if p.is_symlink() else sha(p)) == item['sha256']
            tar.add(p, arcname=item['path'], recursive=False)
    count = verify(archive, inventory)
    assert archive.stat().st_size <= 32 * 1024**2, 'USE_CHUNKS_IF_LARGER'
    dump(D / 'SOURCE_INVENTORY.json', dict(files=inventory, excluded_caches=excluded))
    index = dict(release_tag=TAG, release_url=f'https://github.com/frank8763/phase-/releases/tag/{TAG}',
                 asset=dict(name=archive.name, bytes=archive.stat().st_size, sha256=sha(archive)),
                 files=count, raw_bytes=sum(x['bytes'] for x in inventory), selected_roots=ROOTS,
                 local_full_member_SHA_readback=True, models=0, physical_native=0)
    dump(D / 'RECORD_INDEX.json', index)
    print(json.dumps(index))


if __name__ == '__main__':
    main()
