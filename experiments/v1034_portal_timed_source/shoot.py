"""Deterministic input shooting using only public map/start/goal.

Fast numerical proposals always require whole original-Python reconstruction.
No model init, physical state write, or actuation authority.
"""
import math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1031_timed_causal_guidance'))
from fast_predict import Expander
from whole_input import Predictor,PARAMETERS
CAP=.42722137342572125

def expand(engine,state,memory,request,steps):
 v,w,_=request;target=0. if v==0 else math.atan(.6*w/v);states=[];ctrl=[]
 while steps:
  n=min(334,steps);ss,uu,mm=engine.expand(state,memory,np.array([target]),n,np.array([v]));states.append(ss[0]);ctrl.append(uu[0]);state=ss[0,-1];memory=mm[0];steps-=n
 return state,memory,np.concatenate(states),np.concatenate(ctrl)

def fast(engine,origin,parameters,speed=.03):
 state=np.asarray(origin['state'],float);memory=np.r_[origin['last_ctrl'],origin['integral']];states=[state[None,:]];controls=[];requests=[]
 for target,ticks in zip([0.,CAP,-CAP],parameters):
  ticks=int(round(ticks));assert 1<=ticks<=15000
  request=[speed,speed*math.tan(target)/.6,False];state,memory,ss,uu=expand(engine,state,memory,request,ticks);states.append(ss);controls.append(uu);requests.extend([request]*ticks)
 state,memory,ss,uu=expand(engine,state,memory,[0.,0.,False],200);states.append(ss);controls.append(uu);requests.extend([[0.,0.,False]]*200)
 return np.concatenate(states),np.concatenate(controls),np.asarray(requests,float),memory

def original(setup,origin,requests):
 p=Predictor(setup,origin,PARAMETERS);states=[p.state.copy()];controls=[]
 for request in requests:s,u=p.step(*request);states.append(s);controls.append(u)
 return np.asarray(states),np.asarray(controls),np.r_[p.adapter.last,p.adapter.integral]

def portal(setup,origin,pose):
 engine=Expander(setup);parameters=np.array([3800.,4900.,5900.]);history=[];target=np.asarray(pose,float)
 for iteration in range(16):
  ss,uu,rr,mm=fast(engine,origin,parameters);error=ss[-1,:3]-target;history.append(dict(iteration=iteration,parameters=parameters.tolist(),error=error.tolist()))
  if np.linalg.norm(error[:2])<=.001 and abs(error[2])<=.001:break
  columns=[]
  for axis in range(3):
   p=parameters.copy();p[axis]+=20;s=fast(engine,origin,p)[0];columns.append((s[-1,:3]-ss[-1,:3])/20)
  step=np.linalg.solve(np.asarray(columns).T,error);parameters=np.maximum(1.,parameters-np.clip(step,-1800.,1800.))
 else:return dict(passed=False,history=history)
 states,controls,memory=original(setup,origin,rr);error=states[-1,:3]-target
 return dict(passed=bool(np.linalg.norm(error[:2])<=.001 and abs(error[2])<=.001),parameters=parameters.tolist(),state_path=states,ctrl=controls,requests=rr,memory=memory,history=history,maximum_fast_python_state_error=float(abs(states-ss).max()),maximum_fast_python_ctrl_error=float(abs(controls-uu).max()))
