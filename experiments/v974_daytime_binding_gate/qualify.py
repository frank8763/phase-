"""Real worker/planner seams and actual t0 guard with explicit model-free fixtures."""
import ast,hashlib,importlib.abc,importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace as S
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v974_daytime_binding_gate'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','torch','vehicle','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel())
checks={}
for mode in ['native','planner']:
 old=json.loads((R/'runs/v972_daytime_binding_probe'/('v971_night_entry_continuation_'+mode+'.json')).read_text());new=json.loads((R/'runs/v972_daytime_binding_probe'/('v974_daytime_binding_gate_'+mode+'.json')).read_text())
 checks[mode+'_old_wrong_binding_is_red']=old['passed']is False
 checks[mode+'_actual_fixed_seam_is_green']=new['passed']is True and new['models']==new['integrations']==0
spec=importlib.util.spec_from_file_location('v974_tested_physical_guard',C/'physical.py');physical=importlib.util.module_from_spec(spec);spec.loader.exec_module(physical)
control=physical.base.module.control.Adapter
original=physical.base.create_vehicle
out=O/'binding_fixture';out.mkdir(exist_ok=False)
setup=json.loads((R/'runs/v858_nav2_verified/v968/closed_handoff/physics/SETUP.json').read_text());sensor=json.loads((R/'runs/v858_nav2_verified/v968/closed_handoff/physics/EXACT_SENSOR_BINDING.json').read_text())
(out/'SETUP.json').write_text(json.dumps(setup));(out/'EXACT_SENSOR_BINDING.json').write_text(json.dumps(sensor))
fake=S(count=0,d=S(time=0.),adapter=control.__new__(control),steering_sample=lambda:None)
physical.base.create_vehicle=lambda *_:fake
try:
 physical.create_vehicle(out,{})
 checks['actual_factory_guard_accepts_declared_adapter_and_sensor']=json.loads((out/'SELECTED_NATIVE_BINDING.json').read_text())['passed']
 old_setup=json.loads((R/'runs/v858_nav2_verified/v968/main_we/physics/SETUP.json').read_text());(out/'SETUP.json').write_text(json.dumps(old_setup))
 try:physical.create_vehicle(out,{})
 except(KeyError,AssertionError):checks['actual_old_saved_wrong_adapter_is_rejected_before_step']=True
 else:checks['actual_old_saved_wrong_adapter_is_rejected_before_step']=False
 (out/'SETUP.json').write_text(json.dumps(setup));fake.count=1
 try:physical.create_vehicle(out,{})
 except AssertionError:checks['binding_after_integrations_rejected']=True
 else:checks['binding_after_integrations_rejected']=False
finally:physical.base.create_vehicle=original
for entry in json.loads((C/'MODULE_BINDINGS.json').read_text())['aliases']:
 p=R/entry['alias'];target=R/entry['source'];assert p.is_symlink()and p.resolve()==target and hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(target.read_bytes()).digest()
checks['all_science_aliases_exact_frozen_source']=True
for p in C.glob('*.py'):ast.parse(p.read_text(),str(p))
checks['all_entry_source_AST']=True
flow=json.loads((O/'FULL_PLANNER_FLOW_QUALIFICATION.json').read_text());checks['real_Nav2_global_plan_to_nonzero_RPP']=flow['passed']
tasks=json.loads((C/'TASKS.json').read_text());checks['exact_one_original_task']=len(tasks)==1 and tasks[0]['seed']==10010001 and tasks[0]['case_id']=='WEST_EAST'and tasks[0]['phase']==.6573753567727383 and tasks[0]['wall_limit_s']==180 and tasks[0]['brake_s']==2.
result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,fixture_only=True,scope='Actual resolver/coroutine and t0 factory guard; model-free fixtures are not model or sensor qualification.')
(O/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']
