"""One prospective evidence/audit source freeze, zero model or solver loads."""
import ast,fcntl,json,os,time,traceback
from pathlib import Path
from context import R,C,SOURCE,STUDY,O,read,put,sha,predecessors_closed
P=R/'runs/v2095_svg_common_full_route'
def main():
 assert os.sched_getaffinity(0)=={2};locks=[]
 for name in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/name).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 assert not(SOURCE/'SOURCE_ONCE.json').exists();put(SOURCE/'SOURCE_ONCE.json',dict(unix=time.time(),models=0,pid=os.getpid()))
 result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,constructors=0,queries=0,physics=0,replay=0)
 try:
  predecessors_closed();prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items());files=dict(prior)
  proof=read(SOURCE/'SOFTWARE_CHECK_PROOF.json');assert proof['passed']and proof['models']==proof['DLLs']==proof['physics']==0
  assert all(sha(R/n)==h for n,h in proof['source_pins'].items()),'SOFTWARE_CHECK_SOURCE_CHANGED'
  # Original navigation, safety predictions, actual/prefix/map auditor,
  # native numerical calls, controller, capture and replay remain byte-exact.
  for n in ['navigation.py','response.py','audit_component.py','native_worker.py','native_client.py','binding.py','runtime_binding.py','work.py','capture.py','error_stop.py','compact_record.py','generic_audit.py','observation.py','parallel_events.py','resources.py']:
   assert (C/n).read_bytes()==(R/'experiments/v2095_svg_common_full_route'/n).read_bytes(),'NUMERICAL_OR_SAFETY_CHANGE:'+n
  for folder in [C,R/'experiments/v2100_svg_second_formal_dispatch',R/'experiments/v2098_svg_direct_array_evidence',R/'experiments/v2097_svg_closed_round_recovery']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for n in proof['source_pins']:files[n]=sha(R/n)
  for n in ['CONFIG.json','NATIVE_DEPENDENCIES.json','AUTHORIZATION.json','BASELINE_DRAFT.json','SOFTWARE_CHECK_PROOF.json']:files[str((SOURCE/n).relative_to(R))]=sha(SOURCE/n)
  extra=[R/'runs/v2098_svg_direct_array_evidence/RESULT.json',SOURCE/'software_fixture/FAILED_CHECK_PROOF.json',R/'runs/v2097_svg_closed_round_recovery/FINAL_CHECKPOINT.json',STUDY/'rounds/common_01__SVGMPPI/RUNTIME_CLOSED_REVIEW.json',STUDY/'rounds/common_01__SVGMPPI/POST_ROUND_STORAGE_BARRIER.json',R/'experiments/v2062_bounded_dual_route_transport/net.py',R/'runs/v2062_bounded_dual_route_transport/SOFTWARE_RESULT.json']
  for p in extra:files[str(p.relative_to(R))]=sha(p)
  assert O==STUDY/'rounds/common_02__SVGMPPI'and not(O/'PILOT_ONCE_CLAIM.json').exists()and not(O/'COMPLETION.json').exists()and not(O/'actual').exists()
  assert all((O/n).is_file()and(O/n).stat().st_size==0 for n in ['owner.lock','execution.lock'])
  registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');task=read(O/'PILOT_TASK.json');original=next(x['task']for x in registry['tasks']if x['task']['task_id']=='common_02')
  for k,v in original.items():
   if k not in {'task_id','output','run_id','run_root','method'}:assert task[k]==v,k
  assert task['task_id']=='common_02__SVGMPPI'and task['maximum_control_native']==57600 and task['stop_native']==2200
  # Identical original task template and limits inherited from17164 source.
  for n in ['PILOT_TASK.json','LIMITS_DRAFT.json']:assert prior[str((O/n).relative_to(R))]==sha(O/n)
  assert all(sha(R/n)==h for n,h in files.items());assert all(n not in prior or prior[n]==h for n,h in files.items())
  put(SOURCE/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(SOURCE/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  result.update(passed=True,source_members=len(files),software_proof_sha256=sha(SOURCE/'SOFTWARE_CHECK_PROOF.json'),representation_only_change_no_numerical_reconstruction=True,algorithm_and_safety_modules_byte_exact=True,original_common02_task_byte_exact=True,common01_failure_preserved=True,formal_common_registered=0)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(SOURCE/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 finally:
  result['closed']=True;put(SOURCE/'SOURCE_QUALIFICATION.json',result);put(SOURCE/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,algorithm_DLLs=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
