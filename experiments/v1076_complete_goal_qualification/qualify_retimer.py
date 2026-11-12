"""Generic retimer parity on one actual saved causal failure; zero physics."""
import sys,json,importlib.abc
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1076_complete_goal_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
import numpy as np
from kernel import load
retimer=load('v1076_generic_retimer',C/'retime_complete.py');x=json.loads((R/'runs/v1069_retained_goal_corridor/ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());a=np.load(O/'PATH_PHASE_DIAGNOSIS.npz');q=retimer.propose(x['setup'],x['packet'],x['source'],x['goal'],a['requests']);old=np.load(O/'COMPLETE_GOAL_SOURCE.npz');parity={k:float(abs(q[k]-old[k]).max())for k in ['states','controls','requests']};assert q['passed']and max(parity.values())<=1e-8;negative=[]
for name,rr in [('truncated_tail',a['requests'][:-201]),('reverse_input',np.vstack([[-.03,0,0],a['requests']]))]:
 try:retimer.propose(x['setup'],x['packet'],x['source'],x['goal'],rr);raise RuntimeError('BAD_ACCEPT '+name)
 except AssertionError:negative.append(name)
result={k:v for k,v in q.items()if k not in ['states','controls','requests']};result.update(original_python_parity=parity,negative_cases=negative,no_saved_path_access_in_generic_function=True);(O/'GENERIC_RETIMER_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
