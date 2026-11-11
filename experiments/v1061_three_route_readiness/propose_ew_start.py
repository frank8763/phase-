"""One explicitly unadopted EW start proposal; canonical tasks stay untouched."""
import copy,json,sys,time,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1061_three_route_readiness'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1023_dense_input_route'))
from input_route import construct
from certificate import audit
x=json.loads((O/'EAST_WEST_T0_METADATA.json').read_text());new=copy.deepcopy(x);new['packet']['body'][1]+=.10;plan=construct(new['packet'],None,new['goal'],new['setup'],time.time()+45,'pre_detection_static');proof=audit(plan,new['packet'],None,new['setup'],new['goal'])if plan['passed']else dict(passed=False);result=dict(passed=plan['passed']and proof['passed'],proposal_only=True,adopted=False,canonical_original_task_passed=False,only_change_start_xy_from=x['packet']['body'][:2],only_change_start_xy_to=new['packet']['body'][:2],original_goal_unchanged=True,original_thresholds_unchanged=True,scene_actor_unchanged=True,metadata=new,plan=plan,audit=proof,models=0,integrations=0);(O/'EAST_WEST_START_VARIANT_PROPOSAL.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['plan','audit','metadata']}))
