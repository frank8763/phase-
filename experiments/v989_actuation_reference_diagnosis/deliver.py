"""Incremental saved-data diagnosis delivery; never retry V987's used Git push."""
import fcntl
import importlib.util
import json
import shutil
import time
from pathlib import Path

R = Path(__file__).resolve().parents[2]
C = Path(__file__).parent
O = R / 'runs/v989_actuation_reference_diagnosis'
REC = R / 'records/nav2_v987_20261110'
spec = importlib.util.spec_from_file_location('v989_storage', R / 'experiments/v978_source_only_closure/deliver.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
TAG = 'phase-rpccr-bounded-startup-v987-20261110'
GROUP = 'v989-saved-actuation-diagnosis-next-design'
STAGE = ['CURRENT_EXPERIMENT.json', 'RESEARCH_STATUS.md',
         'docs/RPCCR_V989_ACTUATION_DIAGNOSIS_AND_NEXT_PLAN.md', 'docs/figures/V989_RESPONSE_DIAGNOSIS.png',
         'experiments/v989_actuation_reference_diagnosis',
         'records/nav2_v987_20261110/V989_ACTUATION_ANALYSIS.json',
         'records/nav2_v987_20261110/V989_BASELINE_RED.json',
         'records/nav2_v987_20261110/V989_POSTMORTEM_INDEX.json',
         'records/nav2_v987_20261110/V989_REMOTE_VERIFIED.json',
         'records/nav2_v987_20261110/V989_CLEANUP.json']


def gh(args):
    return t.run([str(t.GH), *args, '--repo', t.REPO], 30)


def main():
    lock = (R / 'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert t.sha(R / 'REVIEW_PENDING') == '4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((REC / 'FINALIZED.json').read_text())['remote_verified']
    sync = json.loads((REC / 'GIT_SYNC_RESULT.json').read_text())
    assert sync['one_attempt'] and sync['remote_head_verified']
    for name, digest in json.loads((R / 'experiments/v987_bounded_startup_components/SOURCE_FREEZE.json').read_text())['files'].items():
        assert t.sha(R / name) == digest, name
    assert not t.run(['git', 'diff', '--cached', '--name-only']).strip()
    assert json.loads((O / 'BASELINE_RED.json').read_text())['original_failure_reproduced']
    assert json.loads((O / 'ANALYSIS.json').read_text())['physical_revision'] is None
    with (O / 'DELIVERY_CLAIM.json').open('x') as f:
        json.dump(dict(at=time.time(), models=0, integrations=0, no_git_push=True), f)
    cloud = O / 'cloud'; cloud.mkdir()
    pack = t.packer(cloud)
    files = list(pack['walk'](C))
    files += [O / name for name in ['ANALYSIS.json', 'BASELINE_RED.json', 'RESTORE_RECEIPT.json', 'DELIVERY_CLAIM.json']]
    files += [R / name for name in STAGE[:4] + STAGE[5:7]]
    group = pack['archive'](GROUP, files)
    index = dict(repository=t.REPO, release_tag=TAG, models=0, integrations=0, no_git_push=True,
        original_outcome='V987_NOT_PASSED', next_candidate_implemented=False, model_authority=False,
        original_raw_trace_not_duplicated=True, original_raw_index='records/nav2_v987_20261110/RECORD_INDEX.json',
        archives=[{k: v for k, v in group.items() if k != 'files'}])
    ix = REC / 'V989_POSTMORTEM_INDEX.json'; t.dump(ix, index)
    assets = list(cloud.iterdir()) + [ix]
    gh(['release', 'upload', TAG, *map(str, assets)])
    back = O / 'readback'; back.mkdir()
    for p in assets:
        gh(['release', 'download', TAG, '--pattern', p.name, '--dir', str(back)])
        assert t.sha(p) == t.sha(back / p.name)
    t.verifier()(back, index)
    verified = REC / 'V989_REMOTE_VERIFIED.json'
    t.dump(verified, dict(passed=True, all_asset_and_member_sha_verified=True, models=0, integrations=0,
        no_git_push=True, original_physical_outcome='V987_NOT_PASSED', candidate_implemented=False, model_authority=False))
    gh(['release', 'upload', TAG, str(verified)])
    gh(['release', 'download', TAG, '--pattern', verified.name, '--dir', str(back)])
    assert t.sha(verified) == t.sha(back / verified.name)
    for row in json.loads((O / 'RESTORE_RECEIPT.json').read_text())['files']:
        assert t.sha(R / row['path']) == row['sha256']
    # Only this turn's exact cache tree. Original members are verified in V987;
    # new analysis/source/figure are verified above; transports are duplicates.
    assert O.resolve().is_relative_to(R / 'runs') and not O.is_symlink()
    for p in O.rglob('*'):
        assert not p.is_symlink() and p.resolve().is_relative_to(O)
    manifest = [dict(path=str(p.relative_to(R)), bytes=p.stat().st_size, sha256=t.sha(p)) for p in pack['walk'](O)]
    removed = sum(p['bytes'] for p in manifest)
    for row in manifest:
        assert t.sha(R / row['path']) == row['sha256']
    shutil.rmtree(O)
    cleanup = REC / 'V989_CLEANUP.json'
    t.dump(cleanup, dict(deleted_cache_bytes=removed, files=manifest, models=0, no_git_push=True,
        original_raw_in_verified_v987_release=True, new_analysis_remote_member_sha_verified=True))
    tmp = R / 'runs/v987_bounded_startup_components/v989_receipt_readback'; tmp.mkdir()
    gh(['release', 'upload', TAG, str(cleanup)])
    gh(['release', 'download', TAG, '--pattern', cleanup.name, '--dir', str(tmp)])
    assert t.sha(cleanup) == t.sha(tmp / cleanup.name)
    shutil.rmtree(tmp)
    t.run(['git', 'add', '--', *STAGE]); t.run(['git', 'diff', '--cached', '--check'])
    for name in t.run(['git', 'diff', '--cached', '--name-only']).splitlines():
        assert (R / name).lstat().st_size < 90 * 1024**2
    print(json.dumps(dict(remote_verified=True, models=0, no_git_push=True, deleted_cache_bytes=removed,
        archive_source_files=group['source_files'], archive_bytes=group['archive_bytes'], staged_for_review=True)))


if __name__ == '__main__':
    main()
