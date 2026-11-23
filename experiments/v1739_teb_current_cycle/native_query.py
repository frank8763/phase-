"""One original HCP constructor/query/destructor in a read-only CPU2 child."""
import ctypes,fcntl,importlib.abc,json,os,sys,time,traceback,resource
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name;sys.path.insert(0,str(C))
from context import read,sha,load,digest

def maps():
 out={}
 for line in Path('/proc/self/maps').read_text().splitlines():
  p=line.split(None,5)
  if len(p)==6 and p[5].startswith('/')and int(p[4]):
   a,b=p[3].split(':');out[(int(a,16),int(b,16),int(p[4]))]=p[5]
 return out
def inode(p):
 s=Path(p).stat();return os.major(s.st_dev),os.minor(s.st_dev),s.st_ino
def emit(tag,value):os.write(1,(tag+' '+json.dumps(value,separators=(',',':'),allow_nan=False)+'\n').encode())

def main():
 assert sys.argv[1:]==['--query-once']and os.sched_getaffinity(0)=={2}
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 guard=load('v1739_native_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(Path.cwd())
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','kernel','factory','vehicle','bindings','rclpy'}:raise AssertionError('NATIVE_TEB_NO_ENGINE_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 a=read(O/'PILOT_ADMISSION.json');assert a['models_authorized']and a['scope']=='TEB_FRESH_T0_ORIGINAL_ACTUATOR_COMPONENT'
 assert not(R/'REVIEW_PENDING').exists()and(O/'PILOT_ONCE_CLAIM.json').is_file()
 lock=(R/'runs/v648_static_unknown/execution.lock').open()
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:pass
 else:raise AssertionError('NATIVE_TEB_PARENT_EXECUTION_LOCK_NOT_HELD')
 envelope=json.loads(sys.stdin.buffer.read(1024**2+1));wire=envelope['wire']
 assert digest(wire)==envelope['wire_sha256']and sha(O/'SOURCE_FREEZE.json')==envelope['source_freeze_sha256']==a['source_freeze_sha256']
 assert wire['config']==read(O/'TEB_CONFIG.json')and wire['schema']=='PHASE_TEB_REAR_AXLE_QUERY_V1'
 assert wire['source_native']==0 and wire['source_sim_time']==0. and not wire['historical_controls_supplied']and not wire['actor_truth_supplied']
 start=time.monotonic();counts=dict(explicit_DLL_loads=0,metadata_FFI_calls=0,constructor_attempts=0,constructor_returns=0,query_attempts=0,query_returns=0,destructor_calls=0,constructor_inflight_unknown=False,query_inflight_unknown=False,internal_optimizer_iterations=None,all_native_work=None,automatic_static_registrations=None)
 result=dict(passed=False,closed=False,wire_sha256=digest(wire),models=0,physical_native=0,replay_native=0,counts=counts,first_error=None);handle=None;lib=None;metadata_bound=False
 try:
  binding=read(O/'NATIVE_BINDING.json');graph=read(R/'runs/v1728_teb_final_link_build/TRANSITIVE_LIBRARY_CANDIDATE.json');expected={}
  for row in graph['nodes']:
   p=Path('/tmp/phase-host'+row['path'])if row['path'].startswith('/usr/')else Path(row['path'])if row['path'].startswith('/')else R/row['path']
   assert sha(p)==row['sha256'];expected[inode(p)]=row
  for row in read(O/'EXACT_NATIVE_ALIASES.json')['aliases']:assert sha(row['target'])==row['sha256']and inode(row['target'])==inode(R/row['source'])
  build=read(O/'BINARY_BINDING.json');binary=R/build['binary_path'];assert sha(binary)==build['binary_sha256'];expected[inode(binary)]={}
  api=load('v1739_original_C_POD',C/'api.py');baseline=maps();original=ctypes.CDLL
  def only(path,*args,**kwargs):
   assert Path(path)==binary and sha(binary)==build['binary_sha256']and counts['explicit_DLL_loads']==0,'TEB_UNREGISTERED_DLL_OR_RETRY'
   counts['explicit_DLL_loads']+=1;return original(path,*args,**kwargs)
  ctypes.CDLL=only;lib=ctypes.CDLL(str(binary),mode=os.RTLD_NOW|os.RTLD_LOCAL);after=maps()
  assert set(expected).issubset(after),'TEB_RUNTIME_DEPENDENCY_IDENTITY'
  for key,path in after.items():
   if key in baseline or key in expected:continue
   with open(path,'rb')as f:assert f.read(4)!=b'\x7fELF','TEB_RUNTIME_UNBOUND_NEW_ELF'
  lib.phase_teb_meta.argtypes=[ctypes.c_uint32];lib.phase_teb_meta.restype=ctypes.c_uint64;metadata_bound=True
  for k,v in api.expected().items():assert lib.phase_teb_meta(k)==v;counts['metadata_FFI_calls']+=1
  lib.phase_teb_create.argtypes=[ctypes.POINTER(api.Config)];lib.phase_teb_create.restype=ctypes.c_void_p
  lib.phase_teb_plan.argtypes=[ctypes.c_void_p,ctypes.POINTER(api.Query),ctypes.POINTER(api.Sample),ctypes.c_uint32,ctypes.POINTER(api.Result)];lib.phase_teb_plan.restype=ctypes.c_int32
  lib.phase_teb_destroy.argtypes=[ctypes.c_void_p];lib.phase_teb_destroy.restype=None
  lib.phase_teb_error.argtypes=[];lib.phase_teb_error.restype=ctypes.c_char_p
  cfg=api.Config();fields=wire['config'];cfg.abi=1;cfg.vertices=len(fields['footprint'])
  for name in ['forward','backward','omega','acceleration','angular_acceleration','wheelbase','min_turning_radius','obstacle_distance']:setattr(cfg,name,fields[name])
  for i,value in enumerate(x for p in fields['footprint']for x in p):cfg.footprint[i]=value
  counts.update(constructor_attempts=1,constructor_inflight_unknown=True);emit('PHASE_TEB_EVENT',counts)
  handle=lib.phase_teb_create(ctypes.byref(cfg));counts.update(constructor_inflight_unknown=False,constructor_returns=1 if handle else 0)
  assert handle,('TEB_ORIGINAL_CONSTRUCTOR_REFUSED',lib.phase_teb_error().decode(errors='replace'))
  obstacles=(api.Obstacle*len(wire['obstacles']))()
  for item,value in zip(obstacles,wire['obstacles']):
   for key in ['x','y','vx','vy','dynamic']:setattr(item,key,value[key])
  q=api.Query()
  for key,value in wire['query'].items():setattr(q,key,value)
  q.obstacles=len(obstacles);q.data=obstacles;samples=(api.Sample*500)();answer=api.Result()
  counts.update(query_attempts=1,query_inflight_unknown=True);emit('PHASE_TEB_EVENT',counts)
  status=lib.phase_teb_plan(handle,ctypes.byref(q),samples,500,ctypes.byref(answer));counts.update(query_returns=1,query_inflight_unknown=False)
  proposal=dict(returncode=status,status=answer.status,samples=answer.samples,classes=answer.classes,vx=answer.vx,vy=answer.vy,omega=answer.omega,sequence=answer.sequence,error=lib.phase_teb_error().decode(errors='replace'),trajectory=[[s.x,s.y,s.yaw,s.time,s.vx,s.vy,s.omega]for s in samples[:answer.samples]])
  result['proposal']=proposal;assert status==0 and answer.status==0,('TEB_ORIGINAL_FINITE_QUERY_REFUSED',proposal['error'],status,answer.status)
  assert answer.sequence==1;result.update(passed=True,all51_dependency_maps_exact=True,source_guard=guard)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  if handle:lib.phase_teb_destroy(handle);counts['destructor_calls']+=1
  if lib and metadata_bound:
   result['native_library_counters']={k:int(lib.phase_teb_meta(k))for k in [20,21,22]};counts['metadata_FFI_calls']+=3
  result.update(closed=True,wall_s=time.monotonic()-start);emit('PHASE_TEB_FINAL',result)
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
