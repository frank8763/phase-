"""Explicit source-acquisition ROS fork. No actual or private launch contract."""
import json
import os
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(Path(p).read_text())


def dump(path,value):
    path=Path(path)
    assert path.is_absolute()and path.is_relative_to(R/'runs')and path.resolve()==path
    data=(json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,
                     default=lambda v:v.tolist())+'\n').encode()
    assert len(data)<=4*1024**2,'SOURCE_EVENT_METADATA_CAP'
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    with temporary.open('xb')as stream:
        stream.write(data);stream.flush()
    descriptor=os.open(temporary,os.O_RDONLY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)
    temporary.replace(path)
    directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(directory)
    finally:os.close(directory)


def task_check(task):
    assert task['case_id']=='WEST_EAST'and task['seed']==10060001 and task['controller_plugin']=='RPP'
    assert task['nav2_params']==str(R/'experiments/v1370_overnight_controller_matrix/rpp_default_params.json')


def remaining(window):
    assert window['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    return min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())


def authorize(task,window):
    task_check(task)
    import importlib.util
    spec=importlib.util.spec_from_file_location('v1615_ROS_exact_scope',C/'lifecycle.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.authorize(task,window)


authorize_startup_close=authorize
