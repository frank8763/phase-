"""Saved actual acceptance callsite only; forbids new models or integration."""
import importlib.abc,importlib.util,json,sys
from pathlib import Path
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('ZERO_MODEL_ONLY')
sys.meta_path.insert(0,NoModels());R=Path(__file__).resolve().parents[2]
def load(path):return json.loads((R/path).read_text())
spec=importlib.util.spec_from_file_location('frozen_acceptance_gate',R/'experiments/goal_acceptance_20261105/evidence_rules.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
tasks=load('experiments/v828_goal_dynamic_confirmation/TASK_LIST.json');actual=load('runs/v828_goal_dynamic_confirmation/FINAL_INDEPENDENT_AUDIT.json')['records'];gate=module.main_gate(tasks,actual,True)
optimistic=actual+[dict(role='MAIN',task=t,physical_passed=True,functional_passed=True)for t in tasks[len(actual):]];best=module.main_gate(tasks,optimistic,True)
assert not gate['passed']and gate['main_attempts']==8 and gate['main_successes']==6 and gate['success_rate']is None
assert not best['passed']and best['main_successes']==22 and best['route_successes']['WEST_EAST']==6 and best['direction_successes']['NEGATIVE_AXIS']==10
# Counterfactual self-check only: demonstrates that the actual callsite can turn green.
positive=[dict(role='MAIN',task=t,physical_passed=True,functional_passed=True)for t in tasks];assert module.main_gate(tasks,positive,True)['passed']
state=load('runs/v841_early_joint/FINAL_INDEPENDENT_AUDIT.json');assert not state['development_passed']and state['records'][0]['result']['outcome']=='BOUNDED_WALL_STOP'
print(json.dumps(dict(actual_gate=gate,even_if_remaining16_all_pass=best,current_development_passed=state['development_passed'],synthetic_positive_gate=True,synthetic_is_not_a_trial=True,models=0,integrations=0),ensure_ascii=False))
if '--expect-original-pass'in sys.argv:assert gate['passed'],'ORIGINAL24_ALREADY_FAILS; completing16 cannot reach23/24 or route7/8 or direction11/12'
if '--expect-current-ready'in sys.argv:assert state['development_passed'],'CURRENT_SINGLE_SCENE_FAILED; confirmation launch gate remains closed'
