"""Original root to goal: regenerate all wait/controller states and gate them."""
import sys,importlib.abc,json,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1076_complete_goal_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODELS '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
import numpy as np
from kernel import Predictor,PARAMETERS,initial,Geometry,REQUIRED,checks,ref
x=json.loads((R/'runs/v1069_retained_goal_corridor/ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());diagnosis=json.loads((O/'SPEED125_DIAGNOSIS.json').read_text());assert diagnosis['analytical_complete_goal_passed'];old=np.load(O/'SPEED125_PROPOSAL.npz');wait=1001+diagnosis['best_wait_native'];requests=np.vstack([np.zeros((wait,3)),old['requests']]);p=Predictor(x['setup'],initial(x['packet']),PARAMETERS);states=[p.state.copy()];controls=[]
for request in requests:q,u=p.step(*request);states.append(q);controls.append(u)
states=np.asarray(states);controls=np.asarray(controls);g=Geometry(x['setup']['known'],x['source']['periodic'],x['packet']['sim_time']);low=g.complete(states);cc,upper=checks(states,controls,requests,x['packet'],x['setup'],np.asarray(x['goal']),low,REQUIRED);a,b=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(states[:wait+1,:3]);cc['initial_hold_full_cycle']=min(a.min(),b.min())>=REQUIRED;a,b=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(states[-1:,:3]);cc['terminal_hold_full_cycle']=min(a[0],b[0])>=REQUIRED;cc['complete2200_stop']=np.array_equal(requests[-2200:],np.zeros((2200,3)));cc={k:bool(v)for k,v in cc.items()};assert all(cc.values()),cc
np.savez_compressed(O/'COMPLETE_GOAL_SOURCE.npz',states=states,controls=controls,requests=requests)
# This regression exercises the exact goal symptom, not an import smoke test.
assert json.loads((O/'RED_REPRODUCTION.json').read_text())['checks']['goal_upper']is False
negative={}
short_states=states[:-2500];short_ctrl=controls[:-2500];short_requests=requests[:-2500];bad,unused=checks(short_states,short_ctrl,short_requests,x['packet'],x['setup'],np.asarray(x['goal']),low,REQUIRED);negative['truncated_before_goal_rejected']=not all(bad.values());bad,unused=checks(states,controls,requests,x['packet'],x['setup'],np.asarray(x['goal']),REQUIRED-1e-6,REQUIRED);negative['under_clearance_gate_rejected']=not bad['full_raw_geometry'];assert all(negative.values())
result=dict(passed=True,scope='Saved original NS failed entry, complete analytical root-to-goal only',checks=cc,negative_cases=negative,original_symptom_red=True,new_complete_goal_green=True,original_packet_native=x['packet']['native_tick'],wait_native=wait,full_native_prediction=len(requests),minimum_raw_m=low,required_raw_m=REQUIRED,terminal_goal_upper_m=upper,maximum_predicted_body_speed=float(abs(states[:,3]).max()),hard_body_cap=.13,new_command_speed=.125,complete_stop_native=2200,models=0,mujoco_integrations=0,training_updates=0,physical_response_qualified=False,physical_ready=False,new_navigation_started=False,scientific_change='Uniform retiming of the existing whole-goal requests at .125 plus a fixed-source finite launch wait; all original predictor gates retained',learned_policy_changed=False,source_sha=hashlib.sha256((O/'COMPLETE_GOAL_SOURCE.npz').read_bytes()).hexdigest());(O/'COMPLETE_GOAL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
