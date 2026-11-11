"""Production Owner with metadata trajectories, no real vehicle/model APIs."""
import importlib.abc,json,sys,time,types
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1024_full_route_execution';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel());from owner import Owner
plan=json.loads((R/'runs/v1023_dense_input_route/we_initial.json').read_text());ss=np.asarray(plan['state_path']);rr=plan['planned_body_requests'];calls=[]
def vehicle():
 v=types.SimpleNamespace(count=0,index=0,state=ss[0].copy());v.body=lambda:[*v.state[:4],v.state[5]]
 def step(*request):
  assert list(request)==rr[v.index];v.index+=1;v.count+=1;v.state=ss[v.index].copy()
 v.step=step;return v
v=vehicle();owner=Owner(v,time.time()+300.,lambda:False);done=owner.execute(plan,True);assert done['completed']and owner.phase=='STOPPED'and v.count==len(rr)
v=vehicle();owner=Owner(v,time.time()+300.,lambda:v.count>=1000);stop=owner.execute(plan,True);assert stop['interrupted_by_causal_discovery']and v.count==1000 and owner.phase=='BRAKE_REQUIRED'
try:owner.execute(plan)
except AssertionError as e:assert str(e)=='MULTIPLE_CONTROL_OWNERS';suffix_blocked=True
else:raise AssertionError('REVOKED_STATIC_SUFFIX_EXECUTED')
owner.authorize_brake();assert owner.phase=='STOPPED'
v=vehicle();bad=Owner(v,time.time()+100.,lambda:False)
try:bad.execute(plan)
except AssertionError as e:assert str(e)=='ABSOLUTE_MODEL_STOP_RESERVE'and v.count==0;deadline_blocked=True
else:raise AssertionError('DEADLINE_STARTED')
v=vehicle();native=v.step
v.step=lambda *args:(native(*args),v.state.__setitem__(0,v.state[0]+.041))
try:Owner(v,time.time()+300.,lambda:False).execute(plan)
except AssertionError as e:assert str(e)=='NATIVE_TRACKING_FAILED'and v.count==1;tracking_blocked=True
else:raise AssertionError('BAD_TRACKING_ACCEPTED')
out=dict(passed=True,actual_production_scheduler=True,complete_metadata_steps=len(rr),first_discovery_interrupt_tick=1000,revoked_static_suffix_blocked=suffix_blocked,
 absolute_deadline_before_first_step=deadline_blocked,first_bad_tracking_stops=tracking_blocked,models=0,integrations=0,physical_ready=False)
(O/'OWNER_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
