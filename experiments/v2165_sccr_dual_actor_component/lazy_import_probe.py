"""Distinct lazy-import observation before source freeze, no networks or forward."""
from common import *
import importlib.abc
assert os.sched_getaffinity(0)=={2}and os.environ.get('CUDA_VISIBLE_DEVICES')==''
class Ban(importlib.abc.MetaPathFinder):
 def find_spec(self,n,*_):
  if n.split('.')[0]in {'mujoco','jax','factory','vehicle','kernel','fast_predict','OpenGL','rclpy'}:raise AssertionError('LAZY_READINESS_NO_PLANT:'+n)
sys.meta_path.insert(0,Ban())
import torch._dynamo,torch.optim
from stable_baselines3.sac.policies import SACPolicy
files={}
for module in list(sys.modules.values()):
 p=getattr(module,'__file__',None)
 if p and '/site-packages/'in p and Path(p).is_file():p=Path(p).resolve();files[str(p)]=sha(p)
libs={}
for line in Path('/proc/self/maps').read_text().splitlines():
 p=line.split()[-1]
 if p.startswith('/')and '.so'in p and Path(p).is_file():
  p=Path(p).resolve()
  if str(p)not in libs:libs[str(p)]=sha(p)
print(json.dumps(dict(passed=True,lazy_torch_optimizer_imports_ready=True,explicit_network_constructors=0,weight_deserializations=0,forward_calls=0,physics=0,replay=0,imports_observed_before_network_authority=True,internal_import_allocations_unknown=True,loaded_python_file_sha256=files,loaded_native_library_sha256=libs)))
