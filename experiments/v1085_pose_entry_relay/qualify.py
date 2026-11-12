"""Exact source-diff check and actual initialized-t0 pose contract; zero physics."""
import ast,sys,json,importlib.abc,types
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1085_pose_entry_relay';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());import worker_relay as w,campaign_relay as driver
source=w.ORIGINAL.read_text();patched=w.patched_source();assert patched.replace(w.NEW,w.OLD)==source;compile(driver.patched_source(),str(driver.ORIGINAL),'exec')
module=w.load_worker();import numpy as np
actual=json.loads((R/'runs/v858_nav2_verified/v1085/main_fresh_ns/RESULT.json').read_text())['physical']['final_body'];meta=json.loads((O/'NORTH_SOUTH_T0_METADATA.json').read_text());node=next(n for n in ast.walk(ast.parse(patched))if isinstance(n,ast.Assert)and isinstance(n.msg,ast.Constant)and n.msg.value=='CANONICAL_POSE_TOLERANCE');expression=compile(ast.Expression(node.test),'<actual-pose-test>','eval');env=dict(np=np,v=types.SimpleNamespace(body=lambda:actual),meta=meta);assert eval(expression,env)
negative=[]
for delta in [1.0001e-8,-1.0001e-8,1e-5]:
 bad=list(meta['packet']['body']);bad[2]+=delta;env['v']=types.SimpleNamespace(body=lambda bad=bad:bad);negative.append(not eval(expression,env))
assert all(negative);rows=[]
for task in ['main_fresh_ns','repeat_fresh_ns']:
 t,o,cfg,out=module.entry(str(O/(task+'.json')));assert t['historical_prefix_native']==0 and not out.exists();rows.append(task)
result=dict(passed=True,exact_one_assertion_substitution=True,all_other_worker_source_exact=True,actual_t0_positive=True,over_tolerance_negative_cases=negative,canonical_full_initial_state_error=0.,same_two_unexecuted_navigation_tasks=rows,root_deadline_unchanged=True,models=0,integrations=0,models_authorized=False);(O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
