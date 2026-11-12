"""Tamper real saved records; the same native auditor must reject each."""
import sys,importlib.abc,json,copy,gzip,hashlib
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from kernel import *
pin_threads();sys.path.insert(0,str(C));from audit import audit_native
fixture=O/'saved_actual_fixture';setup=json.loads((fixture/'physics/SETUP.json').read_text());preflight=O/'PREFLIGHTS.json';assert not preflight.exists();dump(preflight,dict(qualified_archived_input=dict(setup=setup)));task=dict(output=str(fixture),case_id='WEST_EAST',goal_xy=[4.,-2.],preflight_task_id='qualified_archived_input');negative=[]
def denied(name):
 try:
  result=audit_native(task,O/('negative_'+name));assert not result['passed']and not result['safety_passed'],'TAMPER_ACCEPTED'
 except (AssertionError,ValueError,KeyError,IndexError)as error:
  assert str(error)!='TAMPER_ACCEPTED';negative.append(dict(name=name,rejection=str(error)))
 else:negative.append(dict(name=name,rejection='saved safety gate false'))
try:
 journal=fixture/'DIRECT_SEGMENTS.json';original=journal.read_bytes();rows=json.loads(original);plan=json.loads((R/rows[0]['path']).read_text());plan['packet']['body'][0]+=.001;fake=O/'TAMPERED_DIRECT_PLAN.json';dump(fake,plan);rows[0]['path']=str(fake.relative_to(R));dump(journal,rows)
 try:denied('planning_body_not_actual')
 finally:journal.write_bytes(original);fake.unlink()
 path=fixture/'physics/BODY_COMMANDS.json';target=path.resolve();commands=json.loads(path.read_text());commands[0][1]+=.001;path.unlink();path.write_text(json.dumps(commands))
 try:denied('causal_request_changed')
 finally:path.unlink();path.symlink_to(target)
 path=fixture/'physics/SENSORS.json.gz';target=path.resolve()
 with gzip.open(path,'rt')as f:scans=json.load(f)
 scans.insert(4,scans[3]);path.unlink()
 with gzip.open(path,'wt')as f:json.dump(scans,f)
 try:denied('duplicate_owner_scan')
 finally:path.unlink();path.symlink_to(target)
 assert len(negative)==3;dump(O/'SAVED_NATIVE_NEGATIVE_QUALIFICATION.json',dict(passed=True,negative_cases=negative,actual_saved_native=50728,auditor_sha256=sha(C/'audit.py'),models=0,integrations=0));print(json.dumps(dict(passed=True,negative_cases=negative,models=0)),flush=True)
finally:preflight.unlink()
