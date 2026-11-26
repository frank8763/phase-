"""One missing startup environment fix; reuse prior scope proofs unchanged."""
from context import R,C,O,read,put,sha,load
from pathlib import Path
import ast,json,os,subprocess,time,traceback
def main():
 os.sched_setaffinity(0,{5});assert not(O/'SOURCE_ONCE.json').exists();put(O/'SOURCE_ONCE.json',dict(unix=time.time(),models=0));result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,controller_constructors=0,solver_queries=0,physics=0,replay=0);files={}
 try:
  P=R/'runs/v2014_mppi_vehicle_exact_shared_scope';old=R/'experiments/v2014_mppi_vehicle_exact_shared_scope';H=R/'experiments/v2018_mppi_cold_start_evidence'
  assert read(P/'SOURCE_QUALIFICATION.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']and read(P/'COMPONENT_POST_STORAGE_BARRIER.json')['passed'];assert read(P/'COMPLETION.json')['closed']and read(P/'COMPLETION.json')['actual_native']==0
  files.update(read(P/'SOURCE_FREEZE.json')['files']);prior=files.copy();unchanged=[]
  for p in old.glob('*.py'):
   if p.name=='qualify_source.py':continue
   expected=p.read_text().replace(old.name,C.name).replace('v2015_mppi_vehicle_evidence','v2018_mppi_cold_start_evidence')
   if p.name=='owner.py':expected=expected.replace('env=dict(os.environ,PYTHONDONTWRITEBYTECODE',"env=dict(os.environ,LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),PYTHONDONTWRITEBYTECODE")
   assert(C/p.name).read_text()==expected,'UNEXPECTED_DECISION_OR_SAFETY_CHANGE:'+p.name;unchanged.append(p.name)
  # Actual failing seam from V2014 is cold GL import. Fix is at process creation.
  isolate=load('original_Phase_isolation_for_GL_metadata',R/'tools/isolate.py');cmd=isolate.command(C/'gl_metadata_probe.py',writable=False);env=dict(os.environ,PHASE_GL_METADATA_PROBE='1',LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),PYOPENGL_PLATFORM='osmesa',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
  p=subprocess.run(['taskset','-c','6',*cmd],cwd=R,env=env,capture_output=True,timeout=30);(O/'GL_METADATA.console').write_bytes(p.stdout+p.stderr);assert p.returncode==0,p.stderr.decode()[-4000:];gl=json.loads(p.stdout);assert gl['passed']and gl['models']==gl['MuJoCo_imports']==0
  expected=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu/libOSMesa.so.8.0.0';assert files[str(expected.relative_to(R))]==gl['OSMesa_sha256'];put(O/'GL_METADATA_PROOF.json',gl)
  p=subprocess.run(['taskset','-c','6','/usr/bin/python3','-B',str(C/'pilot_entry.py')],cwd=R,env=dict(os.environ,PHASE_REPO=str(R)),capture_output=True,timeout=10);assert p.returncode!=0 and b'MPPI_COMPONENT_NOT_ADMITTED'in p.stderr
  for folder in [C,H]:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [O/n for n in ['PILOT_TASK.json','LIMITS_DRAFT.json','NATIVE_DEPENDENCIES.json','AUTHORIZATION.json','JOINT_RESOURCE_RESERVATION.json','GL_METADATA_PROOF.json']]+[P/n for n in ['SOURCE_QUALIFICATION.json','SOFTWARE_CHECK_PROOF.json','COMPONENT_POST_STORAGE_BARRIER.json','COMPLETION.json','RUNTIME_CLOSED_REVIEW.json']]:files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items())
  proof=dict(passed=True,only_nonnumerical_startup_change='OSMesa LD_LIBRARY_PATH before Python process creation',prior_SOURCE_proof_path=str((P/'SOURCE_QUALIFICATION.json').relative_to(R)),prior_SOURCE_proof_sha256=sha(P/'SOURCE_QUALIFICATION.json'),all_prior_controller_map_response_safety_CPU_quota_bodies_equal_after_namespace=unchanged,cold_actual_graphics_loader_proof=gl,old_no_physics_failure_retained=True,no_old_model_or_controller_repeat=True,unadmitted_new_entry_refuses_before_model=True,physical_admission=False)
  put(O/'SOFTWARE_CHECK_PROOF.json',proof);files[str((O/'SOFTWARE_CHECK_PROOF.json').relative_to(R))]=sha(O/'SOFTWARE_CHECK_PROOF.json')
  put(O/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False));put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(source_members_seen=len(files),models_authorized=False))
 finally:result['closed']=True;put(O/'SOURCE_QUALIFICATION.json',result);put(O/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
