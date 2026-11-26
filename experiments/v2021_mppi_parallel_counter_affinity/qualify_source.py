"""Only counter CPU binding; preserve all numerical bodies and prior proofs."""
from context import R,C,O,read,put,sha
from pathlib import Path
import ast,json,os,subprocess,time,traceback
def main():
 os.sched_setaffinity(0,{5});assert not(O/'SOURCE_ONCE.json').exists();put(O/'SOURCE_ONCE.json',dict(unix=time.time(),models=0));files={};result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,controller_constructors=0,queries=0,physics=0,replay=0)
 try:
  P=R/'runs/v2017_mppi_cold_renderer_startup';old=R/'experiments/v2017_mppi_cold_renderer_startup';H=R/'experiments/v2022_mppi_parallel_counter_evidence'
  assert read(P/'SOURCE_QUALIFICATION.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']and read(P/'COMPONENT_POST_STORAGE_BARRIER.json')['passed'];closed=read(P/'COMPLETION.json');assert closed['closed']and closed['actual_native']==closed['own_replay_native']==200 and closed['independent_audit']['passed']
  assert "sched_getaffinity(0))==[2]"in closed['machine_first_error']['traceback'];files.update(read(P/'SOURCE_FREEZE.json')['files']);prior=files.copy();same=[]
  for p in old.glob('*.py'):
   if p.name=='qualify_source.py':continue
   expected=p.read_text().replace(old.name,C.name).replace('v2018_mppi_cold_start_evidence','v2022_mppi_parallel_counter_evidence')
   if p.name=='work.py':assert expected.count('==[2]')==1;expected=expected.replace('==[2]','==[6]')
   assert(C/p.name).read_text()==expected,'UNEXPECTED_NUMERICAL_OR_SAFETY_CHANGE:'+p.name;same.append(p.name)
  # This exercises only bookkeeping, no Predictor/Engine/model/allocator calls.
  script="import sys,time,json,os;sys.path.insert(0,"+repr(str(C))+");from work import ModelWork;assert os.sched_getaffinity(0)=={6};m=ModelWork(dict(python_native_cap=1,cpp_native_cap=1),time.time()+30);m.before('python',1);m.done('python',1);bad=[]\ntry:m.before('python',1)\nexcept AssertionError:bad.append('cap')\nelse:raise AssertionError('COUNTER_CAP_RELAXED')\nn=ModelWork(dict(python_native_cap=1,cpp_native_cap=1),time.time()-1)\ntry:n.before('python',1)\nexcept AssertionError:bad.append('deadline')\nelse:raise AssertionError('COUNTER_DEADLINE_RELAXED')\nassert bad==['cap','deadline'];print(json.dumps(dict(passed=True,synthetic_bookkeeping_only=True,actual_numerical_calls=0,physical_steps=0,negative=bad,CPU=6,synthetic_counter_state=m.snapshot())))"
  p=subprocess.run(['taskset','-c','6','/usr/bin/python3','-B','-c',script],cwd=R,capture_output=True,timeout=10);assert p.returncode==0,p.stderr.decode();counter=json.loads(p.stdout);put(O/'COUNTER_SOFTWARE_PROOF.json',counter)
  p=subprocess.run(['taskset','-c','6','/usr/bin/python3','-B',str(C/'pilot_entry.py')],cwd=R,env=dict(os.environ,PHASE_REPO=str(R)),capture_output=True,timeout=10);assert p.returncode!=0 and b'MPPI_COMPONENT_NOT_ADMITTED'in p.stderr
  for folder in [C,H]:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [O/n for n in ['PILOT_TASK.json','LIMITS_DRAFT.json','NATIVE_DEPENDENCIES.json','AUTHORIZATION.json','JOINT_RESOURCE_RESERVATION.json','COUNTER_SOFTWARE_PROOF.json']]+[P/n for n in ['SOURCE_QUALIFICATION.json','SOFTWARE_CHECK_PROOF.json','GL_METADATA_PROOF.json','COMPONENT_POST_STORAGE_BARRIER.json','COMPLETION.json','RUNTIME_CLOSED_REVIEW.json']]+list((R/'runs/v2020_mppi_verified_model_duplicate_cleanup').glob('*.json')):files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items())
  proof=dict(passed=True,only_resource_counter_affinity_changed=True,all_numerical_controller_gate_and_closure_bodies_equal_after_namespace=same,synthetic_counter=counter,prior_cold_GL_and_CPU_isolation_proof_reused_SHA=sha(P/'SOURCE_QUALIFICATION.json'),old200errorstop_replay_and_audit_failure_preserved=True,no_old_physical_replay_audit_or_qualification_reexecuted=True,unadmitted_entry_before_model=True)
  put(O/'SOFTWARE_CHECK_PROOF.json',proof);files[str((O/'SOFTWARE_CHECK_PROOF.json').relative_to(R))]=sha(O/'SOFTWARE_CHECK_PROOF.json')
  put(O/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False));put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(source_members_seen=len(files),models_authorized=False))
 finally:result['closed']=True;put(O/'SOURCE_QUALIFICATION.json',result);put(O/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
