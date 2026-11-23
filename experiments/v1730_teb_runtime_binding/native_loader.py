"""CPU2 sourceguarded actual DLL/POD qualification; no planner construction."""
import ctypes,fcntl,importlib.abc,importlib.util,json,os,runpy,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name;OUT=O/'build';sys.path.insert(0,str(C))
from context import read,put,sha,load
def maps():
 result={}
 for line in Path('/proc/self/maps').read_text().splitlines():
  parts=line.split(None,5)
  if len(parts)<6 or not parts[5].startswith('/')or not int(parts[4]):continue
  a,b=parts[3].split(':');result[(int(a,16),int(b,16),int(parts[4]))]=parts[5]
 return result
def inode(p):
 s=Path(p).stat();return os.major(s.st_dev),os.minor(s.st_dev),s.st_ino
def main():
 start=time.monotonic();assert sys.argv[1:]==['--source-only']and os.sched_getaffinity(0)=={2}
 os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));os.sched_setscheduler(0,os.SCHED_IDLE,os.sched_param(0))
 guard=load('v1730_immutable_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(OUT)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','kernel','factory','vehicle','bindings','rclpy'}:raise AssertionError('SOURCE_NO_MODEL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban());assert Path.cwd()==OUT/'empty_cwd'
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(OUT/'SOURCE_NATIVE_ONCE.json').open('x')as f:f.write('{}\n')
 result=dict(passed=False,closed=False,models=0,physical_native=0,replay_native=0,planner_constructors=0,optimizer_calls=0,explicit_DLL_loads=0,metadata_FFI_calls=0,upstream_static_registration_count=None,complete_numeric_or_vehicle_runtime_qualified=False)
 try:
  binding=read(O/'INPUT_BINDING.json');assert all(sha(R/k)==h for k,h in binding['files_SHA256'].items())
  # Host fallback files must be read through the immutable host alias.
  for k,h in binding['external_SHA256'].items():
   p=Path('/tmp/phase-host'+k)if k.startswith('/usr/')else Path(k);assert sha(p)==h
  build=read(O/'BUILD_RESULT.json');assert build['passed']and build['source_unchanged'];binary=R/build['binary_path'];assert sha(binary)==build['binary_sha256']
  graph=read(R/'runs/v1728_teb_final_link_build/TRANSITIVE_LIBRARY_CANDIDATE.json');expected={}
  for row in graph['nodes']:
   p=Path('/tmp/phase-host'+row['path'])if row['path'].startswith('/usr/')else Path(row['path'])if row['path'].startswith('/')else R/row['path'];assert sha(p)==row['sha256'];expected[inode(p)]=dict(path=row['path'],sha256=row['sha256'])
  expected[inode(binary)]=dict(path=str(binary.relative_to(R)),sha256=sha(binary))
  api=load('v1730_C_POD_layout',C/'api.py');baseline=maps();original=ctypes.CDLL
  def dlopen(path,*args,**kwargs):
   assert Path(path)==binary and sha(binary)==build['binary_sha256'],'UNREGISTERED_DLL_TARGET'
   assert result['explicit_DLL_loads']==0,'SOURCE_DLL_NO_RETRY';result['explicit_DLL_loads']+=1;return original(path,*args,**kwargs)
  ctypes.CDLL=dlopen
  lib=ctypes.CDLL(str(binary),mode=os.RTLD_NOW|os.RTLD_LOCAL)
  after=maps();assert set(expected).issubset(after),'EXPECTED_DEPENDENCY_NOT_MAPPED'
  unbound=[]
  for key,path in after.items():
   if key in baseline or key in expected:continue
   assert path.startswith(('/usr/','/lib/','/home/linghu/miniconda3/envs/mk_mujoco/','/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/')),'UNAPPROVED_NEW_MAPPING_PATH'
   with open(path,'rb')as f:magic=f.read(4)
   if magic==b'\x7fELF':unbound.append(path)
  assert not unbound,('UNBOUND_NEW_ELF',unbound)
  lib.phase_teb_meta.argtypes=[ctypes.c_uint32];lib.phase_teb_meta.restype=ctypes.c_uint64
  lib.phase_teb_create.argtypes=[ctypes.POINTER(api.Config)];lib.phase_teb_create.restype=ctypes.c_void_p
  lib.phase_teb_plan.argtypes=[ctypes.c_void_p,ctypes.POINTER(api.Query),ctypes.POINTER(api.Sample),ctypes.c_uint32,ctypes.POINTER(api.Result)];lib.phase_teb_plan.restype=ctypes.c_int32
  lib.phase_teb_destroy.argtypes=[ctypes.c_void_p];lib.phase_teb_destroy.restype=None
  lib.phase_teb_error.argtypes=[];lib.phase_teb_error.restype=ctypes.c_char_p
  values={}
  for k,v in api.expected().items():values[k]=lib.phase_teb_meta(k);result['metadata_FFI_calls']+=1;assert values[k]==v,('C_POD_ABI_MISMATCH',k,values[k],v)
  negatives=[]
  for name,operation in [('numeric_API',lambda:api.numeric_entry()),('real_runtime_CLI',lambda:runpy.run_path(str(C/'entry.py'),run_name='__main__')),('foreign_DLL',lambda:ctypes.CDLL('/usr/lib/x86_64-linux-gnu/libm.so.6'))]:
   try:operation()
   except AssertionError:negatives.append(name)
   else:raise AssertionError('NEGATIVE_ACCEPTED:'+name)
  for module in ['numpy','mujoco','torch']:
   try:__import__(module)
   except AssertionError:negatives.append('model_import_'+module)
   else:raise AssertionError('MODEL_IMPORTED:'+module)
  try:(OUT/'empty_cwd/foreign.so').write_bytes(b'not allowed')
  except OSError:negatives.append('readonly_empty_CWD')
  else:raise AssertionError('RUNTIME_CWD_WRITABLE')
  try:(R/'SOURCE_FORBIDDEN_WRITE').write_bytes(b'not allowed')
  except PermissionError:negatives.append('original_write_guard_scope')
  else:raise AssertionError('OUTSIDE_WRITE_ACCEPTED')
  for k in [20,21,22]:assert lib.phase_teb_meta(k)==0;result['metadata_FFI_calls']+=1
  assert sha(binary)==build['binary_sha256']and all(sha(R/k)==h for k,h in binding['files_SHA256'].items())
  result.update(passed=True,guard=guard,C_POD_layout=values,negative_cases=negatives,expected_ELF_mapped_by_device_inode=len(expected),new_ELF_not_in_binding=[],all_loaded_dependency_identities_exact=True,sourcepass_not_solver_or_safety_PASS=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  result.update(closed=True,wall_s=time.monotonic()-start);put(OUT/'SOURCE_NATIVE_RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
