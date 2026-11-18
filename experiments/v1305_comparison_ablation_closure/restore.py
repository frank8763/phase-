"""Restore one verified evidence group; never follow archived asset links."""
import argparse
import subprocess
from package import *


def safe_path(base, name):
    relative = Path(name)
    assert not relative.is_absolute() and '..' not in relative.parts
    assert relative.parts[0] == 'runs'
    path = base / relative
    assert path.is_relative_to(R) and not path.is_symlink()
    assert not any(parent.is_symlink() for parent in path.parents)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--group')
    parser.add_argument('--destination', help='Optional NEW directory inside repository runs/')
    args = parser.parse_args()
    index = read(D / 'RECORD_INDEX.json')
    if args.list:
        print(json.dumps(dict(groups=[g['group'] for g in index['archives']], release=index['release_url']))); return
    group = next(g for g in index['archives'] if g['group'] == args.group)
    base = R
    if args.destination:
        base = Path(args.destination).absolute()
        assert base.is_relative_to(R / 'runs') and base != R / 'runs'
        assert not base.exists() and not base.is_symlink()
        assert not any(parent.is_symlink() for parent in base.parents)
    items = [x for x in read(D / 'SOURCE_INVENTORY.json')['files'] if x['group'] == group['group']]
    for item in items:
        path = safe_path(base, item['path'])
        if item.get('kind') != 'symlink' and path.exists():
            assert path.is_file() and sha(path) == item['sha256'], 'EXISTING_DIFFERENT_FILE'
    folder = O / ('restore_' + group['group'])
    folder.mkdir(exist_ok=False)
    for part in group['parts']:
        dest = folder / part['name']
        with dest.open('xb') as stream:
            result = subprocess.run([str(R / 'tools/phase_storage_20261107/vendor/gh'), 'release', 'download', index['release_tag'], '--repo', 'frank8763/phase-', '--pattern', part['name'], '--output', '-'], cwd=R, stdout=stream, stderr=subprocess.PIPE, timeout=120)
        assert result.returncode == 0 and dest.stat().st_size == part['bytes'] and sha(dest) == part['sha256'], 'PART_SHA'
    archive = folder / (group['group'] + '.tar.gz')
    with archive.open('xb') as stream:
        for part in group['parts']:
            with (folder / part['name']).open('rb') as source:
                for chunk in iter(lambda: source.read(1048576), b''): stream.write(chunk)
    assert archive.stat().st_size == group['archive_bytes'] and sha(archive) == group['archive_sha256']
    verify(archive, items)
    count = 0
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            if member.issym(): continue
            dest = safe_path(base, member.name)
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                with dest.open('xb') as stream:
                    source = tar.extractfile(member)
                    for chunk in iter(lambda: source.read(1048576), b''): stream.write(chunk)
            count += 1
    for item in items:
        if item.get('kind') != 'symlink': assert sha(safe_path(base, item['path'])) == item['sha256']
    for part in group['parts']: (folder / part['name']).unlink()
    archive.unlink()
    proof = dict(passed=True, group=group['group'], restored_regular_files=count, destination=str(base), all_part_archive_member_SHA_verified=True, historical_links_not_recreated=True, models=0)
    dump(folder / 'RESTORED.json', proof); print(json.dumps(proof))


if __name__ == '__main__': main()
