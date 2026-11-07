"""Idempotent detached launch after all scientific sources and tasks are frozen."""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path
from evidence_rules import dump, read, sha

repo = Path(__file__).resolve().parents[2]
own = Path(__file__).parent
root = repo/'runs/dynamic_acceptance_20261105'
with (root/'launch.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (root/'LAUNCH.json').exists() or (root/'ROUND_WINDOW.json').exists():
        print('ALREADY_LAUNCHED_OR_CLAIMED_NO_SECOND_INSTANCE')
        raise SystemExit(0)
    prepared = read(root/'PREPARED.json')
    assert prepared['status']=='BOTH_STAGES_FROZEN_AND_ZERO_MODEL_QUALIFIED'
    for name in ['v821_norm_route_development','v822_norm_dynamic_confirmation']:
        f = read(repo/'experiments'/name/'CANDIDATE_FREEZE.json')
        assert all(sha(repo/n)==h for n,h in f['files'].items()), 'FROZEN_INPUT_CHANGED'
    auth = read(repo/'RPCCR_DYNAMIC_ACCEPTANCE_AUTHORIZATION_20261105.json')
    assert time.time()+40500 < auth['absolute_deadline_unix'], 'INSUFFICIENT_INITIAL_WINDOW'
    assert (repo/'REVIEW_PENDING').exists()
    with (repo/'runs/v648_static_unknown/execution.lock').open('rb') as probe:
        fcntl.flock(probe,fcntl.LOCK_EX | fcntl.LOCK_NB)
    claim = dict(status='LAUNCH_CLAIMED',claimed_at_unix=time.time(),absolute_deadline_unix=auth['absolute_deadline_unix'],
                 launch_attempts=1,new_models_in_launcher=0,new_integrations_in_launcher=0)
    dump(root/'LAUNCH.json',claim)
    try:
        with (root/'campaign.console').open('x') as stream:
            cap = int(auth['absolute_deadline_unix']-time.time())+1800
            child = subprocess.Popen(['timeout','--signal=TERM','--kill-after=10s',str(cap)+'s',
                sys.executable,'-B',str(own/'campaign.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        claim.update(status='DETACHED_CAMPAIGN_LAUNCHED',outer_pid=child.pid,outer_wall_cap_s=cap)
        dump(root/'LAUNCH.json',claim)
        print(__import__('json').dumps(claim))
    except BaseException as error:
        claim.update(status='LAUNCH_FAILED_NO_RETRY',error=str(error))
        dump(root/'LAUNCH.json',claim)
        day = read(repo/'RPCCR_DYNAMIC_ACCEPTANCE_LEDGER_20261105.json')
        day.update(status='LAUNCH_FAILED_NO_RETRY',development_extensions_started=1,closed=True,active_simulation=False)
        dump(repo/'RPCCR_DYNAMIC_ACCEPTANCE_LEDGER_20261105.json',day)
        raise
