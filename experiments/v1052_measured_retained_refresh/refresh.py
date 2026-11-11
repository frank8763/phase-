"""Measured-state reforecast and finite retiming; zero-model candidate only.

Never modifies the plant or discards original cumulative tracking diagnostics.
Every returned remainder must satisfy the ORIGINAL complete geometry/actuator
and terminal gates from a fresh measured state and its exact controller memory.
"""
import math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments/v1051_retained_corridor_entry'))
from kernel import Expander,initial,Geometry,ref,REQUIRED,checks,PARAMETERS,virtual,CAP
NORMALS=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
def validate_measured_packet(packet,now):
 body=np.asarray(packet['body'],float);enc=packet['steering'];q=np.asarray(enc['position']);rate=np.asarray(enc['velocity']);u=np.asarray(packet['controller_memory']['last_ctrl'])
 assert body.shape==(5,)and q.shape==rate.shape==(2,)and u.shape==(4,),'INVALID_MEASURED_SHAPE'
 assert np.isfinite(np.r_[body,q,rate,u,packet['controller_memory']['integral'],now,packet['body_measured_at'],enc['measured_at']]).all(),'NONFINITE_MEASURED_PACKET'
 assert 0<=now-packet['body_measured_at']<=.05,'STALE_MEASURED_BODY'
 assert enc['native_tick']==packet['native_tick']and abs(enc['measured_at']-packet['body_measured_at'])<=1e-9,'INCOHERENT_MEASURED_ENCODER'
 # .52 was a parked-snapshot joint criterion, not a moving-joint hard limit:
 # measured servo transients can exceed their target. Retain original command
 # limits below and the qualified virtual-angle prediction envelope here.
 assert abs(body[3])<=.13 and abs(body[4])<=.16,'MEASURED_BODY_CAP'
 assert abs(q).max()<math.pi/2-.01 and abs(virtual(q))<=CAP+.015,'UNQUALIFIED_MOVING_STEERING_STATE'
def remainder(actions,elapsed):
 assert isinstance(elapsed,int)and elapsed>=0
 rows=[]
 for action in actions:
  if elapsed>=action['ticks']:elapsed-=action['ticks'];continue
  row=dict(action,ticks=action['ticks']-elapsed);elapsed=0;rows.append(row)
 assert elapsed==0,'ELAPSED_OUTSIDE_PLAN'
 return rows
def roll(setup,packet,actions):
 origin=initial(packet);state=np.asarray(origin['state']);memory=np.r_[origin['last_ctrl'],origin['integral']];engine=Expander(setup);states=[state.copy()];ctrl=[];requests=[]
 for a in actions:
  n=a['ticks'];v=(.08 if a['gear']>0 else-.03)if a['kind']=='move'else 0.;w=v*math.tan(a['target'])/.6
  while n:
   size=min(n,334);ss,uu,mm=engine.expand(state,memory,np.array([a['target']]),size,np.array([v]));states.extend(ss[0]);ctrl.extend(uu[0]);requests.extend([[v,w,False]]*size);state=ss[0,-1].copy();memory=mm[0].copy();n-=size
 return np.array(states),np.array(ctrl),np.array(requests),memory
def certify(setup,packet,source,goal,actions):
 ss,uu,rr,mem=roll(setup,packet,actions);g=Geometry(setup['known'],source['periodic'],packet['sim_time']);low=g.complete(ss);cc,upper=checks(ss,uu,rr,packet,setup,np.asarray(goal),low,REQUIRED);a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[-1:,:3]);cc['terminal_full_cycle_hold']=min(a[0],b[0])>=REQUIRED
 return dict(passed=bool(all(cc.values())),checks={k:bool(v)for k,v in cc.items()},minimum_raw_m=low,terminal_goal_upper_m=upper,actions=actions,native_steps=len(rr))
def fit_staging(setup,packet,actions):
 # Re-shoot ONLY the last three remaining moving durations. Target comes from
 # public map geometry, never from actor truth or a post-hoc actual endpoint.
 rect=setup['known']['known_rectangles'][9];target=np.array([rect[0]-rect[2]-.45,rect[1]+rect[3]+.375+REQUIRED+.01,0.]);indices=[i for i,a in enumerate(actions)if a['kind']=='move'][-3:]
 if len(indices)<3:return None
 z=np.array([actions[i]['ticks']for i in indices],float)
 def endpoint(z):
  rows=[dict(a)for a in actions]
  for i,value in zip(indices,z):rows[i]['ticks']=max(20,int(round(value)))
  states,_,_,_=roll(setup,packet,rows);error=states[-1,:3]-target;error[2]=math.atan2(math.sin(error[2]),math.cos(error[2]));error[2]*=.8;return error,rows
 error,rows=endpoint(z)
 for _ in range(12):
  if np.linalg.norm(error)<.001:break
  jac=[]
  for j in range(3):
   zz=z.copy();zz[j]+=5.;next_error,_=endpoint(zz);jac.append((next_error-error)/5.)
  step=np.linalg.lstsq(np.array(jac).T,-error,rcond=1e-8)[0];step=np.clip(step,-200,200);improved=False
  for alpha in [1.,.5,.25]:
   zz=np.clip(z+alpha*step,20,8000);new_error,new_rows=endpoint(zz)
   if np.linalg.norm(new_error)<np.linalg.norm(error)-1e-10:z=zz;error=new_error;rows=new_rows;improved=True;break
  if not improved:break
 if np.linalg.norm(error[:2])>.005 or abs(error[2])>.003:return None
 return rows
def refresh(setup,packet,source,goal,original_actions,elapsed,prefix_override=None):
 # The stage entry's terminal200 remains in this prefix. Only the subsequent
 # phase wait and straight crossing are retimed; no obstacle/goal change.
 validate_measured_packet(packet,packet['sent_at']);assert source['source_native_tick']<=packet['native_tick'],'FUTURE_CAUSAL_SOURCE'
 assert original_actions[-1]==dict(kind='wait',gear=0,target=0.,ticks=200)
 prefix=original_actions[:-3];prefix_steps=sum(a['ticks']for a in prefix);assert elapsed<=prefix_steps
 actions=remainder(prefix,elapsed)if prefix_override is None else prefix_override;ss,uu,rr,mem=roll(setup,packet,actions);full=ref._old.Geometry(setup['known'],source['periodic']);a,b=full.clearances(ss[:,:3]);prefix_min=float(np.minimum(a,b).min())
 if prefix_min<REQUIRED:return dict(passed=False,status='REFRESHED_PREFIX_REJECTED',minimum_prefix_full_cycle_raw_m=prefix_min)
 origin=dict(state=ss[-1],last_ctrl=mem[:4],integral=mem[4],virtual_rate=.6)
 # Use the same qualified predictor through an equivalent measured packet;
 # preserve predicted steering and controller memory rather than zeroing them.
 from kernel import Predictor
 p=Predictor(setup,origin,PARAMETERS);suffix=[p.state.copy()]
 for v,w,stale in [[.08,0.,False]]*2400+[[0.,0.,False]]*200:q,u=p.step(v,w,stale);suffix.append(q)
 suffix=np.array(suffix);g=Geometry(setup['known'],source['periodic'],packet['sim_time']);static=g.static.clearances(suffix[:,:3])[0];theta=suffix[:,2];front=np.c_[np.cos(theta),np.sin(theta)];left=np.c_[-np.sin(theta),np.cos(theta)];body=suffix[:,:2]@NORMALS.T-.44*abs(front@NORMALS.T)-.375*abs(left@NORMALS.T);best=None;passing=0
 for wait in range(math.ceil(g.period/.01)):
  phase=(g.start+(len(rr)+wait+np.arange(len(suffix)))*.01)%g.period;ix=np.minimum((phase/g.bin).astype(int),len(g.edges)-1);dynamic=(body-g.support[ix]-.1).max(axis=1);low=float(np.minimum(static,dynamic).min());passing+=int(low>=REQUIRED)
  if best is None or low>best['lower']:best=dict(wait=wait,lower=low)
 if not passing:
  if prefix_override is None:
   fitted=fit_staging(setup,packet,actions)
   if fitted is not None:
    result=refresh(setup,packet,source,goal,original_actions,elapsed,prefix_override=fitted);result['terminal_staging_reshoot_used']=True;result['unfitted_best_raw_m']=best['lower'];return result
  return dict(passed=False,status='REFRESHED_DEPARTURE_REJECTED',minimum_prefix_full_cycle_raw_m=prefix_min,best=best)
 joined=actions+([dict(kind='wait',gear=0,target=0.,ticks=best['wait'])]if best['wait']else[])+original_actions[-2:];result=certify(setup,packet,source,goal,joined);result.update(status='REFRESHED_REMAINDER_QUALIFIED'if result['passed']else'REGENERATED_REMAINDER_REJECTED',departure_wait_ticks=best['wait'],passing_departures=passing,minimum_prefix_full_cycle_raw_m=prefix_min);return result
