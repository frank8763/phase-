"""Actual old trigger block at saved282; expected red before added renewal."""
import importlib.abc,json,math,sys,textwrap
from pathlib import Path
import numpy as np
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('RED_TRIGGER_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
repo=Path(__file__).resolve().parents[2];cell=repo/'runs/v821_norm_route_development/main_slot02/paired/geometry_memory'
read=lambda p:json.loads(p.read_text());route=next(json.loads(s)for s in(cell/'route_revalidation.jsonl').read_text().splitlines()if json.loads(s)['step']==282)
current=np.asarray(read(repo/'runs/v823_global_continuation_diagnosis/renewal_probe/INPUT_0282.json')['pose']);path=np.asarray(route['reference_path']);index=route['index']
source=(repo/'experiments/v821_norm_route_development/run_static.py').read_text();begin=source.index("                            if keep['current_route_invalid']:need=True");end=source.index('                        if need and backup_remaining==0:',begin)
block=textwrap.dedent(source[begin:end]);scope=dict(np=np,wrap=lambda a:(a+np.pi)%(2*np.pi)-np.pi,need=False,keep=route,path=path,index=index,current=current,rows=[],step=282,last_plan=265,distances=np.linalg.norm(path[index:index+40,:2]-current[:2],axis=1))
exec(compile(block,'ORIGINAL_RUN_STATIC_TRIGGER_BLOCK','exec'),scope)
out=dict(status='ORIGINAL_TRIGGER_REPRODUCED',step=282,old_need=bool(scope['need']),new_observation=True,full_goal_reference_previously_proven=True,models=0,integrations=0,scope='Actual replanning call-site trigger block, not full navigation regression')
p=repo/'runs/v826_goal_reference_renewal/zero_model_interfaces/OLD_TRIGGER_RED.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
assert scope['need'],'EXPECTED_RED_MISSED_GOAL_REFERENCE_RENEWAL'
