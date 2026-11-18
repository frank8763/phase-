"""Explicit disabled-by-default worker context; no physical imports."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import os
import sys
import time

C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name;RAW=R/'runs/v858_nav2_verified/v1264'
LIMIT=2*1024**3


def read(path):return json.loads(Path(path).read_text())
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def dump(path,value):
    def default(x):
        if hasattr(x,'tolist'):return x.tolist()
        if hasattr(x,'item'):return x.item()
        raise TypeError(type(x).__name__)
    path=Path(path);p=path.with_suffix(path.suffix+'.tmp')
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False,default=default)+'\n');p.replace(path)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def remaining(w=None):
    w=w if w is not None else read(O/'ROUND_WINDOW.json')
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'WRONG_BOOT'
    assert all(type(w[k])in[int,float] and math.isfinite(w[k])for k in ['started_unix','absolute_deadline_unix','started_monotonic','hard_stop_monotonic'])
    assert w['absolute_deadline_unix']>w['started_unix'] and w['hard_stop_monotonic']>w['started_monotonic'],'WINDOW_ORDER'
    return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def task_contract(t):
    assert t in read(C/'TASKS.json'),'UNREGISTERED_TASK'
    assert not RAW.is_symlink() and not Path(t['output']).is_symlink(),'SYMLINK_OUTPUT'
    spec=read(R/'experiments/v1089_route_scene_contract/SCENE_CONTRACT.json')['routes'][t['case_id']]['case']
    assert t['role']in ['development_main','development_repeat'] and t['dynamic']is True
    assert t['qualification_case']in ['slot17']
    if t['qualification_case']!='oldNS':
        original=next(x for x in read(C/'ORIGINAL_TASK_LIST.json')if x['slot']==17)
        assert (t['seed'],t['phase'],t['case_id'])==(original['seed'],original['phase'],original['case_id'])
    else:
        original=next(x for x in read(R/'experiments/v1217_private_three_route/TASKS.json')if x['task_id']=='main_NORTH_SOUTH')
        assert all(t[k]==original[k]for k in ['seed','phase','case_id','start_xy','start_yaw','goal_xy'])
    assert t['start_xy']==spec['start_xy'] and t['goal_xy']==spec['goal_xy'] and t['start_yaw']==spec['yaw']
    assert t['historical_prefix_native']==0 and t['native_limit']==60000
    assert t['run_root']==str(O) and Path(t['output'])==RAW/t['task_id']
    return True
def used():return sum(p.stat().st_size for root in[O,RAW,R/'runs/v1255_ew_component_entry',R/'runs/v1255_ew_component_entry_audit',R/'runs/v1261_ew_reserved_validation',R/'runs/v858_nav2_verified/v1261']for p in root.rglob('*')if p.is_file()and not p.is_symlink())
def envelope(task,approval,window,*,entry_check=False):
    assert approval.get('models_authorized')is True,'NO_NEW_MODEL_AUTHORITY'
    assert entry_check or not approval.get('synthetic_qualification_only',False),'SYNTHETIC_AUTH_NOT_PHYSICAL'
    assert approval.get('stop_on_safety_evidence')is True and approval.get('automatic_new24')is False,'AUTH_SCOPE'
    assert approval.get('allowed_task_ids')==[t['task_id']for t in read(C/'TASKS.json')],'AUTH_TASKS'
    assert type(approval.get('window_seconds'))in[int,float] and approval['window_seconds']==5400,'BOUNDED_AUTH_WINDOW'
    auth=read(O/'AUTHORIZATION.json')
    assert auth['scope']=='EW_slot17_main_repeat_only' and auth['window_seconds']==5400
    if not entry_check:assert window['absolute_deadline_unix']==auth['absolute_ceiling_unix'] and window['hard_stop_monotonic']==auth['monotonic_ceiling'],'ROOT_CHANGED'
    assert abs(window['absolute_deadline_unix']-window['started_unix']-approval['window_seconds'])<=1e-5
    assert abs(window['hard_stop_monotonic']-window['started_monotonic']-approval['window_seconds'])<=1e-5
    assert abs(approval['absolute_deadline_unix']-window['absolute_deadline_unix'])<=1e-8,'ROOT_DEADLINE_CHANGED'
    task_contract(task)
    assert remaining(window)>1700,'INSUFFICIENT_REMAINING_RESERVE'
    assert used()+256*1024**2<LIMIT,'TEMPORARY_STORAGE_LIMIT'
    frozen=read(C/'WORKER_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in frozen.items()),'WORKER_SOURCE_CHANGED'
    assert read(O/'GOAL_AUDIT_QUALIFICATION.json')['passed'] and read(O/'NATIVE_AUDIT_QUALIFICATION.json')['passed'],'AUDIT_GATES_REQUIRED'
    if not entry_check:assert read(O/'READY_FOR_REVIEW.json')['preparation_gates_passed'] and not (R/'REVIEW_PENDING').exists(),'REVIEW_OR_PREPARATION_HOLD'
    return True


def science():
    sys.path.insert(0,str(R/'experiments/v1180_fresh_recovery_chain'))
    import chain_tools as old
    return old
def configure_owner(output,end,window):
    old=science();owner=old.configure_owner(output,end)
    import budget
    budget.O=O;budget.RAW=RAW;budget.LIMIT=LIMIT;budget.used=used
    live=load('phase_v1264_live_owner',C/'ew_live.py')
    owner.execute=lambda *args:live.execute(*args,output=Path(output),remaining_fn=lambda:remaining(window))
    return owner
def factory():
    f=load('v1204_registered_scene',R/'experiments/v1067_causal_replan_brake_reserve/scene_binding.py');f.O=O;f.create=f.create_vehicle
    f.replay=load('v1204_original_exact_replay',R/'experiments/v882_runtime_evidence_repair/physical.py').replay
    return f
