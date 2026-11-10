"""Finish verified evidence transport only; never initialize models or retry Git push."""
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
spec = importlib.util.spec_from_file_location('v976_transport_resume', R / 'experiments/v975_daytime_closure/deliver.py')
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)
t = delivery.transport


def main():
    lock = (R / 'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert t.sha(R / 'REVIEW_PENDING') == '4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((REC / 'COMPLETION.json').read_text())['closed']
    assert json.loads((REC / 'GIT_SYNC_RESULT.json').read_text())['remote_head_verified']
    with (D / 'RESUME_DELIVERY_CLAIM.json').open('x') as stream:
        json.dump(dict(at=time.time(), models=0, integrations=0, git_push_retries=0), stream)
    cloud = delivery.OUT / 'cloud'
    readback = delivery.OUT / 'readback'
    supplement = D / 'supplement_readback'
    index = json.loads((REC / 'RECORD_INDEX.json').read_text())
    supindex = json.loads((REC / 'V976_SUPPLEMENT_INDEX.json').read_text())
    # SimpleNamespace.OUT was changed, but archive's function globals retained
    # the original cloud path. Original archive, source and failure stay intact.
    issue = dict(models=0, integrations=0,
                 original_temp_name_collision_preserved=True,
                 second_transport_error='Supplement files written under original packer function globals OUT, not reassigned SimpleNamespace.OUT; only metadata uploaded, verifier could not find inventory.',
                 correction='Upload the existing, SHA-verified supplemental parts and inventory from their actual path; do not rebuild or overwrite any archive.',
                 no_git_push_or_model_retry=True)
    t.dump(REC / 'SUPPLEMENT_PATH_DIAGNOSIS.json', issue)
    shutil.copyfile(R / 'runs/v974_daytime_binding_gate/CLOSE_ERROR.json', REC / 'ORIGINAL_CLOSE_ERROR.json')
    assets = []
    for group in supindex['archives']:
        assets += [cloud / (group['group'] + '.INVENTORY.json')]
        for part in group['parts']:
            path = cloud / part['name']
            assert path.stat().st_size == part['bytes'] and t.sha(path) == part['sha256']
            assets.append(path)
    t.gh(['release', 'upload', delivery.TAG, *map(str, assets)], 30)
    for path in assets:
        t.gh(['release', 'download', delivery.TAG, '--pattern', path.name, '--dir', str(supplement)], 30)
        assert t.sha(path) == t.sha(supplement / path.name)
    t.shared_verifier()(supplement, supindex)

    # Closed console snapshots, the exact new diagnostic code, and original
    # errors have their own small archive. Bind function globals explicitly.
    finalcloud = D / 'closed_operations_archive'
    finalcloud.mkdir(exist_ok=False)
    pack = t.packer()
    pack.archive.__globals__['OUT'] = finalcloud
    files = [p for p in (R / 'experiments/v976_saved_recovery_diagnosis').iterdir() if p.is_file()]
    files += [D / 'RESUME_DELIVERY_CLAIM.json', REC / 'SUPPLEMENT_PATH_DIAGNOSIS.json', REC / 'ORIGINAL_CLOSE_ERROR.json',
              R / 'runs/v974_daytime_binding_gate/CLOSE_ERROR.json',
              R / 'runs/v974_daytime_binding_gate/close.console', R / 'runs/v974_daytime_binding_gate/campaign.console',
              R / 'docs/RPCCR_DAYTIME_BINDING_V974_REPORT.md']
    group = pack.archive('v976-closed-operations', files)
    finalindex = dict(repository=index['repository'], release_tag=delivery.TAG, models=0, integrations=0,
                      archives=[{k: v for k, v in group.items() if k != 'files'}])
    ixpath = REC / 'V976_CLOSED_OPERATIONS_INDEX.json'
    t.dump(ixpath, finalindex)
    finalassets = [p for p in finalcloud.iterdir() if p.is_file()] + [ixpath]
    t.gh(['release', 'upload', delivery.TAG, *map(str, finalassets)], 30)
    finalread = D / 'closed_operations_readback'
    finalread.mkdir(exist_ok=False)
    for path in finalassets:
        t.gh(['release', 'download', delivery.TAG, '--pattern', path.name, '--dir', str(finalread)], 30)
        assert t.sha(path) == t.sha(finalread / path.name)
    t.shared_verifier()(finalread, finalindex)

    # Recheck original downloaded assets without overwriting the old combined file.
    catalog = {}
    for record in index['archives']:
        with tempfile.TemporaryDirectory(prefix='final_verify_', dir=readback) as tmp:
            view = Path(tmp)
            for name in [record['group'] + '.INVENTORY.json', *[x['name'] for x in record['parts']]]:
                (view / name).symlink_to(readback / name)
            t.shared_verifier()(view, dict(index, archives=[record]))
        inv = json.loads((readback / (record['group'] + '.INVENTORY.json')).read_text())
        catalog.update({x['path']: x for x in inv['files']})
    catalog.update({x['path']: x for x in group['files']})
    catalog.update({x['path']: x for x in json.loads((REC / 'EXCLUDED_REBUILDABLE_CACHE.json').read_text())['files']})
    for folder in delivery.FOLDERS:
        for path in pack.walk(folder):
            row = catalog[str(path.relative_to(R))]
            assert path.stat().st_size == row['bytes'] and t.sha(path) == row['sha256']
    t.gh(['release', 'edit', delivery.TAG, '--draft=false'], 30)
    t.dump(REC / 'REMOTE_VERIFIED.json', dict(passed=True,
           source_commit=json.loads((REC / 'GIT_SYNC_RESULT.json').read_text())['commit'],
           all_asset_and_decompressed_member_sha_verified=True, supplement_verified=True,
           closed_operation_snapshot_verified=True, release_url=index['release_url'], models=0))
    for path in [REC / 'REMOTE_VERIFIED.json', REC / 'GIT_SYNC_RESULT.json']:
        t.upload_receipt(path, readback)
    removed = []
    for folder in [*delivery.FOLDERS, readback, cloud, D / 'supplement', supplement, finalcloud, finalread]:
        if not folder.exists():
            continue
        assert folder.resolve().is_relative_to(R / 'runs') and not folder.is_symlink()
        size = sum(path.stat().st_size for path in pack.walk(folder))
        shutil.rmtree(folder)
        removed.append(dict(path=str(folder.relative_to(R)), bytes=size))
    total = sum(x['bytes'] for x in removed)
    t.dump(REC / 'CLEANUP_RESULT.json', dict(deleted_bytes=total, removed=removed,
           all_remote_member_sha_verified_before_cleanup=True, models=0))
    receipts = D / 'receipt_readback'
    receipts.mkdir(exist_ok=False)
    t.upload_receipt(REC / 'CLEANUP_RESULT.json', receipts)
    t.dump(REC / 'FINALIZED.json', dict(closed=True, scientific_outcome='NOT_PASSED', remote_verified=True,
           necessary_raw_cleaned=True, all_source_and_member_sha_verified=True, supplement_verified=True,
           release_url=index['release_url'], models=0))
    t.upload_receipt(REC / 'FINALIZED.json', receipts)
    shutil.rmtree(receipts)
    print(json.dumps(dict(finalized=True, outcome='NOT_PASSED', deleted_bytes=total, models=0)), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        t.dump(REC / 'RESUME_DELIVERY_ERROR.json', dict(error=repr(error), models=0,
               necessary_unverified_raw_kept=True, no_model_or_git_push_retry=True))
        raise
