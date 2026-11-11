"""Differential qualification against the unchanged causal Python predictor."""
import importlib.abc,json,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0] in {'mujoco','torch','vehicle','physical','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel())
from whole_input import Predictor,PARAMETERS,initial
from fast_predict import Expander
setup=json.loads((R/'runs/v858_nav2_verified/v1020/PREFLIGHTS/ns/SETUP.json').read_text());p=json.loads((R/'runs/v858_nav2_verified/v1020/PREFLIGHTS/ns/PREFLIGHT.json').read_text())
packet=dict(body=p['body'],steering=dict(position=p['steering'][:2],velocity=p['steering'][2:]),controller_memory=dict(last_ctrl=[0.]*4,integral=0.))
reference=Predictor(setup,initial(packet),PARAMETERS);engine=Expander(setup);rng=np.random.default_rng(1022);rows=[];cap=.42722137342572125;start=time.monotonic()
# All five steering branches from each successive actual analytical memory.
for group in range(12):
 state=reference.state.copy();memory=np.r_[reference.adapter.last,reference.adapter.integral];targets=np.linspace(-cap,cap,5)
 states,controls,mem=engine.expand(state,memory,targets)
 errors=[]
 for i,target in enumerate(targets):
  origin=dict(state=state,last_ctrl=memory[:4],integral=memory[4],virtual_rate=.6);other=Predictor(setup,origin,PARAMETERS);ss=[];uu=[]
  for _ in range(334):
   s,u=other.step(.03,.03*np.tan(target)/.6,False);ss.append(s);uu.append(u)
  errors.append(max(float(abs(states[i]-ss).max()),float(abs(controls[i]-uu).max()),float(abs(mem[i]-np.r_[other.adapter.last,other.adapter.integral]).max())))
 selected=int(rng.integers(5))
 for _ in range(334):reference.step(.03,.03*np.tan(targets[selected])/.6,False)
 rows.append(dict(group=group,maximum_state_ctrl_memory_error=max(errors),passed=max(errors)<=1e-10))
out=dict(passed=all(x['passed']for x in rows),models=0,integrations=0,analytical_branch_steps=12*5*334,rows=rows,maximum_error=max(x['maximum_state_ctrl_memory_error']for x in rows),wall_s=time.monotonic()-start,physical_certificate=False)
(R/'runs/v1022_full_route_planner/FAST_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert out['passed']
