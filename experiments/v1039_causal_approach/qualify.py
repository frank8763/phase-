"""Production interfaces and finite-profile executor, with no model permission."""
import ast,copy,hashlib,importlib.abc,importlib.util,json,subprocess,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1039_causal_approach'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
worker=load('v1039_qualified_worker',C/'worker.py');factory=load('v1039_qualified_factory',R/'experiments/v1020_terminal_two_route_development/physical.py');assert callable(factory.create_vehicle)
audit=load('v1039_qualified_audit',C/'audit.py');assert Path(audit.audit.__code__.co_filename).resolve()==C/'audit.py';assert Path(worker.owner_module.Owner.execute.__code__.co_filename).resolve()==R/'experiments/v1030_declared_course_dynamic/owner.py'
H=worker.H;initial=json.loads((H/'DYNAMIC_COMPLETE_PLAN.json').read_text());setup=json.loads((H/'physics/SETUP.json').read_text());requests=np.asarray(json.loads((C/'REQUESTS.json').read_text()));expected=json.loads((O/'SOURCE_QUALIFICATION.json').read_text());actual=worker.component.plan(initial['packet'],initial['source'],setup,requests);assert actual['passed']and actual['state_path']==expected['state_path']and actual['predicted_actuator_controls']==expected['predicted_actuator_controls']
checks=dict(actual_factory_zero_model_import=True,exact_qualified_owner_binding=True,exact_own_audit_binding=True,actual_fresh_plan_function_exact=True);negative=[]
for label,mutation in [('future_source',lambda p,s:s.update(source_native_tick=p['native_tick']+1)),('stale_source',lambda p,s:s.update(source_age_s=.21)),('wrong_frequency',lambda p,s:s['periodic'].update(omega=.33))]:
 p=copy.deepcopy(initial['packet']);s=copy.deepcopy(initial['source']);mutation(p,s)
 try:worker.component.plan(p,s,setup,requests)
 except AssertionError:negative.append(label)
 else:raise AssertionError('INVALID_SOURCE_ACCEPTED '+label)
class Plant:
 def __init__(self,offset=None):self.states=np.asarray(actual['state_path']);self.count=16740;self.offset=offset
 def body(self):
  i=self.count-16740;s=self.states[i].copy()
  if self.offset and i==4:s[self.offset[0]]+=self.offset[1]
  return [*s[:4],s[5]]
 def step(self,*request):assert np.array_equal(request,requests[self.count-16740]);self.count+=1
plant=Plant();owner=worker.owner_module.Owner(plant,time.time()+200,lambda:False);execution=owner.execute(actual);assert execution['completed']and plant.count==23640;checks['production_native_schedule_6900']=True
for label,offset in [('position', (0,.041)),('heading',(2,.036))]:
 try:worker.owner_module.Owner(Plant(offset),time.time()+200,lambda:False).execute(actual)
 except AssertionError:negative.append(label)
 else:raise AssertionError('NATIVE_ERROR_NOT_REJECTED')
bad=copy.deepcopy(actual);bad['planned_body_requests'][-1][0]=.03
try:worker.owner_module.Owner(Plant(),time.time()+200,lambda:False).execute(bad)
except AssertionError:negative.append('missing_full_tail')
else:raise AssertionError('MISSING_TAIL_ACCEPTED')
# Exercise the exact installed command while REVIEW_PENDING still blocks it.
tree=ast.parse((C/'campaign.py').read_text());call=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='Popen');rp=O/'NOT_AUTHORIZED.json';args=eval(compile(ast.Expression(call.args[0]),str(C/'campaign.py'),'eval'),dict(str=str,R=R,C=C,rp=rp));p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=5);assert p.returncode==2 and 'PAUSED_PENDING_USER_REVIEW'in p.stderr;checks['exact_production_command_pause_gate']=True
# Qualified saved-audit implementation is run against the old full actual
# trace shape to verify imports; it must reject absence of this new component.
task=dict(json.loads((C/'TASK.json').read_text()),output=str(H));old_hash=hashlib.sha256((H/'FINAL_INDEPENDENT_AUDIT.json').read_bytes()).hexdigest();proof=audit.audit(task);assert not proof['passed'] and not proof['checks']['new_component_present'];checks['actual_saved_audit_missing_component_rejected']=True
assert hashlib.sha256((H/'FINAL_INDEPENDENT_AUDIT.json').read_bytes()).hexdigest()==old_hash;checks['old_audit_exact_bytes_unchanged']=True
try:audit.audit(task,save=True)
except AssertionError:negative.append('audit_write_outside_new_batch')
else:raise AssertionError('OLD_AUDIT_WRITE_NOT_REJECTED')
for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['all_sources_parse']=True;assert not Path(json.loads((C/'TASK.json').read_text())['output']).exists();checks['new_output_root']=True
result=dict(passed=all(checks.values()),checks=checks,rejected_negative_cases=negative,models=0,integrations=0);(O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
