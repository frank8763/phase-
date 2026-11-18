"""Explicit disabled-by-default worker context; no physical imports."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import os
import sys
import time

C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name;RAW=R/'runs/v858_nav2_verified/v1280'
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
    original=read(R/'experiments/v1275_time_window_fixed24/TASK_main_slot24.json')
    assert t['slot']==24 and t['case_id']=='EAST_WEST' and t['role']in['development_main','development_repeat']
    assert all(t[k]==original[k]for k in ['seed','phase','case_id','start_xy','start_yaw','goal_xy','native_limit','dynamic','historical_prefix_native','original_pool_task'])
    assert t['run_root']==str(O)and Path(t['output'])==RAW/t['task_id']and not RAW.is_symlink()and not Path(t['output']).is_symlink()
    return True
def used():return sum(p.stat().st_size for root in[O,RAW]for p in root.rglob('*')if p.is_file()and not p.is_symlink())
def envelope(task,approval,window,*,entry_check=False):
    assert approval.get('models_authorized')is True,'NO_NEW_MODEL_AUTHORITY'
    assert entry_check or not approval.get('synthetic_qualification_only',False),'SYNTHETIC_AUTH_NOT_PHYSICAL'
    assert approval.get('stop_on_safety_evidence')is True and approval.get('automatic_new24')is False,'AUTH_SCOPE'
    assert approval.get('allowed_task_ids')==[t['task_id']for t in read(C/'TASKS.json')],'AUTH_TASKS'
    assert approval.get('window_seconds')==5400,'BOUNDED_90MIN_WINDOW'
    auth=read(O/'AUTHORIZATION.json');assert auth['scope']=='slot24_clock_only_repeat_continuation'and auth['temporary_bytes']==LIMIT
    if not entry_check:assert auth['authorized']and window['absolute_deadline_unix']==auth['absolute_ceiling_unix']and window['hard_stop_monotonic']==auth['monotonic_ceiling'],'ROOT_CHANGED'
    assert abs(window['absolute_deadline_unix']-window['started_unix']-5400)<=1e-5 and abs(window['hard_stop_monotonic']-window['started_monotonic']-5400)<=1e-5
    assert window['absolute_deadline_unix']<=1794963600.,'NIGHT_09_CEILING'
    assert approval['absolute_deadline_unix']==window['absolute_deadline_unix'],'ROOT_DEADLINE_CHANGED'
    task_contract(task);assert remaining(window)>1700,'INSUFFICIENT_REMAINING_RESERVE'
    assert used()+256*1024**2<LIMIT,'TEMPORARY_STORAGE_LIMIT'
    assert source_ok(),'WORKER_SOURCE_CHANGED'
    assert read(O/'SAVED_STATE_QUALIFICATION.json')['passed'],'SAVED_STATE_REQUIRED'
    if not entry_check:assert read(O/'READY_FOR_REVIEW.json')['preparation_gates_passed']and not(R/'REVIEW_PENDING').exists(),'REVIEW_OR_PREPARATION_HOLD'
    return True
def source_ok():return all(sha(R/n)==h for n,h in read(C/'SOURCE_FREEZE.json')['files'].items())

def science():
    sys.path.insert(0,str(R/'experiments/v1180_fresh_recovery_chain'))
    import chain_tools as old
    return old
def configure_owner(output,end,window):
    old=science();old.configure_owner(output,end)
    import types,budget
    owner=types.ModuleType('phase_v1278_normal_owner');owner.__file__=str(C/'owner.py')
    exec(compile((C/'owner.py').read_text(),str(C/'owner.py'),'exec'),owner.__dict__)
    budget.O=O;budget.RAW=RAW;budget.LIMIT=LIMIT;budget.used=used
    dispatch=load('phase_v1278_unchanged_ew_dispatch',R/'experiments/v1275_time_window_fixed24/route_dispatch.py')
    live=dispatch.ew_executor()
    owner.execute=lambda *args:live.execute(*args,output=Path(output),remaining_fn=lambda:remaining(window))
    return owner

def factory():
    f=load('v1204_registered_scene',R/'experiments/v1067_causal_replan_brake_reserve/scene_binding.py');f.O=O;f.create=f.create_vehicle
    f.replay=load('v1204_original_exact_replay',R/'experiments/v882_runtime_evidence_repair/physical.py').replay
    return f
