from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import R,C,S,O,read,put,sha,load,authority
import ctypes,fcntl,importlib.abc,json,math,os,resource,time,traceback
def main():
 a,frozen=authority();assert not(O/'NATIVE_ONCE.json').exists();put(O/'NATIVE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),CPU=7,constructor_cap=1,query_cap=1,models=0));lock=(O/'execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(300,310));os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in{'numpy','mujoco','torch','jax','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('SVG_NO_PLANT_IMPORT:'+name)
 sys.meta_path.insert(0,Ban());pins=read(S/'NATIVE_DEPENDENCIES.json')['files'];scope=load('pinned_nonexecuting_mapping_scope',R/'experiments/v1963_rpp_nonexecuting_shm_scope/mapping_scope.py');baseline={line.split(None,5)[5]for line in Path('/proc/self/maps').read_text().splitlines()if len(line.split(None,5))==6}
 def verify(label):
  rows={}
  for line in Path('/proc/self/maps').read_text().splitlines():
   cols=line.split(None,5)
   if len(cols)!=6 or not cols[5].startswith('/')or cols[5].endswith(' (deleted)'):continue
   p=Path(cols[5])
   if not p.is_file():continue
   st=p.stat();prev=rows.get(str(p),{});rows[str(p)]=dict(sha256=None if str(p).startswith('/dev/shm/')else sha(p),permissions=prev.get('permissions',[])+[cols[1]],bytes=st.st_size,uid=st.st_uid,regular=__import__('stat').S_ISREG(st.st_mode),symlink=p.is_symlink())
  put(O/(label+'_MAPS.json'),dict(files=rows))
  for n,row in rows.items():
   with Path(n).open('rb')as f:magic=f.read(4)
   if n in baseline and magic!=b'\x7fELF':continue
   scope.classify(n,row,magic,pins,os.getuid())
 result=dict(passed=False,closed=False,CPU=7,DLL_loads=0,constructor_attempts=0,constructor_returns=0,constructor_inflight=False,query_attempts=0,query_returns=0,query_inflight=False,models=0,physics_native=0,replay_native=0,formal_common_tasks=0,whole_navigation_passed=False,full_vehicle_safety_qualified=False,internal_rollout_steps=None,first_error=None,secondary_errors=[]);start=time.monotonic();lib=None;h=None
 def checkpoint(stage):put(O/'CALL_JOURNAL.json',dict(result,stage=stage))
 try:
  from binding import bind
  lib=bind();result['DLL_loads']=1;verify('AFTER_DLL');config=read(S/'CONFIG.json');inp=read(S/'INPUT.json');maps=read(S/'MAPS.json');result.update(constructor_attempts=1,constructor_inflight=True);checkpoint('BEFORE_CONSTRUCTOR');t=time.monotonic();h=lib.phase_svg_create((ctypes.c_double*25)(*config['parameters']),25,(ctypes.c_int*7)(*config['integers']),7);result.update(constructor_returns=int(bool(h)),constructor_inflight=False,constructor_wall_s=time.monotonic()-t);checkpoint('AFTER_CONSTRUCTOR');assert h,'ORIGINAL_SVG_CONSTRUCTOR_REFUSED';verify('AFTER_CONSTRUCTOR')
  planes=[(ctypes.c_double*10000)(*maps[n])for n in ['collision_layer','distance_field','angle_field','speed_field']];code=lib.phase_svg_set_maps(h,maps['nx'],maps['ny'],maps['resolution'],*maps['center'],*planes);assert code==0,'SVG_CAUSAL_MAP_BINDING_REFUSED';state=(ctypes.c_double*5)(*inp['author_state']);controls=(ctypes.c_double*14)(*[float('nan')]*14);rate=ctypes.c_double(float('nan'));result.update(query_attempts=1,query_inflight=True);checkpoint('BEFORE_QUERY');t=time.monotonic();code=lib.phase_svg_solve(h,state,5,controls,14,ctypes.byref(rate));result.update(query_returns=1,query_inflight=False,query_wall_s=time.monotonic()-t);error=ctypes.create_string_buffer(2048);lib.phase_svg_error(error,2048);put(O/'RAW_RETURN.json',dict(returncode=code,controls_double_hex=bytes(controls).hex(),collision_rate_double_hex=bytes(rate).hex(),native_error=error.value.decode(errors='replace')));checkpoint('AFTER_RAW_SAVE');verify('AFTER_QUERY');counts=(ctypes.c_ulonglong*2)();assert lib.phase_svg_call_counts(h,counts,2)==0 and list(counts)==[1,1];assert code==0 and all(math.isfinite(x)for x in controls)and math.isfinite(rate.value)and 0<=rate.value<=1,'SVG_RAW_QUERY_REFUSED'
  assert all(abs(x)<=.45 for x in controls),'SVG_AUTHOR_DOMAIN_REFUSED';result.update(passed=True,raw_steering=list(controls),author_collision_rate=rate.value,outer_solver_counts=list(counts),sample_batch=8000,gradient_samples=100,svgd_iterations=10,horizon=15,original_seed42_and_sampler_i=True,Phase_steering_cap_compatible=all(abs(x)<=.42722137342572125 for x in controls),author_vehicle_not_Phase_plant=True,original_optimizer_body_unchanged=True,causal_saved_map_input_not_live_plant=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if h:
   try:lib.phase_svg_destroy(h);result['destroy_calls']=1
   except BaseException as e:result['secondary_errors'].append(repr(e));result['passed']=False
  result.update(closed=True,wall_s=time.monotonic()-start);put(O/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
