"""Hold a sleep inhibitor only while the already running Phase campaign lives.

Pure operating-system housekeeping: no scientific imports, models, integration,
restart, network, git, or changes to the frozen experiment.
"""

import argparse
import json
import time
from pathlib import Path


def process_identity(pid):
    try:
        proc = Path('/proc') / str(pid)
        fields = (proc / 'stat').read_text().rsplit(') ', 1)[1].split()
        command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
        return fields[0], fields[19], command
    except FileNotFoundError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    initial = process_identity(args.pid)
    expected = '/experiments/overnight_recovery_20261105/campaign.py'
    if initial is None or expected not in initial[2] or initial[0] == 'Z':
        raise SystemExit('Expected live Phase campaign is absent; no job started.')
    print(json.dumps(dict(status='INHIBITOR_ACTIVE', campaign_pid=args.pid,
                          process_start_ticks=initial[1], deadline=args.deadline,
                          models=0, integrations=0, network_calls=0)), flush=True)
    reason = 'ABSOLUTE_HOUSEKEEPING_DEADLINE'
    while time.time() < args.deadline:
        current = process_identity(args.pid)
        if current is None or current[1:] != initial[1:] or current[0] == 'Z':
            reason = 'ORIGINAL_CAMPAIGN_ENDED'
            break
        time.sleep(min(15, max(0, args.deadline - time.time())))
    print(json.dumps(dict(status='INHIBITOR_RELEASED', reason=reason,
                          models=0, integrations=0)), flush=True)


if __name__ == '__main__':
    main()
