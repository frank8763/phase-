"""Persistent original RPP, readonly repo/runs, pipe replies as sole outputs."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import R,C,O,read,sha,load,digest,remaining
from binding import bind
import ctypes,json,math,os,traceback

def mappings():
 out={}
 for line in Path('/proc/self/maps').read_text().splitlines():
  cols=line.split(None,5)
  if len(cols)==6 and cols[5].startswith('/'):
   p=Path(cols[5])
   if p.is_file()and not str(p).endswith(' (deleted)'):
    old=out.get(str(p),{});st=p.stat();out[str(p)]=dict(sha256=sha(p),permissions=old.get('permissions',[])+[cols[1]],bytes=st.st_size,uid=st.st_uid,regular=__import__('stat').S_ISREG(st.st_mode),symlink=p.is_symlink())
 return out
def main():
 h=None;lib=None;calls=0;first=None;before=mappings();pins=read(O/'NATIVE_DEPENDENCIES.json')['namespace_ELF_files_SHA256'];scope=load('current_RPP_exact_mapping_scope',R/'experiments/v1963_rpp_nonexecuting_shm_scope/mapping_scope.py');created=0
 def verify_maps():
  after=mappings()
  for n,row in after.items():
   if n in before:continue
   with Path(n).open('rb')as f:magic=f.read(4)
   scope.classify(n,row,magic,pins,os.getuid())
  return {n:row for n,row in after.items()if n not in before}
 try:
  frozen=read(O/'SOURCE_FREEZE.json')['files'];lib=bind(frozen);h=lib.phase_rpp_create();created=int(bool(h));new=verify_maps();assert h,'RPP_CURRENT_CONSTRUCTOR_REFUSED'
  print('RPP_INIT '+json.dumps(dict(passed=True,constructors=created,DLL_loads=1,maps=new,readonly_peer=True)),flush=True)
  for line in sys.stdin:
   assert len(line)<=1024**2,'RPP_COMPONENT_INPUT_CAP';z=json.loads(line)
   if z.get('close'):break
   assert calls<1,'RPP_COMPONENT_QUERY_CAP'
   assert set(z)=={'request','map','path'};request=z['request'];m=z['map'];assert m['source_request_sha256']==digest(request)and m['native_tick']==request['native_tick']and m['source_receipt_packet_sha256']==request['measurement_source_packet_sha256'];assert request['method']=='RPP'and request['physical_authority']is False
   assert m['width']==m['height']==120 and m['resolution']==.05 and len(m['cells'])==14400 and all(type(v)is int and 0<=v<=255 for v in m['cells'])
   path=z['path'];assert 2<=len(path)<=10000 and all(len(p)==3 and all(math.isfinite(v)for v in p)for p in path);dp=ctypes.c_double;pose=(dp*5)(*m['rear_pose_speed']);pp=(dp*(len(path)*3))(*[v for p in path for v in p]);foot=m['footprint_xy'];fp=(dp*(len(foot)*2))(*[v for p in foot for v in p]);grid=(ctypes.c_ubyte*14400)(*m['cells']);out=(dp*2)(float('nan'),float('nan'));calls+=1
   code=lib.phase_rpp_solve(h,request['native_tick'],pose,pp,len(path),grid,120,120,.05,*m['origin'],fp,len(foot),out);error=ctypes.create_string_buffer(2048);lib.phase_rpp_error(error,2048);new=verify_maps()
   value=dict(passed=code==0,returncode=code,twist=[v if math.isfinite(v)else None for v in out],native_error=error.value.decode(errors='replace'),input_sha256=digest(request),origin_native_tick=request['native_tick'],solver_calls=lib.phase_rpp_call_count(h),constructors=created,maps=new,physical_authority=False)
   print('RPP_REPLY '+json.dumps(value,allow_nan=False),flush=True)
   if code!=0:break
 except BaseException as e:
  first=dict(error=repr(e),traceback=traceback.format_exc());print('RPP_ERROR '+json.dumps(dict(first_error=first,constructors=created,query_attempts=calls)),flush=True)
 finally:
  if h:lib.phase_rpp_destroy(h)
  print('RPP_CLOSED '+json.dumps(dict(closed=True,constructors=created,query_attempts=calls,first_error=first,destroy_calls=int(bool(h)),all_internal_work_unknown=True)),flush=True)
 return 0 if first is None else 1
if __name__=='__main__':raise SystemExit(main())
