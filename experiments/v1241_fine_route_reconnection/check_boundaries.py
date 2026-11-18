"""No-propagation branch and stale real-packet rejection tests."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from package_loader import get_goal_entry
from pathlib import Path
import copy,json,time
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
e=get_goal_entry();g=e.generate.__globals__;original=g['retained'];connection=g['reconnect'];cases=[]
def forbidden(*a,**kw):raise AssertionError('UNQUALIFIED_RECONNECTION_CALLED')
try:
 g['reconnect']=forbidden
 result=dict(passed=True,scientific_original_record='preserved');g['retained']=lambda *a,**k:result
 assert e.generate({}, {},{},0,time.monotonic()+1,shadow_origin={}) is result;cases.append('original_success_exact_object_retained')
 for count in [0,2999,3000,5999]:
  g['retained']=lambda *a,count=count,**kw:dict(passed=False,bounded_total_expansions=count,search_trials=[])
  try:e.generate({}, {},{},0,time.monotonic()+1,shadow_origin={})
  except AssertionError as error:assert 'INCOMPLETE_ORIGINAL_WORK' in str(error);cases.append('partial_'+str(count)+'_not_extended')
  else:raise AssertionError('PARTIAL_SEARCH_EXTENDED')
 g['retained']=lambda *a,**k:(_ for _ in ()).throw(ValueError('cause_evidence_error'))
 try:e.generate({}, {},{},0,time.monotonic()+1,shadow_origin={})
 except ValueError:cases.append('original_exception_preserved')
 else:raise AssertionError('CAUSE_EXCEPTION_HIDDEN')
 g['retained']=lambda *a,**kw:dict(passed=False,bounded_total_expansions=6000,search_trials=[dict(passed=False,phase_expanded=[3000])]*2,analytical_cpp_native=5,admission_python_native=2)
 called=[]
 g['reconnect']=lambda *a,**kw:(called.append(1) or dict(passed=True,analytical_cpp_native=3,admission_python_native=4))
 d=e.generate({}, {},{},0,time.monotonic()+1,shadow_origin={});assert called==[1]and d['analytical_cpp_native']==8 and d['admission_python_native']==6;cases.append('full_exhaustion_only_once_counts_separate')
finally:g['retained']=original;g['reconnect']=connection
x=json.loads((R/'runs/v858_nav2_verified/v1237/main_slot12/LIVE_GOAL_INPUT.json').read_text())
for name,fn in [('time',lambda p:p.update(sim_time=p['sim_time']+.01)),('position',lambda p:p['body'].__setitem__(0,p['body'][0]+.01)),('velocity',lambda p:p.update(body_lateral=p['body_lateral']+.001)),('last_ctrl',lambda p:p['controller_memory']['last_ctrl'].__setitem__(0,p['controller_memory']['last_ctrl'][0]+.001)),('integral',lambda p:p['controller_memory'].update(integral=.01)),('mode',lambda p:p.update(coupled_episode=True))]:
 p=copy.deepcopy(x['packet']);fn(p)
 try:e.bind_current(x,p,False)
 except AssertionError:cases.append(name+'_rejected')
 else:raise AssertionError('STALE_REAL_PACKET_ACCEPTED '+name)
e.q.dump(O/'BOUNDARY_QUALIFICATION.json',dict(passed=True,cases=cases,models=0,physical_native=0,analytical_propagations=0));print(json.dumps(cases))
