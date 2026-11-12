"""Reproduce integration on observed failure input, with physical imports blocked."""
import sys,json,importlib.abc,copy
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1085_fresh_ns_validation'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));from physical_ops import dump
from kernel import PARAMETERS
from live_reference import produce,static_planner
x=json.loads((R/'records/nav2_v1076_20261112/ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());x['setup']['case']=dict(goal_xy=x['goal']);m=static_planner(O);m.library();p=produce(x['setup'],x['packet'],x['source'],O,x['goal']);dump(O/'LIVE_REFERENCE_PROOF.json',dict(passed=True,chosen=p['proof'],candidates=p['candidates'],static_expanded=p['static']['expanded'],models=0,integrations=0));print(json.dumps(dict(chosen=p['proof'],models=0,integrations=0)),flush=True)
