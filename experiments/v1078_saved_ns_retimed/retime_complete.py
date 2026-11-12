"""Generic whole-goal retiming candidate. No plant or learned-policy authority.

Consumes current measured packet, causal support and a known-map static body
profile. Fixed .125 is an unqualified development speed until plant response
qualification. Full original predictor/gates remain the sole analytical gate.
"""
import math,copy
import numpy as np
from kernel import Predictor,PARAMETERS,initial,Geometry,REQUIRED,checks,ref,predict
from recovery_source import forecast_packet
from calibrated_model import Predictor
SPEED=.125

def rollout(setup,packet,requests):
 p=Predictor(setup,initial(packet),PARAMETERS);states=[p.state.copy()];controls=[]
 for request in requests:q,u=p.step(*request);states.append(q);controls.append(u)
 return np.asarray(states),np.asarray(controls)

def propose(setup,packet,source,goal,static_requests):
 original=np.asarray(static_requests,float);assert original.ndim==2 and original.shape[1]==3 and np.isfinite(original).all()and len(original)>=200,'COMPLETE_STATIC_PROFILE_REQUIRED';assert np.array_equal(original[-200:],np.zeros((200,3))),'ORIGINAL_COMPLETE_STOP_REQUIRED';assert np.all(original[:,2]==0)and np.all(np.isin(original[:,0],[0.,.03,.08])),'QUALIFIED_FORWARD_SOURCE_REQUIRED';parts=[];i=0
 while i<len(original):
  j=i+1
  while j<len(original)and np.array_equal(original[i],original[j]):j+=1
  block=original[i:j].copy()
  if original[i,0]==.08:block=np.tile(original[i],(max(1,int(round(len(block)*.08/SPEED))),1));block[:,:2]*=SPEED/.08
  parts.append(block);i=j
 requests=np.vstack([*parts,np.zeros((2000,3))]);s,u,r,m=predict(setup,packet,[dict(kind='wait',gear=0,target=0.,ticks=1001)],tail=False);projected=forecast_packet(packet,s[-1],m[-1],1001);states,controls=rollout(setup,projected,requests);g=Geometry(setup['known'],source['periodic'],projected['sim_time']);limit=int(math.ceil(g.period/.01));times=np.arange(len(states));bounds=[]
 for wait in range(0,limit,25):bounds.append((float(g.clearances(states[:,:3],times+wait,.005).min()),wait))
 minimum,selected=max(bounds)
 for wait in range(max(0,selected-24),min(limit,selected+25)):
  low=float(g.clearances(states[:,:3],times+wait,.005).min())
  if low>minimum:minimum,selected=low,wait
 joined=np.vstack([np.zeros((1001+selected,3)),requests]);ss,uu=rollout(setup,packet,joined);minimum=Geometry(setup['known'],source['periodic'],packet['sim_time']).complete(ss);cc,upper=checks(ss,uu,joined,packet,setup,np.asarray(goal),minimum,REQUIRED);aa,bb=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[:1002+selected,:3]);cc['initial_hold_full_cycle']=bool(min(aa.min(),bb.min())>=REQUIRED);aa,bb=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[-1:,:3]);cc['terminal_hold_full_cycle']=bool(min(aa[0],bb[0])>=REQUIRED);cc['complete2200_stop']=bool(np.array_equal(joined[-2200:],np.zeros((2200,3))));cc={k:bool(v)for k,v in cc.items()}
 return dict(passed=all(cc.values()),analytical_complete_goal_passed=all(cc.values()),checks=cc,source_native_tick=source['source_native_tick'],root_native_tick=packet['native_tick'],wait_native=1001+selected,minimum_raw_m=minimum,terminal_goal_upper_m=upper,maximum_predicted_body_speed=float(abs(ss[:,3]).max()),new_command_speed=SPEED,physical_ready=False,physical_response_qualified=False,learned_policy_changed=False,models=0,mujoco_integrations=0,states=ss,controls=uu,requests=joined)
