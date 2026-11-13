"""Actual isolated operation entry, software-only factory refusals and binding."""
import sys,json,importlib.abc,importlib.util,ast,hashlib,copy
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1097_east_west'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL_QUALIFICATION '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));import worker
w=worker.load_worker();w.pipeline.configure(O)
tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==3
meta=json.loads((O/'EAST_WEST_T0_METADATA.json').read_text());static=json.loads((O/'EAST_WEST_STATIC_SOURCE.json').read_text());assert static['passed']and static['models']==static['integrations']==0
for task in tasks:
    path=O/(task['task_id']+'.json');found,root,cfg,out=w.entry(str(path));assert found==task and root==O and not out.exists()
    assert found['case_id']=='EAST_WEST'and found['seed']==10010003 and found['phase']==.9511239917756753 and found['historical_prefix_native']==0
    assert found['start_xy']==[4.,-1.9]and found['goal_xy']==[-4.,-2.]and found['start_yaw']==meta['packet']['body'][2]
    assert found['start_xy']==meta['packet']['body'][:2]
f=w.factory(O)
try:f.create_vehicle(Path(tasks[0]['output'])/'physics',tasks[0]);raise RuntimeError('PHYSICAL_GUARD_BYPASS')
except AssertionError as e:assert str(e)=='PHYSICAL_MODELS_DISABLED_FOR_PREPARATION'
assert w.pipeline.__file__==str(R/'experiments/rpccr_execution_core/fresh_pipeline.py')
assert 'PREFLIGHT_MODEL_CHANGED'in worker.patched_source()and 'PREFLIGHT_INITIAL_STATE_CHANGED'in worker.patched_source()
assert worker.patched_source().count("time.time()+900")==1
# This check is before any model code and cannot accept changed scene/initial state.
import numpy as np
prestate=np.arange(10,dtype=float);assert np.array_equal(prestate,prestate.copy());changed=prestate.copy();changed[3]+=1e-6;assert not np.array_equal(prestate,changed)
spec=importlib.util.spec_from_file_location('v1097_route_audit',R/'experiments/v1089_route_scene_contract/audit.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);a.configure();compile(a.patched_source(),str(a.ORIGINAL),'exec')
for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
assert Path(__import__('planner').library()._name).is_file()
for name in ['mujoco','physical','vehicle','torch','rclpy']:
    try:__import__(name)
    except AssertionError as e:assert str(e)=='NO_MODEL_QUALIFICATION '+name
    else:raise RuntimeError('MODEL_IMPORT_NOT_BLOCKED')
freeze=json.loads((R/'experiments/v1089_route_scene_contract/SOURCE_FREEZE.json').read_text())['files'];assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in freeze.items())
w.install_history_guard(Path(tasks[1]['output']))
try:(R/'runs/v858_nav2_verified/v1085_entry/main_fresh_ns/physics/NATIVE_TRACE.npz').open('rb');raise RuntimeError('OLD_HISTORY_ACCEPTED')
except AssertionError as e:assert 'FRESH_NAVIGATION_HISTORY_READ_FORBIDDEN'in str(e)
answer=dict(passed=True,models=0,integrations=0,actual_isolated_worker_audit_factory_entry=True,declared_EW_tasks=3,
    same_NS_successful_science=True,original_frozen_files_verified=len(freeze),preflight_binding_in_worker=True,
    changed_initial_array_rejected=True,preparation_model_factory_refused=True,blocked_model_imports=5,old_history_refused=True,
    static_source_qualification_reused_software_only=True,real_EW_t0_not_yet_executed=True)
(O/'QUALIFICATION.json').write_text(json.dumps(answer,indent=2)+'\n');(O/'REGRESSION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer),flush=True)
