"""Zero-model feedback loop at the actual failed recovery-producer seam."""
import importlib.abc,sys,json,time,traceback
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('NO_MODEL_DIAGNOSTIC '+name)
sys.meta_path.insert(0,NoModel())
R=Path(__file__).resolve().parents[2];C=R/'experiments/v1067_causal_replan_brake_reserve';O=R/'runs/v1068_recovery_value_diagnosis';sys.path.insert(0,str(C))
from resource_policy import apply
apply()
from recovery_source import prepare
case=sys.argv[1]if len(sys.argv)>1 else 'NS'
rel={'NS':'A_main_north_south/refresh/epoch01/INPUT.json','EW':'A_main_east_west/refresh/epoch07/INPUT.json','WE':'A_main_west_east/refresh/epoch08/INPUT.json'}[case]
x=json.loads((R/'runs/v858_nav2_verified/v1067'/rel).read_text());begun=time.monotonic()
try:
 result=prepare(x['setup'],x['packet'],x['source'],x['goal'],x['actions'],x['elapsed']);out=dict(passed=result.get('functional_goal_source')is True,source_kind=result.get('source_kind'),terminal_goal_upper_m=result.get('terminal_goal_upper_m'),error=None)
except BaseException as e:out=dict(passed=False,error=repr(e))
out.update(case=case,symptom='No complete safe continuation to the original goal at this saved recovery boundary',wall_s=time.monotonic()-begun,models=0,integrations=0,input=rel);(O/('BASELINE_'+case+'.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True);sys.exit(0 if out['passed']else 1)
