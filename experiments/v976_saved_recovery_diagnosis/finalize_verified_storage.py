"""Close already uploaded, immutable archives; no model or Git operation."""
import fcntl
import importlib.util
import json
import shutil
import tempfile
import time
from pathlib import Path

R = Path(__file__).resolve().parents[2]
REC = R / 'records/nav2_v974_20261110'
D = R / 'runs/v976_saved_recovery_diagnosis'
spec = importlib.util.spec_from_file_location('v976_final_storage', R / 'experiments/v975_daytime_closure/deliver.py')
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)
t = delivery.transport


def main():
    lock = (R / 'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert t.sha(R / 'REVIEW_PENDING') == '4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((REC / 'COMPLETION.json').read_text())['closed']
    assert not (REC / 'FINALIZED.json').exists()
    with (D / 'FINAL_STORAGE_CLAIM.json').open('x') as stream:
        json.dump(dict(at=time.time(), models=0, integrations=0, git_operations=0), stream)
    readback = delivery.OUT / 'readback'
    original = json.loads((REC / 'RECORD_INDEX.json').read_text())
    # The previous check overlaid an old excluded-active-console hash onto its
    # verified final snapshot. Prefer the closed archive, keeping both versions.
    catalog = {x['path']: x for x in json.loads((REC / 'EXCLUDED_REBUILDABLE_CACHE.json').read_text())['files']}
    verified = []
    views = [(readback, original),
             (D / 'supplement_readback', json.loads((REC / 'V976_SUPPLEMENT_INDEX.json').read_text())),
             (D / 'closed_operations_readback', json.loads((REC / 'V976_CLOSED_OPERATIONS_INDEX.json').read_text()))]
    for folder, index in views:
        for group in index['archives']:
            with tempfile.TemporaryDirectory(prefix='final_sha_', dir=folder) as tmp:
                view = Path(tmp)
                names = [group['group'] + '.INVENTORY.json', *[x['name'] for x in group['parts']]]
                for name in names:
                    (view / name).symlink_to(folder / name)
                t.shared_verifier()(view, dict(index, archives=[group]))
            inv = json.loads((folder / (group['group'] + '.INVENTORY.json')).read_text())
            catalog.update({x['path']: x for x in inv['files']})
            verified.append(dict(group=group['group'], sha256=group['archive_sha256'], members=group['source_files']))
    pack = t.packer()
    for folder in delivery.FOLDERS:
        for path in pack.walk(folder):
            row = catalog[str(path.relative_to(R))]
            assert path.stat().st_size == row['bytes'] and t.sha(path) == row['sha256'], str(path)
    receipts = D / 'final_storage_readback'
    receipts.mkdir(exist_ok=False)
    t.dump(REC / 'FINAL_STORAGE_AUDIT.json', dict(passed=True, models=0, integrations=0, groups=verified,
           original_errors_preserved=True, active_console_old_exclusion_overridden_only_by_verified_final_snapshot=True,
           no_git_push_or_model_retry=True))
    # Keep the final operational source and both failed maintenance attempts
    # remotely before deleting the local transport cache.
    sourcecopy = D / 'V976_FINALIZE_VERIFIED_STORAGE.py'
    sourcecopy.write_bytes(Path(__file__).read_bytes())
    for path in [sourcecopy, REC / 'FINAL_STORAGE_AUDIT.json', REC / 'RESUME_DELIVERY_ERROR.json']:
        t.upload_receipt(path, receipts)
    t.gh(['release', 'edit', delivery.TAG, '--draft=false'], 30)
    sync = json.loads((REC / 'GIT_SYNC_RESULT.json').read_text())
    t.dump(REC / 'REMOTE_VERIFIED.json', dict(passed=True, source_commit=sync['commit'],
           all_asset_and_decompressed_member_sha_verified=True, supplement_verified=True,
           closed_operation_snapshot_verified=True, release_url=original['release_url'], models=0))
    for path in [REC / 'REMOTE_VERIFIED.json', REC / 'GIT_SYNC_RESULT.json']:
        t.upload_receipt(path, receipts)
    removed = []
    folders = [*delivery.FOLDERS, readback, delivery.OUT / 'cloud', D / 'supplement',
               D / 'supplement_readback', D / 'closed_operations_archive', D / 'closed_operations_readback']
    for folder in folders:
        if not folder.exists():
            continue
        assert folder.resolve().is_relative_to(R / 'runs') and not folder.is_symlink()
        size = sum(path.stat().st_size for path in pack.walk(folder))
        shutil.rmtree(folder)
        removed.append(dict(path=str(folder.relative_to(R)), bytes=size))
    total = sum(x['bytes'] for x in removed)
    t.dump(REC / 'CLEANUP_RESULT.json', dict(deleted_bytes=total, removed=removed,
           all_remote_member_sha_verified_before_cleanup=True, models=0))
    t.upload_receipt(REC / 'CLEANUP_RESULT.json', receipts)
    t.dump(REC / 'FINALIZED.json', dict(closed=True, scientific_outcome='NOT_PASSED', remote_verified=True,
           necessary_raw_cleaned=True, all_source_and_member_sha_verified=True, supplement_verified=True,
           release_url=original['release_url'], models=0))
    t.upload_receipt(REC / 'FINALIZED.json', receipts)
    shutil.rmtree(receipts)
    sourcecopy.unlink()
    print(json.dumps(dict(finalized=True, outcome='NOT_PASSED', deleted_bytes=total, models=0)), flush=True)


if __name__ == '__main__':
    main()
