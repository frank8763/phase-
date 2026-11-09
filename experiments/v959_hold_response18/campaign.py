"""Explicit user request: one new bounded original18 component attempt, no routes."""
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

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent;OUT=ROOT/'runs/v959_hold_response18'


def dump(p,value):p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    user=json.loads((OUT/'USER_INSTRUCTION.json').read_text());assert user['answer']=='保持轮角刹停，转向交接另验（推荐）'and user['models_authorized']is True
    assert json.loads((OUT/'ZERO_MODEL_QUALIFICATION.json').read_text())['passed']
    with(OUT/'CAMPAIGN_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),at=time.time()),f)
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    guard=(ROOT/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    start=time.time();end=start+5400.;tz=timezone(timedelta(hours=8))
    auth=dict(models_authorized=True,scope='V959_ORIGINAL18_HOLD_RESPONSE_ONLY',started_unix=start,deadline_unix=end,
        started_local=datetime.fromtimestamp(start,tz).isoformat(),deadline_local=datetime.fromtimestamp(end,tz).isoformat(),
        source_freeze_sha256=sha(CODE/'SOURCE_FREEZE.json'),user_instruction_sha256=sha(OUT/'USER_INSTRUCTION.json'),
        max_models=18,max_actual_native=7560,max_replay_native=7560,navigation_authorized=False,new24_authorized=False)
    with(OUT/'AUTHORIZATION.json').open('x')as f:json.dump(auth,f,indent=2)
    (OUT/'REVIEW_PENDING.before').write_bytes(guard)
    from authority import authorized
    child=None;error=None;active=None
    def halt(*_):raise InterruptedError('CAMPAIGN_TERMINATED')
    signal.signal(signal.SIGTERM,halt)
    try:
        authorized()
        (ROOT/'REVIEW_PENDING').unlink()
        for index in range(18):
            assert time.time()<end-110,'INSUFFICIENT_ROOT_TIME'
            used=sum(p.stat().st_size for folder in [OUT,ROOT/'runs/v858_nav2_verified/v956']if folder.exists()for p in folder.rglob('*')if p.is_file()and not p.is_symlink())
            assert used<2*1024**3,'TEMPORARY_EVIDENCE_BUDGET'
            active=index;dump(OUT/'ACTIVE.json',dict(index=index,deadline_unix=end,started_unix=time.time()))
            console=OUT/('case_%02d.console'%index)
            with console.open('x')as stream:
                child=subprocess.Popen([str(ROOT/'run_phase.sh'),str((CODE/'worker.py').relative_to(ROOT)),str(index)],cwd=ROOT,
                    stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                child.wait(timeout=min(70.,end-10-time.time()))
            sys.path.insert(0,str(ROOT/'experiments/v953_stop_align_components'))
            from result_contract import read_parent
            task=json.loads((CODE/'TASKS.json').read_text())[index];item=read_parent(console,ROOT/task['output'])
            assert item['index']==index,'WRONG_RESULT_INDEX'
            dump(OUT/('CASE_%02d_RESULT.json'%index),item)
            assert child.returncode==0 and item['passed'],'FIRST_COMPONENT_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE '+str(index)
            dump(OUT/'PROGRESS.json',dict(completed=index+1,passed=index+1,last_index=index));child=None
    except BaseException as exception:error=dict(error=repr(exception),traceback=traceback.format_exc(),active_index=active)
    finally:
        if child is not None and child.poll()is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=3)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        (ROOT/'REVIEW_PENDING').write_bytes(guard)
        rows=[json.loads(p.read_text())for p in sorted(OUT.glob('CASE_*_RESULT.json'))]
        claims=list(OUT.glob('CASE_*_CLAIM.json'));unknown=len(rows)!=len(claims)
        def count(key):return None if unknown or any(r.get(key)is None for r in rows)else sum(r[key]for r in rows)
        done=dict(closed=True,passed=error is None and len(rows)==18 and all(r['passed']for r in rows),error=error,rows=rows,
            status='PASSED_RESPONSE18_ONLY'if error is None and len(rows)==18 else'NOT_PASSED',attempted_cases=len(claims),
            unexecuted_cases=18-len(claims),model_attempts=count('models_attempted'),models_initialized=count('models_initialized'),
            actual_native=count('actual_native'),replay_native=count('replay_native'),private_native=0,navigation=0,new24=0,handoff=0,
            guard_restored=(ROOT/'REVIEW_PENDING').read_bytes()==guard,started_unix=start,deadline_unix=end,closed_unix=time.time())
        dump(OUT/'COMPLETION.json',done)
        (OUT/'AUTHORIZATION.before_close.json').write_bytes((OUT/'AUTHORIZATION.json').read_bytes())
        auth.update(models_authorized=False,closed=True,closed_unix=done['closed_unix']);dump(OUT/'AUTHORIZATION.json',auth)
        print(json.dumps({k:v for k,v in done.items()if k!='rows'}),flush=True)
    return 0 if done['passed']else 1


if __name__=='__main__':sys.exit(main())
