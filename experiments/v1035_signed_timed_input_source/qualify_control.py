"""Signed source qualification with no vehicle models or fitted new parameters."""
import importlib.abc,json,sys,math,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1035_signed_timed_input_source'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from whole_input import Predictor,PARAMETERS,old
from fast_predict import Expander
setup=json.loads((R/'records/nav2_v1022_20261111/NS_SOURCE_FIXTURE.json').read_text())['setup'];origin=dict(state=[-1.6,4.,-math.pi/2,0.,0.,0.,0.,0.],last_ctrl=[0.]*4,integral=0.,virtual_rate=.6);fast=Expander(setup);maximum=0.;forward_max=0.;steps=0;rows=[]
for speed in [.03,.08,-.03,-.08]:
 for target in [-.42722137342572125,0.,.42722137342572125]:
  p=Predictor(setup,origin,PARAMETERS);previous=old.Predictor(setup,origin,PARAMETERS)if speed>0 else None;state=p.state.copy();memory=np.zeros(5)
  for v,t,n in [(speed,target,300),(0.,0.,200)]:
   ss,uu,mm=fast.expand(state,memory,np.array([t]),n,np.array([v]));states=[];ctrl=[]
   for _ in range(n):
    w=v*math.tan(t)/.6;s,u=p.step(v,w,False);states.append(s);ctrl.append(u)
    if previous is not None:so,uo=previous.step(v,w,False);forward_max=max(forward_max,float(abs(so-s).max()),float(abs(uo-u).max()))
   maximum=max(maximum,float(abs(ss[0]-states).max()),float(abs(uu[0]-ctrl).max()),float(abs(mm[0]-np.r_[p.adapter.last,p.adapter.integral]).max()));state=ss[0,-1];memory=mm[0];steps+=n
  assert abs(p.state[3:6]).max()<=.03 and abs(p.state[7])<=.03;rows.append(dict(speed=speed,target=t,complete_200_stop=True))
assert maximum<=1e-10 and forward_max==0.,(maximum,forward_max)
# Premature direction changes must fail before emitting a new control.
negative=[]
for speed in [.08,-.08]:
 p=Predictor(setup,origin,PARAMETERS)
 for _ in range(30):p.step(speed,0.,False)
 try:p.step(-speed,0.,False)
 except AssertionError:negative.append('premature_flip_'+str(speed))
 else:raise AssertionError('PREMATURE_FLIP_ACCEPTED')
p=Predictor(setup,origin,PARAMETERS)
for speed in [.08,-.08,.08]:
 for _ in range(300):p.step(speed,0.,False)
 for _ in range(200):p.step(0.,0.,False)
assert p.state[3]>=0 and abs(p.state[3:6]).max()<=.03
result=dict(passed=True,models=0,integrations=0,analytical_steps_compared=steps,maximum_cpp_python_error=maximum,maximum_original_forward_difference=forward_max,full_200_brake_in_both_gears=True,complete_forward_reverse_forward_source=True,rejected_negative_cases=negative,reverse_physical_response_qualified=False,physical_ready=False)
(O/'CONTROL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
