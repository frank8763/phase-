"""Single-use, bounded and frozen, no MuJoCo initialization or integration."""
import datetime
import fcntl
import hashlib
import json
import os
import signal
import sys
import time
import traceback
from pathlib import Path
from joint_constructor import construct, write, REPO, PARENT

own = Path(__file__).parent
root = REPO / 'runs/v708_joint_field_qualification'
root.mkdir(exist_ok=False)
with (REPO / 'runs/v648_static_unknown/execution.lock').open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    start = time.time()
    window = dict(started_unix=start, absolute_deadline_unix=start + 1800, limit_s=1800, pid=os.getpid(), round_closed=False)
    write(root / 'ROUND_WINDOW.json', window)
    freeze = json.loads((own / 'SOURCE_FREEZE.json').read_text())
    def unchanged():
        assert all(hashlib.sha256((REPO / p).read_bytes()).hexdigest() == h for p, h in freeze['files'].items()), 'SOURCE_FREEZE_CHANGED'
    def deadline(*_): raise TimeoutError('V708_1800S_ABSOLUTE_DEADLINE')
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(1800)
    results = []
    try:
        unchanged()
        known = json.loads((PARENT / 'KNOWN_FIELD.json').read_text())
        cases = json.loads((PARENT / 'SCENE_CASES.json').read_text())
        for case in cases:
            write(root / 'ACTIVE.json', dict(case_id=case['id'], stage='PURE_GEOMETRY', started_unix=time.time()))
            results.append(construct(case, known, root / case['id']))
            write(root / 'RESULTS.json', results)
        unchanged()
        status = 'ALL_THREE_JOINT_GEOMETRY_CANDIDATES' if all(x['eligible'] for x in results) else 'JOINT_GEOMETRY_NOT_PASSED'
    except BaseException as error:
        status = 'STOPPED_EXCEPTION'
        write(root / 'ERROR.json', dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc()))
    finally:
        signal.alarm(0)
        window.update(round_closed=True, elapsed_s=time.time() - start, status=status)
        write(root / 'ROUND_WINDOW.json', window)
        write(root / 'COMPLETION.json', dict(status=status, results=results, round_closed=True, simulator_imported='mujoco' in sys.modules,
              initializations=0, navigation_integrations=0, private_integrations=0, replay_integrations=0, training_updates=0))
        write(root / 'ACTIVE.json', dict(completed=True, status=status))
        print(json.dumps(dict(status=status, elapsed_s=window['elapsed_s'], routes=[dict(case_id=x['case_id'], eligible=x['eligible']) for x in results])))
