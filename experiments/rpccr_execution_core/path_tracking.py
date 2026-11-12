"""Measured-pose pursuit plus finite causally checked smooth corridor variants.
No physical state writes or actor truth. Old source time is never refreshed.
"""
import math
from functools import lru_cache
from pathlib import Path
import numpy as np
from prediction import Predictor,initial
from kernel import PARAMETERS,Geometry,REQUIRED,checks,ref
R=Path(__file__).resolve().parents[2]
REFERENCE=R/'runs/v858_nav2_verified/v1083/main_saved_ns/PLAN.npz'
LOOKAHEAD=.25
ARRIVAL_TO_REFERENCE=.02
MAX_ACTIVE=2200
STOP_NATIVE=2200
BLOCK=8
OFFSETS=(-.10,-.05,0.,.05,.10)
PREDICTION_NATIVE=0

@lru_cache(maxsize=5)
def reference(offset=.10):
 assert offset in OFFSETS
 with np.load(REFERENCE)as z:
  rr=z['requests'];moving=np.flatnonzero(abs(rr[:,0])>.005);assert len(moving)>0
  path=np.asarray(z['states'][:int(moving[-1])+2,:3]).copy()
 distance=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(path[:,:2],axis=0),axis=1))]
 keep=np.r_[True,np.diff(distance)>1e-8];path=path[keep];distance=distance[keep]
 # Fixed world-axis variants are explicit candidates for this observed NS
 # component, not a changed map/start/goal or a general navigation guarantee.
 path[:,0]+=offset*np.sin(np.pi*distance/distance[-1])
 distance=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(path[:,:2],axis=0),axis=1))]
 path.setflags(write=False);distance.setflags(write=False);return path,distance

@lru_cache(maxsize=1)
def slow_index():
 with np.load(REFERENCE)as z:
  rr=z['requests'];s=z['states'];moving=np.flatnonzero(abs(rr[:,0])>.005);end=int(moving[-1])+1
  keep=np.r_[True,np.linalg.norm(np.diff(s[:end+1,:2],axis=0),axis=1)>1e-8]
  original=np.flatnonzero(keep);slow=int(np.flatnonzero((rr[:end,0]>.005)&(rr[:end,0]<=.03+1e-12))[0])
 return int(np.searchsorted(original,slow))

def request(body,path,distance,progress):
 body=np.asarray(body,float);assert body.shape[0]>=3 and np.isfinite(body).all()
 assert 0<=int(progress)<len(path)
 start=max(0,int(progress)-2);end=min(len(path),int(progress)+81)
 idx=max(int(progress),start+int(np.argmin(np.linalg.norm(path[start:end,:2]-body[:2],axis=1))))
 if np.linalg.norm(body[:2]-path[-1,:2])<=ARRIVAL_TO_REFERENCE:return np.zeros(3),len(path)-1,True
 carrot=min(int(np.searchsorted(distance,distance[idx]+LOOKAHEAD)),len(path)-1)
 delta=path[carrot,:2]-body[:2];c=math.cos(body[2]);s=math.sin(body[2]);local=np.array([c*delta[0]+s*delta[1],-s*delta[0]+c*delta[1]])
 d2=float(local@local);assert d2>1e-8 and local[0]>-.02,'REFERENCE_TARGET_BEHIND'
 k=float(np.clip(2*local[1]/d2,-math.tan(.42722137342572125)/.6,math.tan(.42722137342572125)/.6))
 speed=.03 if idx>=slow_index()else .125
 return np.array([speed,speed*k,0.]),idx,False

def complete_from_measurement(setup,packet,source,progress=0,active_budget=MAX_ACTIVE,offset=.10,stopping=False):
 global PREDICTION_NATIVE
 assert packet['native_tick']>=source['source_native_tick']==15290
 path,arc=reference(offset);p=Predictor(setup,initial(packet),PARAMETERS)
 if packet.get('speed_episode',False):p.high_speed_episode=True;p.adapter._speed_episode=True
 states=[p.state.copy()];controls=[];rr=[];idx=int(progress);steps=[];done=bool(stopping)
 if not stopping:
  for _ in range(active_budget):
   req,idx,done=request(p.state,path,arc,idx)
   if done:break
   s,u=p.step(*req);PREDICTION_NATIVE+=1;states.append(s);controls.append(u);rr.append(req);steps.append(idx)
  assert done,'PURSUIT_DID_NOT_REACH_REFERENCE_END'
 active=len(rr)
 for _ in range(STOP_NATIVE):
  s,u=p.step(0.,0.,False);PREDICTION_NATIVE+=1;states.append(s);controls.append(u);rr.append(np.zeros(3));steps.append(idx)
 ss=np.array(states);uu=np.array(controls);rr=np.array(rr)
 low=Geometry(setup['known'],source['periodic'],packet['sim_time']).complete(ss)
 cc,upper=checks(ss,uu,rr,packet,setup,np.array(setup['case']['goal_xy']),low,REQUIRED)
 a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[-1:,:3])
 cc.update(terminal_hold_full_cycle=min(a[0],b[0])>=REQUIRED,complete2200stop=np.array_equal(rr[-STOP_NATIVE:],np.zeros((STOP_NATIVE,3))))
 cc={k:bool(v)for k,v in cc.items()}
 return dict(passed=all(cc.values()),checks=cc,minimum_raw_m=low,goal_upper_m=upper,active_native=active,reference_progress_start=progress,reference_progress_end=idx,offset_m=offset,stopping=stopping),ss,uu,rr,np.array(steps)

def select_reference(setup,packet,source):
 candidates=[]
 for offset in OFFSETS:
  try:q,*_=complete_from_measurement(setup,packet,source,offset=offset);candidates.append(q)
  except AssertionError as e:candidates.append(dict(passed=False,offset_m=offset,error=str(e)))
 valid=[q for q in candidates if q['passed']];assert valid,'NO_COMPLETE_POSE_REFERENCE'
 chosen=max(valid,key=lambda q:(q['minimum_raw_m'],-abs(q['offset_m']),-q['offset_m']))
 return chosen['offset_m'],candidates
