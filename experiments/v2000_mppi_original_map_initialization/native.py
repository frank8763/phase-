"""One new input per actual algorithm lane; no simulator or full-task score."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import R,C,ROOT,O,LANE,LANES,read,put,sha,load,authority
import ctypes,fcntl,hashlib,importlib.abc,json,math,os,resource,time,traceback

def main():
 a,frozen=authority();assert not(O/'NATIVE_ONCE.json').exists();put(O/'NATIVE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),lane=LANE,cpu=LANES[LANE],constructor_cap=1,query_cap=1))
 lane_lock=(O/'execution.lock').open();fcntl.flock(lane_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 resource.setrlimit(resource.RLIMIT_AS,((6 if LANE=='MPPI'else 2)*1024**3,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(180,190));os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','kernel','factory','vehicle','fast_predict'}:raise AssertionError('PARALLEL_NO_PLANT_IMPORT:'+name)
 sys.meta_path.insert(0,Ban());scope=load('exact_nonexecuting_mapping_scope',R/'experiments/v1963_rpp_nonexecuting_shm_scope/mapping_scope.py')
 def maps():
  out={}
  for line in Path('/proc/self/maps').read_text().splitlines():
   cols=line.split(None,5)
   if len(cols)!=6 or not cols[5].startswith('/')or cols[5].endswith(' (deleted)'):continue
   p=Path(cols[5])
   if p.is_file():
    st=p.stat();prev=out.get(str(p),{});out[str(p)]=dict(sha256=sha(p)if not str(p).startswith('/dev/shm/')else None,permissions=prev.get('permissions',[])+[cols[1]],bytes=st.st_size,uid=st.st_uid,regular=__import__('stat').S_ISREG(st.st_mode),symlink=p.is_symlink())
  return out
 before=maps();baseline=read(ROOT/'NAMESPACE_ELF_PINS.json')['files'];out_result=dict(passed=False,closed=False,lane=LANE,cpu=LANES[LANE],DLL_loads=0,constructor_attempts=0,constructor_returns=0,constructor_inflight=False,query_attempts=0,query_returns=0,query_inflight=False,internal_modelwork=None,internal_optimizer_iterations=None,physics_native=0,replay_native=0,MuJoCo_initializations=0,formal_common_tasks=0,whole_navigation_qualified=False,full_vehicle_safety_qualified=False,first_error=None);h=None;lib=None;start=time.monotonic()
 def checkpoint(stage):put(O/'CALL_JOURNAL.json',dict(out_result,stage=stage))
 def verify(label):
  current=maps();put(O/(label+'_MAPS.json'),dict(files=current))
  for n,row in current.items():
   with Path(n).open('rb')as f:magic=f.read(4)
   if n in before and magic!=b'\x7fELF':continue
   scope.classify(n,row,magic,baseline,os.getuid())
 try:
  verify('BEFORE_DLL');bindings=load('parallel_exact_algorithm_binding',C/'bindings.py');lib=bindings.bind_mppi()if LANE=='MPPI'else bindings.bind_svg();out_result['DLL_loads']=1;verify('AFTER_DLL');fixture=read(O/'INPUT.json');out_result.update(constructor_attempts=1,constructor_inflight=True);checkpoint('BEFORE_CONSTRUCTOR')
  if LANE=='MPPI':
   # Check actual ELF symbol interposition before one irreversible optimizer call.
   symbol='_ZNK4mppi9Optimizer21updateStateVelocitiesERNS_6models5StateE';sampler=ctypes.CDLL(str(R/'runs/v1319_mppi_coherent_sampling/libcoherent.so'),mode=os.RTLD_NOW|os.RTLD_NOLOAD);global_lib=ctypes.CDLL(None)
   assert ctypes.cast(getattr(sampler,symbol),ctypes.c_void_p).value==ctypes.cast(getattr(global_lib,symbol),ctypes.c_void_p).value,'MPPI_COHERENT_INTERPOSITION_NOT_ACTIVE';out_result['coherent_symbol_interposition_exact']=True
   h=lib.phase_mppi_create()
  else:
   config=read(O/'CONFIG.json');h=lib.phase_svg_create((ctypes.c_double*25)(*config['parameters']),25,(ctypes.c_int*7)(*config['integers']),7)
  out_result.update(constructor_returns=int(bool(h)),constructor_inflight=False);checkpoint('AFTER_CONSTRUCTOR');verify('AFTER_CONSTRUCTOR');error=ctypes.create_string_buffer(2048)
  if not h:
   getattr(lib,'phase_mppi_error'if LANE=='MPPI'else'phase_svg_error')(error,2048);raise AssertionError('NATIVE_CONSTRUCTOR_REFUSED:'+error.value.decode(errors='replace'))
  if LANE=='MPPI':
   params=read(R/'experiments/v1344_causal_night_entry/coherent_mppi_causal_params.json');foot=json.loads(params['local_costmap']['local_costmap']['ros__parameters']['footprint']);dp=ctypes.c_double;pose=(dp*5)(*fixture['rear_pose_speed']);path=(dp*(3*len(fixture['path_xyyaw'])))(*[v for p in fixture['path_xyyaw']for v in p]);fp=(dp*(2*len(foot)))(*[v for p in foot for v in p]);grid=(ctypes.c_ubyte*14400)(*fixture['cells']);out=(dp*2)(float('nan'),float('nan'));out_result.update(query_attempts=1,query_inflight=True);checkpoint('BEFORE_QUERY')
   code=lib.phase_mppi_solve(h,0,pose,path,len(fixture['path_xyyaw']),grid,120,120,.05,-3.,-3.,fp,len(foot),out);out_result.update(query_returns=1,query_inflight=False);lib.phase_mppi_error(error,2048);put(O/'RAW_RETURN.json',dict(code=code,twist_hex=bytes(out).hex(),native_error=error.value.decode(errors='replace'),outer_calls=lib.phase_mppi_call_count(h)));checkpoint('AFTER_RAW_RETURN');verify('AFTER_QUERY')
   assert code==0,'MPPI_NATIVE_QUERY_REFUSED:'+error.value.decode(errors='replace');assert lib.phase_mppi_call_count(h)==1 and all(math.isfinite(x)for x in out),'MPPI_QUERY_COUNTS_OR_FINITE';out_result.update(raw_twist=list(out),outer_solver_calls=1,admissible_body_request=abs(out[0])<=.1 and abs(out[1])<=abs(out[0])/1.32+1e-12,RNG_stream_reproducibility_qualified=False,MPPI_batch_samples=1000,MPPI_horizon_steps=56,actual_internal_rollout_total=None)
  else:
   maps_in=read(O/'MAPS.json');planes=[(ctypes.c_double*10000)(*maps_in[n])for n in ['collision_layer','distance_field','angle_field','speed_field']];code=lib.phase_svg_set_maps(h,100,100,.1,0.,0.,*planes);assert code==0,'SVG_MAP_BINDING_REFUSED';state=(ctypes.c_double*5)(*fixture['state']);out=(ctypes.c_double*14)(*[float('nan')]*14);rate=ctypes.c_double(float('nan'));out_result.update(query_attempts=1,query_inflight=True);checkpoint('BEFORE_QUERY');code=lib.phase_svg_solve(h,state,5,out,14,ctypes.byref(rate));out_result.update(query_returns=1,query_inflight=False);lib.phase_svg_error(error,2048);put(O/'RAW_RETURN.json',dict(code=code,controls_hex=bytes(out).hex(),collision_hex=bytes(rate).hex(),native_error=error.value.decode(errors='replace')));checkpoint('AFTER_RAW_RETURN');verify('AFTER_QUERY');counts=(ctypes.c_ulonglong*2)();assert lib.phase_svg_call_counts(h,counts,2)==0 and list(counts)==[1,1],'SVG_QUERY_COUNTER';assert code==0 and all(math.isfinite(x)for x in out)and 0<=rate.value<=1,'SVG_NATIVE_QUERY_REFUSED'
   out_result.update(raw_controls=list(out),author_collision_rate=rate.value,outer_solver_calls=1,author_vehicle_not_Phase_model=True,qualification_parameters_not_common_benchmark=True,steering_within_Phase_cap=all(abs(x)<=.42722137342572125 for x in out),sample_batch=32,horizon=15,actual_internal_rollout_total=None)
  out_result['passed']=True
 except BaseException as e:out_result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if h:
   try:getattr(lib,'phase_mppi_destroy'if LANE=='MPPI'else'phase_svg_destroy')(h);out_result['destroy_calls']=1
   except BaseException as e:out_result['secondary_destroy_error']=repr(e);out_result['passed']=False
  out_result.update(closed=True,wall_s=time.monotonic()-start);put(O/'RESULT.json',out_result)
 print(json.dumps(out_result));return 0 if out_result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
