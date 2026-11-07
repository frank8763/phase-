"""Fixed V830 saved inputs and public causal data; no models at import."""
import copy,hashlib,json,math,os,sys
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
repo=Path(os.environ.get('PHASE_REPO',Path(__file__).resolve().parents[2]));own=Path(__file__).parent
for name in ['runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1','runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','runtime/mk-mini/training/phase14_lidar_depth_nav/envs','experiments/v733_early_low_translation_scan','experiments/v753_coupled_progress_repaired','experiments/v839_reference_differential_development']:sys.path.insert(0,str(repo/name))
pair=repo/'runs/v830_ranked_return_development/main_slot01/paired';cell=pair/'geometry_memory';root=repo/'runs/v838_reference_differential_qualification'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 d=hashlib.sha256()
 with Path(p).open('rb')as f:
  for chunk in iter(lambda:f.read(4*1024**2),b''):d.update(chunk)
 return d.hexdigest()
def serial(x):
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 if isinstance(x,Path):return str(x)
 raise TypeError(type(x).__name__)
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,default=serial,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def poses(q):
 q=np.asarray(q);q=q.reshape(-1,q.shape[-1]);return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
def eligible(entry,goal):
 assert np.array_equal(goal,[4.,-2.])
 return entry['eligible']
