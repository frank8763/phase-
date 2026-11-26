"""Bounded source-only delta: eager original core instead of eager plugin."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;P=R/'runs/v2037_parallel_reserved_source';OLD=R/'experiments/v2039_mppi02_reserved_census';O=P/'lanes/common_02__MPPI'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 p=Path(p);x=json.loads(p.read_text())
 if p.name=='SOURCE_FREEZE.json'and 'inherit_freeze_path'in x:
  parent=R/x['inherit_freeze_path'];assert sha(parent)==x['inherit_freeze_sha256'];base=read(parent)['files'];assert all(n not in base or base[n]==h for n,h in x['files'].items());x=dict(x,files=dict(base,**x['files']))
 return x
def put(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def main():
 os.sched_setaffinity(0,{5});assert not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0));result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,controller_constructors=0,optimizer_queries=0,physics=0,replay=0)
 try:
  assert read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered'];old=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in old.items())
  assert not read(O/'RNG_RUNTIME_PROBE_RESULT.json')['passed']and not(O/'PILOT_ONCE_CLAIM.json').exists()and not(O/'FORMAL_REGISTERED.json').exists()and not(O/'actual').exists()
  # Keep all numerical/physical gates byte identical after only namespace replacement.
  same=[]
  for n in ['capture.py','error_stop.py','resources.py','work.py','history_binding.py','response.py','evidence_service.py','generic_audit.py','observation.py','driver.py','navigation.py','quota.py','reserved_census.py','cpu_policy.py','causal_wire.py','map_adapter.py','path_adapter.py']:
   if not(OLD/n).exists():continue
   assert(C/n).read_text()==(OLD/n).read_text().replace(OLD.name,C.name),'NON_METADATA_CHANGED:'+n;same.append(n)
  # Reconstruct every changed authority-binding file from its old exact bytes.
  metadata=[]
  for p in OLD.glob('*.py'):
   if p.name in same or p.name=='rng_binding.py':continue
   t=p.read_text().replace(OLD.name,C.name)
   for name in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','POST_SOURCE_STORAGE_BARRIER.json']:t=t.replace("O/'"+name+"'","SOURCE/'"+name+"'")
   if p.name=='context.py':t=t.replace("SOURCE=R/'runs/v2037_parallel_reserved_source';O=SOURCE/'lanes'/'common_02__MPPI'","SOURCE=R/'runs/v2042_mppi_core_preload_exact_proof';O=R/'runs/v2037_parallel_reserved_source/lanes/common_02__MPPI'")
   elif p.name=='pilot_entry.py':t=t.replace('C=Path(__file__).resolve().parent',"C=Path(__file__).resolve().parent\nSOURCE=R/'runs/v2042_mppi_core_preload_exact_proof'")
   elif 'SOURCE'in t:
    if 'from context import 'in t:t=t.replace('from context import ','from context import SOURCE,',1)if 'from context import SOURCE,'not in t else t
    elif 'R=Path'in t:t=t.replace('R=Path(__file__).resolve().parents[2];',"R=Path(__file__).resolve().parents[2];SOURCE=R/'runs/v2042_mppi_core_preload_exact_proof';",1)
    elif p.name=='pilot_entry.py':t=t.replace('C=Path(__file__).resolve().parent',"C=Path(__file__).resolve().parent\nSOURCE=R/'runs/v2042_mppi_core_preload_exact_proof'")
   t=t.replace("'RNG_PROBE_ADMISSION.json'","'DIRECT_CORE_RNG_PROBE_ADMISSION.json'").replace("'RNG_RUNTIME_PROBE_RESULT.json'","'DIRECT_CORE_RNG_RUNTIME_PROBE_RESULT.json'").replace("'rng_probe_output'","'direct_core_rng_probe_output'")
   assert(C/p.name).read_text()==t,'AUTHORITY_BODY_CHANGED:'+p.name;metadata.append(p.name)
  t=(OLD/'rng_binding.py').read_text().replace(OLD.name,C.name).replace("'RNG_PROBE_ADMISSION.json'","'DIRECT_CORE_RNG_PROBE_ADMISSION.json'")
  a="plugin_path=R/'runs/v931_deadband_consistent_mppi/install/lib/libphase_deadband_mppi.so';assert source[str(plugin_path.relative_to(R))]==sha(plugin_path);plugin=ctypes.CDLL(str(plugin_path),mode=os.RTLD_NOW|os.RTLD_LOCAL)\n core=ctypes.CDLL('/opt/ros/jazzy/lib/libmppi_controller.so',mode=os.RTLD_NOW|os.RTLD_NOLOAD)"
  b="core_repo=R/'runs/v856_nav2_foundation/rootfs/opt/ros/jazzy/lib/libmppi_controller.so';assert source[str(core_repo.relative_to(R))]==sha(core_repo)\n core=ctypes.CDLL('/opt/ros/jazzy/lib/libmppi_controller.so',mode=os.RTLD_NOW|os.RTLD_LOCAL)"
  t=t.replace(a,b).replace('explicit_original_plugin_preloads=1,original_plugin_preloaded_local_before_seed=True','explicit_original_plugin_preloads=0,explicit_original_core_preloads=1,original_core_preloaded_local_before_seed=True')
  assert(C/'rng_binding.py').read_text()==t
  assert read(S/'DIAGNOSIS.json')['actual_seed_calls']==0
  reserve=load('unchanged_reserved_capacity',C/'reserved_census.py').global_admission(require_launch=True)
  # Real entry refusal, no Python model or DLL imports permitted.
  p=subprocess.run(['taskset','-c','6','/usr/bin/python3','-B',str(C/'run_phase.py')],cwd=R,capture_output=True,timeout=10);assert p.returncode!=0 and b'MPPI_INDEPENDENT_PHASE_NOT_ADMITTED'in p.stderr
  namespace=load('new_native_namespace',C/'run_phase.py');scratch=S/'namespace_software';scratch.mkdir();cmd=namespace.namespace(C/'pilot_entry.py',scratch);i=next(i for i,x in enumerate(cmd)if x.endswith('/envs/mk_mujoco/bin/python'))
  script="from pathlib import Path;import os;assert os.sched_getaffinity(0)=={6};Path("+repr(str(scratch/'PASS'))+").write_text('software')\nfor p in [Path("+repr(str(P/'lanes/common_09__RPP/FORBIDDEN'))+"),Path("+repr(str(C/'FORBIDDEN'))+")]:\n try:p.write_text('forbidden')\n except OSError:pass\n else:raise AssertionError('CROSS_LANE_SOURCE_WRITABLE')"
  p=subprocess.run(['taskset','-c','6',*cmd[:i],cmd[i],'-B','-c',script],cwd=R,capture_output=True,timeout=20);assert p.returncode==0,p.stderr.decode()
  # No global tree scan: new source footprint is accounted in the existing64MiB prep grant.
  allocated=sum(p.lstat().st_blocks*512 for folder in [C,S]for p in folder.rglob('*')if p.is_file());assert allocated<8*1024**2
  proof=dict(passed=True,same_numerical_and_safety_modules=same,authority_only_modules=metadata,exact_original_core_preload_only_change=True,original_pluginlib_semantics_retained=True,original_task_seed_schedule_unchanged=True,namespace_cpu6_crosslane_source_readonly=True,unadmitted_real_entry_refused=True,joint_reserved_peak_bytes=reserve['joint_peak_bytes'],new_source_allocated_bytes=allocated,new_source_probe_subset_cap_bytes=8*1024**2,all_old_probe_failures_preserved=True,new_native_seed_probe_required=True,models=0,algorithm_DLLs=0,controller_constructors=0,optimizer_queries=0,physics=0,replay=0);put(S/'SOFTWARE_CHECK_PROOF.json',proof)
  files=dict(old)
  for folder in [C,S]:
   for p in folder.iterdir():
    if p.is_file()and p.name!='SOURCE_ONCE.json':
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [P/'PREPARATION_FINAL.json',P/'POST_SOURCE_STORAGE_BARRIER.json',P/'CURRENT_SOURCE_REMOTE_RECOVERY.json',O/'RNG_RUNTIME_PROBE_RESULT.json',O/'rng_probe_output/RESULT.json',O/'rng_probe.console']:files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items())
  put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if old.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 finally:result['closed']=True;put(S/'SOURCE_QUALIFICATION.json',result);put(S/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
