"""Real isolated worker/audit installation and original negative safety gates."""
import sys,json,ast,importlib.abc,importlib.util,copy
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1092_stopped_replan'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('MODELS_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));import worker
w=worker.load_worker();owner=w.pipeline.configure(O)
for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==2
for task in tasks:
    found,root,cfg,out=w.entry(str(O/(task['task_id']+'.json')))
    assert found==task and not out.exists()and found['historical_prefix_native']==0
f=w.factory(O)
try:f.create_vehicle(Path(tasks[0]['output'])/'physics',tasks[0]);raise RuntimeError('MODEL_GUARD_BYPASSED')
except AssertionError as e:assert str(e)=='PHYSICAL_MODELS_DISABLED_FOR_PREPARATION'
assert w.pipeline.__file__==str(C/'pipeline.py')and callable(w.pipeline.execute)
s=importlib.util.spec_from_file_location('finite_all_source_audit',C/'audit.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.patched_module()
assert callable(m.audit)and callable(m.rebuild_corridor_or_original)
assert Path(__import__('planner').library()._name).is_file()
import corridor,numpy as np
x=json.loads((R/'runs/v1092_stopped_replan_preparation/ACTUAL_STOPPED_INPUT.json').read_text())
short,_,_=corridor.proof(x['setup'],x['packet'],x['source'],np.zeros((2199,3)));assert not short['passed']
bad=copy.deepcopy(x['source']);bad['source_native_tick']=x['packet']['native_tick']+1
try:corridor.proof(x['setup'],x['packet'],bad,np.zeros((2200,3)));raise RuntimeError('FUTURE_SOURCE_ACCEPTED')
except AssertionError as e:assert str(e)=='NONCAUSAL_RECOVERY_SOURCE'
assert json.loads((O/'QUALIFICATION.json').read_text())['passed']
assert json.loads((R/'runs/v1091_certified_exit/FINALIZED.json').read_text())['passed']
w.install_history_guard(Path(tasks[0]['output']))
try:(R/'runs/v858_nav2_verified/v1091/exit_saved_we/physics/NATIVE_TRACE.npz').open('rb');raise RuntimeError('OLD_TRACE_READ_ALLOWED')
except AssertionError as e:assert 'FRESH_NAVIGATION_HISTORY_READ_FORBIDDEN'in str(e)
print(json.dumps(dict(passed=True,models=0,integrations=0,real_isolated_worker_and_audit=True,all_two_task_entries=True,
                     production_pipeline_bound=True,original_actual_exit_qualified=True,short_tail_rejected=True,
                     future_source_rejected=True,old_physical_history_rejected=True,goal_success_only_actual=True)),flush=True)
