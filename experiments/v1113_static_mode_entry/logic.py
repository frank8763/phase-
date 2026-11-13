"""Frozen profile and verdict, shared by preparation and live execution."""
import math,sys
import numpy as np
from common import R
sys.path.insert(0,str(R/'experiments/rpccr_execution_core'))
import kernel
from prediction import Predictor,initial
sys.path.insert(0,str(R/'experiments/v1108_parked_steering_handoff'))
from parked_control import Adapter
CAP=.42722137342572125
ERROR_LIMIT=np.array([.01,.008,.015])
def schedule(sign):
 assert sign in [-1,1]
 return [('initial_hold',2200,0.,0.,False),('park_first',300,0.,-sign*CAP,True),('full_hold',2200,0.,0.,False),('park_reverse',300,0.,sign*CAP,True),('restart',300,.08,sign*CAP,False),('final_stop',2200,0.,0.,False)]
def predict_profile(setup,packet,sign):
 p=Predictor(setup,initial(packet),kernel.PARAMETERS);p.adapter.__class__=Adapter
 states=[p.state.copy()];controls=[];requests=[];modes=[];targets=[];phases=[];memory=[]
 for name,n,v,target,parked in schedule(sign):
  begin=len(controls);p.adapter.parked_target=target if parked else None
  w=v*math.tan(target)/.6 if v else 0.
  for _ in range(n):
   memory.append(np.r_[p.adapter.last,p.adapter.integral])
   s,u=p.step(v,w,False);states.append(s);controls.append(u);requests.append([v,w,False]);modes.append(int(parked));targets.append(target)
  phases.append(dict(name=name,begin=begin,end=len(controls),target=target,parked=parked))
 return dict(states=np.array(states),controls=np.array(controls),requests=np.array(requests),modes=np.array(modes),targets=np.array(targets),memory=np.array(memory)),phases
def response_error(body,virtual_steering,expected):
 d=float(body[2]-expected[2]);return np.array([np.linalg.norm(np.asarray(body)[:2]-expected[:2]),abs(math.atan2(math.sin(d),math.cos(d))),abs(virtual_steering-expected[6])])
def response_passed(errors):
 errors=np.asarray(errors);return bool(np.isfinite(errors).all()and np.all(errors<=ERROR_LIMIT))
def measured_rest(body,enc):
 return bool(abs(body[3])<=.003 and abs(body[4])<=.003 and abs(np.asarray(enc)[2:]).max()<=.015)
def ready_to_drive(body,enc,target):
 return measured_rest(body,enc)and abs(kernel.virtual(enc[:2])-target)<=.005
