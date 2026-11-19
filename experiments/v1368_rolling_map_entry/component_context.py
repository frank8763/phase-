"""Exact task and separately authorized bounded component window; no models."""
import hashlib
import json
import math
from pathlib import Path
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
RAW=R/'runs/v858_nav2_verified/v1368'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p,x):
    def native(v):
        if hasattr(v,'tolist'):return v.tolist()
        if hasattr(v,'item'):return v.item()
        raise TypeError(type(v).__name__)
    p=Path(p);temporary=p.with_suffix(p.suffix+'.tmp');temporary.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False,default=native)+'\n');temporary.replace(p)


def sources():return all(sha(R/p)==h for p,h in read(C/'SOURCE_FREEZE.json')['files'].items())


def task_check(task):
    assert task in read(C/'TASKS.json'),'UNREGISTERED_COMPONENT_TASK'
    assert task['origin_native_tick']==15105 and abs(task['origin_sim_time']-151.05)<1e-7
    assert task['dynamic'] is True and task['stage']=='component' and task['component_gear']==-1
    assert task['case_id']=='WEST_EAST' and task['seed']==10060001
    assert task['component_native_limit']==4000 and task['complete_stop_native']==200
    assert task['component_goal_radius_m']==.08 and task['minimum_component_reverse_progress_m']==.6
    assert task['original_goal_navigation'] is False
    assert Path(task['output'])==RAW/task['task_id']
    assert sources(),'FROZEN_SOURCE_CHANGED'
    return True


def remaining(window):
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==window['boot_id'],'BOOT_CHANGED'
    return min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())


def authorize(task,window):
    task_check(task);assert window==read(O/'ROUND_WINDOW.json'),'WINDOW_CHANGED'
    approval=read(O/'APPROVAL.json');user=read(O/'USER_WINDOW.json')
    assert user['approved_single_entry_continuation'] is True,'SINGLE_ENTRY_CONTINUATION_NOT_AUTHORIZED'
    assert window==read(R/'runs/v1367_shared_recovery_component/ROUND_WINDOW.json'),'ORIGINAL_WINDOW_CHANGED'
    assert approval['models_authorized'] is True and task['task_id'] in approval['allowed_task_ids']
    assert 0<window['absolute_deadline_unix']-window['started_unix']<=5400.001
    assert abs(window['hard_stop_monotonic']-window['started_monotonic']-5400)<.001
    assert window['absolute_deadline_unix']>1795078800. and remaining(window)>300,'WINDOW_EXPIRED_OR_INSUFFICIENT'
    return True
