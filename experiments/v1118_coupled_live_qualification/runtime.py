"""Full measured-origin mode state and bounded suffix simulation, no physics."""
import sys,json,math,ctypes,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1118_coupled_live_qualification'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1117_fixed_tick_native_sqp'))
from bindings import Predictor as QualifiedPredictor,initial as qualified_initial,PARAMETERS,GAIN
import numpy as np

def initial(packet):
 x=qualified_initial(packet);x['steering_motion_active']=bool(packet.get('steering_motion_active',False));assert not x['steering_motion_active']or x['coupled_episode'],'ACTIVE_MODE_MISSING_EPISODE';return x

class Predictor(QualifiedPredictor):
 def __init__(self,setup,origin,parameters=PARAMETERS):
  super().__init__(setup,origin,parameters);self.adapter._steering_motion_active=bool(origin.get('steering_motion_active',False))

class Engine:
 def __init__(self,setup):
  self.setup=setup;self.native=0;self.calls=0;self.lib=ctypes.CDLL(str(O/'profile.so'));a=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');i=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS');self.lib.profile.argtypes=[a,a,a,a,i,i,ctypes.c_int,a,a,a,a,a];self.lib.profile.restype=ctypes.c_int;self.lib.profile_work.argtypes=[];self.lib.profile_work.restype=ctypes.c_int
 def simulate(self,origin,rows):
  assert rows and all(len(r)==4 and int(r[2])==r[2] and 0<r[2]<=12000 and r[3]in [0,1]for r in rows),'INVALID_SCHEDULE'
  n=sum(int(r[2])for r in rows);assert n<=40000,'SOURCE_NATIVE_CAP'
  state=np.asarray(origin['state'],float);mem=np.r_[origin['last_ctrl'],origin['integral']];assert state.shape==(8,)and mem.shape==(5,)and np.isfinite(state).all()and np.isfinite(mem).all()
  coupled=bool(origin.get('coupled_episode',False));active=bool(origin.get('steering_motion_active',False));assert not active or coupled,'ACTIVE_MODE_MISSING_EPISODE'
  p=PARAMETERS;params=np.array([p['gain_a'],p['steering_rate_b'],*p['steering_discrete'],*p['speed_discrete'],*p['lateral_discrete'],p['curvature_speed_coefficient'],GAIN,float(coupled),float(active)])
  tt=np.array([r[0]for r in rows]);vv=np.array([r[1]for r in rows]);nn=np.array([r[2]for r in rows],np.int32);mm=np.array([r[3]for r in rows],np.int32);ss=np.empty((n,8));uu=np.empty((n,4));limits=np.array(self.setup['limits'],float);rates=np.array(self.setup['slew_per_second'],float)
  code=self.lib.profile(state,mem,tt,vv,nn,mm,len(rows),limits,rates,params,ss,uu);work=int(self.lib.profile_work());self.native+=work;self.calls+=1;assert code==work==n,('COMPLETE_SUFFIX_CONTRACT',code,work,n)
  return np.vstack([state,ss]),uu

def remaining_rows(rows,offset):
 assert isinstance(offset,int)and 0<=offset<sum(r[2]for r in rows),'INVALID_SUFFIX_OFFSET'
 cursor=0;result=[]
 for target,speed,ticks,mode in rows:
  end=cursor+int(ticks)
  if offset<end:result.append((target,speed,end-max(offset,cursor),mode))
  cursor=end
 assert sum(r[2]for r in result)==cursor-offset;return result

def python_replay(setup,origin,rows):
 p=Predictor(setup,origin);ss=[p.state.copy()];uu=[];memory=[np.r_[p.adapter.last,p.adapter.integral]];episodes=[p.coupled_episode];active=[bool(getattr(p.adapter,'_steering_motion_active',False))]
 for target,speed,ticks,mode in rows:
  p.adapter.parked_target=target if mode else None;w=0. if mode or speed==0. else speed*math.tan(target)/.6
  for _ in range(ticks):
   s,u=p.step(speed,w,False);ss.append(s);uu.append(u);memory.append(np.r_[p.adapter.last,p.adapter.integral]);episodes.append(p.coupled_episode);active.append(bool(getattr(p.adapter,'_steering_motion_active',False)))
 return np.array(ss),np.array(uu),np.array(memory),np.array(episodes),np.array(active)
