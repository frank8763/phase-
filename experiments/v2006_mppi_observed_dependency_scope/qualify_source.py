"""Once lane authority/isolation/source check; zero algorithm calls."""
from common import R,C,ROOT,O,read,put,sha,load,LANES
from pathlib import Path
import ast,os,subprocess,time,traceback

def main():
 os.sched_setaffinity(0,{5});start=time.monotonic();assert not(ROOT/'SOURCE_ONCE.json').exists();put(ROOT/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),algorithm_calls=0));files={};result=dict(passed=False,closed=False,algorithm_DLL_loads=0,constructor_calls=0,optimizer_calls=0,MuJoCo_models=0,physics_native=0,replay_native=0)
 try:
  prior=R/'runs/v2000_mppi_original_map_initialization';assert read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered'];assert read(prior/'COMPLETION.json')['closed']and read(prior/'POST_NUMERIC_STORAGE_BARRIER.json')['passed'];files.update(read(prior/'SOURCE_FREEZE.json')['files']);parent_files=files.copy();pins=read(ROOT/'NAMESPACE_ELF_PINS.json');files.update(pins['repo_dependency_files'])
  for n in files:assert sha(R/n)==files[n],'INHERITED_OR_LIBRARY_BYTES_CHANGED:'+n
  for folder in [C,R/'experiments/v2007_mppi_observed_source_recovery',R/'experiments/v2008_mppi_observed_runtime_recovery']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [ROOT/n for n in ['AUTHORIZATION.json','PREPARATION.json','NAMESPACE_ELF_PINS.json','BOOTSTRAP_ELF_INVENTORY.json','OBSERVED_DEPENDENCY_PROOF.json','JOINT_RESOURCE_RESERVATION.json']]+list((ROOT/'lanes').glob('*/INPUT.json'))+list((ROOT/'lanes').glob('*/CONFIG.json'))+list((ROOT/'lanes').glob('*/MAPS.json'))+[prior/'COMPLETION.json',prior/'POST_NUMERIC_STORAGE_BARRIER.json',prior/'RUNTIME_CLOSED_REVIEW.json']:
   files[str(p.relative_to(R))]=sha(p)
  namespace=load('lane_actual_namespace_source_check',C/'namespace.py');negative=[];probes=[]
  for lane,cpu in LANES.items():
   cmd,env=namespace.command(lane,C/'native.py');env.pop('LD_PRELOAD',None);env.pop('PHASE_COHERENT_NOISE',None);p=subprocess.run(['taskset','-c',str(cpu),*cmd],cwd=R,env=env,capture_output=True,timeout=20);(ROOT/'lanes'/lane/'source_refusal.console').write_bytes(p.stdout+p.stderr);assert p.returncode!=0 and b'ADMISSION.json'in p.stderr and not(ROOT/'lanes'/lane/'NATIVE_ONCE.json').exists()and not(ROOT/'lanes'/lane/'RESULT.json').exists();negative.append(lane+'_real_native_CLI_refuses_before_algorithm_DLL')
   other=ROOT/'lanes'/('SVG-MPPI'if lane=='MPPI'else'MPPI');script="import os,json,pathlib;here=pathlib.Path("+repr(str(ROOT/'lanes'/lane))+ ");here.joinpath('SOURCE_ISOLATION_WRITE_PROBE').write_text('lane-only');blocked=[]\nfor p in [pathlib.Path("+repr(str(other/'FORBIDDEN_CROSS_WRITE'))+"),pathlib.Path("+repr(str(C/'FORBIDDEN_SOURCE_WRITE'))+")]:\n try:p.write_text('forbidden')\n except OSError:blocked.append(str(p))\n else:raise AssertionError('CROSS_LANE_OR_SOURCE_WRITABLE')\nassert os.sched_getaffinity(0)=={"+str(cpu)+"};print(json.dumps(dict(passed=True,cpu="+str(cpu)+",blocked=blocked,models=0)))"
   assert '/usr/bin/python3.12'in cmd
   position=cmd.index('/usr/bin/python3.12');probe=cmd[:position]+['/usr/bin/python3.12','-I','-B','-S','-c',script];p=subprocess.run(['taskset','-c',str(cpu),*probe],cwd=R,env=env,capture_output=True,timeout=15);assert p.returncode==0,p.stderr.decode();proof=__import__('json').loads(p.stdout);assert proof['passed']and len(proof['blocked'])==2;probes.append(proof)
  for p in [R/'runs/v1999_phase_cpu_allocation/RESULT.json',R/'runs/v1998_mppi_map_bootstrap_preparation/RESULT.json']:files[str(p.relative_to(R))]=sha(p)
  assert not(C/'FORBIDDEN_SOURCE_WRITE').exists()and not any((ROOT/'lanes'/n/'FORBIDDEN_CROSS_WRITE').exists()for n in LANES)
  binding=load('lane_CABI_source_no_runtime',C/'bindings.py')
  for name in ['bind_mppi','bind_svg']:
   try:getattr(binding,name)()
   except AssertionError as e:assert str(e)=='PARALLEL_LANE_AFFINITY';negative.append(name+'_no_authority_no_algorithm_DLL')
   else:raise AssertionError('UNADMITTED_CABI_BOUND')
  assert sha(R/'runs/v1998_mppi_map_bootstrap_preparation/libphase_mppi_map_bootstrap.so')==files['runs/v1998_mppi_map_bootstrap_preparation/libphase_mppi_map_bootstrap.so'];assert sha(R/'runs/v1656_svg_solver_interface/libphase_svg_bridge.so')==files['runs/v1656_svg_solver_interface/libphase_svg_bridge.so']
  proof=dict(passed=True,actual_isolated_CPU_lane_probes=probes,actual_unadmitted_CLI_and_binding_negatives=negative,latest_user_parallel_math_authorization=True,algorithm_DLL_calls=0,constructors=0,optimizer_calls=0,physical_steps=0,common_task_slots_claimed=0,full_vehicle_parallelism_not_yet_qualified=True,original_RPP_closed_failure_preserved=True,one_constructor_query_each_only=True);put(ROOT/'SOFTWARE_CHECK_PROOF.json',proof);files[str((ROOT/'SOFTWARE_CHECK_PROOF.json').relative_to(R))]=sha(ROOT/'SOFTWARE_CHECK_PROOF.json');assert all(sha(R/n)==h for n,h in files.items());delta={n:h for n,h in files.items()if parent_files.get(n)!=h};put(ROOT/'SOURCE_FREEZE.json',dict(files=delta,inherit_freeze_path=str((prior/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),logical_source_members=len(files),namespace_ELF_pins_sha256=sha(ROOT/'NAMESPACE_ELF_PINS.json'),models_authorized=False));put(ROOT/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(prior.relative_to(R)),freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),recovery_path=str((prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),software_proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(ROOT/'FAILED_SOURCE_FREEZE.json',dict(source_members_seen=len(files),inventory_digest=__import__('hashlib').sha256(__import__('json').dumps(files,sort_keys=True).encode()).hexdigest(),source_not_qualified=True,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(ROOT/'SOURCE_QUALIFICATION.json',result);put(ROOT/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,algorithm_DLL_calls=0,source_only=True,all_frozen_SHA_after_qualification=result['passed']))
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
