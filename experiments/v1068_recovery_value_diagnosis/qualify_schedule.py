import importlib.abc,sys,json,time
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('NO_MODEL_DIAGNOSTIC '+name)
sys.meta_path.insert(0,NoModel());R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1068_recovery_value_diagnosis';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
from kernel import predict
sys.path.insert(0,str(C))
from schedule import prepare
case=sys.argv[1];rel={'NS':'A_main_north_south/refresh/epoch01/INPUT.json','EW':'A_main_east_west/refresh/epoch07/INPUT.json','WE':'A_main_west_east/refresh/epoch08/INPUT.json'}[case];x=json.loads((R/'runs/v858_nav2_verified/v1067'/rel).read_text());start=time.monotonic()
try:
 result=prepare(x);out={k:v for k,v in result.items()if k not in ['actions','original_python_states','original_python_controls','original_python_requests']};(O/('SCHEDULE_'+case+'_SOURCE.json')).write_text(json.dumps(result)+'\n')
except BaseException as e:out=dict(passed=False,error=repr(e),wall_s=time.monotonic()-start,models=0,integrations=0)
out['case']=case;(O/('SCHEDULE_'+case+'.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True);sys.exit(0 if out['passed']else 1)
