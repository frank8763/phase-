"""Fixed V830 saved inputs and public causal data; no models at import."""
import copy,hashlib,json,math,os,sys
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
repo=Path(os.environ.get('PHASE_REPO',Path(__file__).resolve().parents[2]));own=Path(__file__).parent
for name in ['runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1','runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','runtime/mk-mini/training/phase14_lidar_depth_nav/envs','experiments/v733_early_low_translation_scan','experiments/v753_coupled_progress_repaired','experiments/v834_timed_escape_development']:sys.path.insert(0,str(repo/name))
pair=repo/'runs/v830_ranked_return_development/main_slot01/paired';cell=pair/'geometry_memory';root=repo/'runs/v833_timed_escape_qualification'
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
 rows=[];seen=set()
 for rank,c in enumerate(entry['nominal']):
  z=np.load(cell/'nominal_forecasts'/c['nominal_saved_forecast']);gain=float(np.linalg.norm(z['initial_pose'][:2]-goal)-np.linalg.norm(z['poses'][-1,:2]-goal));key=tuple(c['first_command'])
  if gain<.02 or key in seen:continue
  seen.add(key);old=next(x for x in entry['old_attempts']if np.array_equal(x['first_command'],c['first_command']))
  rows.append(dict(rank=rank,command=c['first_command'],nominal_progress_m=gain,old=old))
 return rows
