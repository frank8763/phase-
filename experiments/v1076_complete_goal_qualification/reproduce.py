"""Rebuild the missing-complete-goal failure from actual archived causal input."""
import sys,importlib.abc,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1076_complete_goal_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
import numpy as np
from kernel import predict,checks,Geometry,REQUIRED
from recovery_source import forecast_packet
x=json.loads((R/'runs/v1069_retained_goal_corridor/ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());candidate=json.loads((R/'runs/v1069_retained_goal_corridor/CANDIDATE_SOURCE.json').read_text());s,u,rr,m=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=1001)],tail=False);packet=forecast_packet(x['packet'],s[-1],m[-1],1001);s,u,rr,m=predict(x['setup'],packet,candidate['actions'],tail=False);low=Geometry(x['setup']['known'],x['source']['periodic'],packet['sim_time']).complete(s);cc,upper=checks(s,u,rr,packet,x['setup'],np.asarray(x['goal']),low,REQUIRED);result=dict(complete_goal_passed=bool(all(cc.values())),checks=cc,terminal_goal_upper_m=upper,minimum_raw_m=low,same_stored_prediction=float(abs(s-np.asarray(candidate['state_path'])).max()),models=0,integrations=0);result['checks']={k:bool(v)for k,v in cc.items()};(O/'RED_REPRODUCTION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['complete_goal_passed'],'ORIGINAL_CAUSAL_CANDIDATE_HAS_NO_COMPLETE_GOAL'
