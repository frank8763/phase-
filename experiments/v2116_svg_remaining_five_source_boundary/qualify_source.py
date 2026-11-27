"""One source delta qualification, zero model/numeric calls."""
from pathlib import Path
import ast,fcntl,os,time,json,traceback
import evidence as e
R=e.R;C=e.C;S=e.ROOT;P=R/'runs/v2109_evening_multialgorithm';STUDY=R/'runs/v2095_svg_common_full_route'
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
  software=e.read(S/'SOFTWARE_CHECK_PROOF.json');assert software['passed']and software['models']==software['solvers']==software['physics']==0
  old=R/'experiments/v2099_svg_direct_array_scope'
  for n in software['unchanged_numerical_modules']+['owner.py']:assert(C/n).read_bytes()==(old/n).read_bytes(),n
  ctx=e.load('remaining_five_context',C/'context.py');ctx.predecessors_closed()
  for n in ['CONFIG.json','NATIVE_DEPENDENCIES.json']:assert e.sha(S/n)==e.sha(R/'runs/v2099_svg_direct_array_scope'/n)
  registry=e.read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');auth=e.read(S/'AUTHORIZATION.json')
  assert auth['scope']=='NEW_DAYTIME_FINITE_REMAINING_FIVE'and auth['formal_maximum']==5 and time.time()<auth['absolute_end_unix']-7630
  assert auth['finite_formal_assignments']==[f'common_{i:02d}__SVGMPPI'for i in range(8,13)]
  events=R/'runs/v1805_common_algorithm_registry/PARALLEL_METHOD_EVENTS';scientific=e.read(R/'runs/v2099_svg_direct_array_scope/SOURCE_FREEZE.json')['files']
  for rid in auth['finite_formal_assignments']:
   O=STUDY/'rounds'/rid;task=e.read(O/'PILOT_TASK.json');original=next(x['task']for x in registry['tasks']if x['task']['task_id']==rid.split('__')[0])
   for k,v in original.items():
    if k not in {'task_id','output','run_id','run_root','method'}:assert task[k]==v,(rid,k)
   assert scientific[str((O/'PILOT_TASK.json').relative_to(R))]==e.sha(O/'PILOT_TASK.json')
   assert task['formal_common_task']and task['maximum_control_native']==57600 and task['stop_native']==2200
   assert all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual/RESULT.json'])
   assert not(events/(rid+'.REGISTERED.json')).exists()and e.scope(rid)==(O,S/'runtime_archives'/rid)
  from reserved_census import admission
  reserve=admission()
  for folder in [C,S]:
   for p in folder.iterdir():
    if p.is_file()and p.name not in {'SOURCE_ONCE.json','owner.lock'}and p.suffix not in {'.log','.console'}:
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=e.sha(p)
  extra=[STUDY/'rounds/common_07__SVGMPPI/POST_ROUND_STORAGE_BARRIER.json',STUDY/'rounds/common_07__SVGMPPI/RUNTIME_CLOSED_REVIEW.json',R/'runs/v2114_svg07_closed_transport/FINAL_CHECKPOINT.json',R/'runs/v2114_svg07_closed_transport/COMPILE_PROOF.json',R/'runs/v2114_svg07_closed_transport/RESULT.json',R/'experiments/v2114_svg07_closed_transport/recover.py',R/'experiments/v2114_svg07_closed_transport/PROTOCOL.md',P/'closed_cache/common_07__SVGMPPI/RESULT.json']
  for p in extra:files[str(p.relative_to(R))]=e.sha(p)
  assert all(e.sha(R/n)==h for n,h in files.items())and all(n not in prior or prior[n]==h for n,h in files.items())
  e.put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=e.sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  e.put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=e.sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=e.sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  result.update(passed=True,source_members=len(files),delta_members=len(files)-len(prior),original_numerical_modules_byte_exact=True,original_owner_byte_exact=True,all5_original_task_templates_byte_exact=True,source_scope_queue_storage_transport_only_change=True,source_software_proof_sha256=e.sha(S/'SOFTWARE_CHECK_PROOF.json'),reservation=reserve,formal_common120_denominator_unchanged=True)
 except BaseException as x:result.update(first_error=repr(x),traceback=traceback.format_exc());e.put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 finally:result['closed']=True;e.put(S/'SOURCE_QUALIFICATION.json',result);e.put(S/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,solvers=0,physics=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
