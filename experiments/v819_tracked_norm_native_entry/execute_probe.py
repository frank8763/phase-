"""Exactly one native component launch with a fixed absolute wall cap."""
import fcntl,json,os,signal,subprocess,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;read=lambda p:json.loads(p.read_text())
launch=repo/'runs/v819_launch.json';assert not launch.exists() and not(repo/'runs/v819_tracked_norm_native_entry').exists()
assert read(repo/'runs/tracked_norm_20261105/V819_ZERO_MODEL_ENTRY_AUDIT.json')['status']=='ALL_REGISTERED_IMPORTS_AND_FIELDS_ZERO_MODEL_PASS'
auth=read(repo/'RPCCR_TRACKED_NORM_AUTHORIZATION_20261105.json');ledger_path=repo/'RPCCR_TRACKED_NORM_LEDGER_20261105.json';ledger=read(ledger_path)
assert ledger['candidates_started']==1 and ledger['component_started']and ledger['interface_repairs']==0
assert read(repo/'runs/v817_tracked_norm_qualification/ARCHIVE_VERIFIED.json')['status']=='ALL_STAGE_SOURCES_AND_DECOMPRESSED_SHA_VERIFIED'
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
guard=repo/'REVIEW_PENDING';backup=repo/'runs/v819_review_guard.before';backup.write_bytes(guard.read_bytes())
original=read(repo/'runs/v818_launch.json');started=original['started_unix'];deadline=original['absolute_deadline_unix'];assert deadline+600<auth['absolute_deadline_unix']
launch.write_text(json.dumps(dict(started_unix=started,absolute_deadline_unix=deadline,overall_absolute_deadline_unix=auth['absolute_deadline_unix'],pid=os.getpid(),no_scientific_retries=True),indent=2)+'\n')
ledger.update(status='V819_NATIVE_COMPONENT_SINGLE_ENTRY_CONTINUATION',interface_repairs=1,component_entry_continuation_started=True,active_simulation=True,master_pid=os.getpid(),component_deadline_unix=deadline,model_initializations=None)
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
env=dict(os.environ,PHASE_NORM_STARTED=str(started),PHASE_NORM_DEADLINE=str(deadline),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
child=None;code=None
try:
    guard.unlink()
    with(repo/'runs/v819_probe.console').open('x')as stream:
        child=subprocess.Popen([str(repo/'run_phase.sh'),str(own/'probe.py')],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:code=child.wait(timeout=max(1,deadline-time.time())+2)
        finally:
            if child.poll()is None:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=2)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
finally:
    guard.write_bytes(backup.read_bytes());ledger=read(ledger_path);ledger.update(status='V819_COMPONENT_CLOSED_NEEDS_AUDIT',active_simulation=False,master_pid=None,component_exit=code)
    cp=repo/'runs/v819_tracked_norm_native_entry/COMPLETION.json'
    if cp.exists():ledger.update(component_completion=read(cp)['status'],component_accounts=read(cp)['counts'])
    ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps(dict(child_exit=code,guard_restored=guard.read_bytes()==backup.read_bytes())))
raise SystemExit(code if code is not None else 1)
