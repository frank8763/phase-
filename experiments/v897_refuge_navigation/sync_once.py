"""Closed-night source/metadata delivery once; no models, no offline retry loop."""
import fcntl, hashlib, json, pathlib, subprocess, time

R = pathlib.Path(__file__).resolve().parents[2]
O = R / 'runs/v896_overnight_20261108'
REC = R / 'records/nav2_overnight_20261108'
NAMES = ['experiments/v896_overnight_platform', 'experiments/v897_refuge_navigation',
         'experiments/v898_platform_output_continuation', 'experiments/v899_refuge_qualification',
         'records/nav2_overnight_20261108', 'records/nav2_v899_20261108',
         'docs/NAV2_REFUGE_OVERNIGHT_20261108_REPORT.md', 'CURRENT_EXPERIMENT.json', 'RESEARCH_STATUS.md']

def run(args, timeout=15):
    return subprocess.run(args, cwd=R, capture_output=True, text=True, timeout=timeout)

def dump(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')

def main():
    assert json.loads((O/'COMPLETION.json').read_text())['closed']
    assert json.loads((O/'FINALIZED.json').read_text())['all_archive_source_and_decompressed_sha_verified']
    lock = (R/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert (R/'REVIEW_PENDING').read_bytes() == (O/'REVIEW_PENDING.before').read_bytes()
    claim = O/'GIT_SYNC_CLAIM.json'
    assert not (O/'GIT_SYNC_RESULT.json').exists()
    with claim.open('x') as f:
        json.dump(dict(at=time.time(), push_budget_s=30, read_budget_s=5, no_retry=True, models=0), f)
    result = dict(status='LOCAL_CLOSED_REMOTE_PENDING', models=0, integrations=0, raw_deleted=False,
                  raw_release_upload_pending=True, old_batch_sync_retried=False, push_attempted=False)
    try:
        assert not run(['git','diff','--cached','--name-only']).stdout.strip(), 'UNRELATED_STAGED_CHANGES'
        assert run(['git','remote','get-url','origin']).stdout.strip() == 'https://github.com/frank8763/phase-.git'
        names = [name for name in NAMES if (R/name).exists()]
        for name in names:
            p = R/name
            for item in p.rglob('*') if p.is_dir() else [p]:
                if item.is_file():
                    assert not item.is_symlink() and item.stat().st_size < 90*1024**2, 'INVALID_GIT_PAYLOAD'
        staged = run(['git','add','--',*names]); assert staged.returncode == 0, staged.stderr
        check = run(['git','diff','--cached','--check']); assert check.returncode == 0, check.stdout
        (O/'SOURCE_REVIEW.console').write_text(run(['git','diff','--cached','--stat']).stdout)
        commit = run(['git','commit','-m','Record bounded causal refuge development and offline night accounting'],30)
        assert commit.returncode == 0, commit.stderr
        result['source_commit'] = run(['git','rev-parse','HEAD']).stdout.strip()
        result['push_attempted'] = True
        try:
            pushed = run(['git','push','origin','main'],30)
            result.update(push_returncode=pushed.returncode, push_succeeded=pushed.returncode == 0)
            (O/'push.console').write_text(pushed.stdout+pushed.stderr)
        except subprocess.TimeoutExpired:
            result['push_error'] = '30S_TIMEOUT_NO_RETRY'
        try:
            remote = run(['git','ls-remote','origin','refs/heads/main'],5)
            head = remote.stdout.split()[0] if remote.returncode == 0 and remote.stdout.strip() else None
            result.update(remote_head=head, remote_head_verified=head == result['source_commit'])
        except subprocess.TimeoutExpired:
            result['read_error'] = '5S_TIMEOUT_NO_RETRY'
        result['status'] = 'SOURCE_REMOTE_VERIFIED_RAW_RELEASE_PENDING' if result.get('remote_head_verified') else 'REMOTE_UNVERIFIED_NO_RETRY'
    except BaseException as e:
        result['error'] = repr(e)
    dump(O/'GIT_SYNC_RESULT.json',result); dump(REC/'GIT_SYNC_RESULT.json',result)
    print(json.dumps(result),flush=True)

if __name__ == '__main__':
    main()
