"""Import readiness only; no torch network constructors, deserialize or forward."""
import os,sys,json,hashlib,importlib.metadata
from pathlib import Path
assert os.sched_getaffinity(0)=={2}and os.environ.get('CUDA_VISIBLE_DEVICES')==''
import torch,numpy,gymnasium
from stable_baselines3.sac.policies import SACPolicy
assert importlib.metadata.version('stable-baselines3')=='2.9.0'
files={}
for module in list(sys.modules.values()):
 p=getattr(module,'__file__',None)
 if p and Path(p).is_file()and '/site-packages/'in p:
  p=Path(p).resolve();files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
libs={}
for line in Path('/proc/self/maps').read_text().splitlines():
 parts=line.split();p=parts[-1]
 if p.startswith('/')and Path(p).is_file()and '.so'in p:
  p=Path(p).resolve()
  if str(p)not in libs:libs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
print(json.dumps(dict(passed=True,scope='IMPORT_READINESS_NO_NETWORK_CONSTRUCTOR',explicit_network_constructors=0,weight_deserializations=0,forward_calls=0,physics=0,replay=0,import_internal_registration_and_allocations=None,versions={n:importlib.metadata.version(n)for n in ['torch','numpy','gymnasium','stable-baselines3']},loaded_python_file_sha256=files,loaded_native_library_sha256=libs)))
