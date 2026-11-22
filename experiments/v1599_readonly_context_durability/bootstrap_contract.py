"""Original native environment and single-task factory approval, no models."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def environment(source):
    binding=json.loads((C/'MESA_BINDING.json').read_text())
    path=R/binding['original_environment_source']
    assert sha(path)==binding['original_environment_source_sha256']==source[str(path.relative_to(R))]
    real=R/binding['real_path'];assert real.is_file()and not real.is_symlink()
    assert real.stat().st_size==binding['real_bytes']and sha(real)==binding['real_sha256']==source[str(real.relative_to(R))]
    for name,target in binding['links'].items():
        link=R/name;assert link.is_symlink()and link.readlink().as_posix()==target and link.resolve()==real
    function=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='env')
    scope=dict(R=R,os=os)
    exec(compile(ast.Module(body=[function],type_ignores=[]),str(path),'exec'),scope)
    value=scope['env']()
    assert value['MUJOCO_GL']==value['PYOPENGL_PLATFORM']=='osmesa'
    assert value['LD_LIBRARY_PATH']==str(real.parent)and value['CUDA_VISIBLE_DEVICES']==''
    assert 'LD_PRELOAD'not in value
    assert all(value[k]=='1'for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'))
    return value


def factory_authority(authority,*,task,output):
    value=copy.deepcopy(authority);output=Path(output)
    assert output==O/'first_event'and Path(task['output'])==output
    assert value['scope']=='REVISION12_FIRST_GOAL_BOUND_SEGMENT_ACTUAL_RUNTIME'
    assert value['scientific_revision']==12 and value['physical_authorized']is value['models_authorized']is True
    assert value['whole_route_admission']is value['repeat_authorized']is False
    assert task['case_id']=='WEST_EAST'and task['seed']==10060001 and task['controller_plugin']=='RPP'
    assert time.time()<value['absolute_deadline_unix']<=1795395600
    assert 'allowed_task_ids'not in value
    value['allowed_task_ids']=[task['task_id']]
    return value
