"""Actual new navigation function with explicitly fake physical/NN/response boundaries."""
from context import R,C,read,load,digest
from pathlib import Path
from types import SimpleNamespace
import os,copy,json,traceback
import numpy as np
S=R/'runs'/C.name;assert os.sched_getaffinity(0)=={0}and not(S/'NAVIGATION_PREFLIGHT.json').exists()
actual=R/'runs/v2170_sccr_live_source_scope/components/SCCR/actual';saved={k:read(actual/f'SCCR_UNION_{k:06d}.json')for k in [0,5,10]}
controller_module=load('CP_navigation_fixture_controller',C/'cp_controller.py');assembly=load('CP_navigation_fixture_assembly',C/'assemble.py')
nav=load('CP_actual_navigation_software',C/'navigation.py');task=read(S/'components/SCCR/PILOT_TASK.json');original_load=nav.load;original_read=nav.read
flags={};memory={};events=[]
class V:
 def __init__(self):self.count=0;self.commands=[];self.adapter=SimpleNamespace(parked_target=None);self.d=SimpleNamespace(time=0.)
 def fixture(self,k):return saved[min(10,(k//5)*5)]
 def body(self):return self.fixture(self.count)['sensor_packet']['body'].copy()
 def scan(self):
  scan=copy.deepcopy(self.fixture(self.count)['receipt']['scan']);scan.update(native_tick=self.count,time=.01*self.count,xy=self.body()[:2],yaw=self.body()[2]);return scan
 def step(self,v,w,stale):
  self.commands.append([float(self.count),v+(.001 if flags.get('wrong_request')else 0.),w,0.,0.,stale]);self.count+=1;self.d.time=.01*self.count
 def state_for(self,k):
  s=np.zeros(8);s[:3]=self.fixture(k)['sensor_packet']['body'][:3];return s
class Obs:
 @staticmethod
 def scan_only(scan,k,t):return copy.deepcopy(scan)
 @staticmethod
 def acquire(v,binding,z):
  r=copy.deepcopy(v.fixture(v.count)['receipt']);r['packet'].update(native_tick=v.count,sim_time=float(v.d.time),body=v.body());r['scan']=z;return r
class Evidence:
 def __init__(self,*a):self.first=None
 def update(self,*a):pass
class Response:
 @staticmethod
 def prove(q,setup,p,requests,goal,cs):
  assert len(requests) in [2210,2205,2200]and all(z==[0.,0.,False]for z in requests[-2200:]);assert cs is None
  ss=np.asarray([v.state_for(p['native_tick']+i)for i in range(len(requests)+1)])
  return dict(passed=not flags.get('refuse_prediction'),native=len(requests),origin_packet=p),ss,np.zeros((len(requests),4)),np.zeros((len(requests)+1,5))
class Service:
 def persist(self,p,arrays):
  assert set(arrays)=={'states','controls','memory','requests'}and 'receipt'in p and 'arrays'in p
  events.append(['full_profile_persist',p['native']]);return dict(explicit_fake_proof_arrays=True)
class Sampler:
 def __init__(self,*args):self.controller=args[-1];self.frames=0;self.closed=False;events.append(['fake_sampler_constructor'])
 def capture(self,r):
  k=r['packet']['native_tick'];a=copy.deepcopy(saved[k]);p=a['sensor_packet'];previous=self.controller.previous_action()
  p.update(previous_body_command=previous['virtual_action'],body=r['packet']['body'],sim_time=r['packet']['sim_time']);p['producer_proof'].update(episode_id=task['run_id'],previous_action_commit=previous['commit'])
  a['receipt']=copy.deepcopy(r);base=np.asarray(a['assembly']['base_action_2'],np.float32);obs,parts=assembly.build(np,p,lambda _:base.copy());a.update(sensor_packet_sha256=digest(p),assembly=parts,observation186=obs.tolist())
  self.frames+=1;memory[f'SCCR_UNION_{k:06d}.json']=copy.deepcopy(a);events.append(['fake_actor_output_stub_frame',k]);return a
 def close(self):self.closed=True;events.append(['sampler_closed'])

def loader(n,p):
 name=Path(p).name
 if name=='observation.py':return Obs
 if name=='response.py':return Response
 if name=='causal.py':return SimpleNamespace(Evidence=Evidence)
 if name=='cp_controller.py':return controller_module
 if name=='union_sampler.py':return SimpleNamespace(Sampler=Sampler)
 return original_load(n,p)
def save(name,value):memory[name]=copy.deepcopy(value)
nav.load=loader;nav.read=lambda p:dict(known={})if Path(p).name=='SETUP.json'else original_read(p)
def reset(f=None):
 global flags,memory,events,v
 flags=f or{};memory={};events=[];v=V()
def execute():
 q=SimpleNamespace(np=np,initial=lambda p:dict(state=v.state_for(p['native_tick'])))
 binding=dict(q=q,packet=lambda v:dict(native_tick=v.count,sim_time=v.d.time,body=v.body()),old=SimpleNamespace(previous=SimpleNamespace(stopped=lambda p:True)),predictive_arrays=Service())
 return nav.run(v,binding,task,{},S/'SOFTWARE_OUTPUT_NEVER_ACTUAL',save,None,lambda *a,**kw:None)
try:
 reset();out=execute();assert out['passed']and v.count==2210 and out['learned_control_prefixes']==2
 assert len([x for x in events if x[0]=='full_profile_persist'])==5 and len([x for x in events if x[0]=='fake_actor_output_stub_frame'])==3
 assert memory['SCCR_CP_COMMIT_000005.json']['commit']['end_native']==5 and memory['SCCR_CP_COMMIT_000010.json']['commit']['end_native']==10
 assert memory['SCCR_UNION_000005.json']['sensor_packet']['previous_body_command']!=[0.,0.]
 assert all(row[1]==row[2]==0 and row[5]is False for row in v.commands[10:])and events[-1]==['sampler_closed']
 normal=list(v.commands[:10]);neg=[]
 for label,flag,count in [('prediction_refusal','refuse_prediction',0),('applied_request_changed','wrong_request',5)]:
  reset({flag:True})
  try:execute()
  except AssertionError as e:
   assert v.count==count and events[-1]==['sampler_closed'];neg.append(dict(case=label,refused_at_fake_native=v.count,first_error=str(e)))
  else:raise AssertionError('FLOW_NEGATIVE_ACCEPTED')
 result=dict(passed=True,closed=True,scope='PRODUCTION_NAVIGATION_CONTROL_FLOW_WITH_EXPLICIT_FAKE_PHYSICS_NN_RESPONSE_BOUNDARIES',
  fake_event_native=2210,complete_original_2200_tail_sequence_checked=True,full_profile_API_calls=5,frame_stub_calls=3,positive_prefix_requests=normal,
  persistent_commits=2,negative_cases=neg,actual_physical_model_steps_NN_render_replay_audit_source_claims=0,
  all_proof_and_physics_gates_are_EXPLICIT_SOFTWARE_STUBS_NOT_SAFETY_EVIDENCE=True)
 (S/'NAVIGATION_PREFLIGHT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['positive_prefix_requests','negative_cases']}))
except BaseException as e:
 (S/'NAVIGATION_PREFLIGHT_FAILED.json').write_text(json.dumps(dict(error=repr(e),traceback=traceback.format_exc(),new_models_physics=0),indent=2)+'\n');raise
