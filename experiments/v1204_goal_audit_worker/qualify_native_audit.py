"""Real saved observer/native safety witness through the adapted native auditor."""
import fcntl
import json
from pathlib import Path
import signal
import sys
import time
import traceback
from qualify_goal_audit import R,C,O,q,np
import native_audit


def main():
    assert not (O/'NATIVE_AUDIT_QUALIFICATION.json').exists()
    assert json.loads((O/'GOAL_AUDIT_QUALIFICATION.json').read_text())['passed']
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    task=next(t for t in json.loads((R/'experiments/v1195_eight_gib_timed_refuge/TASKS.json').read_text())if t['task_id']=='recovery_main_slot01')
    parent=Path(task['output'])
    files={str(p.relative_to(R)):q.sha(p)for p in [C/'qualify_native_audit.py',C/'native_audit.py',C/'audit_goal.py',C/'PROTOCOL.md']}
    for p in parent.rglob('*'):
        if p.is_file() and p.suffix not in ['.mp4','.png']:files[str(p.relative_to(R))]=q.sha(p)
    for module in list(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name and Path(name).resolve().is_relative_to(R) and Path(name).suffix=='.py':
            p=Path(name).resolve();files[str(p.relative_to(R))]=q.sha(p)
    q.dump(C/'NATIVE_AUDIT_FREEZE.json',dict(files=files,task=task,wall_cap_s=180))
    started=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('NATIVE_SAVED_AUDIT180')));signal.alarm(180)
    error=None;answer=None
    try:answer=native_audit.audit(task,output_path=O/'SAVED_OBSERVER_NATIVE_AUDIT.json',legacy_observer_only=True)
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc(),incomplete_work='unknown')
    finally:
        signal.alarm(0)
        result=dict(closed=True,passed=error is None and answer is not None and answer['passed'],
            witness=answer,error=error,wall_s=time.monotonic()-started,
            source_unchanged=all(q.sha(R/p)==h for p,h in files.items()),
            models=0,new_mujoco_native=0,new_goal_physical_passed=False)
        q.dump(O/'NATIVE_AUDIT_QUALIFICATION.json',result);print(json.dumps(result))


if __name__=='__main__':main()
