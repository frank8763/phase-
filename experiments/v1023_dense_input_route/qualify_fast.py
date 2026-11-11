import importlib.abc,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1023_dense_input_route';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel());from whole_input import Predictor,PARAMETERS,initial;from fast_predict import Expander
fixture=json.loads((R/'records/nav2_v1022_20261111/NS_SOURCE_FIXTURE.json').read_text());setup=fixture['setup'];original=Predictor(setup,initial(fixture['packet']),PARAMETERS);engine=Expander(setup);cap=.42722137342572125;rows=[]
for group in range(12):
 state=original.state.copy();memory=np.r_[original.adapter.last,original.adapter.integral];targets=np.linspace(-cap,cap,5);speeds=np.array([.03]*5)if group%2==0 else np.array([0.]*5)
 ss,uu,mm=engine.expand(state,memory,targets,speeds=speeds)
 errors=[]
 for j,target in enumerate(targets):
  p=Predictor(setup,dict(state=state,last_ctrl=memory[:4],integral=memory[4],virtual_rate=.6),PARAMETERS);vs=[];us=[]
  for _ in range(334):s,u=p.step(speeds[j],speeds[j]*np.tan(target)/.6,False);vs.append(s);us.append(u)
  errors.append(max(float(abs(ss[j]-vs).max()),float(abs(uu[j]-us).max()),float(abs(mm[j]-np.r_[p.adapter.last,p.adapter.integral]).max())))
 pick=group%5
 for _ in range(334):original.step(speeds[pick],speeds[pick]*np.tan(targets[pick])/.6,False)
 rows.append(dict(group=group,braking=group%2==1,maximum_error=max(errors),passed=max(errors)<=1e-10))
out=dict(passed=all(x['passed']for x in rows),rows=rows,maximum_error=max(x['maximum_error']for x in rows),analytical_branch_steps=20040,models=0,integrations=0);(O/'FAST_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert out['passed']
