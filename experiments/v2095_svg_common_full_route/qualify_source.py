"""One source-only freeze after bounded software proofs; no numerical imports."""
import ast,fcntl,json,os,sys,time,traceback
from pathlib import Path
from context import R,C,SOURCE,read,put,sha,load,predecessors_closed
P=R/'runs/v2090_svg_persistent_counter_fixture'
def main():
 assert os.sched_getaffinity(0)=={2};locks=[]
 for name in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/name).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 assert not(SOURCE/'SOURCE_ONCE.json').exists();put(SOURCE/'SOURCE_ONCE.json',dict(unix=time.time(),models=0,pid=os.getpid()))
 result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,constructors=0,queries=0,physics=0,replay=0)
 try:
  predecessors_closed();prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items());files=dict(prior)
  proof=read(SOURCE/'SOFTWARE_CHECK_PROOF.json');assert proof['passed']and proof['models']==proof['DLLs']==proof['formal_claims']==0
  assert all(sha(R/n)==h for n,h in proof['source_pins'].items()),'SOFTWARE_CHECK_SOURCE_CHANGED'
  assert read(SOURCE/'NAVIGATION_FLOW_SOFTWARE_PROOF.json')['passed']
  for folder in [C,R/'experiments/v2096_svg_first_formal_dispatch']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for n in proof['source_pins']:files[n]=sha(R/n)
  names=['CONFIG.json','NATIVE_DEPENDENCIES.json','AUTHORIZATION.json','BASELINE_DRAFT.json','PLAN_LOCKED.json','SOFTWARE_CHECK_PROOF.json','NAVIGATION_FLOW_SOFTWARE_PROOF.json']
  for n in names:files[str((SOURCE/n).relative_to(R))]=sha(SOURCE/n)
  for row in read(SOURCE/'PLAN_LOCKED.json')['tasks']:
   O=R/row['root'];assert not(O/'PILOT_ONCE_CLAIM.json').exists()and not(O/'COMPLETION.json').exists()and not(O/'actual').exists()
   assert all((O/n).is_file()and(O/n).stat().st_size==0 for n in ['owner.lock','execution.lock'])
   for n in ['PILOT_TASK.json','LIMITS_DRAFT.json']:files[str((O/n).relative_to(R))]=sha(O/n)
  for p in [P/'COMPLETION.json',P/'POST_COMPONENT_STORAGE_BARRIER.json',R/'runs/v2094_svg_compact_receipt_order/RESULT.json',SOURCE/'software_checks_01/RESULT.json'] :files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items());assert all(n not in prior or prior[n]==h for n,h in files.items())
  put(SOURCE/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(SOURCE/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  result.update(passed=True,source_members=len(files),software_proof_sha256=sha(SOURCE/'SOFTWARE_CHECK_PROOF.json'),navigation_flow_proof_sha256=sha(SOURCE/'NAVIGATION_FLOW_SOFTWARE_PROOF.json'),formal_common_registered=0)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(SOURCE/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 finally:
  result['closed']=True;put(SOURCE/'SOURCE_QUALIFICATION.json',result);put(SOURCE/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,algorithm_DLLs=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
