"""Fixed speed-error feedback and source rejection checks, no MuJoCo imports."""
import sys,json,copy,math,importlib.abc
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1085_fresh_ns_validation'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));import live_reference as l
from kernel import PARAMETERS,Geometry,REQUIRED
from prediction import Predictor,initial
import numpy as np
x=json.loads((R/'records/nav2_v1076_20261112/ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());setup=x['setup'];setup['case']=dict(goal_xy=x['goal']);source=x['source'];root=x['packet'];proof=json.loads((O/'LIVE_REFERENCE_PROOF.json').read_text())['chosen'];static=l.static_planner(O).construct(setup,root,None,x['goal'],wall_s=30.,max_expansions=5000);assert static['passed'];rr=l.retime_requests(static);_,_,p=l.run_requests(setup,root,np.zeros((1001,3)));nominal,_,_=l.run_requests(setup,l.forecast(root,p,1001),rr);reference=l.Reference(nominal,rr,proof['offset_m']);waits=np.zeros((proof['wait_native'],3));wait_states,_,p=l.run_requests(setup,root,waits);start=l.forecast(root,p,len(waits))
class Proxy(Predictor):
 def step(self,v,w,stale=False):
  old=self.state.copy();s,u=super().step(v,w,stale);error=self.bias if abs(v)>.005 else math.copysign(min(abs(self.bias),.02*abs(s[3])),self.bias);nv=s[3]+error;nd=s[6];nr=s[7];mv=(old[3]+nv)/2;md=(old[6]+nd)/2;da=self.p['gain_a']*mv*math.tan(md)/.6*.01+self.p['steering_rate_b']*(nd-old[6]);nw=self.p['gain_a']*nv*math.tan(nd)/.6+self.p['steering_rate_b']*nr;lc=self.p['lateral_discrete'];nl=lc[0]*nv*math.tan(nd)/.6+lc[1]*nr;ml=(old[4]+nl)/2;a=old[2]+da/2;self.state=np.array([old[0]+.01*(mv*math.cos(a)-ml*math.sin(a)),old[1]+.01*(mv*math.sin(a)+ml*math.cos(a)),old[2]+da,nv,nl,nw,nd,nr]);return self.state.copy(),u
rows=[]
for name,bias in [('lag',-.0012),('boost',.002)]:
 plant=Proxy(setup,initial(start),PARAMETERS);plant.bias=bias;idx=0;n=0;next_check=0;allstates=[plant.state.copy()];maximum=np.zeros(3);cross=0.;checkpoint=[];done=False
 while n<l.MAX_ACTIVE:
  packet=l.forecast(start,plant,n)
  if n>=next_check:
   check,*_=reference.complete(setup,packet,source,idx,l.MAX_ACTIVE-n);checkpoint.append(check);next_check+=400
  pred=l.engine(setup,packet);requests=[];expected=[];nextidx=idx
  for j in range(l.BLOCK):
   r,nextidx,done=reference.request(pred.state,nextidx)
   if done:break
   s,u=pred.step(*r);requests.append(r);expected.append(s)
  if not requests:break
  for r,ss in zip(requests,expected):
   s,u=plant.step(*r);allstates.append(s);n+=1;angle=s[2]-ss[2];maximum=np.maximum(maximum,[np.linalg.norm(s[:2]-ss[:2]),abs(math.atan2(math.sin(angle),math.cos(angle))),abs(s[6]-ss[6])]);cross=max(cross,float(np.linalg.norm(reference.path[:,:2]-s[:2],axis=1).min()))
  idx=nextidx
 for _ in range(l.STOP):s,u=plant.step(0.,0.);allstates.append(s)
 full=np.array(allstates);low=Geometry(setup['known'],source['periodic'],start['sim_time']).complete(full);distance=float(np.linalg.norm(full[-1,:2]-x['goal']));passed=done and all(c['passed']for c in checkpoint)and low>=REQUIRED and distance<=.45 and np.all(maximum<=[.04,.035,.015])and cross<=.04 and abs(full[:,3]).max()<=.13+1e-10 and np.linalg.norm(full[-1,3:6])<=.03;rows.append(dict(name=name,passed=bool(passed),active_native=n,goal_m=distance,minimum_raw_m=low,maximum_local_tracking=maximum.tolist(),maximum_reference_cross_m=cross,checkpoints=len(checkpoint)))
negative=[]
for name,p in [('future_source',dict(source,source_native_tick=start['native_tick']+1)),('clock_mismatch',dict(source,source_native_tick=source['source_native_tick']+1))]:
 try:reference.complete(setup,start,p);negative.append(False)
 except AssertionError:negative.append(True)
try:reference.request([np.nan,0,0],0);negative.append(False)
except AssertionError:negative.append(True)
result=dict(passed=all(r['passed']for r in rows)and all(negative),cases=rows,negative_cases=negative,models=0,integrations=0,scope='Proxy feedback on observed input, no new physical navigation or global uncertainty guarantee');(O/'FEEDBACK_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);assert result['passed']
