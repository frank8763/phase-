"""Same low-order dynamics, new signed allocator, no reverse fit claimed."""
import importlib.util,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load('v1035_old_causal_predictor',R/'experiments/v1003_causal_recovery_execution/predictor.py');law=load('v1035_signed_allocator',C/'signed_control.py')
PARAMETERS=json.loads((R/'experiments/v1002_causal_response_predictor/PARAMETERS.json').read_text());virtual=old.virtual;virtual_rate=old.virtual_rate
class Predictor(old.Predictor):
 def __init__(self,setup,initial,parameters=PARAMETERS):
  super().__init__(setup,initial,parameters);previous=self.adapter;self.adapter=old.Metadata.make(law.Adapter,setup);self.adapter.last=previous.last.copy();self.adapter.integral=previous.integral;self.adapter.virtual_rate=previous.virtual_rate

def initial(packet):
 b=packet['body'];s=packet['steering'];memory=packet['controller_memory'];return dict(state=[*b[:4],0.,b[4],virtual(s['position']),virtual_rate(s['position'],s['velocity'])],last_ctrl=memory['last_ctrl'],integral=memory['integral'],virtual_rate=.6)
def public_setup(setup):return {name:setup[name]for name in ['known','limits','slew_per_second']}
def checks(states,controls,requests,packet,setup,goal,minimum,required):
 limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])*.01;upper=float(np.linalg.norm(states[-1,:2]-goal))+.08
 return dict(finite=bool(np.isfinite(states).all()and np.isfinite(controls).all()),full_states=len(states)==len(controls)+1==len(requests)+1,full_raw_geometry=minimum>=required,full_200_stop=bool((requests[-200:]==0).all()and abs(states[-50:,3:6]).max()<=.03 and abs(states[-50:,7]).max()<=.03),goal_upper=upper<=.45,speed_yaw=bool(abs(states[:,3]).max()<=.13 and abs(states[:,5]).max()<=.16 and abs(states[:,4]).max()<=.03),legal_ctrl=bool((controls>=limits[:,0]-1e-10).all()and(controls<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([packet['controller_memory']['last_ctrl'],controls]),axis=0))<=rates+1e-10).all())),upper
