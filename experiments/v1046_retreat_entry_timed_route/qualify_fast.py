"""Qualified Python versus proposal C++; no actual models or state writes."""
import importlib.abc,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1046_retreat_entry_timed_route'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));from whole_input import Predictor,PARAMETERS,initial;from fast_predict import Expander
fixture=json.loads((R/'records/nav2_v1022_20261111/NS_SOURCE_FIXTURE.json').read_text());x=json.loads((R/'runs/v1040_approach_information_audit/REBUILT_SOURCE.json').read_text());maximum=0.;steps=0
for row in [dict(setup=fixture['setup'],packet=fixture['packet']),x]:
 setup=row['setup'];p=initial(row['packet']);engine=Expander(setup)
 for speed in [-.03,.03,.08]:
  for target in np.linspace(-.42722137342572125,.42722137342572125,5):
   original=Predictor(setup,p,PARAMETERS);state=original.state.copy();memory=np.r_[original.adapter.last,original.adapter.integral]
   for moving,n in [(True,300),(False,200)]:
    v=speed if moving else 0.;w=v*np.tan(target)/.6;ss,uu,mm=engine.expand(state,memory,np.array([target]),n,np.array([v]))
    for i in range(n):s,u=original.step(v,w,False);maximum=max(maximum,float(abs(s-ss[0,i]).max()),float(abs(u-uu[0,i]).max()));steps+=1
    state=ss[0,-1];memory=mm[0]
assert maximum<=1e-10
out=dict(passed=True,models=0,integrations=0,complete_branch_steps=steps,maximum_state_ctrl_difference=maximum,exact_original_allocator=True,actual_forward_short_responses_passed=json.loads((R/'runs/v1044_curvature_speed_prediction/COMPLETION.json').read_text())['passed']);out['reverse_physically_qualified']=False;out['actual_response_scope']='V1044 forward .08 short responses only';(O/'FAST_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
