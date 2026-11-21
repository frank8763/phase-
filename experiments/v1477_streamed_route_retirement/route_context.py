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


def authorize(task,window):
    task_check(task)
    import importlib.util
    spec=importlib.util.spec_from_file_location('v1477_ROS_live_event_scope',C/'contract.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.authorize(task,window,native=False)


def authorize_startup_close(task,window):
    """A finite no-input ROS standby qualification; never a vehicle authority."""
    task_check(task)
    parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');authority=read(O/'STARTUP_CLOSE_AUTHORITY.json')
    assert parent['active_round']is None and not parent['models_now_authorized']
    assert authority['models_authorized']is False and authority['scope']=='ZERO_MODEL_ACTUAL_ROS_START_CLOSE_QUALIFICATION'
    assert task==read(O/'STARTUP_CLOSE_TASK.json')and window==read(O/'STARTUP_CLOSE_WINDOW.json')
    assert Path(task['output']).is_relative_to(O)and Path(task['output']).name=='startup_close_task'
    original=read(C/'TASKS.json')[0];remap={'task_id','run_id','output','run_root','role','depends_on'}
    assert {k:v for k,v in task.items()if k not in remap}=={k:v for k,v in original.items()if k not in remap}
    assert window['boot_id']==parent['boot_id']==read_boot()
    assert 0<window['absolute_deadline_unix']-window['started_unix']<=60
    assert abs((window['hard_stop_monotonic']-window['started_monotonic'])-(window['absolute_deadline_unix']-window['started_unix']))<=1e-5
    assert window['absolute_deadline_unix']<=1795395600 and window['hard_stop_monotonic']<=parent['hard_stop_monotonic']and remaining(window)>10
    import hashlib
    assert authority['source_hashes']and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in authority['source_hashes'].items())
    assert not(O/'COMPLETE_INTEGRATED_ROUTE_QUALIFICATION.json').exists()
    return authority
