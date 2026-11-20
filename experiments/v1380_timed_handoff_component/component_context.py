"""Supplemental same32210 handoff pair; original day17:00 cutoff, no route."""
import hashlib
import json
from pathlib import Path
import time
from evidence_io import atomic as dump
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;RAW=R/'runs/v858_nav2_verified/v1380';DAY=R/'runs/v1374_day_handoff_validation'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sources():return all(sha(R/p)==h for p,h in read(C/'SOURCE_FREEZE.json')['files'].items())
def remaining(w):
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'BOOT_CHANGED'
    return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def task_check(t):
    assert t in read(C/'TASKS.json') and Path(t['output'])==RAW/t['task_id'],'TASK_NOT_REGISTERED'
    assert t['origin_native_tick']==32600 and t['component_native_limit']==1200 and not t['original_goal_navigation']
    assert t['causal_source_tick']==32200 and t['seed']==10060001 and t['case_id']=='WEST_EAST'
    assert sources(),'SOURCE_CHANGED';return True
def authorize(t,w):
    task_check(t);a=read(O/'APPROVAL.json');d=read(DAY/'DAY_LEDGER.json')
    assert a['models_authorized'] and t['task_id'] in a['allowed_task_ids'],'MODELS_DISABLED'
    assert w==read(O/'ROUND_WINDOW.json') and w['absolute_deadline_unix']==1795165200 and remaining(w)>300
    assert d['supplemental_component_limit']==2 and d['supplemental_components_started']<=2
    assert d['component_tasks_started']==4 and not d.get('safety_or_evidence_fault_stops_today_physics',False)
    return True
