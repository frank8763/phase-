"""Fixed two-task capture; inherited today's human authority and17:00 cap."""
import hashlib
import json
from pathlib import Path
import time
from evidence_io import atomic as dump
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;RAW=R/'runs/v858_nav2_verified/v1378'
DAY=R/'runs/v1374_day_handoff_validation'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sources():return all(sha(R/p)==h for p,h in read(C/'SOURCE_FREEZE.json')['files'].items())
def remaining(w):
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'BOOT_CHANGED'
    return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def task_check(t):
    assert t in read(C/'TASKS.json') and Path(t['output'])==RAW/t['task_id'],'TASK_NOT_REGISTERED'
    assert t['origin_native_tick']==32210 and t['component_native_limit']==600 and t['original_goal_navigation'] is False
    assert sources(),'SOURCE_CHANGED';return True
def authorize(t,w):
    task_check(t);a=read(O/'APPROVAL.json');d=read(DAY/'DAY_LEDGER.json')
    assert a['models_authorized'] and t['task_id'] in a['allowed_task_ids'],'MODELS_DISABLED'
    assert w==read(O/'ROUND_WINDOW.json') and w['absolute_deadline_unix']==1795165200,'DAY_WINDOW_CHANGED'
    assert d['component_tasks_started']<=4 and d['navigation_tasks_started']==0 and remaining(w)>300
    assert not d.get('safety_or_evidence_fault_stops_today_physics',False),'DAY_SAFETY_OR_EVIDENCE_STOP_PRESERVED'
    return True
