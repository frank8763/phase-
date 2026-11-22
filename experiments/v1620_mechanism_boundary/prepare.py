"""One task/authority preregistration, before any model outcome is inspected."""
import ast
import fcntl
import hashlib
import json
import time
from spec import C, O, R, STOP, encoded, manifest


def main():
    assert time.time()+120 < STOP
    parent = json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
    assert parent['active_round'] is None and not parent['models_now_authorized']
    assert hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest() == \
        '4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    with (R/'runs/v648_static_unknown/execution.lock').open() as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        tasks = manifest()
        assert tasks['task_count'] == 12 and tasks['assignment_count'] == 20
        sources = {}
        for p in C.iterdir():
            if p.is_file():
                if p.suffix == '.py':
                    ast.parse(p.read_text())
                sources[str(p.relative_to(R))] = hashlib.sha256(p.read_bytes()).hexdigest()
        with (O/'PREREGISTRATION.json').open('xb') as f:
            f.write(encoded(dict(user_instruction='抓紧解决机制收益与新任务边界，开始',
                recorded_unix=time.time(),weekend_restarted=False, old_automation_restored=False,
                models_authorized=False, science12_old_ledger_unchanged=True,
                root_stop_unix=STOP, maximum_root_seconds=28800,
                source_files=sources, task_manifest_sha256=hashlib.sha256(encoded(tasks)).hexdigest())))
        with (O/'TASKS_LOCKED.json').open('xb') as f:
            f.write(encoded(tasks))
    print(json.dumps(dict(preregistered=True,tasks=12,assignments=20,
                         models=0,physical_native=0,numeric_admission=False)))


if __name__ == '__main__':
    main()
