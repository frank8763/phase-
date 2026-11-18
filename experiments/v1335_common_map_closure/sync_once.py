"""One bounded source sync and one distinct final metadata sync; no retries."""
import argparse
import subprocess
import time
from package import *


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--final-metadata', action='store_true'); args = parser.parse_args()
    prefix = 'FINAL_METADATA_SYNC' if args.final_metadata else 'GIT_SYNC'
    claim = D / (prefix + '_CLAIM.json'); result_path = D / (prefix + '_RESULT.json')
    assert not claim.exists() and not result_path.exists(), 'ONE_SYNC_PER_PHASE'
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip()
    dump(claim, dict(head=head, started_unix=time.time(), push_timeout_s=30, verification_timeout_s=5, models=0))
    result = dict(head=head, push_succeeded=False, remote_head_verified=False, models=0)
    try:
        p = subprocess.run(['git', 'push', 'origin', 'HEAD:main'], cwd=R, capture_output=True, text=True, timeout=30)
        result.update(push_succeeded=p.returncode == 0, push_returncode=p.returncode, push_stdout=p.stdout, push_stderr=p.stderr)
    except subprocess.TimeoutExpired: result['push_error'] = 'TIMEOUT_NO_RETRY'
    try:
        p = subprocess.run(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=R, capture_output=True, text=True, timeout=5)
        remote = p.stdout.split()[0] if p.returncode == 0 and p.stdout.split() else None
        result.update(remote_head=remote, remote_head_verified=remote == head)
    except subprocess.TimeoutExpired: result['verification_error'] = 'TIMEOUT_NO_RETRY'
    result['completed_unix'] = time.time(); dump(result_path, result); print(json.dumps(result))


if __name__ == '__main__': main()
