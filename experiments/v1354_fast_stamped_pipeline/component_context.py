"""Bounded data-only authorization, paths, and source checks."""
import hashlib
import json
import math
from pathlib import Path
import time

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name
RAW = R / 'runs/v858_nav2_verified/v1354'


def read(p):
    return json.loads(Path(p).read_text())


def dump(p, x):
    def default(a):
        if hasattr(a, 'tolist'):
            return a.tolist()
        if hasattr(a, 'item'):
            return a.item()
        raise TypeError(type(a).__name__)
    p = Path(p)
    temporary = p.with_suffix(p.suffix + '.tmp')
    temporary.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False, default=default) + '\n')
    temporary.replace(p)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def remaining(window):
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip() == window['boot_id'], 'BOOT_CHANGED'
    return min(window['absolute_deadline_unix'] - time.time(), window['hard_stop_monotonic'] - time.monotonic())


def sources():
    return all(sha(R / p) == h for p, h in read(C / 'SOURCE_FREEZE.json')['files'].items())


def authorize(task, window):
    assert task in read(C / 'TASKS.json'), 'UNREGISTERED_TASK'
    assert window == read(O / 'ROUND_WINDOW.json'), 'WINDOW_CHANGED'
    assert read(O / 'APPROVAL.json')['models_authorized'] is True, 'NO_MODEL_AUTHORITY'
    assert window['absolute_deadline_unix']-window['started_unix']<=5400.001,'WINDOW_TOO_LONG'
    assert abs((window['hard_stop_monotonic']-window['started_monotonic'])-(window['absolute_deadline_unix']-window['started_unix']))<.001,'DUAL_CLOCK_CHANGED'
    assert remaining(window) > 1700, 'INSUFFICIENT_REMAINING_TIME'
    assert sources(), 'SOURCE_CHANGED'
    return True
