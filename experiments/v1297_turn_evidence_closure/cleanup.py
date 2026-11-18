"""Clean only closed, remotely verified data and reproducible renderer caches."""
from package import *


def main():
    assert not (D / 'CLEANUP_RESULT.json').exists(), 'ONE_SELECTED_CLEANUP'
    proof = read(D / 'FULL_REMOTE_VERIFIED.json')
    assert proof['passed'] and proof['published'] and proof['every_member_SHA_verified'] and proof['all_assets_downloaded_SHA_verified']
    assert read(R / 'CURRENT_EXPERIMENT.json')['active_run'] is None and (R / 'REVIEW_PENDING').exists()
    lock = (R / 'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    catalog = read(D / 'SOURCE_INVENTORY.json')
    frozen = set(read(R / 'experiments/v1296_rpp_turn_brake/SOURCE_FREEZE.json')['files'])
    for item in catalog['files']:
        p = R / item['path']
        assert item['path'] not in frozen and any(item['path'].startswith(root + '/') for root in ROOTS)
        if item.get('kind') == 'symlink':
            assert p.is_symlink() and str(p.readlink()) == item['link_target']
        else:
            assert p.is_file() and not p.is_symlink() and p.stat().st_size == item['bytes'] and sha(p) == item['sha256']
    for item in catalog['excluded_caches']:
        p = R / item['path']
        assert '/paired/cache/' in item['path'] and p.is_file() and not p.is_symlink() and sha(p) == item['sha256']
    for item in [*catalog['files'], *catalog['excluded_caches']]:
        (R / item['path']).unlink()
    for root in ROOTS:
        path = R / root
        for sub in sorted(path.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            if sub.is_dir() and not sub.is_symlink():
                try:
                    sub.rmdir()
                except OSError:
                    pass
        try:
            path.rmdir()
        except OSError:
            pass
    duplicate = []
    for path in [O / proof['archive']['name'], *(O / 'downloaded').iterdir()]:
        if path.is_file() and not path.is_symlink():
            duplicate.append(dict(path=str(path.relative_to(R)), bytes=path.stat().st_size, sha256=sha(path)))
    for item in duplicate:
        (R / item['path']).unlink()
    (O / 'downloaded').rmdir()
    result = dict(passed=True, remotely_verified_members_removed=len(catalog['files']),
                  verified_raw_logical_bytes_removed=sum(x['bytes'] for x in catalog['files']),
                  reconstructible_cache_files_removed=len(catalog['excluded_caches']),
                  reconstructible_cache_bytes_removed=sum(x['bytes'] for x in catalog['excluded_caches']),
                  duplicate_archives_removed=duplicate,
                  total_logical_bytes_removed=sum(x['bytes'] for x in [*catalog['files'], *catalog['excluded_caches'], *duplicate]),
                  frozen_source_or_dependency_files_removed=0, restore_index=str((D / 'RECORD_INDEX.json').relative_to(R)),
                  release_url=proof['release_url'], models=0, physical_native=0, completed_unix=time.time())
    dump(D / 'CLEANUP_RESULT.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
