"""Exactly one source-only qualification; cannot load a controller or admit math."""
import datetime,fcntl,os
from context import R,C,S,read,sha,put,REVIEW_SHA
from budget import check
from readiness import candidate,inherited_chain,future_metadata,packed_forecast

def main():
    assert os.sched_getaffinity(0)=={5};check('source')
    assert not any((S/n).exists()for n in ['SOURCE_ONCE.json','SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','NUMERICAL_ADMISSION.json'])
    ready=read(S/'SOURCE_READY_PREFLIGHT.json');assert ready['passed']and ready['algorithm_queries_DLL_FFI_models_physics']==0
    old,new=candidate();assert new==ready['candidate_files']and all(sha(R/n)==h for n,h in {**old,**new}.items())
    assert packed_forecast(new,ready)[0]+8192<=96*1024
    locks=[]
    for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
        h=(R/n).open();fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(h)
    assert sha(R/'REVIEW_PENDING')==REVIEW_SHA
    assert datetime.datetime.now().astimezone().isoformat()<'2026-11-29T07:00:00+08:00'
    put(S/'SOURCE_ONCE.json',dict(source_only=True,started_at=datetime.datetime.now().astimezone().isoformat()))
    values=future_metadata(new,ready);put(S/'SOURCE_FREEZE.json',values['SOURCE_FREEZE.json'])
    q=values['SOURCE_QUALIFICATION.json'];q.update(source_ready_sha256=sha(S/'SOURCE_READY_PREFLIGHT.json'),source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'))
    put(S/'SOURCE_INHERITED_CHAINS.json',inherited_chain());put(S/'SOURCE_QUALIFICATION.json',q)
    put(S/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=True,source_only=True,numerical_admission=False,original_REVIEW_exact=True,algorithm_queries_DLL_FFI_models_physics=0))
    check('source');print('SOURCE_ONLY_PASS_NO_NUMERICAL_PERMISSION');return 0
if __name__=='__main__':raise SystemExit(main())
