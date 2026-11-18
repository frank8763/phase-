"""Restore selected component data only after full archive/member verification."""
import argparse
import io
import subprocess
from package import *


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--task', choices=['main', 'repeat', 'v1293-entry'])
    args = parser.parse_args()
    inventory = read(D / 'SOURCE_INVENTORY.json')['files']; index = read(D / 'RECORD_INDEX.json')
    if args.list:
        print(json.dumps(dict(tasks=['main', 'repeat', 'v1293-entry'], release=index['release_url'], archive=index['asset']), indent=2)); return
    assert args.task, 'SELECT_TASK_OR_LIST'
    prefix = 'runs/v1293_rpp_component90/main/' if args.task == 'v1293-entry' else 'runs/v858_nav2_verified/v1294/' + args.task + '/'
    selected = [x for x in inventory if x['path'].startswith(prefix) and x.get('kind') != 'symlink']
    for item in selected:
        p = R / item['path']
        assert not p.exists() and not p.is_symlink(), 'EXISTING_OUTPUT_NOT_OVERWRITTEN'
        assert p.is_relative_to(R) and not any(parent.is_symlink() for parent in p.parents), 'SYMLINK_PARENT'
    folder = O / ('restore_' + args.task)
    folder.mkdir(parents=True, exist_ok=False); archive = folder / index['asset']['name']
    gh = R / 'tools/phase_storage_20261107/vendor/gh'
    with archive.open('xb') as stream:
        p = subprocess.run([str(gh), 'release', 'download', index['release_tag'], '--repo', 'frank8763/phase-', '--pattern', archive.name, '--output', '-'], cwd=R, stdout=stream, stderr=subprocess.PIPE, timeout=90)
    assert p.returncode == 0 and sha(archive) == index['asset']['sha256'], 'DOWNLOADED_ARCHIVE_SHA'
    verify(archive, inventory)
    selected_names = {x['path'] for x in selected}
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            if member.name not in selected_names:
                continue
            destination = R / member.name; destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as stream:
                source = tar.extractfile(member)
                for chunk in iter(lambda: source.read(1048576), b''):
                    stream.write(chunk)
    for item in selected:
        assert sha(R / item['path']) == item['sha256']
    archive.unlink()
    # Historical absolute asset links are verified in the archive, not recreated
    # on the host. MJB replay uses the saved compiled model; source reconstruction
    # uses the declared repository runtime assets inside run_phase isolation.
    dump(folder / 'RESTORED.json', dict(passed=True, restored_files=len(selected), task=args.task,
                                      historical_asset_links_not_recreated=True, models=0, physical_native=0))
    print(json.dumps(dict(passed=True, restored_files=len(selected), models=0, physical_native=0)))


if __name__ == '__main__':
    main()
