"""No-model qualification of the exact pending continuation namespace."""
import copy
import fcntl
import gzip
import importlib.abc
import json
from pathlib import Path
import subprocess
import sys
import time
import types
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('CONTINUATION_QUAL_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from worker_context import *


class BeforeStep(BaseException):pass


def main():
    assert not (O/'QUALIFICATION.json').exists()
    guard=(R/'REVIEW_PENDING').read_bytes()
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    frozen=read(C/'WORKER_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in frozen.items())
    parent=R/'runs/v858_nav2_verified/v1204/main_slot01';setup=read(parent/'physics/SETUP.json');packet=read(parent/'CANONICAL_INITIAL_PACKET.json')
    with gzip.open(parent/'physics/SENSORS.json.gz','rt')as f:scan=next(x for x in json.load(f)if x['native_tick']==0)
    window=read(R/'runs/v1204_goal_audit_worker/ROUND_WINDOW.json');assert remaining(window)>1700
    old=science();np=old.np;owner=configure_owner(O,time.time()+1000,window)
    first=[]
    class Interface:
        count=0;d=types.SimpleNamespace(time=packet['sim_time'])
        adapter=types.SimpleNamespace(last=np.asarray(packet['controller_memory']['last_ctrl']),integral=packet['controller_memory']['integral'])
        def body(self):return packet['body']
        def steering_sample(self):return np.asarray(packet['steering']['position']+packet['steering']['velocity'])
        def scan(self):return copy.deepcopy(scan)
        def step(self,*row):first.append(row);raise BeforeStep()
    output=O/'OWNER_PRE_STEP';output.mkdir()
    try:owner.navigate(Interface(),setup,read(C/'TASK_main_slot01.json'),time.time()+1000,output,{})
    except BeforeStep:pass
    else:raise AssertionError('CONTINUATION_OWNER_PRE_STEP_NOT_REACHED')
    assert len(first)==1
    plan=read(output/'00_STATIC_00_PLAN.json');assert plan['passed']and all(plan['checks'].values())
    fixture=O/'ENTRY_FIXTURES';fixture.mkdir()
    approval=dict(models_authorized=True,synthetic_qualification_only=True,stop_on_first_failure=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in read(C/'TASKS.json')],window_seconds=5400,absolute_deadline_unix=window['absolute_deadline_unix'])
    dump(fixture/'APPROVAL.json',approval);dump(fixture/'WINDOW.json',window)
    base=[str(R/'run_phase.sh'),str(C/'worker.py'),str(C/'TASK_main_slot01.json')]
    results=[]
    try:
        (R/'REVIEW_PENDING').unlink()
        for name,args,expected in [('blocked',base,2),('positive',base+['--entry-check','--approval',str(fixture/'APPROVAL.json'),'--window',str(fixture/'WINDOW.json')],0)]:
            fcntl.flock(lock,fcntl.LOCK_UN)
            try:p=subprocess.run(args,cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
            finally:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            assert p.returncode==expected,(name,p.stdout,p.stderr)
            data=json.loads(p.stdout.strip().splitlines()[-1]);assert data['models']==data['new_mujoco_native']==0 and data['physical_started']is False
            results.append(dict(case=name,returncode=p.returncode,receipt=data))
    finally:(R/'REVIEW_PENDING').write_bytes(guard)
    assert not RAW.exists() and read(O/'APPROVAL.json')['models_authorized']is False
    dump(O/'QUALIFICATION.json',dict(closed=True,passed=True,original_deadline_unix=window['absolute_deadline_unix'],first_request=first,
        real_owner_first_step_reached_without_execution=True,isolated_entries=results,
        source_unchanged=all(sha(R/p)==h for p,h in frozen.items()),
        guard_original=sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66',
        analytical_cpp_native=4405,analytical_python_native=len(plan['planned_body_requests']),models=0,new_mujoco_native=0,physical_authorized=False))
    dump(C/'ENTRY_QUALIFICATION_FREEZE.json',dict(files={str((C/'qualify_entry.py').relative_to(R)):sha(C/'qualify_entry.py')},scientific_source_frozen_unchanged=True))
    print('exact continuation namespace: owner first-step + blocked/isolated entries PASS; physical remains disabled')


if __name__=='__main__':main()
