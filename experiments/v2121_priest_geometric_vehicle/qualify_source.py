"""Source-only check while SVG runs; canonical plant locks stay with SVG."""
from pathlib import Path
import ast,os,time,json,traceback
from context import R,C,SOURCE as S,O,read,put,sha
def main():
 assert os.sched_getaffinity(0)=={5}and not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0))
 result=dict(passed=False,closed=False,models=0,DLLs=0,optimizer_queries=0,physics=0,replay=0,formal_trials=0)
 try:
  P=R/'runs/v2119_parallel_components_release_scope';prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items())and read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(P/'POST_COMPONENT_STORAGE_BARRIER.json')['passed']
  proof=read(S/'COMPONENT_INTERFACE_PROOF.json');assert proof['passed']and proof['models']==proof['optimizer_queries']==0
  old=R/'experiments/v2101_parallel_priest_vehicle'
  for n in proof['unchanged_low_level_modules']:assert(C/n).read_bytes()==(old/n).read_bytes(),n
  for n in ['navigation.py','audit_component.py']:assert(C/n).read_text()==(old/n).read_text().replace("R/'experiments/v2076_priest_current_control/interface.py'","C/'preview_adapter.py'")
  assert(C/'tracking.py').read_bytes()==(R/'experiments/v2119_parallel_components_release_scope/tracking.py').read_bytes()
  assert(C/'optimizer_call.py').read_text()==(old/'optimizer_call.py').read_text().replace('runs/v2101_parallel_priest_vehicle/vehicle/actual/PRIEST_OPTIMIZER_ADMISSION.json','runs/v2121_priest_geometric_vehicle/vehicle/actual/PRIEST_OPTIMIZER_ADMISSION.json')
  task=read(O/'PILOT_TASK.json');parent=read(R/'runs/v2101_parallel_priest_vehicle/vehicle/PILOT_TASK.json')
  for k,v in parent.items():
   if k not in {'output','run_root','run_id','method'}:assert task[k]==v,k
  assert task['component_not_navigation']and not task['formal_common_task']and task['maximum_control_native']==5 and task['stop_native']==2200
  assert all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual'])and not(S/'DISPATCH_ONCE.json').exists()
  auth=read(S/'AUTHORIZATION.json');prior_auth=read(R/'runs/v2116_svg_remaining_five_source_boundary/AUTHORIZATION.json');assert auth['latest_component_start_unix']==prior_auth['absolute_end_unix']and auth['absolute_end_unix']==auth['latest_component_start_unix']+7200
  from reserved_census import admission
  reserve=admission();files=dict(prior)
  for folder in[C,S]:
   for p in folder.iterdir():
    if p.is_file()and p.suffix not in{'.log','.console'}and p.name not in{'SOURCE_ONCE.json','owner.lock','dispatcher.lock'}:
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in[S/'software'/n for n in['PRIEST_CURRENT_INPUT_WIRE.json','PRIEST_NATIVE_CONSOLE.json','PRIEST_NATIVE_CLOSED.json','PRIEST_NATIVE_RESULT.json']]:
   if p.exists():files[str(p.relative_to(R))]=sha(p)
  for p in[O/'PILOT_TASK.json',O/'LIMITS_DRAFT.json',P/'POST_COMPONENT_STORAGE_BARRIER.json',P/'priest/SAVED_POLYNOMIAL_PREVIEW.json',R/'experiments/v2120_priest_preview_adapter/interface.py',R/'runs/v2120_priest_preview_adapter/RESULT.json']:
   files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items())
  put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  result.update(passed=True,source_members=len(files),delta_members=len(files)-len(prior),preview_and_independent_auditor_bound=True,original_lower_level_unchanged=True,original_author_params_and_callgraph_unchanged=True,wait_for_SVG_full_closure=True,reservation=reserve,software_proof_sha256=sha(S/'COMPONENT_INTERFACE_PROOF.json'))
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc());put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 result['closed']=True;put(S/'SOURCE_QUALIFICATION.json',result);put(S/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,optimizer_queries=0));print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
