"""Real isolated four-task entry and public per-route binding, zero models."""
import sys,json,ast,importlib.abc
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1088_remaining_routes'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
import worker,campaign
w=worker.load_worker();import numpy as np
source=worker.patched_source();assert source.replace(worker.NEW,worker.OLD)==worker.worker_relay.patched_source()
compile(campaign.patched_source(),str(campaign.ORIGINAL),'exec')
tasks=json.loads((C/'TASKS.json').read_text());bindings=[]
cases={c['id']:c for c in json.loads((R/'experiments/v1067_causal_replan_brake_reserve/SCENE_CASES.json').read_text())}
pose_node=next(n for n in ast.walk(ast.parse(source))if isinstance(n,ast.Assert)and isinstance(n.msg,ast.Constant)and n.msg.value=='CANONICAL_POSE_TOLERANCE');pose=compile(ast.Expression(pose_node.test),'<production-pose>','eval')
import types
for task in tasks:
 t,root,cfg,out=w.entry(str(O/(task['task_id']+'.json')));assert t==task and root==O and not out.exists();case=cases[t['case_id']];meta=json.loads((O/(t['case_id']+'_T0_METADATA.json')).read_text());static=json.loads((O/(t['case_id']+'_STATIC_SOURCE.json')).read_text());assert static['passed']and static['audit']['passed']
 assert np.max(abs(np.asarray(meta['packet']['body'][:3])-np.asarray(case['start_xy']+[case['yaw']])))<=1e-8
 assert t['start_xy']==case['start_xy']and t['goal_xy']==case['goal_xy']and t['start_yaw']==case['yaw']and meta['goal']==t['goal_xy']
 assert np.array_equal(np.asarray(static['plan']['planned_body_requests'])[-200:],np.zeros((200,3)))
 actual=meta['packet']['body'];assert eval(pose,dict(np=np,v=types.SimpleNamespace(body=lambda:actual),meta=meta))
 other=json.loads((O/('EAST_WEST_T0_METADATA.json'if t['case_id']=='WEST_EAST'else'WEST_EAST_T0_METADATA.json')).read_text());assert not eval(pose,dict(np=np,v=types.SimpleNamespace(body=lambda:actual),meta=other))
 bindings.append(dict(task_id=t['task_id'],case_id=t['case_id'],metadata_matches_declared_course=True,wrong_route_metadata_rejected=True,initial_static_source_passed=True))
f=w.factory(O);owner=w.pipeline.configure(O);assert callable(f.create_vehicle)and callable(f.replay)and callable(owner.navigate)
assert Path(__import__('planner').library()._name).is_file()
sys.path.insert(0,str(R/'experiments/v1086_ns_complete_repeat'));import audit
audit.load_audit()
w.install_history_guard(Path(tasks[0]['output']))
try:(R/'runs/v858_nav2_verified/v1085_entry/main_fresh_ns/physics/NATIVE_TRACE.npz').open('rb');rejected=False
except AssertionError:rejected=True
assert rejected
answer=dict(passed=True,models=0,integrations=0,scientific_worker_source_unchanged_except_public_metadata_dispatch=True,old_ns_dispatch_resolves_identical_file=True,real_isolated_factory_and_planner_import=True,history_reads_rejected=True,bindings=bindings,old_scientific_qualification_reused=True)
(O/'QUALIFICATION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer),flush=True)
