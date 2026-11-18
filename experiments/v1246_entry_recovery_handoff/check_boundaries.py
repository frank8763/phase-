"""No-propagation branch and stale real-packet rejection tests."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from package_loader import get_goal_entry
import importlib.util
from pathlib import Path
import copy,json,time
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
e=get_goal_entry();g=e.generate.__globals__;old=g['original'];status=g['entry_status'];cases=[]
try:
 g['entry_status']=lambda *a:('WHOLE_GOAL_READY',1.)
 result=dict(passed=True,preserved=True)
 g['original']=lambda *a,**kw:result
 assert e.generate({}, {},{},0,time.monotonic()+1,shadow_origin={}) is result
 cases.append('original_success_exact_object_retained')
 for value in ['ORIGINAL_SAFETY_REFUSED']:
  g['entry_status']=lambda *a,value=value:(value,0.)
  try:e.generate({}, {},{},0,time.monotonic()+1,shadow_origin={})
  except AssertionError:cases.append('unsafe_start_refused_before_recovery')
  else:raise AssertionError('UNSAFE_START_ACCEPTED')
finally:g['original']=old;g['entry_status']=status
x=json.loads((R/'runs/v858_nav2_verified/v1243/main_slot13/LIVE_GOAL_INPUT.json').read_text())
for name,fn in [('time',lambda p:p.update(sim_time=p['sim_time']+.01)),('position',lambda p:p['body'].__setitem__(0,p['body'][0]+.01)),('velocity',lambda p:p.update(body_lateral=p['body_lateral']+.001)),('last_ctrl',lambda p:p['controller_memory']['last_ctrl'].__setitem__(0,p['controller_memory']['last_ctrl'][0]+.001)),('integral',lambda p:p['controller_memory'].update(integral=.01)),('mode',lambda p:p.update(coupled_episode=True))]:
 p=copy.deepcopy(x['packet']);fn(p)
 try:e.bind_current(x,p,False)
 except AssertionError:cases.append(name+'_rejected')
 else:raise AssertionError('STALE_REAL_PACKET_ACCEPTED '+name)
# Each prior exact-success fixture must dispatch to the unchanged source.
real=g['original'];inherited=[]
try:
 for case,folder,kind in [('slot12','v1237/main_slot12','LIVE_GOAL'),('slot10','v1230/main_slot10','LIVE_GOAL'),('slot09','v1230/main_slot09','LIVE_GOAL'),('oldNS','v1220/regression_main_NORTH_SOUTH','ROUTE')]:
  root=R/'runs/v858_nav2_verified'/folder
  x0=json.loads((root/('ROUTE_RECOVERY_INPUT.json'if kind=='ROUTE'else'LIVE_GOAL_INPUT.json')).read_text())
  with e.np.load(root/('ROUTE_JOINT_TABLE.npz'if kind=='ROUTE'else'LIVE_GOAL_TABLE.npz'))as z:table={k:z[k].copy()for k in z.files}
  origin=e.bind_current(x0,x0['packet'],False);tag,lower=status(x0,table,origin,origin,0)
  assert tag=='WHOLE_GOAL_READY',(case,tag,lower)
  answer=dict(passed=True,fixture=case);g['original']=lambda *a,answer=answer,**k:answer
  assert e.generate(x0,table,origin,0,time.monotonic()+1,shadow_origin=origin)is answer
  q=json.loads((R/'runs/v1241_fine_route_reconnection'/('QUALIFICATION_'+case+'.json')).read_text());assert q['passed']
  inherited.append(dict(case=case,full_saved_executor_and_three_audits_inherited=True,unchanged_source_exact=True,current_entry_status=tag))
finally:g['original']=real
e.q.dump(O/'INHERITED_OLD_SUCCESS_QUALIFICATION.json',dict(passed=True,cases=inherited,models=0,physical_native=0,analytical_propagations=0))
e.q.dump(O/'BOUNDARY_QUALIFICATION.json',dict(passed=True,cases=cases,models=0,physical_native=0,analytical_propagations=0));print(json.dumps(cases))
