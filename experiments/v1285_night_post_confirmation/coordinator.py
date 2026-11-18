"""Offline bounded coordinator. Only its own worker can be stopped."""
from pathlib import Path
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
P=R/'runs/v1281_partial_reconnection_fixed24'
GUARD='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
def rd(p):return json.loads(Path(p).read_text())
def dump(p,x):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def alive(receipt):
    try:
        s=Path('/proc',str(receipt['pid']),'stat').read_text().split()
        return s[2]!='Z'and s[21]==str(receipt['proc_start'])
    except FileNotFoundError:return False
def remaining(w,now=None,mono=None,boot=None):
    assert (boot or Path('/proc/sys/kernel/random/boot_id').read_text().strip())==w['boot_id'],'WRONG_BOOT_NO_RESUME'
    return min(w['absolute_deadline_unix']-(time.time()if now is None else now),w['hard_stop_monotonic']-(time.monotonic()if mono is None else mono))
def parent_ready(d,f):
    return bool(d.get('closed')and d.get('source_unchanged')and d.get('guard_original')and
        f.get('closed')and f.get('source_unchanged')and f.get('manifest_readback')and f.get('guard_original'))
def lock_idle():
    with(R/'runs/v648_static_unknown/execution.lock').open('a+')as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
def stop_owned(child):
    if child is None or child.poll()is not None:return
    try:
        os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
    except ProcessLookupError:pass
def source_ok():return all(sha(R/n)==h for n,h in rd(C/'SOURCE_FREEZE.json')['files'].items())
def finalize(reason,error,summary,restored):
    closed=dict(closed=True,reason=reason,error=error,software_passed=bool(summary and summary.get('passed')),
        parent_confirmation_passed=bool(summary and summary.get('parent_confirmation_passed')),
        models=0,physical_native=0,training_updates=0,software=summary,guard_restored=restored,
        source_unchanged=source_ok(),no_restart=True,closed_unix=time.time())
    dump(O/'COMPLETION.json',closed);dump(O/'LEDGER.json',closed)
    a=rd(O/'AUTHORIZATION.json');a.update(authorized=False,closed=True);dump(O/'AUTHORIZATION_CLOSED.json',a)
    report=R/'docs/RPCCR_OVERNIGHT_EVIDENCE_V1285_REPORT.md'
    report.write_text('# V1285 夜间保存证据与加速实验\n\n'+
        '硬截止2026-11-18 09:00+08；V1281原模型窗口不变，0新模型/实际积分/训练。\n\n'+
        '结论：`'+json.dumps(closed,ensure_ascii=False)+'`。\n\n'+
        '多核测量仅为三条独立保存轨迹的公共原生安全审核吞吐量；不代表完整路线审核或单导航实时性能。'+
        '时间消融仅为已暴露课程的保存态机制核验，不是新车辆成功率或泛化证据。父失败原结论保持。'+
        '必要证据未经远端下载SHA回读不删除，本夜不自动push。\n')
    current=rd(R/'CURRENT_EXPERIMENT.json')
    if current.get('active_run')in[None,str(O.relative_to(R))]:
        current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,
            next_physical_authorized=False,active_zero_model_diagnostic=None,pending_zero_model_relay=None,
            latest_v1285={k:closed[k]for k in['closed','reason','software_passed','parent_confirmation_passed','models','physical_native']})
        dump(R/'CURRENT_EXPERIMENT.json',current)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V1285夜间零模型接力闭批：'+reason+'；软件通过='+str(closed['software_passed'])+'，父确认通过='+str(closed['parent_confirmation_passed'])+'；0新模型/实际积分/训练。报告'+str(report.relative_to(R))+'。\n')
    files={str(p.relative_to(R)):dict(sha256=sha(p),bytes=p.stat().st_size)for root in[C,O]for p in root.rglob('*')
        if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.suffix!='.console'and p.name not in['LOCAL_MANIFEST.json','FINALIZED.json']}
    files[str(report.relative_to(R))]=dict(sha256=sha(report),bytes=report.stat().st_size)
    dump(O/'LOCAL_MANIFEST.json',dict(files=files,raw_parent_retained=True,remote_verified=False))
    assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in files.items())
    dump(O/'FINALIZED.json',dict(closed=True,manifest_readback=True,files=len(files),bytes=sum(v['bytes']for v in files.values()),software_passed=closed['software_passed'],models=0,physical_native=0))
def main():
    assert not(O/'STARTED.json').exists(),'ONE_NIGHT_NO_RESTART'
    own=(O/'coordinator.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
    w=rd(O/'ROUND_WINDOW.json');assert remaining(w)>60 and source_ok()
    dump(O/'STARTED.json',dict(pid=os.getpid(),proc_start=Path('/proc/self/stat').read_text().split()[21],models=0))
    launch=rd(P/'LAUNCH_RECEIPT.json');watch=rd(P/'WATCHDOG_LAUNCH.json');pw=rd(P/'ROUND_WINDOW.json')
    child=None;guard=None;error=None;summary=None;reason='UNKNOWN';restored=None
    def halt(*_):raise TimeoutError('NIGHT_ROOT_HARD_STOP')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt)
    signal.setitimer(signal.ITIMER_REAL,max(.1,remaining(w)-15))
    try:
        dump(O/'PROGRESS.json',dict(stage='WAITING_FOR_V1281_CLOSE',models=0,physical_native=0))
        while True:
            assert remaining(w)>60,'NIGHT_ROOT_EXPIRED'
            if(P/'FINALIZED.json').exists()and not alive(launch)and not alive(watch):break
            if time.time()>pw['absolute_deadline_unix']+360 or time.monotonic()>pw['hard_stop_monotonic']+360:
                raise RuntimeError('PARENT_NOT_FINALIZED_WITHIN_ORIGINAL_ROOT_AND_GRACE_NO_RESTART')
            if not alive(launch)and not alive(watch)and not(P/'FINALIZED.json').exists():
                raise RuntimeError('PARENT_CLOSED_WITHOUT_FINAL_ARCHIVE_NO_PROPAGATION')
            time.sleep(5)
        d=rd(P/'COMPLETION.json');f=rd(P/'FINALIZED.json')
        assert parent_ready(d,f),'PARENT_ARCHIVE_OR_SOURCE_GATE_FAILED_NO_PROPAGATION'
        assert source_ok(),'NIGHT_FROZEN_SOURCE_CHANGED'
        assert sha(R/'REVIEW_PENDING')==GUARD,'GUARD_NOT_CANONICAL'
        current=rd(R/'CURRENT_EXPERIMENT.json');assert current.get('active_run')is None,'OTHER_PHASE_RUN_NO_CONCURRENCY'
        lock_idle();guard=(R/'REVIEW_PENDING').read_bytes();(O/'GUARD.bin').write_bytes(guard)
        current.update(status='RUNNING_V1285_ZERO_MODEL_SAVED_EVIDENCE',active_run=str(O.relative_to(R)),
            active_entrypoint=str((C/'worker.py').relative_to(R)),active_window=str((O/'ROUND_WINDOW.json').relative_to(R)),
            active_zero_model_diagnostic=str(O.relative_to(R)),next_physical_authorized=False)
        dump(R/'CURRENT_EXPERIMENT.json',current)
        (R/'REVIEW_PENDING').unlink()
        with(O/'worker.console').open('x')as log:
            child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R))],cwd=R,
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        dump(O/'ACTIVE.json',dict(pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],models=0,physical_native=0))
        rc=child.wait(timeout=max(1,remaining(w)-20));stop_owned(child)
        summary=rd(O/'SOFTWARE_COMPLETION.json')if(O/'SOFTWARE_COMPLETION.json').exists()else None
        reason='SOFTWARE_FINITE_JOBS_COMPLETE'if rc==0 and summary and summary['passed']else'SOFTWARE_FAILED_NO_RETRY'
        if summary is None:summary=dict(passed=False,partial_counts_unknown=True,error='MISSING_SOFTWARE_COMPLETION',models=0,physical_native=0)
    except BaseException as exc:
        error=dict(error=repr(exc),traceback=traceback.format_exc());dump(O/'COORDINATOR_ERROR.json',error);reason='NIGHT_OPERATION_OR_DEADLINE_STOP_NO_RETRY'
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);stop_owned(child)
        if guard is not None:
            lock_idle();(R/'REVIEW_PENDING').write_bytes(guard);restored=sha(R/'REVIEW_PENDING')==GUARD
        if summary is None and(O/'SOFTWARE_COMPLETION.json').exists():summary=rd(O/'SOFTWARE_COMPLETION.json')
        finalize(reason,error,summary,restored)
    return 0 if reason=='SOFTWARE_FINITE_JOBS_COMPLETE'else 1
if __name__=='__main__':sys.exit(main())
