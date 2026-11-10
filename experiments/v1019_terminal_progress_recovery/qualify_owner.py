"""Actual native commitment/goal-completion guards with a metadata vehicle only."""
import copy,hashlib,importlib.abc,importlib.util,json,sys,tempfile,types
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1019_terminal_progress_recovery';sys.path[:0]=[str(C),str(R/'experiments/v1018_input_progress_night'),str(R/'experiments/v1004_planned_input_navigation')]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('NO_MODEL_NATIVE_QUALIFICATION '+name)
sys.meta_path.insert(0,NoModel())
spec=importlib.util.spec_from_file_location('real_goal_native',C/'native_contract.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
f=json.loads((O/'TERMINAL_CAPTURE_PLAN.json').read_text());record=dict(plan=f['plan'],packet=f['packet'],source=f['source']);switches=[]
m.original.switch=lambda *args:(switches.append('metadata-only')or dict(physical_state_unchanged=True))
with tempfile.TemporaryDirectory(prefix='owner-',dir=O)as td:
 out=Path(td)
 def session():
  initial=np.asarray(record['plan']['initial']['state']);v=types.SimpleNamespace(count=record['packet']['native_tick'],state=initial.copy(),adapter=types.SimpleNamespace(last=np.asarray(record['plan']['initial']['last_ctrl']),integral=record['plan']['initial']['integral']))
  v.body=lambda:[v.state[0],v.state[1],v.state[2],v.state[3],v.state[5]]
  owner=m.Startup(record['packet']['run_id']);owner.phase='RUNNING';owner.armed_at=0.;owner.bind_vehicle(v,out)
  def step(*args):v.state=np.asarray(record['plan']['state_path'][owner.profile_index+1]);v.count+=1
  v.step=step;return owner,v
 def submit(owner,data):
  path=out/'profile.json';raw=json.dumps(data).encode();path.write_bytes(raw)
  packet=dict(kind='commit_profile',run_id=owner.run_id,issued_at=10.,profile_id=1,path=str(path),sha256=hashlib.sha256(raw).hexdigest())
  owner.receive(packet,10.005,record['packet']['native_tick'],record['packet']['sim_time'])
 owner,v=session();submit(owner,record);assert owner.profile is not None and switches==['metadata-only']
 for i in range(len(record['plan']['planned_body_requests'])):owner.step(v,10.+i*.01)
 assert owner.holding and owner.profile is None and owner.profiles[0]['completed']and np.linalg.norm(v.state[:2]-record['plan']['original_goal'])<=.45
 bad=copy.deepcopy(record);bad['plan']['terminal_goal_distance_upper_m']=.5;owner,v=session();before=len(switches)
 try:submit(owner,bad)
 except AssertionError:assert owner.profile is None and not owner.holding and len(switches)==before
 else:raise AssertionError('FALSE_CAPTURE_COMMITTED')
 result=dict(passed=True,models=0,integrations=0,actual_production_receiver=True,actual_native_completion_guard=True,metadata_steps=len(record['plan']['planned_body_requests']),false_goal_bound_rejected_before_control_switch=True,scope='Metadata scheduling only; not physical tracking')
 (O/'NATIVE_GOAL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
