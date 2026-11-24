"""Read-only original HCP: one constructor, sequential current plans, one destroy."""
import fcntl,importlib.abc,json,os,sys,time,traceback,resource
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];SOURCE=R/'runs/v1844_evening_common_campaign';RID=os.environ.get('PHASE_EVENING_ASSIGNMENT','');O=SOURCE/'rounds'/RID if RID else SOURCE;sys.path.insert(0,str(C))
from context import read,sha,load,digest,remaining

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
 assert sys.argv[1:]==['--serve-current']and os.sched_getaffinity(0)=={2}
 assert (O/'PILOT_ADMISSION.json').is_file(),'TEB_NATIVE_NOT_ADMITTED'
 a=read(O/'PILOT_ADMISSION.json');assert a['models_authorized']and a['scope']=='TEB_COMMON_CONDITION_FULL_TASK'
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 guard=load('v1824_native_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(Path.cwd())
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','kernel','factory','vehicle','bindings','rclpy'}:raise AssertionError('NATIVE_TEB_NO_ENGINE_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 assert not(R/'REVIEW_PENDING').exists()and(O/'PILOT_ONCE_CLAIM.json').is_file()
 lock=(R/'runs/v648_static_unknown/execution.lock').open()
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:pass
 else:raise AssertionError('NATIVE_TEB_PARENT_EXECUTION_LOCK_NOT_HELD')
 import ctypes
 freeze=sha(O/'SOURCE_FREEZE.json');assert a['source_freeze_sha256']==freeze
 window=read(O/'PILOT_WINDOW.json');out=Path(a['assignment']['output']);mailbox=out/'teb_native'
 cfgfields=read(O/'TEB_CONFIG.json');contract=load('v1824_native_session_contract',C/'session_contract.py').Session(freeze,cfgfields)
 counts=dict(explicit_DLL_loads=0,metadata_FFI_calls=0,constructor_attempts=0,constructor_returns=0,query_attempts=0,query_returns=0,destructor_calls=0,constructor_inflight_unknown=False,query_inflight_unknown=False,internal_optimizer_iterations=None,all_native_work=None,automatic_static_registrations=None)
 result=dict(passed=False,closed=False,models=0,physical_native=0,replay_native=0,counts=counts,first_error=None,source_guard=guard);handle=None;lib=None;metadata_bound=False
 try:
  graph=read(R/'runs/v1728_teb_final_link_build/TRANSITIVE_LIBRARY_CANDIDATE.json');expected={}
  for row in graph['nodes']:
   p=Path('/tmp/phase-host'+row['path'])if row['path'].startswith('/usr/')else Path(row['path'])if row['path'].startswith('/')else R/row['path']
   assert sha(p)==row['sha256'];expected[inode(p)]=row
  aliases=read(O/'EXACT_NATIVE_ALIASES.json')['aliases']
  for row in aliases:assert sha(row['target'])==row['sha256']and inode(row['target'])==inode(R/row['source'])
  build=read(O/'BINARY_BINDING.json');binary=R/build['binary_path'];assert sha(binary)==build['binary_sha256'];expected[inode(binary)]={}
  api=load('v1824_original_C_POD',C/'api.py');baseline=maps();original=ctypes.CDLL
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
  cfg=api.Config();cfg.abi=1;cfg.vertices=len(cfgfields['footprint'])
  for name in ['forward','backward','omega','acceleration','angular_acceleration','wheelbase','min_turning_radius','obstacle_distance']:setattr(cfg,name,cfgfields[name])
  for i,value in enumerate(x for p in cfgfields['footprint']for x in p):cfg.footprint[i]=value
  # Native construction is deferred until the first admitted current input.
  while True:
   path=mailbox/'requests'/f'{contract.sequence+1:06d}.json';wait=time.monotonic();wall=time.time()
   while not path.exists():
    if(mailbox/'STOP.json').exists():
     assert read(mailbox/'STOP.json')['sequence']==contract.sequence
     result['passed']=True;return 0
    assert remaining(window)>1200,'TEB_CURRENT_MAILBOX_NORMAL_DEADLINE'
    time.sleep(.01)
   assert path.stat().st_size<=1024**2 and not path.is_symlink()
   envelope=read(path);wire=contract.accept(envelope)
   assert sha(O/'SOURCE_FREEZE.json')==freeze and sha(binary)==build['binary_sha256']
   for row in aliases:assert sha(row['target'])==row['sha256']and inode(row['target'])==inode(R/row['source'])
   if handle is None:
    counts.update(constructor_attempts=1,constructor_inflight_unknown=True);emit('PHASE_TEB_EVENT',counts)
    handle=lib.phase_teb_create(ctypes.byref(cfg));counts.update(constructor_inflight_unknown=False,constructor_returns=1 if handle else 0)
    assert handle,('TEB_ORIGINAL_CONSTRUCTOR_REFUSED',lib.phase_teb_error().decode(errors='replace'))
   obstacles=(api.Obstacle*len(wire['obstacles']))()
   for item,value in zip(obstacles,wire['obstacles']):
    for key in ['x','y','vx','vy','dynamic']:setattr(item,key,value[key])
   q=api.Query()
   for key,value in wire['query'].items():setattr(q,key,value)
   q.obstacles=len(obstacles);q.data=obstacles;samples=(api.Sample*500)();answer=api.Result()
   counts['query_attempts']+=1;counts['query_inflight_unknown']=True;emit('PHASE_TEB_EVENT',counts)
   status=lib.phase_teb_plan(handle,ctypes.byref(q),samples,500,ctypes.byref(answer));counts['query_returns']+=1;counts['query_inflight_unknown']=False
   assert answer.sequence==contract.sequence and answer.samples<=500,'TEB_NATIVE_SEQUENCE_OR_CAPACITY'
   proposal=dict(returncode=status,status=answer.status,samples=answer.samples,classes=answer.classes,vx=answer.vx,vy=answer.vy,omega=answer.omega,sequence=answer.sequence,error=lib.phase_teb_error().decode(errors='replace'),trajectory=[[s.x,s.y,s.yaw,s.time,s.vx,s.vy,s.omega]for s in samples[:answer.samples]])
   passed=status==0 and answer.status==0
   emit('PHASE_TEB_ANSWER',dict(passed=passed,sequence=contract.sequence,source_native=wire['source_native'],wire_sha256=digest(wire),proposal=proposal,counts=counts.copy(),all51_dependency_maps_exact=True))
   if not passed:contract.refuse();result['first_error']=dict(kind='METHOD_FINITE_REFUSAL'if status in [1,2,3]else'NATIVE_INTERFACE_ERROR',proposal=proposal);break
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  if handle:lib.phase_teb_destroy(handle);counts['destructor_calls']+=1
  if lib and metadata_bound:
   result['native_library_counters']={str(k):int(lib.phase_teb_meta(k))for k in [20,21,22]};counts['metadata_FFI_calls']+=3
  result.update(closed=True,last_sequence=contract.sequence);emit('PHASE_TEB_FINAL',result)
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
