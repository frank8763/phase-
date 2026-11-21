"""Preparation route context. No production route admission exists yet."""
import json
from pathlib import Path
import time

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    path = Path(path)
    assert path.is_absolute() and path.is_relative_to(R / 'runs'), 'PREPARATION_WRITE_ESCAPE'
    def scalar(x):
        if hasattr(x, 'tolist'): return x.tolist()
        raise TypeError(type(x).__name__)
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=scalar) + '\n'
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(data); temporary.replace(path)


def remaining(window):
    assert read_boot() == window['boot_id'], 'BOOT_CHANGED'
    return min(window['absolute_deadline_unix'] - time.time(), window['hard_stop_monotonic'] - time.monotonic())


def read_boot():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def task_check(task):
    assert task['case_id'] == 'WEST_EAST' and task['seed'] == 10060001
    assert task['controller_plugin'] == 'RPP'
    assert task['nav2_params'] == str(R / 'experiments/v1370_overnight_controller_matrix/rpp_default_params.json')
    return True


def authorize(task, window):
    task_check(task)
    import importlib.util
    spec=importlib.util.spec_from_file_location('v1427_ros_route_admission',C/'budget.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.complete_admission();approval=read(O/'APPROVAL.json');parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
    assert approval['models_authorized']and parent['models_now_authorized']and approval['round_id']==parent['active_round']
    assert task in read(C/'TASKS.json')and window==read(O/'ROUND_WINDOW.json')
    module.clocks(window,parent,reserve_s=read(C/'LIMITS.json')['finalization_reserve_s'])
