"""Continuous fresh-start owner and task-driven finite observation approach."""
import math,time
import numpy as np
from kernel import Predictor,initial,PARAMETERS,ref,REQUIRED,virtual,checks,predict,dump
def actions_from_requests(requests):
 actions=[]
 for v,w,stale in requests:
  assert not stale and(v==0 or abs(v)in [.03,.08]);kind='wait'if v==0 else'move';target=0. if v==0 else math.atan(.6*w/v);gear=0 if v==0 else 1 if v>0 else-1;row=dict(kind=kind,gear=gear,target=target,speed=v,ticks=1)
  if actions and all(actions[-1][k]==row[k]for k in ['kind','gear','target','speed']):actions[-1]['ticks']+=1
  else:actions.append(row)
 return actions
def finite_plan(setup,packet,source,requests,scope):
 p=Predictor(setup,initial(packet),PARAMETERS);ss=[p.state.copy()];uu=[]
 for request in requests:s,u=p.step(*request);ss.append(s);uu.append(u)
 ss=np.array(ss);uu=np.array(uu);a,b=ref._old.Geometry(setup['known'],None if source is None else source['periodic']).clearances(ss[:,:3]);low=float(np.minimum(a,b).min());rate=np.asarray(setup['slew_per_second'])*.01;limits=np.asarray(setup['limits']);gates=dict(full_geometry=low>=REQUIRED,complete_200_stop=bool(np.array_equal(np.array(requests)[-200:],np.zeros((200,3)))and abs(ss[-50:,3:6]).max()<=.03 and abs(ss[-50:,7]).max()<=.03),legal_ctrl=bool((uu>=limits[:,0]-1e-10).all()and(uu<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([packet['controller_memory']['last_ctrl'],uu]),axis=0))<=rate+1e-10).all()),body_caps=bool(abs(ss[:,3]).max()<=.13 and abs(ss[:,4]).max()<=.03 and abs(ss[:,5]).max()<=.16))
 return dict(passed=all(gates.values()),checks=gates,minimum_raw_m=low,state_path=ss.tolist(),predicted_actuator_controls=uu.tolist(),planned_body_requests=np.array(requests).tolist(),scope=scope,packet=packet,source=source)
def follow(vehicle,plan,deadline,evidence,out,label,interrupt=False):
 assert plan['passed'];ss=np.array(plan['state_path']);rr=np.array(plan['planned_body_requests']);origin=vehicle.count;maximum=np.zeros(3);discovered=False
 try:
  for i,request in enumerate(rr):
   assert time.time()<deadline-150,'FULL_OWN_REPLAY_RESERVE';vehicle.step(*request);b=np.array(vehicle.body());a=b[2]-ss[i+1,2];error=np.array([np.linalg.norm(b[:2]-ss[i+1,:2]),abs(math.atan2(math.sin(a),math.cos(a))),abs(virtual(vehicle.steering_sample()[:2])-ss[i+1,6])]);maximum=np.maximum(maximum,error);assert(error<=np.array([.04,.035,.015])).all(),'FRESH_NATIVE_TRACKING'
   assert abs(b[3])<=.13 and abs(b[4])<=.16,'FRESH_BODY_CAP'
   if vehicle.count%5==0:
    seen=evidence.update(vehicle.scan())
    if interrupt and seen:discovered=True;break
   if vehicle.count%500==0:dump(out/'PARTIAL.json',dict(phase=label,native=vehicle.count,maximum_position_m=float(maximum[0])))
 finally:dump(out/(label+'_EXECUTION.json'),dict(origin_native=origin,end_native=vehicle.count,executed_native=vehicle.count-origin,maximum_position_m=float(maximum[0]),maximum_heading_rad=float(maximum[1]),maximum_steering_rad=float(maximum[2]),causal_discovery_interrupt=discovered))
 return dict(completed=not discovered,discovered=discovered,executed=vehicle.count-origin)
def approach(setup,packet,source,static_requests,discovery_index):
 candidates=[]
 for movement in [4500,3000,1500,0]:
  selected=np.array(static_requests)[discovery_index:discovery_index+movement]
  if movement and len(selected)!=movement:continue
  req=np.vstack([selected,np.zeros((2400,3))])if movement else np.zeros((2400,3));plan=finite_plan(setup,packet,source,req,'ONLINE_CERTIFIED_INFORMATION_APPROACH');candidates.append(dict(movement_native=movement,passed=plan['passed'],minimum_raw_m=plan['minimum_raw_m']))
  if plan['passed']:plan['movement_native']=movement;plan['candidate_checks']=candidates;return plan
 raise AssertionError('NO_COMPLETE_OBSERVATION_APPROACH')
def choose_seed(setup,packet,source,goal,static_requests,discovery,movement,warm):
 # The developed control library is guidance only. Select it by a public-goal
 # endpoint check, never case id, saved state, actor truth or old trajectory.
 s,u,r,m=predict(setup,packet,warm,tail=False);upper=float(np.linalg.norm(s[-1,:2]-goal))+.08
 if upper<=.45:return dict(actions=warm,goal=goal,mode='STAGED_STRAIGHT',warm_endpoint_upper=upper)
 remainder=np.asarray(static_requests)[discovery+movement:];best=None
 for extra in [0,100,200,400]:
  requests=np.vstack([remainder[:-200],np.tile([.03,0.,False],(extra,1)),np.zeros((200,3))]);actions=actions_from_requests(requests);ss,uu,rr,mm=predict(setup,packet,actions,tail=False);error=float(np.linalg.norm(ss[-1,:2]-goal))+.08
  if best is None or error<best[0]:best=(error,actions)
 assert best[0]<=.45,'NO_ORIGINAL_GOAL_INPUT_SEED'
 return dict(actions=best[1],goal=goal,mode='ARBITRARY_TIMED',original_goal_upper=best[0])
