"""Saved actual call-site feedback and negative cases, zero models."""
import copy,importlib.abc,importlib.util,json,sys
from pathlib import Path
import numpy as np
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('TRIGGER_QUALIFICATION_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
from goal_renewal import evaluate
from exact_footprint import build
from current_guide import attach
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
read=lambda p:json.loads(p.read_text());root=repo/'runs/v826_goal_reference_renewal/zero_model_interfaces'
assert read(root/'OLD_TRIGGER_RED.json')['old_need']is False
saved=read(repo/'runs/v823_global_continuation_diagnosis/renewal_probe/INPUT_0282.json');field=build(F,saved['world']);field.base_heuristic=F.base._heuristic_grid;attach(field,saved['motion_state']);current=np.asarray(saved['pose']);goal=saved['world']['goal'];state=saved['motion_state']
yes=evaluate(field,current,goal,state,282,265,'SAFE_PROGRESS_PREFIX');assert yes['should_replan'] and yes['authorizes_control']is False
old=copy.deepcopy(state);old['observed_this_frame']=False;none=evaluate(field,current,goal,old,282,265,'SAFE_PROGRESS_PREFIX');assert none is None
assert evaluate(field,current,goal,state,282,281,'SAFE_PROGRESS_PREFIX')is None
assert evaluate(field,current,goal,state,282,265,'GLOBAL_GOAL_PATH')is None
unknown=copy.deepcopy(state);unknown['center']=None;assert evaluate(field,current,goal,unknown,282,265,'SAFE_PROGRESS_PREFIX')is None
outside=evaluate(field,current,[100.,100.],state,282,265,'SAFE_PROGRESS_PREFIX');assert outside['should_replan']is False
out=dict(status='SAVED_CALLSITE_RENEWAL_TRIGGER_AND_NEGATIVES_PASS',old_trigger_red=True,new_saved282_green=yes,negative_cases=['NO_NEW_OBSERVATION','ORIGINAL_12_STEP_COOLDOWN','ALREADY_GLOBAL_GOAL_PATH','NO_TRACKED_ACTOR','DISCONNECTED_OUTSIDE_GOAL'],models=0,integrations=0,not_full_navigation_regression=True)
(root/'TRIGGER_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
