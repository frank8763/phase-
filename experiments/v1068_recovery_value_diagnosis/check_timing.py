"""Evaluate an existing static-control proposal against the unchanged timed set."""
import importlib.abc,sys,json,time,math
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('NO_MODEL_DIAGNOSTIC '+name)
sys.meta_path.insert(0,NoModel());R=Path(__file__).resolve().parents[2];O=R/'runs/v1068_recovery_value_diagnosis';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
from kernel import predict,Geometry,REQUIRED,ref
from recovery_source import forecast_packet
case=sys.argv[1];rel={'NS':'A_main_north_south/refresh/epoch01/INPUT.json','EW':'A_main_east_west/refresh/epoch07/INPUT.json','WE':'A_main_west_east/refresh/epoch08/INPUT.json'}[case];x=json.loads((R/'runs/v858_nav2_verified/v1067'/rel).read_text());a=json.loads((O/('phase_free_'+case+'_5000_static_SOURCE.json')).read_text());s,u,r,m=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=1001)],tail=False);p=forecast_packet(x['packet'],s[-1],m[-1],1001)
states=__import__('numpy').asarray(a['state_path']);g=Geometry(x['setup']['known'],x['source']['periodic'],p['sim_time']);low=g.complete(states);print(json.dumps(dict(case=case,minimum_raw_m=low,required=REQUIRED,complete_goal=a['functional_goal_source'],goal_upper=a['terminal_goal_upper_m'],models=0)),flush=True)
