"""One explicitly requested new90min window, locked before any vehicle model."""
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'runs/v945_rpccr_observation_liveness'
sys.path[:0]=[str(CODE),str(ROOT/'experiments/v862_ready_static')]
from handshake import verify_sources


def write_new(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')


assert not(OUT/'AUTHORIZATION.json').exists() and not(OUT/'CAMPAIGN_CLAIM.json').exists(),'ALREADY_LOCKED_OR_LAUNCHED'
freeze=json.loads((CODE/'SOURCE_FREEZE.json').read_text());assert freeze['final'] is True
verify_sources(ROOT,CODE/'SOURCE_FREEZE.json')
for name in ['ZERO_MODEL_QUALIFICATION.json','FULL_STARTUP_QUALIFICATION.json','CORRIDOR_AUDIT_QUALIFICATION.json','SEGMENT_QUALIFICATION.json','RPP_HANDOFF_QUALIFICATION.json','WATCHDOG_QUALIFICATION.json','SUPERVISOR_QUALIFICATION.json','LIVENESS_QUALIFICATION.json']:
    assert json.loads((OUT/name).read_text())['passed'],name
assert hashlib.sha256((ROOT/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
start=time.time();deadline=start+5400.
iso=lambda value:datetime.fromtimestamp(value,ZoneInfo('Asia/Shanghai')).isoformat()
authority=dict(scope='V945_DECLARED_PERIODIC_COURSE',models_authorized=True,
               user_instruction='之前24项成功八个；现在越调越差；思考下一步实验，继续推进',authority_date='2026-11-09',
               interpretation='New bounded90min original WE dynamic main then all-gates-success-only full repeat; no other experiment.',
               started_unix=start,deadline_unix=deadline,started_iso=iso(start),deadline_iso=iso(deadline),
               source_freeze_sha256=hashlib.sha256((CODE/'SOURCE_FREEZE.json').read_bytes()).hexdigest(),
               max_navigation=2,first_failure_stops=True,old_windows_unchanged=True,
               training=0,hardware=0,new24=0)
write_new(OUT/'ROUND_WINDOW.json',dict(started_unix=start,deadline_unix=deadline,started_iso=iso(start),deadline_iso=iso(deadline)))
write_new(OUT/'AUTHORIZATION.json',authority)
fcntl.flock(lock,fcntl.LOCK_UN)
with (OUT/'campaign.console').open('x') as console:
    job=subprocess.Popen(['timeout','--signal=TERM','--kill-after=5s','5700',sys.executable,'-B',str(CODE/'campaign.py')],
                         cwd=ROOT,stdin=subprocess.DEVNULL,stdout=console,stderr=subprocess.STDOUT,start_new_session=True)
write_new(OUT/'DRIVER.json',dict(pid=job.pid,launched_unix=time.time(),deadline_unix=deadline,models_launched_by_this_parent=0))
print(json.dumps(dict(pid=job.pid,started=iso(start),deadline=iso(deadline)),indent=2))
