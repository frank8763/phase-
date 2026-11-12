"""V1084 geometric pursuit on a newly generated live causal complete reference.
No saved trace, command log or previous sensory packet is read by this module.
"""
import math,copy,time,importlib.util
from pathlib import Path
import numpy as np
from prediction import Predictor,initial
from kernel import PARAMETERS,Geometry,REQUIRED,checks,ref
from recovery_source import forecast_packet
R=Path(__file__).resolve().parents[2]
OFFSETS=(-.10,-.05,0.,.05,.10)
BLOCK=8;STOP=2200;MAX_ACTIVE=7000
PREDICTION_NATIVE=0

def engine(setup,packet):
 p=Predictor(setup,initial(packet),PARAMETERS)
 if packet.get('speed_episode',False):p.high_speed_episode=True;p.adapter._speed_episode=True
 return p

def advance(p,v,w,stale=False):
 global PREDICTION_NATIVE
 s,u=p.step(v,w,stale);PREDICTION_NATIVE+=1;return s,u

def forecast(template,p,ticks):
 x=forecast_packet(template,p.state,np.r_[p.adapter.last,p.adapter.integral],ticks)
 x['steering'].update(position=p.front.tolist(),velocity=p.front_rate.tolist());x['speed_episode']=bool(p.high_speed_episode)
 return x

def run_requests(setup,packet,rr):
 p=engine(setup,packet);ss=[p.state.copy()];uu=[]
 for r in rr:s,u=advance(p,*r);ss.append(s);uu.append(u)
 return np.array(ss),np.array(uu),p

class Reference:
 def __init__(self,states,requests,offset):
  assert offset in OFFSETS;moving=np.flatnonzero(abs(requests[:,0])>.005);assert len(moving)
  end=int(moving[-1])+1;path=states[:end+1,:3].copy();d=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(path[:,:2],axis=0),axis=1))];keep=np.r_[True,np.diff(d)>1e-8];original=np.flatnonzero(keep)
  path=path[keep];d=d[keep];path[:,0]+=offset*np.sin(np.pi*d/d[-1]);self.path=path;self.arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(path[:,:2],axis=0),axis=1))];self.offset=offset
  slow=np.flatnonzero((requests[:end,0]>.005)&(requests[:end,0]<=.03+1e-12));self.slow_index=int(np.searchsorted(original,slow[0]))if len(slow)else len(path)
 def request(self,body,progress):
  body=np.asarray(body,float);assert body.shape[0]>=3 and np.isfinite(body).all()and 0<=progress<len(self.path)
  start=max(0,int(progress)-2);end=min(len(self.path),int(progress)+81);idx=max(int(progress),start+int(np.argmin(np.linalg.norm(self.path[start:end,:2]-body[:2],axis=1))))
  if np.linalg.norm(body[:2]-self.path[-1,:2])<=.02:return np.zeros(3),len(self.path)-1,True
  carrot=min(int(np.searchsorted(self.arc,self.arc[idx]+.25)),len(self.path)-1);delta=self.path[carrot,:2]-body[:2];c=math.cos(body[2]);s=math.sin(body[2]);x=c*delta[0]+s*delta[1];y=-s*delta[0]+c*delta[1];d2=x*x+y*y;assert d2>1e-8 and x>-.02,'REFERENCE_TARGET_BEHIND';k=float(np.clip(2*y/d2,-math.tan(.42722137342572125)/.6,math.tan(.42722137342572125)/.6));v=.03 if idx>=self.slow_index else .125;return np.array([v,v*k,0.]),idx,False
 def complete(self,setup,packet,source,progress=0,budget=MAX_ACTIVE,geometry=True):
  assert source['source_native_tick']==source['periodic']['source_tick']<=packet['native_tick'];p=engine(setup,packet);ss=[p.state.copy()];uu=[];rr=[];ii=[];done=False;idx=progress
  for _ in range(budget):
   req,idx,done=self.request(p.state,idx)
   if done:break
   s,u=advance(p,*req);ss.append(s);uu.append(u);rr.append(req);ii.append(idx)
  assert done,'REFERENCE_ACTIVE_LIMIT';active=len(rr)
  for _ in range(STOP):s,u=advance(p,0.,0.);ss.append(s);uu.append(u);rr.append(np.zeros(3));ii.append(idx)
  ss=np.array(ss);uu=np.array(uu);rr=np.array(rr)
  if not geometry:return {},ss,uu,rr,np.array(ii)
  low=Geometry(setup['known'],source['periodic'],packet['sim_time']).complete(ss);cc,upper=checks(ss,uu,rr,packet,setup,np.array(setup['case']['goal_xy']),low,REQUIRED);a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[-1:,:3]);cc.update(terminal_full_cycle_hold=min(a[0],b[0])>=REQUIRED,complete2200stop=np.array_equal(rr[-STOP:],np.zeros((STOP,3))));cc={k:bool(v)for k,v in cc.items()}
  return dict(passed=all(cc.values()),checks=cc,minimum_raw_m=low,goal_upper_m=upper,active_native=active,offset_m=self.offset),ss,uu,rr,np.array(ii)

class ScenarioPlant(Predictor):
 """Fixed empirical one-step speed innovations; not a global error bound."""
 def step(self,v,w,stale=False):
  old=self.state.copy();state,u=super().step(v,w,stale)
  error=self.bias if abs(v)>.005 else math.copysign(min(abs(self.bias),.02*abs(state[3])),self.bias)
  nv=state[3]+error;nd=state[6];nr=state[7];mv=(old[3]+nv)/2;md=(old[6]+nd)/2
  da=self.p['gain_a']*mv*math.tan(md)/.6*.01+self.p['steering_rate_b']*(nd-old[6]);nw=self.p['gain_a']*nv*math.tan(nd)/.6+self.p['steering_rate_b']*nr;lc=self.p['lateral_discrete'];nl=lc[0]*nv*math.tan(nd)/.6+lc[1]*nr;ml=(old[4]+nl)/2;a=old[2]+da/2
  self.state=np.array([old[0]+.01*(mv*math.cos(a)-ml*math.sin(a)),old[1]+.01*(mv*math.sin(a)+ml*math.cos(a)),old[2]+da,nv,nl,nw,nd,nr]);return self.state.copy(),u

def scenario(reference,setup,packet,bias):
 p=ScenarioPlant(setup,initial(packet),PARAMETERS);p.bias=bias
 if packet.get('speed_episode',False):p.high_speed_episode=True;p.adapter._speed_episode=True
 ss=[p.state.copy()];uu=[];rr=[];n=0;idx=0;done=False;cross=0.
 while n<MAX_ACTIVE:
  state=forecast(packet,p,n);pred=engine(setup,state);commands=[];nextidx=idx
  for _ in range(BLOCK):
   request,nextidx,done=reference.request(pred.state,nextidx)
   if done:break
   advance(pred,*request);commands.append(request)
  if not commands:break
  for r in commands:
   q,u=advance(p,*r);ss.append(q);uu.append(u);rr.append(r);n+=1;cross=max(cross,float(np.linalg.norm(reference.path[:,:2]-q[:2],axis=1).min()))
  idx=nextidx
 assert done,'SCENARIO_ACTIVE_LIMIT'
 for _ in range(STOP):q,u=advance(p,0.,0.);ss.append(q);uu.append(u);rr.append(np.zeros(3))
 return np.array(ss),np.array(uu),np.array(rr),cross

def static_planner(output):
 name='fresh_live_static_topology';s=importlib.util.spec_from_file_location(name,R/'experiments/v1068_recovery_value_diagnosis/static_planner.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.O=Path(output);return m

def retime_requests(static):
 original=np.array(static['planned_body_requests']);parts=[];i=0
 while i<len(original):
  j=i+1
  while j<len(original)and np.array_equal(original[i],original[j]):j+=1
  row=original[i];block=original[i:j].copy()
  assert row[0]in [0.,.03,.08]and row[2]==0.,'FORWARD_REFERENCE_REQUIRED'
  if row[0]==.08:block=np.tile(row,(max(1,int(round(len(block)*.08/.125))),1));block[:,:2]*=.125/.08
  parts.append(block);i=j

 return np.vstack([*parts,np.zeros((2000,3))])

def produce(setup,packet,source,output,goal):
 # Input topology is reconstructed from THIS measured state, public map and
 # original goal. Actor geometry enters only the complete causal time gate.
 assert packet['dynamic_discovered']and source['source_native_tick']<=packet['native_tick']
 static=static_planner(output).construct(setup,packet,None,goal,wall_s=30.,max_expansions=5000)
 assert static['passed']and static['functional_goal_source'],'LIVE_COMPLETE_STATIC_REFERENCE_REQUIRED'
 rr=retime_requests(static);settled,_,p=run_requests(setup,packet,np.zeros((1001,3)));projected=forecast(packet,p,1001);nominal,controls,_=run_requests(setup,projected,rr);period=int(math.ceil(2*math.pi/.32/.01));rows=[];best=None
 for offset in OFFSETS:
  reference=Reference(nominal,rr,offset)
  try:
   _,ss,uu,requests,indices=reference.complete(setup,projected,source,geometry=False);scenarios=[ss]+[scenario(reference,setup,projected,bias)[0]for bias in [-.0012,.002]];g=Geometry(setup['known'],source['periodic'],projected['sim_time']);ticks=np.arange(len(ss))
   def robust(wait):return min(float(g.clearances(states[:,:3],np.arange(len(states))+wait,.005).min())for states in scenarios)
   bounds=[(robust(wait),wait)for wait in range(0,period,25)];low,wait=max(bounds)
   for k in range(max(0,wait-24),min(period,wait+25)):
    value=robust(k)
    if value>low:low,wait=value,k
   waits=np.zeros((1001+wait,3));prefix,pu,p=run_requests(setup,packet,waits);at=forecast(packet,p,len(waits));proof,ss,uu,requests,indices=reference.complete(setup,at,source);a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(prefix[:,:3]);hold=float(min(a.min(),b.min()));scenario_checks=[]
   for bias in [-.0012,.002]:
    qs,qu,qr,cross=scenario(reference,setup,at,bias);qlow=Geometry(setup['known'],source['periodic'],at['sim_time']).complete(qs);qc,qgoal=checks(qs,qu,qr,at,setup,np.array(goal),qlow,REQUIRED);scenario_checks.append(dict(bias=bias,passed=bool(all(qc.values())and cross<=.04),minimum_raw_m=qlow,goal_upper_m=qgoal,cross_m=cross))
   robust_low=min([proof['minimum_raw_m']]+[q['minimum_raw_m']for q in scenario_checks]);proof.update(initial_full_cycle_hold_m=hold,wait_native=len(waits),scenario_checks=scenario_checks,scenario_minimum_raw_m=robust_low);proof['passed']=bool(proof['passed']and hold>=REQUIRED and all(q['passed']for q in scenario_checks));rows.append(proof)
   if proof['passed']and(best is None or(proof['scenario_minimum_raw_m'],-abs(offset),-offset)>(best[0]['scenario_minimum_raw_m'],-abs(best[0]['offset_m']),-best[0]['offset_m'])):best=(proof,reference,waits,prefix,pu)
  except AssertionError as e:rows.append(dict(passed=False,offset_m=offset,error=str(e)))
 assert best is not None,('NO_LIVE_COMPLETE_DYNAMIC_REFERENCE',rows)
 proof,reference,waits,prefix,pu=best
 return dict(proof=proof,candidates=rows,static=static,nominal_states=nominal,nominal_requests=rr,reference=reference,wait_requests=waits,wait_states=prefix,wait_controls=pu)
