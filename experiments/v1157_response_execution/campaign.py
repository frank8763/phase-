"""Exactly one main and success-dependent repeat under one locked window."""
from response_tools import *
import fcntl
import gzip
import signal
import subprocess
import traceback
import numpy as np


def repeat_check(first,second):
    a,b=Path(first),Path(second)
    with np.load(a/'physics/NATIVE_TRACE.npz')as x,np.load(b/'physics/NATIVE_TRACE.npz')as y:
        keys=['qpos','qvel','ctrl','mocap_pos','mocap_quat','time']
        same=all(x[k].shape==y[k].shape for k in keys)
        error=max(float(abs(x[k]-y[k]).max()) if x[k].size else 0. for k in keys) if same else None
    identical={}
    for file in ['CONTACTS.json.gz','SENSORS.json.gz']:
        with gzip.open(a/'physics'/file,'rt')as x,gzip.open(b/'physics'/file,'rt')as y:identical[file]=json.load(x)==json.load(y)
    with np.load(a/'physics/INITIAL_STATE.npz')as x,np.load(b/'physics/INITIAL_STATE.npz')as y:
        initial_same=x['state'].shape==y['state'].shape and float(abs(x['state']-y['state']).max())<=1e-8
    model=sha(a/'physics/scene_model.mjb')==sha(b/'physics/scene_model.mjb')
    ra,rb=read(a/'RESULT.json'),read(b/'RESULT.json')
    functional=ra['passed'] is True and rb['passed'] is True and ra['capture_native']==rb['capture_native']
    return dict(passed=bool(same and error<=1e-8 and all(identical.values()) and initial_same and model and functional),
        same_complete_lengths=same,maximum_qpos_qvel_ctrl_mocap_error=error,contacts_and_sensors=identical,
        model_same=model,initial_same=bool(initial_same),same_capture_length_and_success=functional)


def known_sum(rows,key):
    return sum(r['result'][key]for r in rows) if all(r.get('result')and r['result'].get(key)is not None for r in rows) else None


def main():
    assert read(O/'APPROVAL.json')['models_authorized']is True and source_ok()
    assert not (O/'DRIVER_STARTED.json').exists() and not (O/'COMPLETION.json').exists()
    guard=(O/'GUARD.bin').read_bytes();assert hashlib.sha256(guard).hexdigest()==GUARD_SHA and sha(R/'REVIEW_PENDING')==GUARD_SHA
    lock=(O/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    dump(O/'DRIVER_STARTED.json',dict(pid=os.getpid(),proc_start=Path('/proc/self/stat').read_text().split()[21]))
    tasks=read(C/'TASKS.json');stages=[];child=None;error=None;pair=None;reason='FIXED_COMPONENT_QUEUE_COMPLETE';passed=False
    def stop():
        nonlocal child
        if child and child.poll()is None:
            try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
            except BaseException:
                try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
                except ProcessLookupError:pass
        child=None
    def halt(*_):raise TimeoutError('V1157_ABSOLUTE_ROOT_STOP')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt);signal.signal(signal.SIGALRM,halt)
    signal.setitimer(signal.ITIMER_REAL,max(.001,remaining()-5))
    def job(stage,script,args,seconds,physical=False):
        nonlocal child
        assert source_ok()and used()+128*1024**2<2*1024**3,'SOURCE_OR_STORAGE'
        assert remaining()>seconds+40,'INSUFFICIENT_ROOT_REMAINDER'
        assert (R/'REVIEW_PENDING').read_bytes()==guard
        command=[str(R/'run_phase.sh'),str((C/script).relative_to(R)),*map(str,args)] if physical else [sys.executable,'-B',str(C/script),*map(str,args)]
        if physical:(R/'REVIEW_PENDING').unlink()
        try:
            with (O/(stage+'.console')).open('x')as log:
                child=subprocess.Popen(command,cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                dump(O/'ACTIVE.json',dict(stage=stage,pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],physical=physical))
                return child.wait(timeout=min(seconds,remaining()-20))
        finally:stop();(R/'REVIEW_PENDING').write_bytes(guard)
    try:
        assert all(read(O/p)['passed']for p in ['QUALIFICATION.json','ISOLATED_QUALIFICATION.json','LAUNCH_QUALIFICATION.json'])
        for task in tasks:
            if remaining()<1000:reason='NO_TIME_FOR_COMPLETE_COMPONENT_AND_AUDIT';return
            row=dict(stage=task['task_id'],result=None,audit=None);stages.append(row)
            dump(O/'RESULTS.json',stages)
            code=job(task['task_id'],'worker.py',[C/('TASK_'+task['task_id']+'.json')],910,True)
            path=Path(task['output'])/'RESULT.json';row.update(returncode=code,result=read(path)if path.exists()else None);dump(O/'RESULTS.json',stages)
            if code!=0 or not row['result'] or row['result'].get('passed')is not True:
                reason='FIRST_PHYSICAL_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE';return
            acode=job(task['task_id']+'_audit','audit.py',[C/('TASK_'+task['task_id']+'.json')],130)
            path=Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json';row.update(audit_returncode=acode,audit=read(path)if path.exists()else None);dump(O/'RESULTS.json',stages)
            if acode!=0 or not row['audit']or row['audit']['passed']is not True:
                reason='INDEPENDENT_PHYSICAL_EVIDENCE_FAILURE';return
        pair=repeat_check(tasks[0]['output'],tasks[1]['output']);dump(O/'COMPLETE_REPEAT.json',pair)
        if not pair['passed']:reason='COMPLETE_REPEAT_MISMATCH';return
        passed=True
    except BaseException as exc:
        error=dict(error=repr(exc),traceback=traceback.format_exc());reason='EXCEPTION_OR_DEADLINE';dump(O/'ERROR.json',error)
        for row in stages:
            task=next(t for t in tasks if t['task_id']==row['stage']);path=Path(task['output'])/'RESULT.json'
            if row.get('result')is None and path.exists():row['result']=read(path)
    finally:
        stop();(R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0)
        counts={k:known_sum(stages,k)for k in ['models','new_actual_native','own_replay_native','analytical_cpp_native','analytical_python_native']}
        audits={k:sum(r['audit'][k]for r in stages if r.get('audit'))for k in ['analytical_cpp_native','analytical_python_native']}
        summary=dict(closed=True,passed=passed,stop_reason=reason,error=error,stages=stages,complete_repeat=pair,
            physical_counts=counts,independent_audit_analytical_counts=audits,
            unexecuted=[t['task_id']for t in tasks if t['task_id']not in [r['stage']for r in stages]],
            scope='fixed static changing-steering and capture response component only',
            original_goal_passed=False,same_version_three_routes_passed=False,new24_executed=False,new24_denominator=None,
            guard_original=sha(R/'REVIEW_PENDING')==GUARD_SHA,source_unchanged=source_ok(),
            absolute_deadline_unix=read(O/'ROUND_WINDOW.json')['absolute_deadline_unix'],closed_unix=time.time(),remote_verified=False)
        dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True))
        dump(O/'COMPLETION.json',summary);dump(O/'LEDGER.json',summary)
        report=R/'docs/RPCCR_CHANGING_STEERING_RESPONSE_V1157_REPORT.md'
        report.write_text('# V1157固定转向变化与前向捕获实际组件\n\n'+encode(summary)+'\n\n仅静态响应组件，不是完整动态恢复、三路线或24。旧V1155拟合拒绝和旧失败/截止保持。全部实际模型/回放run_phase隔离；必要原件远端SHA下载回读前保留。\n')
        current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',active_run=None,active_window=None,
            active_entrypoint=None,next_physical_authorized=False,latest_report=str(report.relative_to(R)),latest_v1157_response=summary)
        dump(R/'CURRENT_EXPERIMENT.json',current)
        with (R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V1157固定静态响应组件闭批：passed='+str(passed)+', reason='+reason+'；非动态整路/三路线/24，旧失败截止保持。docs/RPCCR_CHANGING_STEERING_RESPONSE_V1157_REPORT.md。\n')
        files=[]
        for root in [C,O,R/'runs/v858_nav2_verified/v1157']:
            if root.exists():
                for p in root.rglob('*'):
                    if p.is_file()and not p.is_symlink()and p.name not in ['campaign.console','watchdog.console','LOCAL_MANIFEST.json'] and '__pycache__'not in p.parts:
                        files.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
        files.append(dict(path=str(report.relative_to(R)),bytes=report.stat().st_size,sha256=sha(report)))
        dump(O/'LOCAL_MANIFEST.json',dict(files=files,local_readback=all(sha(R/p['path'])==p['sha256']for p in files),remote_verified=False,raw_retained=True))
        print(encode(summary))


if __name__=='__main__':main()
