"""Real navigation+cursor+independent query audit, EXPLICIT FAKE plant/NLP/proofs."""
from pathlib import Path
from types import SimpleNamespace
from context import R,C,SOURCE as S,load,read,digest,sha
import numpy as np
import sys,os,json,copy,math,traceback,types,datetime
from fresh_problem import FreshProjection,known,PUBLIC
from handshake import bind
assert os.sched_getaffinity(0)=={0}and not(S/'NAVIGATION_SOFTWARE.json').exists()
nav=load('CP_actual_navigation_under_fakes',C/'navigation.py');original_load=nav.load;original_read=nav.read;cursor=load('CP_preflight_cursor_helpers',R/'experiments/v2179_current_plan_cursor/cursor.py');audit=load('CP_real_query_independent_auditor',C/'audit_query_cursor.py');original_audit=json.loads
base_task=read(S/'components/PROJ/PILOT_TASK.json');flags={};memory={};events=[];v=None;profile=None;task=None
class V:
 def __init__(self):self.count=0;self.commands=[];self.adapter=SimpleNamespace(parked_target=None);self.d=SimpleNamespace(time=0.);self.journal=[]
 def pose(self,n):
  n=min(n,120)
  if profile is None:return[-4.3,-2.,0.],0.
  i=n//50;local=(n-i*50)*.01;vv=profile['speeds'];kap=profile['curvatures'][i];p=cursor.arc(profile['rear_poses'][i],vv[i],vv[i+1],kap,local,.5);speed=vv[i]+(vv[i+1]-vv[i])*local/.5;return p,speed
 def body(self):
  p,s=self.pose(self.count);return[p[0]+.3*math.cos(p[2]),p[1]+.3*math.sin(p[2]),p[2],s,0.]
 def scan(self):return dict(native_tick=self.count,time=.01*self.count,xy=self.body()[:2],yaw=self.body()[2],ranges=[3.]*32)
 def packet(self):
  t=__import__('time').monotonic();return dict(body=self.body(),body_lateral=0.,native_tick=self.count,sim_time=.01*self.count,body_measured_at=t,sent_at=t,dynamic_discovered=False,steering=dict(position=[0.,0.],velocity=[0.,0.],native_tick=self.count,measured_at=t),controller_memory=dict(last_ctrl=[0.,0.,0.,0.],integral=0.),coupled_episode=False,steering_motion_active=False)
 def step(self,vr,wr,stale):
  request=[vr,wr,stale];actual=[vr+(.001 if flags.get('wrongrequest')and self.count==0 else 0.),wr,stale];self.journal.append(dict(before_native=self.count,phase=self._chain_phase,request=actual,applied=True));self.commands.append([float(self.count),*actual[:2],0.,0.,actual[2]]);self.count+=1;self.d.time=.01*self.count
 def state(self,n):
  p,s=self.pose(n);a=np.zeros(8);a[:3]=[p[0]+.3*math.cos(p[2]),p[1]+.3*math.sin(p[2]),p[2]];a[3]=s;return a
class Evidence:
 def __init__(self,*args):self.first=None
 def update(self,*args):pass
class Response:
 @staticmethod
 def prove(q,setup,p,requests,goal,cs):
  assert cs is None and goal.tolist()==[4.,-2.]and len(requests)in [2200,2205,2210]and requests[-2200:]==[[0.,0.,False]]*2200
  n=p['native_tick'];ss=np.asarray([v.state(n+i)for i in range(len(requests)+1)]);checks={k:True for k in cursor.RESPONSE_CHECKS};checks['full_raw_geometry']=not(flags.get('refuse')and n==0)
  return dict(passed=all(checks.values()),checks=checks,native=len(requests),origin_packet=p),ss,np.zeros((len(requests),4)),np.zeros((len(requests)+1,5))
class Service:
 def persist(self,p,arrays):events.append(p['native']);assert arrays['states'].shape==(p['native']+1,8);return dict(fake_model_proof=True,arrays_sha256=digest(p['arrays']))
class FakeClient:
 def __init__(self,save,receipt,tt):
  self.save=save;self.receipt=receipt;self.task=tt;self.closed=False
 def query(self):
  global profile
  auth=dict(scope='ONE_FRESH_REST_ORIENTATION_PROJECTION_ONLY',models_authorized=False,maximum_queries=1,run_id=task['run_id'],query_nonce='EXPLICIT_FAKE_NAVIGATION_ONLY',source_freeze_sha256='a'*64,worker_sha256=sha(C/'peer_entry.py'))
  self.save('PROJECTION_OPTIMIZER_ADMISSION.json',auth);raw=(json.dumps(auth,separators=(',',':'))+'\n').encode()
  f=dict(schema='FRESH_REST_ORIENTATION_PROJECTION_V1',episode_id=task['run_id'],query_sequence=0,query_nonce=auth['query_nonce'],source_freeze_sha256=auth['source_freeze_sha256'],numerical_admission_sha256='',receipt=self.receipt,public_known=known(),public_known_sha256=sha(PUBLIC),whole_goal_xy=task['goal_xy']);f,once=bind(raw,f);p=FreshProjection(f);profile=p.proposal(p.initial,success=True,status=0)
  self.save('PROJECTION_QUERY_FRAME.json',f);self.save('PROJECTION_PEER_ONCE.json',once);self.save('PROJECTION_NATIVE_RAW_RETURN.json',dict(success=True,status=0,explicit_fake_no_NLP=True))
  reply=dict(proposal=profile,passed=True,query_sha256=digest(f),query_nonce=f['query_nonce'],NLP_attempted_calls=1,NLP_returns=1,inflight_unknown=False,raw_return=memory['PROJECTION_NATIVE_RAW_RETURN.json']);self.save('PROJECTION_NATIVE_REPLY.json',reply);self.save('PROJECTION_NATIVE_CLOSED.json',dict(math_passed=True,query_nonce=f['query_nonce'],NLP_attempted_calls=1,NLP_returns=1,inflight_unknown=False));self.close()
  if flags.get('peerfail'):raise AssertionError('EXPLICIT_FAKE_NUMERICAL_REFUSAL')
  return copy.deepcopy(profile)
 def close(self):
  if self.closed:return
  self.closed=True;self.save('PROJECTION_NATIVE_ACCOUNTING.json',dict(complete_reply_and_peer_close=True,NLP_returns=1,inflight_unknown=False));memory['CLIENT_CLOSED']=True

def loader(n,p):
 if Path(p).name=='response.py':return Response
 if Path(p).name=='causal.py':return SimpleNamespace(Evidence=Evidence)
 return original_load(n,p)
nav.load=loader;nav.read=lambda p:dict(known={})if Path(p).name=='SETUP.json'else original_read(p)
fake_module=types.ModuleType('client_once');fake_module.Client=FakeClient;sys.modules['client_once']=fake_module

def save(name,value):memory[name]=json.loads(json.dumps(value,default=lambda x:x.tolist(),allow_nan=False))
def run(label,options):
 global memory,events,flags,v,profile,task
 memory={};events=[];flags=options;profile=None;task=dict(base_task,run_id=base_task['run_id']+'_SOFTWARE_'+label);v=V();binding=dict(q=SimpleNamespace(np=np,initial=lambda p:dict(state=v.state(p['native_tick']))),packet=lambda v:v.packet(),old=SimpleNamespace(previous=SimpleNamespace(stopped=lambda p:True)),predictive_arrays=Service());quota=SimpleNamespace(retire_grant=lambda:None)
 return nav.run(v,binding,task,{},S/'SOFTWARE_NEVER_ACTUAL',save,quota,lambda *a,**k:None)
try:
 out=run('positive',{});assert out['passed']and v.count==2320 and len(events)==49 and memory['CLIENT_CLOSED']and out['nonzero_requested_native']>0
 assert all(row['request']==[0.,0.,False]for row in v.journal[120:]);assert len([n for n in memory if n.startswith('PROJECTION_COMMIT_')])==24
 folder=S/'navigation_fixture';folder.mkdir(exist_ok=False)
 for name,value in memory.items():
  if name.endswith('.json'):(folder/name).write_text(json.dumps(value,separators=(',',':'))+'\n')
 (folder/'APPLIED_JOURNAL.json').write_text(json.dumps(v.journal,separators=(',',':'))+'\n')
 result=audit.audit(folder,task,{'experiments/v2180_fresh_projection_component/peer_entry.py':sha(C/'peer_entry.py')},np,require_complete=True);assert result['passed']and result['covered_normal_native']==120
 # Independently reject mutated saved data without re-running navigation.
 rejects=[]
 for name,file,key,value in [('wrong_cursor_origin','PROJECTION_000001_PROPOSAL.json','original_plan_origin_native',5),('wrong_fresh_nonce','PROJECTION_NATIVE_REPLY.json','query_nonce','foreign')]:
  p=folder/file;raw=p.read_bytes();z=json.loads(raw);z[key]=value;p.write_text(json.dumps(z)+'\n')
  try:audit.audit(folder,task,{'experiments/v2180_fresh_projection_component/peer_entry.py':sha(C/'peer_entry.py')},np,require_complete=True)
  except AssertionError:rejects.append(name)
  else:raise AssertionError('MUTATED_QUERY_AUDIT_ACCEPTED')
  finally:p.write_bytes(raw)
 negatives=[]
 for label,options,count in [('prediction',{'refuse':True},0),('wrong_applied',{'wrongrequest':True},5),('numerical',{'peerfail':True},0)]:
  try:run(label,options)
  except AssertionError as e:assert v.count==count and memory['CLIENT_CLOSED'];negatives.append(dict(case=label,fake_native=v.count,error=repr(e)))
  else:raise AssertionError('EXPECTED_NAVIGATION_REFUSAL')
 x=dict(passed=True,scope='ACTUAL_NAVIGATION_AND_AUDIT_WITH_EXPLICIT_FAKE_PLANT_NLP_MODEL',fake_native_events=2320,current_proof_profiles=49,committed_prefixes=24,independent_query_cursor_audit=result,mutated_saved_audit_rejects=rejects,negative_cases=negatives,complete2200tail=True,actual_NLP_NN_models_physics_replay_Source=0,source_SHA256={str(p.relative_to(R)):sha(p)for p in [C/'navigation.py',C/'navigation_preflight.py',C/'audit_query_cursor.py']},created_at=datetime.datetime.now().astimezone().isoformat());(S/'NAVIGATION_SOFTWARE.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({k:v for k,v in x.items()if k not in ['source_SHA256','negative_cases','independent_query_cursor_audit']}))
except BaseException as e:(S/'NAVIGATION_SOFTWARE_FAILED.json').write_text(json.dumps(dict(error=repr(e),traceback=traceback.format_exc(),actual_NLP_models_physics=0),indent=2)+'\n');raise
