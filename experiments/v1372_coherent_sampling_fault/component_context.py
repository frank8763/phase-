"""One registered fault component; model authority disabled until human window reply."""
import hashlib
import json
from pathlib import Path
import time
from evidence_io import atomic as dump

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
RAW=R/'runs/v858_nav2_verified/v1372'

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sources():return all(sha(R/p)==h for p,h in read(C/'SOURCE_FREEZE.json')['files'].items())
def remaining(w):
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'BOOT_CHANGED'
    return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def task_check(t):
    assert t in read(C/'TASKS.json') and len(read(C/'TASKS.json'))==1,'UNREGISTERED_TASK'
    assert Path(t['output'])==RAW/t['task_id']
    assert t['origin_native_tick']==41390 and t['expected_new_native']==225
    assert t['stage']=='component' and t['original_goal_navigation'] is False
    assert sources(),'FROZEN_SOURCE_CHANGED'
    return True
def authorize(t,w):
    task_check(t);user=read(O/'USER_AUTHORIZATION.json')
    assert user['models_authorized'] is True and user['total_window_seconds']==5400,'NEW_WINDOW_NOT_APPROVED'
    assert user['scope']=='one_sampling_fault_component_only'
    assert w==read(O/'ROUND_WINDOW.json'),'WINDOW_CHANGED'
    approval=read(O/'APPROVAL.json')
    assert approval['models_authorized'] and approval['allowed_task_ids']==[t['task_id']]
    assert abs(w['absolute_deadline_unix']-w['started_unix']-5400)<1e-6
    assert abs(w['hard_stop_monotonic']-w['started_monotonic']-5400)<1e-6
    assert remaining(w)>300,'ROOT_DEADLINE_RESERVE'
    return True
