"""OriginalRPP complete9390 forward segment, same saved captured origin."""
import hashlib
import json
from pathlib import Path
import time
from evidence_io import atomic as dump
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;RAW=R/'runs/v858_nav2_verified/v1396';DAY=R/'runs/v1382_weekend_campaign'
ROOT_END=1795395600
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sources():return all(sha(R/p)==h for p,h in read(C/'SOURCE_FREEZE.json')['files'].items())
def remaining(w):
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'BOOT_CHANGED'
    return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic(),ROOT_END-time.time())
def task_check(t):
    assert t in read(C/'TASKS.json') and Path(t['output'])==RAW/t['task_id'],'TASK_NOT_REGISTERED'
    assert t['origin_native_tick']==10775 and t['component_native_limit']==3000 and not t['original_goal_navigation']
    assert t['causal_source_tick']==9360 and t['seed']==10060001 and t['case_id']=='WEST_EAST'
    assert sources(),'SOURCE_CHANGED';return True
def authorize(t,w):
    task_check(t);a=read(O/'APPROVAL.json');d=read(DAY/'LEDGER.json')
    assert a['models_authorized'] and t['task_id'] in a['allowed_task_ids'],'MODELS_DISABLED'
    assert w==read(O/'ROUND_WINDOW.json') and w['absolute_deadline_unix']<=ROOT_END and remaining(w)>300
    assert d['active_round']==C.name and d['absolute_hard_stop_unix']==ROOT_END
    assert read(O/'ROUND_LEDGER.json')['task_starts']<=2 and d['vehicle_task_starts']<=256
    assert d['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    return True
