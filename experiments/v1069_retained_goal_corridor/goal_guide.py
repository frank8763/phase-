import sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
def reference(setup,packet,goal,actions=None):
 from kernel import predict,checks,ref,REQUIRED
 states=None
 if actions:
  s,u,r,m=predict(setup,packet,actions,tail=False);low=float(ref._old.Geometry(setup['known'],None).clearances(s[:,:3])[0].min());cc,upper=checks(s,u,r,packet,setup,np.asarray(goal),low,REQUIRED)
  if all(cc.values()):states=s
 if states is None:
  import importlib.util
  p=R/'experiments/v1068_recovery_value_diagnosis/static_planner.py';s=importlib.util.spec_from_file_location('v1069_static_phase_free_guide',p);module=importlib.util.module_from_spec(s);s.loader.exec_module(module)
  result=module.construct(setup,packet,None,goal,wall_s=4.,max_expansions=5000)
  assert result['passed']and result['functional_goal_source'],'NO_COMPLETE_STATIC_GUIDANCE'
  states=np.asarray(result['state_path'])
 indices=list(range(0,len(states),25))
 if indices[-1]!=len(states)-1:indices.append(len(states)-1)
 return np.ascontiguousarray(states[indices][:,[0,1,2,3]])
