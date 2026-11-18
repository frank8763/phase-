"""Delete only closed, remote member-SHA-verified temporary evidence/cache."""
import subprocess
import time
from package import *


def main():
    assert not (D / 'CLEANUP_RESULT.json').exists(), 'ONE_CLEANUP'
    proof = read(D / 'FULL_REMOTE_VERIFIED.json')
    assert proof['passed'] and proof['published'] and proof['every_decompressed_member_SHA_verified']
    assert read(R / 'CURRENT_EXPERIMENT.json')['status'] == 'REVIEW_PENDING' and (R / 'REVIEW_PENDING').exists()
    assert read(O / 'FINAL_CLOSURE_CHECK.json')['closed']
    lock = (R / 'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    inv = read(D / 'SOURCE_INVENTORY.json')
    frozen = set()
    for pattern in ['experiments/v1299*/SOURCE_FREEZE.json', 'experiments/v130[0-4]*/SOURCE_FREEZE.json']:
        for path in R.glob(pattern):
            files = read(path).get('files', [])
            if isinstance(files, dict): frozen.update(files)
            else:
                for x in files:
                    if isinstance(x, str): frozen.add(x)
                    elif isinstance(x, dict): frozen.add(x.get('path', ''))
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=R).decode().split('\0'))
    candidates = []
    for item in inv['files'] + inv['excluded_caches']:
        # Small restoration provenance remains in Git beside the results.
        if item['path'].endswith('/RESTORED.json'): continue
        path = R / item['path']
        assert item['path'] not in frozen and str(path) not in frozen and item['path'] not in tracked, 'DEPENDENCY_OR_TRACKED'
        assert path.is_relative_to(R / 'runs') and not any(p.is_symlink() for p in path.parents)
        if item.get('kind') == 'symlink':
            assert path.is_symlink() and str(path.readlink()) == item['target']
        else:
            assert path.is_file() and not path.is_symlink() and sha(path) == item['sha256'], 'CHANGED_RAW'
        candidates.append(dict(item, reason='remote verified raw' if 'group' in item else 'reconstructible Mesa cache'))
    selected = {Path(x['path']).name + ':' + x['sha256'] for x in inv['files'] if x['group'] == 'compact_ablation_inputs'}
    indexed = {x['path'] for x in candidates}
    for path in (R / 'runs/v1299_paired_mechanism_study').glob('input_slot*/EW_ONWARD_*'):
        relative = str(path.relative_to(R))
        if relative in indexed: continue
        assert path.is_file() and not path.is_symlink() and not any(p.is_symlink() for p in path.parents)
        assert relative not in frozen and str(path) not in frozen and relative not in tracked
        digest = sha(path)
        assert path.name + ':' + digest in selected, 'PARTIAL_COPY_DIFFERS'
        candidates.append(dict(path=relative, bytes=path.stat().st_size, sha256=digest, reason='duplicate exact remotely verified input'))
    # Duplicate local transport/readback contains no unique scientific record.
    for folder in [O / 'transport', O / 'readback']:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                assert not path.is_symlink() and not any(p.is_symlink() for p in path.parents)
                candidates.append(dict(path=str(path.relative_to(R)), bytes=path.stat().st_size, sha256=sha(path), reason='duplicate verified transport'))
    dump(D / 'CLEANUP_MANIFEST.json', dict(files=candidates, release_url=proof['release_url'], models=0))
    for item in candidates: (R / item['path']).unlink()
    result = dict(passed=True, files_removed=len(candidates), logical_bytes_removed=sum(x['bytes'] for x in candidates), unique_evidence_lost=False, frozen_dependencies_deleted=0, release_url=proof['release_url'], models=0, completed_unix=time.time())
    dump(D / 'CLEANUP_RESULT.json', result); print(json.dumps(result))


if __name__ == '__main__': main()
