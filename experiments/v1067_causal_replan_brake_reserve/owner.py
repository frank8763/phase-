"""One physical owner; static stop reserve and labelled recovery corridors."""
import math,time
import numpy as np
from kernel import R,C,load,dump,virtual
from fresh import finite_plan,approach,choose_seed
from brake_reserve import Reserve
from static_source import renew
from execute import execute

def navigate(v,setup,task,end,out,result):
 causal=load('v1067_raw_causal_sensor',R/'experiments/v1024_full_route_execution/causal.py');norm=load('v1067_raw_periodic_coefficients',R/'experiments/v1037_periodic_norm_source/periodic_norm.py')
 class Evidence(causal.Evidence):
  def __init__(self,known):super().__init__(known);self.periodic=norm.PeriodicSupport()
 evidence=Evidence(setup['known']);result['_evidence']=evidence;segments=[];result['_direct_segments']=segments;assert not evidence.update(v.scan()),'DYNAMIC_VISIBLE_AT_T0';reserve=Reserve(setup);preemptions=[]
 def follow(plan,label,interrupt=False,guard=False):
  assert plan['passed'];path=out/('%02d_%s_PLAN.json'%(len(segments),label));dump(path,plan);ss=np.array(plan['state_path']);rr=np.array(plan['planned_body_requests']);origin=v.count;segment=dict(path=str(path.relative_to(R)),origin_native=origin,executed_native=0,label=label,source_kind=plan.get('source_kind','DIRECT_FINITE_PROFILE'));segments.append(segment);maximum=np.zeros(3);i=0;status='COMPLETE'
  try:
   while i<len(rr):
    assert time.time()<end-150,'FULL_OWN_REPLAY_RESERVE';count=min(5,len(rr)-i)
    if guard:
     proof=reserve.check(causal.packet(v,evidence.first is not None),rr[i:i+count])
     if not proof['passed']:
      assert proof['current_stop_passed'],'CURRENT_STATIC_STOP_CERTIFICATE_LOST';preemptions.append(dict(native=v.count,proof=proof,plan=str(path.relative_to(R)),planned_index=i));dump(out/'BRAKE_PREEMPTIONS.json',preemptions);status='BRAKE_RESERVE_PREEMPTION';break
    for request in rr[i:i+count]:
     v.step(*request);i+=1;b=np.asarray(v.body());angle=b[2]-ss[i,2];errors=[np.linalg.norm(b[:2]-ss[i,:2]),abs(math.atan2(math.sin(angle),math.cos(angle))),abs(virtual(v.steering_sample()[:2])-ss[i,6])];maximum=np.maximum(maximum,errors);assert np.all(maximum<=[.04,.035,.015]),'FRESH_NATIVE_TRACKING';assert abs(b[3])<=.13 and abs(b[4])<=.16,'FRESH_BODY_CAP'
    if v.count%5==0:
     seen=evidence.update(v.scan())
     if interrupt and seen:status='REAL_CAUSAL_DISCOVERY';break
    if v.count%500==0:dump(out/'PARTIAL.json',dict(phase=label,native=v.count,maximum_local_tracking=maximum.tolist(),static_preemptions=len(preemptions)))
  except BaseException:
   status='EXCEPTION_INTERRUPTED';raise
  finally:
   segment.update(executed_native=v.count-origin,maximum_position_m=float(maximum[0]),maximum_heading_rad=float(maximum[1]),maximum_steering_rad=float(maximum[2]),status=status);dump(out/'DIRECT_SEGMENTS.json',segments)
  return status
 initial_source=__import__('json').loads((__import__('kernel').O/(task['case_id']+'_STATIC_SOURCE.json')).read_text());p=causal.packet(v,False);dump(out/'INITIAL_METADATA.json',dict(setup=setup,packet=p,task=task));plan=finite_plan(setup,p,None,initial_source['plan']['planned_body_requests'],'ORIGINAL_COMPLETE_STATIC_GUIDANCE');static_renewals=0
 while evidence.first is None:
  status=follow(plan,'STATIC_%02d'%static_renewals,interrupt=True,guard=True)
  if status=='REAL_CAUSAL_DISCOVERY':break
  assert status=='BRAKE_RESERVE_PREEMPTION','REAL_SENSOR_DISCOVERY_REQUIRED';p=causal.packet(v,False);brake=finite_plan(setup,p,None,np.zeros((2200,3)),'COMPLETE_PREEMPTIVE_STATIC_STOP');assert brake['passed'],'PREEMPTIVE_STOP_ORIGINAL_PYTHON_REJECTED';follow(brake,'PREEMPTIVE_STOP_%02d'%static_renewals)
  assert evidence.first is None,'FIRST_DISCOVERY_DURING_STATIC_STOP';static_renewals+=1;assert static_renewals<=8,'STATIC_RENEWAL_LIMIT';p=causal.packet(v,False);plan=renew(setup,p,task['goal_xy'],wall_s=min(10.,end-time.time()-180),max_expansions=20000);assert plan['passed'],'NO_STATIC_RECOVERY_SOURCE';plan.update(packet=p,source=None,scope='STATIC_RENEWAL_FINITE_PROFILE',source_kind='COMPLETE_GOAL'if plan['functional_goal_source']else'SAFE_PROGRESS_NOT_ARRIVAL');reserve=Reserve(setup,use_wide_reserve=False)
 discovery=v.count;local_discovery=segments[-1]['executed_native'];result['first_causal_discovery_native']=discovery;assert abs(v.commands[-1][1])>.005,'FIRST_DISCOVERY_NOT_NORMAL_DRIVING';brake=finite_plan(setup,causal.packet(v,True),evidence.source(v),np.zeros((2200,3)),'COMPLETE_DISCOVERY_STOP_AND_OBSERVE');assert brake['passed'],'DISCOVERY_STOP_PREDICTION_REJECTED';follow(brake,'DISCOVERY_STOP');assert np.linalg.norm(v.body()[3:])<=.03,'DISCOVERY_ACTUAL_STOP_REQUIRED'
 information_approach=approach(setup,causal.packet(v,True),evidence.source(v),plan['planned_body_requests'],local_discovery,(4500,3000,1500,0));follow(information_approach,'ORIGINAL_CERTIFIED_OBSERVATION_APPROACH');result['observation_approach_native']=len(information_approach['planned_body_requests']);warm=__import__('json').loads((C/'RECOVERY_WARM_SEED.json').read_text())['actions']
 try:seed=choose_seed(setup,causal.packet(v,True),evidence.source(v),task['goal_xy'],plan['planned_body_requests'],local_discovery,information_approach['movement_native'],warm)
 except AssertionError as e:
  assert str(e)=='NO_ORIGINAL_GOAL_INPUT_SEED';dump(out/'GUIDANCE_REJECTION.json',dict(error=str(e),guidance_only=True,models=0));seed=dict(actions=warm,goal=task['goal_xy'],mode='UNQUALIFIED_GUIDANCE_ONLY')
 result['recovery_origin_native']=v.count;result['feedback_execution']=execute(v,setup,seed,end,evidence,out,causal.packet);goal=float(np.linalg.norm(np.asarray(v.body()[:2])-task['goal_xy']));assert goal<=.45 and np.linalg.norm(v.body()[3:])<=.03,'FRESH_ORIGINAL_GOAL_AND_STOP';assert np.linalg.norm(np.asarray(v.body()[:2])-evidence.first['xy'])>=1.,'FRESH_ONE_METRE_AFTER_DISCOVERY';result.update(passed=True,status='FRESH_T0_GOAL_AND_STOP',actual_original_goal_reached=True,actual_goal_distance_m=goal,static_renewals=static_renewals)
