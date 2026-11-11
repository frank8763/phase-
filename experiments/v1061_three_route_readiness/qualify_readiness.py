"""Manifest identity, original EW exclusion, and hard model-disabled gates."""
import ast,copy,importlib.abc,json,sys
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from contracts import validate_tasks,readiness,launch_physics
from execute import ProcessJob
pin_threads();tasks=json.loads((C/'TASKS.json').read_text());assert validate_tasks(tasks);negative=[]
for name,change in [('missing_task',lambda t:t.pop()),('changed_start',lambda t:t[4]['start_xy'].__setitem__(1,-1.8)),('changed_goal',lambda t:t[2]['goal_xy'].__setitem__(0,0.)),('changed_goal_yaw',lambda t:t[2].update(goal_yaw=0.)),('changed_phase',lambda t:t[1].update(phase=0.)),('changed_seed',lambda t:t[3].update(seed=10019999)),('changed_order',lambda t:t.reverse()),('shared_output',lambda t:t[1].update(output=t[0]['output']))]:
 candidate=copy.deepcopy(tasks);change(candidate)
 try:validate_tasks(candidate)
 except AssertionError:negative.append(name)
 else:raise AssertionError('TASK_IDENTITY_MUTATION_ACCEPTED '+name)
for label,fn in [('explicit_model_launcher',launch_physics),('implicit_old_window',remaining_root)]:
 try:fn()
 except(PermissionError,AssertionError):negative.append(label)
 else:raise AssertionError('MODEL_OR_WINDOW_NOT_BLOCKED')
try:__import__('mujoco')
except AssertionError:negative.append('mujoco_import_before_loading_blocked')
else:raise AssertionError('MODEL_IMPORT_ALLOWED')
assert ProcessJob.__init__.__globals__['C']==C,'PRODUCER_WRONG_NAMESPACE'
# Existing atomic/hold gates used in the requalified publication path are
# unchanged by the generic-profile performance optimization.
old_ast=ast.parse((R/'experiments/v1058_fresh_repeat_entry/handoff.py').read_text());new_ast=ast.parse((C/'baseline_handoff.py').read_text());names=['parked','source_check','hold_permission','planes','contained'];old={n.name:ast.dump(n,include_attributes=False)for n in old_ast.body if isinstance(n,ast.FunctionDef)};new={n.name:ast.dump(n,include_attributes=False)for n in new_ast.body if isinstance(n,ast.FunctionDef)};assert all(old[n]==new[n]for n in names)
static={case:json.loads((O/(case+'_STATIC_SOURCE.json')).read_text())for case in ['WEST_EAST','NORTH_SOUTH','EAST_WEST']};meta=json.loads((O/'EAST_WEST_T0_METADATA.json').read_text());ss,dd=ref._old.Geometry(meta['setup']['known'],None).clearances(np.array([meta['packet']['body'][:3]]));initial=float(ss[0]);assert initial<REQUIRED and static['EAST_WEST']['plan']['expanded']==0 and not static['EAST_WEST']['passed'];assert all(static[c]['passed']for c in ['WEST_EAST','NORTH_SOUTH']);ew=dict(passed=False,scope='canonical metadata initial contract only; not new physical contact audit',raw_static_clearance_m=initial,required_raw_m=REQUIRED,deficit_m=REQUIRED-initial,start_unchanged=meta['packet']['body'][:3],cannot_pass_same_uniform_contract_by_more_search=True,models=0,integrations=0);dump(O/'EAST_WEST_ORIGINAL_START_GATE.json',ew)
active_static=dict(static);active_static['EAST_WEST']=json.loads((O/'EAST_WEST_ACTIVE_STATIC_SOURCE.json').read_text());assert active_static['EAST_WEST']['declared_new_course']and not active_static['EAST_WEST']['original_canonical_task_passed']
publication=json.loads((O/'PUBLICATION_QUALIFICATION.json').read_text());contract=json.loads((O/'CONTRACT_QUALIFICATION.json').read_text());ns=json.loads((O/'NS_SOFTWARE_CONTRACT_QUALIFICATION.json').read_text());scene=json.loads((O/'SCENE_BINDING_QUALIFICATION.json').read_text());fixed=json.loads((O/'FIXED_CLOCK_PUBLICATION_AUDIT.json').read_text());independent=json.loads((O/'INDEPENDENT_SOFTWARE_AUDIT.json').read_text());assert scene['passed']and fixed['passed']and independent['passed'];result=readiness(tasks,active_static,publication,contract,ns);result.update(model_disabled_negative_cases=negative,course_id=json.loads((C/'COURSE.json').read_text())['id'],only_EW_start_north_010_user_selected=True,original_EW_task_still_rejected=True,scene_array_binding_passed=True,new_MJB_initialization_qualified=False,publication_hold_functions_ast_unchanged=True,correct_analytical_producer_namespace=True,user_selected_no_models=True,old_failures_and_windows_unchanged=True);assert result['preparation_checks_passed']and result['route_admission_passed']and not result['models_authorized']and not result['ready_for_physics']
for path in C.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
assert not any((C/name).exists()for name in ['worker.py','start.py','driver.py']);assert all(not Path(t['output']).exists()for t in tasks);dump(O/'READINESS.json',result);print(json.dumps(result))
