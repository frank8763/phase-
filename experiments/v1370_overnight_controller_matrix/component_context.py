"""Frozen overnight authority and task membership; zero models on import."""
import hashlib
import json
from pathlib import Path
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
RAW=R/'runs/v858_nav2_verified/v1370'

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):
    def scalar(x):
        if hasattr(x,'tolist'):return x.tolist()
        if hasattr(x,'item'):return x.item()
        raise TypeError(type(x).__name__)
    p=Path(p);temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False,default=scalar)+'\n');temp.replace(p)
def sources():return all(sha(R/p)==h for p,h in read(C/'SOURCE_FREEZE.json')['files'].items())
def remaining(w):
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'BOOT_CHANGED'
    return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def task_check(t):
    assert t in read(C/'TASKS.json'),'UNREGISTERED_TASK'
    assert Path(t['output'])==RAW/t['task_id'] and t['controller_kind'] in ['rpp','mppi']
    assert t['case_id']=='WEST_EAST' and t['start_xy']==[-4.,-2.] and t['goal_xy']==[4.,-2.]
    assert t['controller_plugin'] in ['RPP','Deadband'] and t['planner_mode'] in [0,1]
    if t['stage']=='component':assert t['origin_native_tick']==15105 and t['component_native_limit']==4000
    else:assert t['stage'] in ['static','dynamic'] and t['dynamic']==(t['stage']=='dynamic')
    assert sources(),'FROZEN_SOURCE_CHANGED'
    return True
def authorize(t,w):
    task_check(t);assert w==read(O/'ROUND_WINDOW.json'),'WINDOW_CHANGED'
    user=read(O/'USER_AUTHORIZATION.json');approval=read(O/'APPROVAL.json')
    assert user['overnight_approved'] and user['storage_limit_bytes']==10*1024**3
    assert w['absolute_deadline_unix']==1795136400. and 0<w['absolute_deadline_unix']-w['started_unix']<=16*3600
    assert abs(w['hard_stop_monotonic']-w['started_monotonic']-(w['absolute_deadline_unix']-w['started_unix']))<1e-6
    assert approval['models_authorized'] and t['task_id'] in approval['allowed_task_ids']
    assert remaining(w)>300,'ROOT_DEADLINE_RESERVE'
    return True
