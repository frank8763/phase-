"""One bounded Git backup of the closed zero-vehicle software diagnosis."""
import json
from pathlib import Path
import subprocess
import time

R = Path(__file__).resolve().parents[2]
D = R / 'records/v1320_mppi_diagnosis_20261118'


def dump(name, value):
    (D / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    assert not (D / 'GIT_SYNC_CLAIM.json').exists(), 'ONE_CURRENT_SYNC_NO_RETRY'
    assert json.loads((D / 'FINAL_DIAGNOSIS.json').read_text())['closed']
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip()
    dump('GIT_SYNC_CLAIM.json', dict(head=head, started_unix=time.time(), push_limit_s=30, verification_limit_s=5, models=0))
    result = dict(head=head, push_succeeded=False, remote_head_verified=False, models=0)
    try:
        run = subprocess.run(['git', 'push', 'origin', 'HEAD:main'], cwd=R, capture_output=True, text=True, timeout=30)
        result.update(push_succeeded=run.returncode==0, push_returncode=run.returncode, stderr=run.stderr)
    except subprocess.TimeoutExpired: result['push_error'] = 'TIMEOUT_NO_RETRY'
    try:
        run = subprocess.run(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=R, capture_output=True, text=True, timeout=5)
        remote = run.stdout.split()[0] if run.returncode==0 and run.stdout.split() else None
        result.update(remote_head=remote, remote_head_verified=remote==head)
    except subprocess.TimeoutExpired: result['verification_error'] = 'TIMEOUT_NO_RETRY'
    result['completed_unix'] = time.time(); dump('GIT_SYNC_RESULT.json', result); print(json.dumps(result))


if __name__ == '__main__': main()
