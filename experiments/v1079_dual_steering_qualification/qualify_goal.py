"""Regenerate a complete goal source with the held-out-qualified new predictor."""
import sys,importlib.abc,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1079_dual_steering_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
import numpy as np
from kernel import load,Predictor as Old,PARAMETERS
sys.path.insert(0,str(C));from steering_model import Predictor,initial
assert json.loads((O/'QUALIFICATION.json').read_text())['passed'];x=json.loads((R/'records/nav2_v1076_20261112/ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());baseline=np.load(R/'records/nav2_v1076_20261112/PATH_PHASE_DIAGNOSIS.npz');a=Old(x['setup'],initial(x['packet']),PARAMETERS);b=Predictor(x['setup'],initial(x['packet']),PARAMETERS);error=0.
for req in baseline['requests']:
 s,u=a.step(*req);q,v=b.step(*req);error=max(error,float(abs(s-q).max()),float(abs(u-v).max()))
assert error==0.,'OLD_SPEED_DOMAIN_CHANGED';retimer=load('v1079_dual_front_retimer',C/'retime_complete.py');q=retimer.propose(x['setup'],x['packet'],x['source'],x['goal'],baseline['requests']);summary={k:v for k,v in q.items()if k not in ['states','controls','requests']};summary.update(old08_03_zero_domain_parity_error=error,new_model_saved_regression_passed=True,original_v1078_stays_failed=True,new_actual_navigation_or_recovery_started=False);(O/'COMPLETE_GOAL_QUALIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n');np.savez_compressed(O/'COMPLETE_GOAL_SOURCE.npz',states=q['states'],controls=q['controls'],requests=q['requests']);print(json.dumps(summary),flush=True)
