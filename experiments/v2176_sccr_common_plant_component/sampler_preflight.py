"""Exercise the actual sampler with explicit fake live/NN/render boundaries.

All packets below are in-memory software fixtures, never actual sensor evidence.
No Torch, MuJoCo, actor deserialization, renderer or physical model is imported.
"""
from pathlib import Path
from types import SimpleNamespace,ModuleType
import ast,copy,fcntl,hashlib,importlib.util,json,os,sys,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
assert os.sched_getaffinity(0)=={2}
locks=[]
for name in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
 f=(R/name).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
assert hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
assert not(S/'SOURCE_ONCE_CLAIM.json').exists()and not(S/'SAMPLER_PREFLIGHT_RESULT.json').exists()
import numpy as np
OLD=R/'runs/v2144_sccr_depth_resource_units/components/SCCR/actual'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def module(n,p):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
setup=read(OLD/'physics/SETUP.json');task=read(S/'components/SCCR/PILOT_TASK.json')
receipts=[read(OLD/f'cycle_{i:06d}_origin.json')['receipt']for i in range(3)]
with np.load(OLD/'FULL_STATE_NPLUS1.npz')as z:states={n:z[n][[0,5,10]].copy()for n in z.files}
private=module('preflight_real_private_snapshot',C/'private_snapshot.py')
features=module('preflight_real_union_features',C/'union_features.py')
assembly=module('preflight_real_union_assemble',C/'assemble.py')
rows=[];negative=[];source={str(p.relative_to(R)):sha(p)for p in [C/'union_sampler.py',C/'private_snapshot.py',C/'union_features.py',C/'assemble.py',Path(__file__)]}
original_context=sys.modules.get('context');fake_context=ModuleType('context')
fake_context.__dict__.update(R=R,C=C,O=S/'components/SCCR',read=read,sha=sha,digest=digest)
sys.modules['context']=fake_context
class MarkerFinder:
 def find_spec(self,*args,**kwargs):return None
class V:
 def __init__(self):
  self.count=0;self.commands=[];self.index=0;self.d=SimpleNamespace();self.m=SimpleNamespace(geom_size=np.tile([.1,.2,0.],(53,1)),geom_type=np.full(53,123),geom_bodyid=np.zeros(53,dtype=int),body_mocapid=np.array([0]),geom_pos=np.tile([0.,0.,.22],(53,1)));self.at(0)
 def at(self,i):
  self.index=i;self.count=[0,5,10][i]
  for n in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:setattr(self.d,n,states[n][i].copy())
  self.d.time=float(states['time'][i]);self.commands=[[j,.1,.005,None,None,False]for j in range(self.count)]
 def body(self):return copy.deepcopy(receipts[self.index]['packet']['body'])
class FakeDepth:
 def __init__(self,*args):self.closed=False;self.v=args[0]
 def capture(self,r):
  if flags.get('depth_capture_fail'):raise RuntimeError('EXPLICIT_FAKE_RENDER_FAILURE')
  memory[f'SCCR_DEPTH_{self.v.count:06d}.json']=dict(packet=dict(depth24=read(OLD/f'SCCR_DEPTH_{self.v.count:06d}.json')['packet']['depth24']))
 def close(self):self.closed=True;events.append('fake_depth_closed')
class FakeActor:
 def __init__(self,d):
  events.append(['fake_actor_constructor',d])
  if flags.get('constructor_fail')==d:raise RuntimeError('EXPLICIT_FAKE_ACTOR_CONSTRUCTOR_FAILURE')
  self.d=d;self.calls=0
 def predict_component(self,x,receipt_id):
  assert np.asarray(x).shape==(self.d,)and np.isfinite(x).all();self.calls+=1;assert self.calls<=3
  if flags.get('forward_fail')==self.d:raise RuntimeError('EXPLICIT_FAKE_FORWARD_FAILURE')
  if flags.get('mutate_state'):v.d.ctrl[0]+=1.
  return np.array([.125,-.25],np.float32)
policy=SimpleNamespace(PinnedLibraries=MarkerFinder,FrozenActor=FakeActor)
class Route:
 def propose(self,*args,**kwargs):
  assert os.sched_getaffinity(0)=={4}and args[3]is None and kwargs==dict(guard=.22)
  if flags.get('route_fail'):return None,dict(explicit_fake_route=True)
  b=args[1];x=np.linspace(b[0]-.3,b[0]+.7,30);return np.column_stack([x,np.full(30,b[1]),np.zeros(30),np.ones(30)]),dict(explicit_fake_route=True)
 def revalidate(self,*args,**kwargs):return not flags.get('route_invalid'),dict(explicit_fake_route=True)
def save(name,value):
 if flags.get('save_fail')==name:raise RuntimeError('EXPLICIT_FAKE_METADATA_FAILURE')
 memory[name]=copy.deepcopy(value)
def loader(n,p):
 if Path(p).name=='observed_route.py':return Route()
 if Path(p).name=='depth.py':
  if flags.get('depth_module_fail'):raise RuntimeError('EXPLICIT_FAKE_DEPTH_IMPORT_FAILURE')
  return SimpleNamespace(Sampler=FakeDepth)
 if Path(p).name=='policy.py':
  if flags.get('policy_load_fail'):raise RuntimeError('EXPLICIT_FAKE_POLICY_LOAD_FAILURE')
  return policy
 if Path(p).name=='private_snapshot.py':return private
 if Path(p).name=='union_features.py':return features
 if Path(p).name=='assemble.py':return assembly
 raise AssertionError('UNEXPECTED_PRODUCTION_LOAD:'+str(p))
def read_fixture(p):
 if Path(p).name=='SETUP.json':return setup
 if Path(p).name in memory:return copy.deepcopy(memory[Path(p).name])
 return read(p)
flags={};memory={};events=[]
def allowed(task):assert task['scope']=='SCCR_CP_SHARED_ROUTE_NONZERO_COMPONENT';return({}, {}, source)
fake_context.__dict__.update(read=read_fixture,load=loader,admission=allowed,put=lambda p,v:save(Path(p).name,v))
fake_mujoco=ModuleType('mujoco');fake_mujoco.mjtGeom=SimpleNamespace(mjGEOM_CYLINDER=123);prior_mujoco=sys.modules.get('mujoco');assert prior_mujoco is None;sys.modules['mujoco']=fake_mujoco
before_meta=sys.meta_path[:]
def reset(newflags=None):
 global flags,memory,events,v
 flags=newflags or{};memory={};events=[];v=V();assert sys.meta_path==before_meta
class SoftwareController:
 def previous_action(self):
  k=v.count;commit=None if k==0 else dict(episode_id=task['run_id'],origin_native=k-5,end_native=k,applied_prefix_sha256='EXPLICIT_SOFTWARE_PREFIX_HASH')
  previous=dict(episode_id=task['run_id'],virtual_action=[0.,0.]if k==0 else[.2,2.],commit=commit,units='virtual_steer_rad_and_wheel_rad_s')
  if k:memory[f'SCCR_CP_COMMIT_{k:06d}.json']=copy.deepcopy(previous)
  if flags.get('uncommitted'):previous['commit']['end_native']-=5
  return previous
controller=SoftwareController()
def make():return sampler.Sampler(v,np,save,None,source,OLD,task,{},controller)
def refusal(label,fn,expected=None):
 try:fn()
 except BaseException as e:
  if expected:assert expected in str(e),(label,repr(e))
  negative.append(dict(case=label,error=repr(e)))
 else:raise AssertionError('NEGATIVE_NOT_REFUSED:'+label)
start=time.monotonic()
try:
 sampler=module('preflight_production_sampler',C/'union_sampler.py')
 reset();s=make()
 for i,r in enumerate(receipts):v.at(i);s.capture(copy.deepcopy(r))
 assert s.frames==3 and s.counts['forward_returns']==6 and s.counts['actor_constructor_returns']==2
 for k in [0,5,10]:
  z=memory[f'SCCR_UNION_{k:06d}.json'];assert len(z['observation186'])==186 and len(z['all_ten_consumer_methods'])==10 and z['actual_commands_not_implied_by_capture']
  assert z['sensor_packet']['previous_body_command']==([0.,0.]if k==0 else[.2,2.])and not any(n in z['sensor_packet']for n in ['world','actor','mocap_pos','phase'])
  assert max(z['assembly']['phase6_107'][98:101])<=1.
 rows.append(dict(three_complete_frames=True,forward_stub_calls=6,constructor_stub_calls=2,production_sensor_and_observation_functions=True,nonzero_previous_virtual_fixture=True,all_packets_in_memory_explicit_software_fixture=True))
 s.close();s.close();assert events.count('fake_depth_closed')==1 and sys.meta_path==before_meta
 for label,options,expected in [
  ('route_missing',{'route_fail':True},'UNION_PUBLIC_ROUTE_NOT_FOUND'),
  ('route_invalid',{'route_invalid':True},'UNION_PUBLIC_ROUTE_REFUSED'),
  ('depth_module_load',{'depth_module_fail':True},'EXPLICIT_FAKE_DEPTH_IMPORT_FAILURE'),
  ('policy_load',{'policy_load_fail':True},'EXPLICIT_FAKE_POLICY_LOAD_FAILURE'),
  ('actor_constructor_107',{'constructor_fail':107},'EXPLICIT_FAKE_ACTOR_CONSTRUCTOR_FAILURE'),
  ('actor_constructor_186',{'constructor_fail':186},'EXPLICIT_FAKE_ACTOR_CONSTRUCTOR_FAILURE')]:
  reset(options);refusal(label,make,expected);assert sys.meta_path==before_meta
  if label in ['policy_load','actor_constructor_107','actor_constructor_186']:assert events.count('fake_depth_closed')==1
 for label,options,expected in [
  ('render_failure',{'depth_capture_fail':True},'EXPLICIT_FAKE_RENDER_FAILURE'),
  ('base_forward_failure',{'forward_fail':107},'EXPLICIT_FAKE_FORWARD_FAILURE'),
  ('residual_forward_failure',{'forward_fail':186},'EXPLICIT_FAKE_FORWARD_FAILURE'),
  ('actual_state_mutation',{'mutate_state':True},'UNION_SENSOR_OR_NETWORK_MUTATED_ACTUAL_STATE')]:
  reset(options);s=make();refusal(label,lambda:s.capture(copy.deepcopy(receipts[0])),expected)
  if 'forward_failure'in label:assert memory['SCCR_UNION_POLICY_PROGRESS.json']['inflight']is not None
  s.close();assert events.count('fake_depth_closed')==1 and sys.meta_path==before_meta
 reset({'uncommitted':True});s=make();v.at(1);refusal('uncommitted_nonzero_prior_request',lambda:s.capture(copy.deepcopy(receipts[1])));s.close()
 reset();s=make();r=copy.deepcopy(receipts[0]);r['packet']['sim_time']=.05;refusal('foreign_clock',lambda:s.capture(r));s.close()
 reset();s=make();s.capture(copy.deepcopy(receipts[0]));refusal('duplicate_native',lambda:s.capture(copy.deepcopy(receipts[0])));s.close()
 # The real private sensor guard, not a stub, must check admission before
 # any live object's property is accessed.
 fake_context.admission=lambda task:(_ for _ in ()).throw(AssertionError('EXPLICIT_SOFTWARE_ADMISSION_DENIAL'))
 class Untouchable:
  def __getattribute__(self,n):raise RuntimeError('LIVE_OBJECT_ACCESSED_BEFORE_ADMISSION')
 refusal('private_snapshot_admission_before_model_access',lambda:private.live(np,Untouchable(),{},None,None,task,source,{}),'EXPLICIT_SOFTWARE_ADMISSION_DENIAL')
 # Sampler's actual production admission is likewise its first operation.
 sampler.admission=fake_context.admission;refusal('sampler_admission_before_vehicle_access',lambda:sampler.Sampler(Untouchable(),np,save,None,source,OLD,task,{},controller),'EXPLICIT_SOFTWARE_ADMISSION_DENIAL')
 assert 'torch'not in sys.modules and sys.meta_path==before_meta
 result=dict(passed=True,closed=True,scope='PRODUCTION_SAMPLER_WITH_EXPLICIT_FAKE_PHYSICAL_NN_RENDER_BOUNDARIES',cases=rows,negative_cases=negative,source_SHA256=source,software_stub_receipt_inputs_SHA256={str((OLD/f'cycle_{i:06d}_origin.json').relative_to(R)):sha(OLD/f'cycle_{i:06d}_origin.json')for i in range(3)},models=0,renderer_constructors=0,neural_inference=0,physics=0,replay=0,source_once_claimed=False,all_generated_packets_only_in_memory_not_actual_sensor_evidence=True,real_live_union_not_yet_qualified=True,wall_s=time.monotonic()-start)
 (S/'SAMPLER_PREFLIGHT_RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({k:x for k,x in result.items()if k not in ['cases','source_SHA256','negative_cases','software_stub_receipt_inputs_SHA256']}))
except BaseException as e:
 p=next(S/f'SAMPLER_PREFLIGHT_ATTEMPT{i:02d}.json'for i in range(1,10)if not(S/f'SAMPLER_PREFLIGHT_ATTEMPT{i:02d}.json').exists());p.write_text(json.dumps(dict(passed=False,error=repr(e),traceback=traceback.format_exc(),models=0,physics=0,source_once_claimed=False),indent=2)+'\n');raise
finally:
 if original_context is None:sys.modules.pop('context',None)
 else:sys.modules['context']=original_context
 sys.modules.pop('mujoco',None);sys.meta_path[:]=before_meta
