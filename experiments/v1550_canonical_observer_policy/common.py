"""Metadata-only source/byte utilities; CPU5, never model bootstrap."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
BASE=R/'runs/v1549_original_catalogue_gear_obligation/SOURCE_FREEZE.json'
read=lambda p:json.loads(p.read_text())
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as stream:
        for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    return h.hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def put(path,value,maximum=65536):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(raw)<=maximum
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_bytes(raw);temp.replace(path)
def bootstrap():
    assert sorted(os.sched_getaffinity(0))==[5]
    inherited=os.environ.get('MUJOCO_GL')
    os.environ.update(CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    os.sched_setscheduler(0,os.SCHED_IDLE,os.sched_param(0))
    assert os.getpriority(os.PRIO_PROCESS,0)==19
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''and os.environ.get('MUJOCO_GL')=='osmesa'
    assert all(os.environ.get(k)=='1'for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'])
    return dict(cpu=[5],nice=19,scheduler=os.sched_getscheduler(0),inherited_mujoco_gl=inherited,mujoco_gl=os.environ['MUJOCO_GL'],gpu_visible=os.environ['CUDA_VISIBLE_DEVICES'],backend_loaded=False,models=False)
def guard():return load('v1550_original_immutable_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
