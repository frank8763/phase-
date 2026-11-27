"""Exactly one new full-union source qualification, no model or numerical calls."""
from context import R,C,SOURCE as S,read,put,sha
import os,time,json,traceback
from preflight import check,candidate,P
def main():
 assert os.sched_getaffinity(0)=={5};proof=check(require_auth=True)
 with(S/'SOURCE_ONCE.json').open('x')as f:json.dump(dict(pid=os.getpid(),unix=time.time(),models=0,NN_inference=0,physics=0),f)
 v=dict(passed=False,closed=False,models=0,NN_inference=0,renderer_constructors=0,physics=0,replay=0,formal_tasks=0)
 try:
  parent,files=candidate();delta={n:h for n,h in files.items()if parent.get(n)!=h};assert all(sha(R/n)==h for n,h in files.items())
  put(S/'SOURCE_FREEZE.json',dict(files=delta,inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  v.update(passed=True,source_members=len(files),delta_members=len(delta),scope='FRESH_REGISTERED_SCCR_LIVE_UNION_AND107_THEN186_LOGONLY_COMPONENT',no_full_SCCR_control_or_formal_admission=True,preflight=proof,preflight_sha256=sha(S/'PRE_SOURCE_PREFLIGHT.json'),original_actor_backend_proof_inherited_without_new_inference=True)
 except BaseException as e:v.update(error=repr(e),traceback=traceback.format_exc());put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 v['closed']=True;put(S/'SOURCE_QUALIFICATION.json',v);put(S/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=v['passed'],models=0,NN_inference=0));print(json.dumps(v));return 0 if v['passed']else 1
if __name__=='__main__':raise SystemExit(main())
