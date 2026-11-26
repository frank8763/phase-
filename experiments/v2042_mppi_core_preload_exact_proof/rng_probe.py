"""Cold original-plugin preload/seed component, zero controller/plant calls."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import SOURCE,R,C,O,SOURCE,read,put,sha,load
import ctypes,importlib.abc,json,os,resource,time,traceback
def main():
 assert os.sched_getaffinity(0)=={6};a=read(O/'DIRECT_CORE_RNG_PROBE_ADMISSION.json');assert a['scope']=='MPPI_PRECONSTRUCTOR_RNG_PROBE'and a['models_authorized']is False and time.time()<a['deadline_unix']and time.monotonic()<a['deadline_monotonic']
 assert a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')and read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered'];frozen=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 out=O/'direct_core_rng_probe_output';assert not(out/'NATIVE_ONCE.json').exists();put(out/'NATIVE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),algorithm_constructor_cap=0,query_cap=0,plant_cap=0,RNG_seed_cap=1));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','kernel','factory','vehicle','torch','jax','fast_predict'}:raise AssertionError('RNG_PROBE_NO_MODEL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban());result=dict(passed=False,closed=False,actual_controller_constructors=0,actual_optimizer_queries=0,models=0,physics_native=0,replay_native=0,RNG_seed_attempts=0,explicit_controller_CABI_DLL_loads=0,first_error=None)
 baseline_paths={line.split(None,5)[5]for line in Path('/proc/self/maps').read_text().splitlines()if len(line.split(None,5))==6}
 try:
  bridge=R/'runs/v1998_mppi_map_bootstrap_preparation/libphase_mppi_map_bootstrap.so';assert sha(bridge)==frozen[str(bridge.relative_to(R))];lib=ctypes.CDLL(str(bridge));result['explicit_controller_CABI_DLL_loads']=1
  from rng_binding import seed_before_constructor
  result['RNG_seed_attempts']=1;proof=seed_before_constructor(frozen,runtime_probe=True);result['RNG_seed_returns']=1
  scope=load('original_exact_ELF_and_nonexec_mapping_scope',R/'experiments/v1963_rpp_nonexecuting_shm_scope/mapping_scope.py');pins=read(O/'NATIVE_DEPENDENCIES.json')['namespace_ELF_files_SHA256'];maps={}
  for line in Path('/proc/self/maps').read_text().splitlines():
   cols=line.split(None,5)
   if len(cols)!=6 or not cols[5].startswith('/')or cols[5].endswith(' (deleted)'):continue
   p=Path(cols[5])
   if not p.is_file():continue
   st=p.stat();old=maps.get(str(p),{});row=dict(sha256=None if str(p).startswith('/dev/shm/')else sha(p),permissions=old.get('permissions',[])+[cols[1]],bytes=st.st_size,uid=st.st_uid,regular=__import__('stat').S_ISREG(st.st_mode),symlink=p.is_symlink());maps[str(p)]=row
  put(out/'LOADED_MAPS.json',dict(files=maps))
  for name,row in maps.items():
   with Path(name).open('rb')as f:magic=f.read(4)
   if magic!=b'\x7fELF'and name in baseline_paths:continue
   scope.classify(name,row,magic,pins,os.getuid())
  result.update(passed=True,seed_proof=proof,all_actual_ELF_pins_passed=True,original_plugin_constructor_never_called=True,all_internal_loader_static_initialization_work_unknown=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result['closed']=True;put(out/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
