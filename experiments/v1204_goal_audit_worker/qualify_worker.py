"""Real isolated zero-model worker-entry qualification; never authorizes physics."""
import ast
import copy
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback
from qualify_goal_audit import q,np
import worker_context as ctx
C,R,O=ctx.C,ctx.R,ctx.O


def main():
    assert not (O/'WORKER_QUALIFICATION.json').exists()
    assert ctx.read(O/'GOAL_AUDIT_QUALIFICATION.json')['passed'] and ctx.read(O/'NATIVE_AUDIT_QUALIFICATION.json')['passed']
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard=(R/'REVIEW_PENDING').read_bytes();assert q.sha(R/'REVIEW_PENDING')==q.GUARD
    assert ctx.read(O/'APPROVAL.json')['models_authorized']is False
    started=time.monotonic();error=None;negatives=[];processes=[];source_files={};guard_restored=False
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('WORKER_QUAL120')));signal.alarm(120)
    def trial(name,task,approval,window,reason):
        try:ctx.envelope(task,approval,window,entry_check=True)
        except AssertionError as exc:negatives.append(dict(case=name,rejected=True,reason=str(exc)));return
        raise AssertionError('WORKER_BAD_CONTEXT_ACCEPTED '+name)
    try:
        fixture=O/'ENTRY_FIXTURES';fixture.mkdir()
        tasks=ctx.read(C/'TASKS.json');task=tasks[0]
        now=time.time();mono=time.monotonic()
        window=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),started_unix=now,absolute_deadline_unix=now+3600,started_monotonic=mono,hard_stop_monotonic=mono+3600)
        approval=dict(models_authorized=True,synthetic_qualification_only=True,stop_on_first_failure=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in tasks],window_seconds=3600,absolute_deadline_unix=window['absolute_deadline_unix'])
        # Real owner assembly and lazy factory denial: no model imported/created.
        owner=ctx.configure_owner(O,time.time()+3600,window);assert callable(owner.execute)
        try:ctx.factory().create(Path(task['output'])/'physics',task)
        except AssertionError as exc:
            assert str(exc)=='PHYSICAL_MODELS_DISABLED_FOR_PREPARATION';negatives.append(dict(case='factory_no_authority',rejected=True,reason=str(exc)))
        else:raise AssertionError('FACTORY_AUTHORITY_BYPASSED')
        for p in C.glob('*.py'):ast.parse(p.read_text())
        source_files.update(ctx.read(R/'experiments/v1203_goal_entry_handoff/SOURCE_FREEZE.json')['files'])
        source_files.update(ctx.read(R/'experiments/v1203_goal_entry_handoff/LIVE_ENTRY_BINDING_FREEZE.json')['files'])
        for module in list(sys.modules.values()):
            name=getattr(module,'__file__',None)
            if name and Path(name).resolve().is_relative_to(R) and Path(name).suffix=='.py':
                p=Path(name).resolve();source_files[str(p.relative_to(R))]=q.sha(p)
        for p in [*C.glob('*.py'),C/'PROTOCOL.md',C/'TASKS.json',R/'run_phase.sh',R/'tools/isolate.py',R/'experiments/v1159_bounded_steering_load/PARAMETERS.json',R/'runs/v1159_bounded_steering_load/profile.so',R/'runs/v1122_cache_entry_relay/WEST_EAST_T0_METADATA.json']:
            source_files[str(p.relative_to(R))]=q.sha(p)
        ctx.dump(C/'WORKER_FREEZE.json',dict(files=source_files,models_authorized=False))
        assert ctx.envelope(task,approval,window,entry_check=True)
        for t in tasks:assert ctx.task_contract(t)
        for key,value in [('seed',99999999),('phase',0.),('native_limit',60001),('historical_prefix_native',1),('output',str(O/'wrong')),('scope','new24')]:
            one=dict(task,**{key:value});trial('task_'+key,one,approval,window,key)
        for key,value in [('models_authorized',False),('window_seconds',3600.),('automatic_new24',True),('stop_on_first_failure',False),('allowed_task_ids',[]),('absolute_deadline_unix',window['absolute_deadline_unix']+1)]:
            one=dict(approval,**{key:value});trial('auth_'+key,task,one,window,key)
        bad=dict(window,boot_id='wrong')
        trial('wrong_boot',task,approval,bad,'WRONG_BOOT')
        try:ctx.envelope(task,approval,window,entry_check=False)
        except AssertionError as exc:
            assert str(exc)=='SYNTHETIC_AUTH_NOT_PHYSICAL';negatives.append(dict(case='synthetic_not_physical',rejected=True,reason=str(exc)))
        else:raise AssertionError('SYNTHETIC_PHYSICAL_AUTH_ACCEPTED')
        ctx.dump(fixture/'APPROVAL.json',approval);ctx.dump(fixture/'WINDOW.json',window)
        task_path=C/'TASK_main_slot01.json'
        base=[str(R/'run_phase.sh'),str(C/'worker.py'),str(task_path)]
        def process(name,args,expected,reason=None):
            result=subprocess.run(args,cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
            assert result.returncode==expected,(name,result.returncode,result.stdout,result.stderr)
            item=dict(case=name,returncode=result.returncode,stdout=result.stdout[-2500:],stderr=result.stderr[-1000:])
            if reason:assert reason in result.stdout+result.stderr
            if name!='review_guard':
                data=json.loads(result.stdout.strip().splitlines()[-1]);assert data['models']==data['new_mujoco_native']==0 and data['physical_started']is False
                item['zero_models_verified']=True
            processes.append(item)
        process('review_guard',base,2,'PAUSED_PENDING_USER_REVIEW')
        # Only the blocked/entry-check branch can execute while review is lifted.
        # All scientific physical authority remains False in the actual root.
        (R/'REVIEW_PENDING').unlink()
        try:
            process('no_authority',base,2,'NO_NEW_MODEL_AUTHORITY')
            args=base+['--entry-check','--approval',str(fixture/'APPROVAL.json'),'--window',str(fixture/'WINDOW.json')]
            process('busy_lock',args,2,'EXECUTION_LOCK_BUSY')
            fcntl.flock(lock,fcntl.LOCK_UN)
            try:process('isolated_positive_entry',args,0)
            finally:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            expired=dict(window,started_unix=now-4000,absolute_deadline_unix=now-400,started_monotonic=mono-4000,hard_stop_monotonic=mono-400)
            expired_auth=dict(approval,absolute_deadline_unix=expired['absolute_deadline_unix'])
            ctx.dump(fixture/'EXPIRED_WINDOW.json',expired);ctx.dump(fixture/'EXPIRED_APPROVAL.json',expired_auth)
            process('expired',base+['--entry-check','--approval',str(fixture/'EXPIRED_APPROVAL.json'),'--window',str(fixture/'EXPIRED_WINDOW.json')],2,'INSUFFICIENT_REMAINING_RESERVE')
        finally:(R/'REVIEW_PENDING').write_bytes(guard)
        guard_restored=q.sha(R/'REVIEW_PENDING')==q.GUARD
        assert guard_restored and not ctx.RAW.exists()
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        if not (R/'REVIEW_PENDING').exists() or (R/'REVIEW_PENDING').read_bytes()!=guard:(R/'REVIEW_PENDING').write_bytes(guard)
        guard_restored=q.sha(R/'REVIEW_PENDING')==q.GUARD
        result=dict(closed=True,passed=error is None and len(processes)==5 and guard_restored,
            negatives=negatives,isolated_processes=processes,error=error,wall_s=time.monotonic()-started,
            source_unchanged=all(q.sha(R/p)==h for p,h in source_files.items()),
            guard_original=guard_restored,models=0,new_mujoco_native=0,analytical_cpp_native=0,analytical_python_native=0,
            physical_worker_started=False,actual_approval_disabled=ctx.read(O/'APPROVAL.json')['models_authorized']is False)
        ctx.dump(O/'WORKER_QUALIFICATION.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['negatives','isolated_processes']}))


if __name__=='__main__':main()
