"""One explicitly approved 90-minute component stage; first failure closes it."""
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
import traceback
from datetime import datetime,timedelta,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'runs/v951_component_output_entry';LOCAL=timezone(timedelta(hours=8))


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')


def main():
    approval=json.loads((OUT/'USER_ENTRY_APPROVAL.json').read_text())
    assert approval['answer']=='允许这一次输出接续，截止不变'and approval['models_authorized']is True
    assert json.loads((OUT/'ZERO_MODEL_QUALIFICATION.json').read_text())['passed']
    with(OUT/'CAMPAIGN_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),at=time.time()),f)
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    guard=(ROOT/'REVIEW_PENDING').read_bytes()
    assert hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    original=json.loads((ROOT/'runs/v950_steering_response/AUTHORIZATION.original.json').read_text())
    start=original['started_unix'];end=original['deadline_unix']
    assert time.time()<end-110,'ORIGINAL_WINDOW_EXPIRED'
    auth=dict(models_authorized=True,scope='18_FIXED_RESPONSES_THEN_ONE_HANDOFF_ONLY',
        started_unix=start,deadline_unix=end,started_local=datetime.fromtimestamp(start,LOCAL).isoformat(),
        deadline_local=datetime.fromtimestamp(end,LOCAL).isoformat(),
        source_freeze_sha256=sha(CODE/'SOURCE_FREEZE.json'),entry_approval_sha256=sha(OUT/'USER_ENTRY_APPROVAL.json'),one_output_exception=True,
        navigation_authorized=False,training_updates=0,real_robot=0)
    with(OUT/'AUTHORIZATION.json').open('x')as f:json.dump(auth,f,indent=2)
    (OUT/'REVIEW_PENDING.before').write_bytes(guard)
    from entry_authority import authorized
    authorized();rows=[json.loads((ROOT/'runs/v950_steering_response/ACCOUNTING_RECOVERED.json').read_text())];error=None;child=None;active_index=None
    assert rows[0]['passed']and rows[0]['actual_native']==420 and rows[0]['replay_native']==420
    def halted(*_):raise InterruptedError('CAMPAIGN_TERMINATED')
    signal.signal(signal.SIGTERM,halted)
    try:
        (ROOT/'REVIEW_PENDING').unlink()
        for index in range(1,19):
            assert time.time()<end-110,'INSUFFICIENT_ROOT_TIME'
            used=sum(p.stat().st_size for folder in [OUT,ROOT/'runs/v858_nav2_verified/v950']if folder.exists()for p in folder.rglob('*')if p.is_file())
            assert used<2*1024**3,'TEMPORARY_EVIDENCE_BUDGET'
            active_index=index
            dump(OUT/'ACTIVE.json',dict(index=index,deadline_unix=end,started_unix=time.time()))
            with(OUT/('case_%02d.console'%index)).open('x')as console:
                child=subprocess.Popen([str(ROOT/'run_phase.sh'),str((CODE/'worker.py').relative_to(ROOT)),str(index)],cwd=ROOT,
                    stdout=console,stderr=subprocess.STDOUT,start_new_session=True)
                dump(OUT/'CHILD.json',dict(pid=child.pid,index=index))
                child.wait(timeout=min(70. if index<18 else 100.,end-10-time.time()))
            task=json.loads((ROOT/'experiments/v950_steering_response/TASKS.json').read_text())[index]
            result=ROOT/task['output']/'QUALIFICATION.json'
            if result.is_file():
                item=json.loads(result.read_text());rows.append(item);dump(OUT/('CASE_%02d_RESULT.json'%index),item)
            assert child.returncode==0 and rows[-1]['passed'],'FIRST_COMPONENT_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE '+str(index)
            dump(OUT/'RESULTS.json',dict(rows=rows,models=len(rows)))
            child=None
    except BaseException as exception:error=dict(error=repr(exception),traceback=traceback.format_exc(),active_index=active_index)
    finally:
        if child is not None and child.poll()is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=3)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        (ROOT/'REVIEW_PENDING').write_bytes(guard)
        # Re-read only this registered case table; missing/partial work is UNKNOWN.
        results=[json.loads((ROOT/'runs/v950_steering_response/ACCOUNTING_RECOVERED.json').read_text())]+[json.loads(p.read_text())for p in sorted(OUT.glob('CASE_*_RESULT.json'))]
        claims=list(OUT.glob('CASE_*_CLAIM.json'))
        unknown=len(claims)+1!=len(results)
        def count(key):return None if unknown or any(r.get(key)is None for r in results)else sum(r[key]for r in results)
        result=dict(closed=True,passed=error is None and len(results)==19 and all(r['passed']for r in results),
            status='PASSED_COMPONENT_QUALIFICATION_ONLY'if error is None and len(results)==19 else'NOT_PASSED',
            error=error,rows=results,unexecuted_cases=18-len(claims),attempted_cases=1+len(claims),old_v950_metadata_failure_preserved=True,first_case_not_rerun=True,
            model_attempts=count('models_attempted'),actual_native=count('actual_native'),
            replay_native=count('replay_native'),private_native=0,navigation=0,new24=0,
            guard_restored=(ROOT/'REVIEW_PENDING').read_bytes()==guard,
            started_unix=start,deadline_unix=end,closed_unix=time.time(),
            next_full_route_authorized=False)
        dump(OUT/'COMPLETION.json',result)
        print(json.dumps({k:v for k,v in result.items()if k!='rows'}),flush=True)
    return 0 if result['passed']else 1


if __name__=='__main__':sys.exit(main())
