"""CPU5 independent software source check, no global plant lock or imports."""
import ast,os,time,json,traceback
from common import R,C,S,read,put,sha
def main():
 assert os.sched_getaffinity(0)=={5}and not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0))
 result=dict(passed=False,closed=False,models=0,DLLs=0,solvers=0,physics=0,replay=0,formal_registered=0)
 try:
  P=R/'runs/v2116_svg_remaining_five_source_boundary';prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items())
  assert read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  software=read(S/'SOFTWARE_CHECK_PROOF.json');assert software['passed']and software['models']==software['solvers']==0
  assert read(S/'CASES_LOCKED.json')['maximum_NLP_returns']==18
  from reservation import admission
  reserve=admission();files=dict(prior)
  for folder in [C,S]:
   for p in folder.iterdir():
    if p.is_file()and p.suffix not in {'.log','.console'}and p.name not in {'SOURCE_ONCE.json','owner.lock'}:
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  runtime=R/'runs/v2101_parallel_priest_vehicle/runtime_archives/parallel_priest_vehicle'
  barrier=R/'runs/v2101_parallel_priest_vehicle/POST_COMPONENT_STORAGE_BARRIER.json';proof=read(barrier)
  assert proof['passed']and read(runtime/'FULL_REMOTE_VERIFIED.json')['passed']and read(runtime/'TRANSPORT_CLEANUP.json')['passed']
  assert proof['proof_paths_SHA256'][str((runtime/'ARCHIVE_INDEX.json').relative_to(R))]==sha(runtime/'ARCHIVE_INDEX.json')
  inventory={x['path']:x for x in read(runtime/'ARCHIVE_INDEX.json')['files']}
  for name in ['PRIEST_CURRENT_INPUT.json','PRIEST_NATIVE_RESULT.json','PRIEST_RAW_CURRENT_PROPOSAL.json']:
   p=R/'runs/v2101_parallel_priest_vehicle/vehicle/actual'/name;n=str(p.relative_to(R))
   assert inventory[n]['sha256']==sha(p)and inventory[n]['bytes']==p.stat().st_size;files[n]=sha(p)
  for p in [barrier,runtime/'ARCHIVE_INDEX.json',runtime/'FULL_REMOTE_VERIFIED.json',runtime/'TRANSPORT_CLEANUP.json',R/'experiments/v1937_sccr_frozen_policy_bridge/feature_contract.py',R/'runs/v2117_parallel_ackermann_components/SOURCE_QUALIFICATION.json']:
   files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items())
  put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  result.update(passed=True,source_members=len(files),delta_members=len(files)-len(prior),original_live_source_unchanged=True,reservation=reserve,workerCPU=[4,6],no_Phase_physics_authority=True)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc());put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 finally:result['closed']=True;put(S/'SOURCE_QUALIFICATION.json',result);put(S/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,solvers=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
