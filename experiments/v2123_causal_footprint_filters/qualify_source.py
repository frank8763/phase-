"""One source-only qualification; never takes live vehicle locks."""
import ast,json,os,time,traceback
from common import R,C,S,read,put,sha,load

def main():
 assert os.sched_getaffinity(0)=={5}and not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0,solvers=0))
 result=dict(passed=False,closed=False,models=0,DLLs=0,solvers=0,physics=0,replay=0,formal_registered=0)
 try:
  P=R/'runs/v2122_priest_quiescent_handoff';prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items())
  assert read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  assert read(S/'GEOMETRY_SOFTWARE_RESULT.json')['passed']and read(S/'REQUEST_SOFTWARE_RESULT.json')['passed']
  assert read(S/'CASES_LOCKED.json')['maximum_NLP_returns']==18
  reservation=load('original_shared_4MiB_subgrant',C/'reservation.py').admission();files=dict(prior)
  pins=read(S/'INPUTS_LOCKED.json')['files'];assert all(sha(R/n)==h for n,h in pins.items())
  archive=R/'runs/v2101_parallel_priest_vehicle/runtime_archives/parallel_priest_vehicle';index=read(archive/'ARCHIVE_INDEX.json');inventory={x['path']:x for x in index['files']}
  receipt=read(S/'INPUTS_LOCKED.json')['saved_receipt'];assert inventory[receipt]['sha256']==pins[receipt]and inventory[receipt]['bytes']==(R/receipt).stat().st_size
  assert read(archive/'FULL_REMOTE_VERIFIED.json')['passed']and read(archive/'TRANSPORT_CLEANUP.json')['passed']
  files.update(pins)
  for p in[archive/'ARCHIVE_INDEX.json',archive/'FULL_REMOTE_VERIFIED.json',archive/'TRANSPORT_CLEANUP.json']:files[str(p.relative_to(R))]=sha(p)
  for folder in[C,S]:
   for p in folder.iterdir():
    if p.is_file()and p.suffix not in{'.log','.console','.initial'}and p.name not in{'SOURCE_ONCE.json','owner.lock'}:
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  from evidence import deliver
  for rid in[None,'components']:
   # Runtime preview does not execute and its bound completion gate stays in generated code.
   compile(deliver(rid,preview=True),str(C/'generated_transport.py'),'exec')
  # No-admission numerical entry must refuse before scipy or models.
  import subprocess
  p=subprocess.run(['taskset','-c','6','/usr/bin/python3','-B',str(C/'worker.py')],cwd=R,capture_output=True,timeout=10)
  assert p.returncode!=0 and b'COMPONENT_ADMISSION.json'in p.stderr
  assert all(sha(R/n)==h for n,h in files.items())
  put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  result.update(passed=True,source_members=len(files),delta_members=len(files)-len(prior),reservation=reservation,models_authorized=False,full_generated_transport_compiled=True,unadmitted_worker_refused=True,original_live_sources_unchanged=True)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc());put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 result['closed']=True;put(S/'SOURCE_QUALIFICATION.json',result);put(S/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,solvers=0));print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
