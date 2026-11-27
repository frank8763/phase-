"""One new zero-network source qualification, complete checks before SOURCE_ONCE."""
from common import *
import traceback

def main():
 assert os.sched_getaffinity(0)=={5}
 from preflight import check,candidate,P
 check();auth=read(S/'AUTHORIZATION.json');assert time.time()+1500<auth['absolute_end_unix']
 dump(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),explicit_network_constructors=0,forward_calls=0));v=dict(passed=False,closed=False,models_authorized=False,explicit_network_constructors=0,weight_deserializations=0,forward_calls=0,physical_native=0,replay=0,formal_tasks=0)
 try:
  parent,files=candidate();delta={n:h for n,h in files.items()if parent.get(n)!=h};assert all(sha(R/n)==h for n,h in files.items())
  dump(S/'SOURCE_FREEZE.json',dict(files=delta,inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  dump(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  v.update(passed=True,source_members=len(files),delta_members=len(delta),component='TWO_FROZEN_SCCR_ACTORS_ONE_IMPORT_BINDING_REVISION',physical_or_full_SCCR_admission=False,preflight_sha256=sha(S/'PRE_SOURCE_PREFLIGHT.json'),host_dependency_manifests_pinned_raw_libraries_not_in_archive=True)
 except BaseException as e:v.update(error=repr(e),traceback=traceback.format_exc());dump(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 v['closed']=True;dump(S/'SOURCE_QUALIFICATION.json',v);dump(S/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=v['passed'],explicit_network_constructors=0,forward_calls=0));print(json.dumps(v));return 0 if v['passed']else 1
if __name__=='__main__':raise SystemExit(main())
