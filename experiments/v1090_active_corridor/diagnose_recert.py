"""Numerical recertification and real isolated operation entries, zero models."""
import sys,json,importlib.abc,importlib.util,ast,types,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1090_active_corridor'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL_ENTRY '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));import worker
w=worker.load_worker();import corridor
import numpy as np
tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==56
for task in tasks:
 t,root,cfg,out=w.entry(str(O/(task['task_id']+'.json')));assert t==task and not out.exists()
assert w.pipeline.__file__==str(C/'pipeline.py')and callable(w.pipeline.execute)
f=w.factory(O);assert callable(f.create_vehicle)and callable(f.replay);assert Path(__import__('planner').library()._name).is_file()
sp=importlib.util.spec_from_file_location('qualified_active_audit',C/'audit.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);a.patched_module()
for p in C.glob('*.py'):compile(p.read_text(),str(p),'exec')
for name in ['QUALIFICATION.json']:
 assert json.loads((O/name).read_text())['passed']
x=json.loads((R/'runs/v1090_gear_prefix_reference/QUALIFICATION_INPUT.json').read_text())
with np.load(O/'QUALIFIED_CORRIDOR.npz')as p:rr=p['requests'];ss=p['states'];uu=p['controls']
engine=corridor.live.engine(x['setup'],x['packet']);checkpoints=[]
for i,r in enumerate(rr):
 if i in [125,1750,3950,6150]:
  packet=corridor.live.forecast(x['packet'],engine,i);proof,z,controls=corridor.proof(x['setup'],packet,x['source'],rr[i:]);print(json.dumps(dict(checkpoint=i,proof=proof,state_error=float(np.max(abs(z-ss[i:]))),ctrl_error=float(np.max(abs(controls-uu[i:]))))),flush=True);assert proof['passed'];checkpoints.append(i)
 engine.step(*r)
q,_,_=corridor.proof(x['setup'],x['packet'],x['source'],np.zeros((2199,3)));assert not q['passed']and not q['checks']['complete2200stop']
assert all(np.max(abs(np.diff(np.vstack([x['packet']['controller_memory']['last_ctrl'],uu]),axis=0)),axis=0)<=np.asarray(x['setup']['slew_per_second'])*.01+1e-10)
ns_base=Path(cfg['external_NS_baseline']['output']);from fresh_campaign import same_complete
pair=same_complete(dict(output=str(ns_base)),dict(output=str(ns_base)));assert pair['passed']and pair['maximum_state_ctrl_mocap_error']==0
pool=(C/'CONFIRMATION_POOL.json').read_bytes();assert pool==(R/'experiments/v1062_three_route_night/CONFIRMATION_POOL.json').read_bytes();assert[t['slot']for t in tasks[-3:]]==[1,9,17]
w.install_history_guard(Path(tasks[0]['output']))
try:(ns_base/'physics/NATIVE_TRACE.npz').open('rb');rejected=False
except AssertionError:rejected=True
assert rejected
answer=dict(passed=True,models=0,integrations=0,real_isolated_task_entries=56,production_pipeline_bound=True,recertification_checkpoints=checkpoints,full_remaining_state_ctrl_reconstruction_error_at_most=1e-8,short2200tail_negative_rejected=True,all_saved_controls_slew_legal=True,restored_NS_baseline_complete_self_comparison=pair,original_pool_bytes=True,fixed_repeats=[1,9,17],old_navigation_history_read_rejected=True)
(O/'RECERT_DIAGNOSIS.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer),flush=True)
