"""Original 8000/100/10 SVG core, current causal input, no plant imports/writes."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import R,C,O,read,sha,digest,load,native_authority
import ctypes,importlib.abc,json,math,os,resource,time,traceback
def main():
 a,source=native_authority();resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,65));os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in{'numpy','mujoco','torch','jax','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('SVG_NATIVE_NO_PLANT_IMPORT:'+name)
 sys.meta_path.insert(0,Ban());sequence=0;h=None;lib=None;counts=dict(DLL_loads=0,constructor_attempts=0,constructor_returns=0,query_attempts=0,query_returns=0,destroy_calls=0,constructor_inflight=False,query_inflight=False,internal_rollout_steps=None)
 def emit(label,v):print(label+json.dumps(v,allow_nan=False),flush=True)
 def event(stage):
  nonlocal sequence
  emit('SVG_EVENT ',dict(sequence=sequence,stage=stage,counts=dict(counts)));sequence+=1
 pins=read(O/'NATIVE_DEPENDENCIES.json')['files'];scope=load('SVG_exact_ELF_mapping_scope',R/'experiments/v1963_rpp_nonexecuting_shm_scope/mapping_scope.py');baseline=set()
 for line in Path('/proc/self/maps').read_text().splitlines():
  columns=line.split(None,5)
  if len(columns)==6:baseline.add(columns[5])
 def verify():
  seen={}
  for line in Path('/proc/self/maps').read_text().splitlines():
   columns=line.split(None,5)
   if len(columns)!=6 or not columns[5].startswith('/')or columns[5].endswith(' (deleted)'):continue
   p=Path(columns[5])
   if not p.is_file():continue
   st=p.stat();row=seen.setdefault(str(p),dict(sha256=None if str(p).startswith('/dev/shm/')else sha(p),permissions=[],bytes=st.st_size,uid=st.st_uid,regular=__import__('stat').S_ISREG(st.st_mode),symlink=p.is_symlink()));row['permissions'].append(columns[1])
  for n,row in seen.items():
   with Path(n).open('rb')as f:magic=f.read(4)
   if n in baseline and magic!=b'\x7fELF':continue
   scope.classify(n,row,magic,pins,os.getuid())
 try:
  from peer_contract import decode,verify_author_counts
  line=sys.stdin.buffer.readline(1024**2+1);frame,ack=decode(line,sequence=0,run_id=a['assignment']['run_id'])
  request=frame['request'];maps=frame['maps']
  from binding import bind
  lib=bind();counts['DLL_loads']=1;verify();cfg=read(O/'CONFIG.json');assert cfg['integers']==[15,8000,1,100,10,1,1]
  counts.update(constructor_attempts=1,constructor_inflight=True);event('BEFORE_CONSTRUCTOR');t=time.monotonic();h=lib.phase_svg_create((ctypes.c_double*25)(*cfg['parameters']),25,(ctypes.c_int*7)(*cfg['integers']),7);counts.update(constructor_returns=int(bool(h)),constructor_inflight=False,constructor_wall_s=time.monotonic()-t);event('AFTER_CONSTRUCTOR');assert h,'SVG_CONSTRUCTOR_REFUSED';verify()
  query_sequence=0
  while True:
   assert maps['nx']==maps['ny']==100;planes=[(ctypes.c_double*10000)(*maps[n])for n in ['collision_layer','distance_field','angle_field','speed_field']];assert lib.phase_svg_set_maps(h,100,100,maps['resolution'],*maps['center'],*planes)==0,'SVG_MAP_BINDING_REFUSED'
   state=(ctypes.c_double*5)(*frame['author_state']);controls=(ctypes.c_double*14)(*[float('nan')]*14);rate=ctypes.c_double(float('nan'));counts.update(query_attempts=counts['query_attempts']+1,query_inflight=True);event('BEFORE_QUERY');t=time.monotonic();code=lib.phase_svg_solve(h,state,5,controls,14,ctypes.byref(rate));counts.update(query_returns=counts['query_returns']+1,query_inflight=False,query_wall_s=time.monotonic()-t);verify();outer=(ctypes.c_ulonglong*2)();assert lib.phase_svg_call_counts(h,outer,2)==0,'SVG_COUNTER_READ_REFUSED';counts.update(author_solve_attempts=int(outer[0]),author_solve_returns=int(outer[1]),native_solve_returncode=code);event('AFTER_QUERY');verify_author_counts(list(outer),attempts=counts['query_attempts'],returns=counts['query_returns'],code=code)
   assert code==0 and all(math.isfinite(x)and abs(x)<=.45 for x in controls)and math.isfinite(rate.value)and 0<=rate.value<=1,'SVG_RAW_QUERY_REFUSED'
   raw=dict(run_id=request['run_id'],origin_native_tick=request['native_tick'],input_sha256=digest(request),map_sha256=frame['maps_sha256'],steering=list(controls),collision_rate=rate.value);emit('SVG_REPLY ',dict(passed=True,raw=raw,transport_ack=ack,counts=dict(counts),controls_double_hex=bytes(controls).hex(),collision_rate_double_hex=bytes(rate).hex(),all_actual_ELF_pins_verified=True))
   query_sequence+=1
   line=sys.stdin.buffer.readline(1024**2+1)
   if not line:break
   frame,ack=decode(line,sequence=query_sequence,run_id=a['assignment']['run_id']);request=frame['request'];maps=frame['maps']
  assert counts['constructor_returns']==1 and 1<=counts['query_returns']<=2,'SVG_PERSISTENT_QUERY_LIMIT'
 except BaseException as e:emit('SVG_ERROR ',dict(error=repr(e),traceback=traceback.format_exc(),counts=dict(counts)));return 1
 finally:
  if h:lib.phase_svg_destroy(h);counts['destroy_calls']=1
  emit('SVG_CLOSED ',dict(counts=dict(counts),models=0,physics=0,internal_rollout_steps=None))
 return 0
if __name__=='__main__':raise SystemExit(main())
