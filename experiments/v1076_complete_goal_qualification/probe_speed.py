"""One changed local-reference steering proposal, same actual failed input."""
import sys,importlib.abc,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1076_complete_goal_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
from kernel import predict,load
from recovery_source import forecast_packet
sys.path.insert(0,str(R/'experiments/v1069_retained_goal_corridor'))
planner=load('v1076_local_reference_candidate',C/'speed_planner.py')
x=json.loads((R/'runs/v1069_retained_goal_corridor/ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());s,u,r,m=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=1001)],tail=False);p=forecast_packet(x['packet'],s[-1],m[-1],1001);start=time.monotonic();q=planner.construct(x['setup'],p,x['source'],x['goal'],wall_s=30,max_expansions=30000,guidance_actions=x['actions']);summary={k:v for k,v in q.items()if k not in ['state_path','predicted_actuator_controls','planned_body_requests','actions']};summary['complete_goal_passed']=bool(q['passed']and q.get('functional_goal_source'));summary['wall_total_s']=time.monotonic()-start;(O/'SPEED_SEARCH_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
if q['passed']:(O/'SPEED_SEARCH_CANDIDATE.json').write_text(json.dumps(q)+'\n')
print(json.dumps(summary),flush=True)
