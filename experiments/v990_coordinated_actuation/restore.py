"""Small, SHA-verified saved inputs only; never initializes a vehicle."""
import fcntl
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

R = Path(__file__).resolve().parents[2]
O = R / 'runs/v990_coordinated_actuation'
GH = R / 'tools/phase_storage_20261107/vendor/gh'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    lock = (R / 'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    O.mkdir(exist_ok=True)
    rows = []; archives = []
    for version in [982, 987]:
        index = json.loads((R / f'records/nav2_v{version}_20261110/RECORD_INDEX.json').read_text())
        assert json.loads((R / f'records/nav2_v{version}_20261110/FINALIZED.json').read_text())['remote_verified']
        group = index['archives'][0]; folder = O / f'saved_v{version}'; folder.mkdir(exist_ok=True)
        def download(name):
            p = folder / name
            if not p.exists():
                result = subprocess.run([str(GH), 'release', 'download', index['release_tag'], '--repo', index['repository'],
                    '--pattern', name, '--dir', str(folder)], capture_output=True, text=True, timeout=30)
                assert result.returncode == 0, result.stderr[-1200:]
            return p
        inventory = download(group['group'] + '.INVENTORY.json')
        catalog = {x['path']: x for x in json.loads(inventory.read_text())['files']}
        prefix = f'runs/v858_nav2_verified/v{version}/component_0/'
        names = ['physics/BODY_COMMANDS.json', 'physics/NATIVE_TRACE.npz', 'physics/SETUP.json']
        if version == 982:
            names += ['physics/MODEL_BUILD_CONTRACT.json']
        else:
            names += ['physics/YAW_FEEDBACK.json.gz']
        wanted = {prefix + n: n for n in names}
        if version == 982:
            for name in ['physics/NATIVE_TRACE.npz', 'physics/BODY_COMMANDS.json']:
                wanted['runs/v982_precise_recovery_gate/prior_v974/' + name] = 'prior/' + name
        assert set(wanted) <= catalog.keys()
        assert len(group['parts']) == 1
        part = group['parts'][0]; archive = download(part['name'])
        assert sha(archive) == part['sha256'] == group['archive_sha256'] and archive.stat().st_size == part['bytes']
        decoder = subprocess.Popen(['zstd', '-q', '-dc', str(archive)], stdout=subprocess.PIPE)
        seen = set()
        with tarfile.open(fileobj=decoder.stdout, mode='r|') as stream:
            for member in stream:
                if member.name not in wanted:
                    continue
                assert member.isfile() and '..' not in Path(member.name).parts
                dest = folder / wanted[member.name]; dest.parent.mkdir(parents=True, exist_ok=True)
                assert not dest.is_symlink()
                if not dest.exists():
                    with stream.extractfile(member) as source, dest.open('xb') as target:
                        shutil.copyfileobj(source, target)
                item = catalog[member.name]
                assert sha(dest) == item['sha256'] and dest.stat().st_size == item['bytes']
                rows.append(dict(path=str(dest.relative_to(R)), original=member.name, sha256=item['sha256'], bytes=item['bytes']))
                seen.add(member.name)
        assert decoder.wait() == 0 and seen == set(wanted)
        archive.unlink()
        archives.append(dict(version=version, original_index=f'records/nav2_v{version}_20261110/RECORD_INDEX.json',
            archive_sha256=group['archive_sha256']))
    receipt = dict(passed=True, files=rows, archives=archives, models=0, integrations=0)
    (O / 'RESTORE_RECEIPT.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(restored_files=len(rows), bytes=sum(x['bytes'] for x in rows), models=0)))


if __name__ == '__main__':
    main()
