"""Unqualified .12 command diagnostic; original .13 body gate is NOT relaxed.

This probes the .08 progress/time bottleneck. Even if analytical gates pass,
.12 response is extrapolation: it cannot authorize a whole-route model run.
"""
import sys,importlib.abc,json,math,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1076_complete_goal_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
import numpy as np
from kernel import Predictor,initial,PARAMETERS,checks,Geometry,REQUIRED,ref,predict
from recovery_source import forecast_packet
start=time.monotonic();x=json.loads((R/'runs/v1069_retained_goal_corridor/ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());ss,uu,rr,mm=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=1001)],tail=False);packet=forecast_packet(x['packet'],ss[-1],mm[-1],1001);original=np.load(O/'PATH_PHASE_DIAGNOSIS.npz')['requests'];parts=[];i=0
while i<len(original):
 j=i+1
 while j<len(original)and np.array_equal(original[i],original[j]):j+=1
 block=original[i:j]
 if original[i,0]==.08:
  count=int(round(len(block)*2/3));block=np.tile(original[i],(count,1));block[:,:2]*=1.5
 parts.append(block);i=j
requests=np.vstack([*parts,np.zeros((2000,3))]);p=Predictor(x['setup'],initial(packet),PARAMETERS);states=[p.state.copy()];ctrl=[]
for request in requests:q,u=p.step(*request);states.append(q);ctrl.append(u)
states=np.asarray(states);ctrl=np.asarray(ctrl);g=Geometry(x['setup']['known'],x['source']['periodic'],packet['sim_time']);bounds=[];period_ticks=int(math.ceil(g.period/.01))
for wait in range(0,period_ticks,25):bounds.append((float(g.clearances(states[:,:3],np.arange(len(states))+wait,.005).min()),wait))
low,wait=max(bounds);static_min=float(g.static.clearances(states[:,:3])[0].min());
for refined_wait in range(max(0,wait-24),min(period_ticks,wait+25)):
 candidate_low=float(g.clearances(states[:,:3],np.arange(len(states))+refined_wait,.005).min())
 if candidate_low>low:low,wait=candidate_low,refined_wait
cc,upper=checks(states,ctrl,requests,packet,x['setup'],np.asarray(x['goal']),low,REQUIRED);result=dict(analytical_complete_goal_passed=all(cc.values()),checks={k:bool(v)for k,v in cc.items()},static_minimum_raw_m=static_min,maximum_predicted_body_speed=float(abs(states[:,3]).max()),best_timing_minimum_raw_m=low,best_wait_native=wait,terminal_goal_upper_m=upper,new_command_speed=.12,actual_body_cap=.13,model_response_extrapolation=True,physical_ready=False,models=0,integrations=0,wall_s=time.monotonic()-start);(O/'SPEED_LIMIT_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
