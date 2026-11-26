"""Zero-model source-only prospective finite queue qualification."""
import ast,fcntl,os,json,sys,time,traceback,subprocess
from pathlib import Path
import evidence as e
R=e.R;C=e.C;S=e.ROOT;P=R/'runs/v2105_svg03_exact_transport_parent';STUDY=R/'runs/v2095_svg_common_full_route'
def main():
 assert os.sched_getaffinity(0)=={2};locks=[]
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 assert e.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 assert not(S/'SOURCE_ONCE.json').exists();e.put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0))
 result=dict(passed=False,closed=False,models=0,DLLs=0,constructors=0,optimizer_queries=0,physics=0,replay=0,formal_registered=0)
 try:
  prior=e.read(P/'SOURCE_FREEZE.json')['files'];assert all(e.sha(R/n)==h for n,h in prior.items());files=dict(prior)
  assert e.P==P and e.read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']and e.read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
  assert e.read(STUDY/'rounds/common_03__SVGMPPI/POST_ROUND_STORAGE_BARRIER.json')['passed']and e.read(R/'runs/v2107_svg03_closed_transport/FINAL_CHECKPOINT.json')['no_numerical_or_transport_worker_active']
  assert e.read(R/'runs/v2108_svg_verified_cache_retirement/RESULT.json')['passed']
  software=e.read(S/'SOFTWARE_CHECK_PROOF.json');assert software['passed']and software['models']==software['solvers']==software['physics']==0
  old=R/'experiments/v2099_svg_direct_array_scope'
  for n in software['unchanged_numerical_modules']+['owner.py']:assert(C/n).read_bytes()==(old/n).read_bytes(),n
  ctx=e.load('source_new_night_context',C/'context.py');ctx.predecessors_closed()
  for n in ['CONFIG.json','NATIVE_DEPENDENCIES.json']:assert e.sha(S/n)==e.sha(R/'runs/v2099_svg_direct_array_scope'/n)
  registry=e.read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json')
  auth=e.read(S/'AUTHORIZATION.json');assert auth['absolute_end_unix']==1795741200. and time.time()<auth['absolute_end_unix']-6860 and len(auth['finite_formal_assignments'])==9
  events=R/'runs/v1805_common_algorithm_registry/PARALLEL_METHOD_EVENTS';scientific=e.read(R/'runs/v2099_svg_direct_array_scope/SOURCE_FREEZE.json')['files']
  for rid in auth['finite_formal_assignments']:
   O=STUDY/'rounds'/rid;task=e.read(O/'PILOT_TASK.json');original=next(x['task']for x in registry['tasks']if x['task']['task_id']==rid.split('__')[0])
   for k,v in original.items():
    if k not in {'task_id','output','run_id','run_root','method'}:assert task[k]==v,(rid,k)
   assert task['formal_common_task']and task['maximum_control_native']==57600 and task['stop_native']==2200
   assert scientific[str((O/'PILOT_TASK.json').relative_to(R))]==e.sha(O/'PILOT_TASK.json')
   for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual/RESULT.json']:assert not(O/n).exists()
   assert not(events/(rid+'.REGISTERED.json')).exists()
   assert e.scope(rid)==(O,S/'runtime_archives'/rid)
  assert e.scope(None)==(S,S/'recovery')and not(S/'ONCE.json').exists()
  from reserved_census import admission
  reserve=admission()
  for folder in [C,S]:
   for p in folder.iterdir():
    if p.is_file()and p.name not in {'SOURCE_ONCE.json','owner.lock'}:
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=e.sha(p)
  extra=[
   P/'FINAL_CHECKPOINT.json',P/'POST_COMPONENT_STORAGE_BARRIER.json',
   STUDY/'rounds/common_03__SVGMPPI/POST_ROUND_STORAGE_BARRIER.json',STUDY/'rounds/common_03__SVGMPPI/RUNTIME_CLOSED_REVIEW.json',
   R/'runs/v2106_pcbf_saved_return_analysis/RESULT.json',R/'runs/v2106_pcbf_saved_return_analysis/SVG03_PREFIX_PHASE_READOUT.json',
   R/'runs/v2107_svg03_closed_transport/FINAL_CHECKPOINT.json',R/'runs/v2107_svg03_closed_transport/PATCH_PROOF.json',
   R/'experiments/v2108_svg_verified_cache_retirement/run.py',R/'experiments/v2108_svg_verified_cache_retirement/PROTOCOL.md',
   R/'runs/v2108_svg_verified_cache_retirement/RESULT.json',R/'runs/v2108_svg_verified_cache_retirement/ELIGIBLE_MANIFEST.json']
  for p in extra:files[str(p.relative_to(R))]=e.sha(p)
  for p in(R/'runs/v2108_svg_verified_cache_retirement').rglob('*.original_record'):files[str(p.relative_to(R))]=e.sha(p)
  for p in [R/'runs/v2101_parallel_priest_vehicle/vehicle/actual/cycle_000000_shadow.json',R/'runs/v2101_parallel_priest_vehicle/vehicle/actual/PRIEST_RAW_CURRENT_PROPOSAL.json']:files[str(p.relative_to(R))]=e.sha(p)
  assert all(e.sha(R/n)==h for n,h in files.items())and all(n not in prior or prior[n]==h for n,h in files.items())
  e.put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=e.sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  e.put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=e.sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=e.sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  result.update(passed=True,source_members=len(files),delta_members=len(files)-len(prior),original_numerical_modules_byte_exact=True,original_owner_byte_exact=True,all9_original_task_templates_byte_exact=True,source_scope_queue_storage_only_change=True,original144_futureclosed_224task_15GiB_caps_unchanged=True,deadline_local='2026-11-27T09:00:00+08:00',source_software_proof_sha256=e.sha(S/'SOFTWARE_CHECK_PROOF.json'),reservation=reserve,formal_common120_denominator_unchanged=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc());e.put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 finally:result['closed']=True;e.put(S/'SOURCE_QUALIFICATION.json',result);e.put(S/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,solvers=0,physics=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
