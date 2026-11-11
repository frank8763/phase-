"""Single explicit binding of qualified analytical dynamics and original geometry."""
import hashlib,importlib.util,json,math,os,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1053_parked_refresh_handoff';HARD_END=1794400200.
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
# All generic names come from one qualified namespace in each fresh process.
sys.path.insert(0,str(R/'experiments/v1046_retreat_entry_timed_route'))
from whole_input import Predictor,PARAMETERS,initial,checks,public_setup
from fast_predict import Expander
from geometry_model import ref,REQUIRED,RHO
from timed_input import Geometry
law=load('v1050_signed_control',R/'experiments/v1035_signed_timed_input_source/signed_control.py')
virtual=load('v1050_original_virtual',R/'experiments/v1003_causal_recovery_execution/predictor.py').virtual
CAP=.42722137342572125;TARGETS=np.linspace(-CAP,CAP,5)
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def predict(setup,packet,actions,tail=True):
 p=Predictor(setup,initial(packet),PARAMETERS);states=[p.state.copy()];ctrl=[];requests=[];mem=[np.r_[p.adapter.last,p.adapter.integral]]
 for action in [*actions,*([dict(kind='wait',gear=0,target=0.,ticks=200)]if tail else[])]:
  v=(.08 if action['gear']>0 else-.03)if action['kind']=='move'else 0.;w=v*math.tan(action['target'])/.6
  for _ in range(action['ticks']):s,u=p.step(v,w,False);states.append(s);ctrl.append(u);requests.append([v,w,False]);mem.append(np.r_[p.adapter.last,p.adapter.integral])
 return np.asarray(states),np.asarray(ctrl),np.asarray(requests,float),np.asarray(mem)
def stop_witness(engine,geometry,state,memory,elapsed):
 s,u,m=engine.expand(state,memory,np.array([0.]),200,np.array([0.]));dense=np.vstack([state[None,:3],s[0,:,:3]]);low=geometry.clearances(dense,elapsed+np.arange(201),.005)
 return bool(low.min()>=REQUIRED and abs(s[0,:,3]).max()<=.13 and abs(s[0,:,4]).max()<=.03 and abs(s[0,:,5]).max()<=.16 and abs(s[0,-50:,3:6]).max()<=.03 and abs(s[0,-50:,7]).max()<=.03),float(low.min())
def pin_threads():
 cpu=2 if 2 in os.sched_getaffinity(0) else min(os.sched_getaffinity(0))
 for p in Path('/proc/self/task').iterdir():
  try:os.sched_setaffinity(int(p.name),{cpu})
  except ProcessLookupError:pass
 return cpu

def remaining_root():
 wall=HARD_END-time.time();p=O/'ROUND_WINDOW.json'
 if p.exists():wall=min(wall,json.loads(p.read_text())['hard_stop_monotonic']-time.monotonic())
 return wall

# Legacy dependencies prepend their own paths; relay entry names must resolve
# to this canonical directory after all shared analytical bindings complete.
sys.path.insert(0,str(C))
