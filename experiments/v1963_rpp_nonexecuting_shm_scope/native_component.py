"""Exactly one native synthetic straight query; no simulator or common task."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import R,C,O,read,sha,put
import ctypes,math,time,os,traceback
from binding import bind
from mapping_scope import classify

def maps():
 out={}
 for line in __import__('pathlib').Path('/proc/self/maps').read_text().splitlines():
  cols=line.split(None,5)
  if len(cols)==6 and cols[5].startswith('/'):
   p=__import__('pathlib').Path(cols[5])
   if p.is_file()and not str(p).endswith(' (deleted)'):
    old=out.get(str(p),{});out[str(p)]=dict(sha256=sha(p),permissions=old.get('permissions',[])+[cols[1]],bytes=p.stat().st_size,uid=p.stat().st_uid,regular=__import__('stat').S_ISREG(p.stat().st_mode),symlink=p.is_symlink())
 return out

def main():
 assert not(O/'NATIVE_ONCE_CLAIM.json').exists();put(O/'NATIVE_ONCE_CLAIM.json',dict(unix=time.time(),pid=os.getpid(),constructor_cap=1,solver_cap=1));before=maps();result=dict(passed=False,closed=False,explicit_DLL_loads=0,controller_constructor_attempts=0,controller_constructors_returned=0,costmap_constructors_internal_unknown=True,valid_solver_attempts=0,solver_calls_returned=0,models=0,physical_native=0,replay_native=0,synthetic_fixture_only=True,whole_navigation_qualified=False,upstream_static_registration_and_internal_model_counts_unknown=True);h=None;lib=None
 try:
  frozen=read(O/'SOURCE_FREEZE.json');lib=bind(frozen['files']);result['explicit_DLL_loads']=1;result['controller_constructor_attempts']=1;h=lib.phase_rpp_create();result['controller_constructors_returned']=int(bool(h));after=maps();put(O/'AFTER_CONSTRUCTOR_MAPS.json',dict(before=before,new={k:v for k,v in after.items()if k not in before}))
  for name,row in after.items():
   if name in before:continue
   p=__import__('pathlib').Path(name)
   with p.open('rb')as f:magic=f.read(4)
   classify(name,row,magic,frozen['namespace_ELF_files_SHA256'],os.getuid())
  error=ctypes.create_string_buffer(2048)
  if not h:lib.phase_rpp_error(error,2048);raise AssertionError('RPP_CONSTRUCTOR_REFUSED:'+error.value.decode(errors='replace'))
  result['controller_constructors_returned']=1;fixture=read(O/'FIXTURE.json');params=read(R/fixture['original_parameter_file']);foot=__import__('json').loads(params['local_costmap']['local_costmap']['ros__parameters']['footprint']);dp=ctypes.c_double;pose=(dp*5)(*fixture['rear_pose_speed']);path=(dp*(3*len(fixture['path_xyyaw'])))(*[v for p in fixture['path_xyyaw']for v in p]);fp=(dp*(2*len(foot)))(*[v for p in foot for v in p]);grid=(ctypes.c_ubyte*(120*120))();out=(dp*2)(float('nan'),float('nan'));result['valid_solver_attempts']=1
  code=lib.phase_rpp_solve(h,0,pose,path,len(fixture['path_xyyaw']),grid,120,120,.05,-3.,-3.,fp,len(foot),out);lib.phase_rpp_error(error,2048);result.update(returncode=code,twist=[v if math.isfinite(v)else None for v in out],native_error=error.value.decode(errors='replace'),solver_calls_returned=lib.phase_rpp_call_count(h))
  after_query=maps();put(O/'AFTER_QUERY_MAPS.json',dict(before=before,new={n:v for n,v in after_query.items()if n not in before}))
  for name,row in after_query.items():
   if name in before:continue
   with __import__('pathlib').Path(name).open('rb')as f:magic=f.read(4)
   classify(name,row,magic,frozen['namespace_ELF_files_SHA256'],os.getuid())
  assert code==0,'RPP_SYNTHETIC_SOLVE_REFUSED';assert all(math.isfinite(v)for v in out)and abs(out[0]-.1)<=1e-12 and abs(out[1])<=1e-12,'RPP_STRAIGHT_OUTPUT_MISMATCH';assert lib.phase_rpp_call_count(h)==1 and lib.phase_rpp_poisoned(h)==0
  duplicate=lib.phase_rpp_solve(h,0,pose,path,len(fixture['path_xyyaw']),grid,120,120,.05,-3.,-3.,fp,len(foot),out);assert duplicate==-3 and lib.phase_rpp_call_count(h)==1 and lib.phase_rpp_poisoned(h)==1,'RPP_DUPLICATE_TICK_ACCEPTED';result.update(passed=True,duplicate_tick_rejected_before_solver=True,negative_duplicate_returncode=duplicate)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if h and lib is not None:lib.phase_rpp_destroy(h);result['destroy_calls']=1
  result['closed']=True;put(O/'RESULT.json',result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
