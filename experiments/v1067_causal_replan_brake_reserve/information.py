"""Complete, full-cycle-safe observation corridors; never arrival success."""
import math,time
import numpy as np
from kernel import Expander,initial,Predictor,PARAMETERS,predict,ref,REQUIRED,CAP,TARGETS

def propose(setup,packet,source,goal):
 origin=initial(packet);initial_state=np.array(origin['state']);initial_memory=np.r_[origin['last_ctrl'],origin['integral']];geometry=ref._old.Geometry(setup['known'],source['periodic']);v=source['periodic']['vertices'];phase=.32*packet['sim_time'];center=np.array([np.mean(np.asarray(v[j])@np.array([1.,math.sin(phase),math.cos(phase)]))for j in [0,4]])
 bearing=math.atan2(center[1]-initial_state[1],center[0]-initial_state[0]);start_distance=np.linalg.norm(initial_state[:2]-goal);engine=Expander(setup);candidates=[]
 for speed in [-.03,.03]:
  for target in TARGETS:
   state=initial_state.copy();memory=initial_memory.copy();states=[state.copy()];valid=True
   for duration,request_speed in [(2000,speed),(2200,0.)]:
    left=duration
    while left:
     count=min(left,334);ss,uu,mm=engine.expand(state,memory,np.array([target if request_speed else 0.]),count,np.array([request_speed]));states.extend(ss[0]);state=ss[0,-1].copy();memory=mm[0].copy();left-=count
   states=np.array(states);a,b=geometry.clearances(states[:,:3]);low=float(np.minimum(a,b).min());valid=low>=REQUIRED and abs(states[:,3]).max()<=.13 and abs(states[:,4]).max()<=.03 and abs(states[:,5]).max()<=.16 and abs(states[-50:,3:6]).max()<=.03 and abs(states[-50:,7]).max()<=.03
   end_bearing=math.atan2(center[1]-state[1],center[0]-state[0]);angle=abs(math.atan2(math.sin(end_bearing-bearing),math.cos(end_bearing-bearing)));yaw=abs(math.atan2(math.sin(state[2]-initial_state[2]),math.cos(state[2]-initial_state[2])));score=angle+.3*yaw-.05*max(0.,float(np.linalg.norm(state[:2]-goal)-start_distance));actions=[dict(kind='move',gear=1 if speed>0 else-1,target=float(target),speed=speed,ticks=2000),dict(kind='wait',gear=0,target=0.,ticks=2200)];candidates.append(dict(passed=bool(valid and(angle>=.04 or yaw>=.05)),speed=speed,target=float(target),minimum_full_cycle_raw_m=low,bearing_change_rad=angle,yaw_change_rad=yaw,score=score,actions=actions))
 eligible=[x for x in candidates if x['passed']];assert eligible,'NO_FULL_CYCLE_INFORMATION_CORRIDOR';chosen=max(eligible,key=lambda x:x['score']);states,controls,requests,mem=predict(setup,packet,chosen['actions'],tail=False);a,b=geometry.clearances(states[:,:3]);low=float(np.minimum(a,b).min());assert low>=REQUIRED and abs(states[-50:,3:6]).max()<=.03 and abs(states[-50:,7]).max()<=.03,'INFORMATION_ORIGINAL_PYTHON_REJECTED'
 return dict(passed=True,actions=chosen['actions'],candidate_checks=candidates,minimum_full_cycle_raw_m=low,mode='INFORMATION_RECOVERY_NOT_ARRIVAL',full_goal_source=False,models=0,integrations=0,raw_source_only=True,no_evaluator_actor_inputs=True)
