"""Saved actual-state analytical search probes; imports models are blocked."""
import importlib.abc,sys,json,time
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('NO_MODEL_DIAGNOSTIC '+name)
sys.meta_path.insert(0,NoModel());R=Path(__file__).resolve().parents[2];C=R/'experiments/v1067_causal_replan_brake_reserve';O=R/'runs/v1068_recovery_value_diagnosis';sys.path.insert(0,str(C))
from resource_policy import apply
apply()
from kernel import predict
from recovery_source import forecast_packet
sys.path.insert(0,str(Path(__file__).resolve().parent))
from static_planner import construct
case=sys.argv[1];count=int(sys.argv[2]);static=len(sys.argv)>3 and sys.argv[3]=='static';rel={'NS':'A_main_north_south/refresh/epoch01/INPUT.json','EW':'A_main_east_west/refresh/epoch07/INPUT.json','WE':'A_main_west_east/refresh/epoch08/INPUT.json'}[case]
x=json.loads((R/'runs/v858_nav2_verified/v1067'/rel).read_text());s,u,rr,m=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=1001)],tail=False);p=forecast_packet(x['packet'],s[-1],m[-1],1001);a=time.monotonic();result=construct(x['setup'],p,None if static else x['source'],x['goal'],wall_s=30.,max_expansions=count);summary={k:v for k,v in result.items()if k not in ['state_path','predicted_actuator_controls','planned_body_requests','actions']};summary.update(case=case,fixed_expansions=count,static_only=static,wall_total_s=time.monotonic()-a,models=0,integrations=0);name='phase_free_'+case+'_'+str(count)+('_static'if static else'_dynamic');(O/(name+'.json')).write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
if result['passed']:(O/(name+'_SOURCE.json')).write_text(json.dumps(result)+'\n')
