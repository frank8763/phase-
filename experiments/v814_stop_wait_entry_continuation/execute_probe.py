"""Single physical launch with a fixed absolute cap and guard restoration."""
import fcntl, json, os, signal, subprocess, time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
auth=read(repo/'RPCCR_STOP_WAIT_AUTHORIZATION_20261105.json')
root=repo/'runs/v814_stop_wait_entry_continuation';ledger_path=repo/'RPCCR_STOP_WAIT_LEDGER_20261105.json'
assert not(root/'LAUNCH.json').exists() and not(root/'physical').exists()
assert read(repo/'runs/v813_certified_stop_wait_probe/pre_navigation/RESULT.json')['status']=='FIXED_STOP_WAIT_SAVED_INPUTS_EXACT'
assert read(root/'ZERO_MODEL_ENTRY_AUDIT.json')['status']=='FIELD_AND_TAIL_ENTRY_ZERO_MODEL_PASS'
assert (own/'INPUT_FREEZE.json').exists()
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
guard=repo/'REVIEW_PENDING';backup=root/'REVIEW_PENDING.before';backup.write_bytes(guard.read_bytes())
original=read(repo/'runs/v813_certified_stop_wait_probe/LAUNCH.json');start=original['started_unix'];deadline=original['absolute_deadline_unix']
assert deadline+620<auth['absolute_deadline_unix'],'INSUFFICIENT_REGISTERED_TIME'
ledger=read(ledger_path);assert ledger['physical_launches']==1 and not ledger.get('entry_continuation_started',False)
ledger.update(status='V814_SINGLE_INTERFACE_CONTINUATION_RUNNING',physical_launches=2,entry_continuation_started=True,physical_deadline_unix=deadline,active_simulation=True,master_pid=os.getpid())
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
(root/'LAUNCH.json').write_text(json.dumps(dict(started_unix=start,absolute_deadline_unix=deadline,overall_absolute_deadline_unix=auth['absolute_deadline_unix'],no_retries=True),indent=2)+'\n')
env=dict(os.environ,PHASE_STOP_WAIT_STARTED=str(start),PHASE_STOP_WAIT_DEADLINE=str(deadline),
         OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
         PHASE_PROPOSAL_MODEL=str(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json'))
child=None;code=None
try:
    guard.unlink()
    with(repo/'runs/v814_probe.console').open('x')as stream:
        child=subprocess.Popen([str(repo/'run_phase.sh'),str(own/'probe.py')],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:code=child.wait(timeout=max(1,deadline-time.time())+2)
        finally:
            if child.poll()is None:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=2)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
finally:
    guard.write_bytes(backup.read_bytes());ledger=read(ledger_path)
    ledger.update(status='PHYSICAL_CLOSED_NEEDS_SAVED_AUDIT',active_simulation=False,master_pid=None,probe_exit=code)
    if(root/'physical/COMPLETION.json').exists():
        completion=read(root/'physical/COMPLETION.json');ledger['physical_completion']=completion['status'];ledger['actual_accounts']=completion['counts']
    ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps(dict(child_exit=code,guard_restored=guard.read_bytes()==backup.read_bytes(),no_retry=True)))
raise SystemExit(code if code is not None else 1)
