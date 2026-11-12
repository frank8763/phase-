"""One saved failure, one changed search heuristic, zero model imports."""
import importlib.abc,sys,json,time,traceback
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('NO_MODELS '+name)
sys.meta_path.insert(0,NoModel());R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1069_retained_goal_corridor';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
from kernel import predict
from recovery_source import forecast_packet
sys.path.insert(0,str(C))
from retained_planner import construct
x=json.loads((O/'ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());start=time.monotonic();w=json.loads((O/'PREPARATION_WINDOW.json').read_text());assert time.time()<w['checkpoint_unix']
try:
 s,u,rr,m=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=1001)],tail=False);p=forecast_packet(x['packet'],s[-1],m[-1],1001);assert Path(construct.__code__.co_filename).resolve()==C/'retained_planner.py';result=construct(x['setup'],p,x['source'],x['goal'],wall_s=30.,max_expansions=int(sys.argv[1])if len(sys.argv)>1 else 5000,guidance_actions=x['actions']);out={k:v for k,v in result.items()if k not in ['state_path','predicted_actuator_controls','planned_body_requests','actions']};out['passed']=bool(result['passed']and result.get('functional_goal_source'))
 if result['passed']:(O/'CANDIDATE_SOURCE.json').write_text(json.dumps(result)+'\n')
except BaseException as e:out=dict(passed=False,error=repr(e),traceback=traceback.format_exc())
out.update(wall_total_s=time.monotonic()-start,models=0,integrations=0,case='ACTUAL_NS_ENTRY_BEFORE_FAILED_FINITE_CORRIDOR',physical_ready=False);(O/'QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True);sys.exit(0 if out['passed']else 1)
