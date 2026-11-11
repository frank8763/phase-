"""Reproduce stale publication acceptance at the ORIGINAL production seam."""
import importlib.abc,sys,json,copy
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import load
old=load('v1053_actual_old_executor',R/'experiments/v1051_retained_corridor_entry/execute.py')
x=json.loads((R/'runs/v1051_retained_corridor_entry/INPUT_SOURCE.json').read_text());plan=json.loads((R/'runs/v1051_retained_corridor_entry/SELECTED_PLAN.json').read_text());packet=copy.deepcopy(x['packet']);packet['sent_at']+=5.
old.regenerate(x['setup'],packet,plan)
raise AssertionError('LEGACY_STALE_PUBLISH_ACCEPTED: original production regeneration accepted a five-second-old measured body/encoder packet; zero models')
