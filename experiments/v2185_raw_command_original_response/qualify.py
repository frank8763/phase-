"""One source-only qualification; no numeric/backend import or construction."""
import datetime,fcntl,os
from context import R,S,read,sha
from budget import check
from readiness import candidate,metadata,forecast
from recovery import put

def main():
    assert os.sched_getaffinity(0)=={5};check('source')
    assert not any((S/n).exists()for n in ['SOURCE_ONCE.json','SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','NUMERICAL_ADMISSION.json'])
    ready=read(S/'SOURCE_READY.json');assert ready['passed']and ready['Source_or_Predictor_model_physics']==0
    old,new=candidate();assert new==ready['candidate_files']and all(sha(R/n)==h for n,h in dict(old,**new).items())
    assert forecast(new,ready)[0]+16*1024<4*1024**2
    locks=[]
    for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
        f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert datetime.datetime.now().astimezone().isoformat()<'2026-11-29T07:00:00+08:00'
    put(S/'SOURCE_ONCE.json',dict(source_only=True,created_at=datetime.datetime.now().astimezone().isoformat()))
    data=metadata(new,ready);put(S/'SOURCE_FREEZE.json',data['SOURCE_FREEZE'])
    value=data['SOURCE_QUALIFICATION'];value.update(source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'),source_ready_sha256=sha(S/'SOURCE_READY.json'))
    put(S/'SOURCE_QUALIFICATION.json',value);check('source');print('SOURCE_ONLY_PASS_NO_PREDICTOR_ADMISSION')
if __name__=='__main__':main()
