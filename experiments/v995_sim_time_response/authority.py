"""New bounded root, strict task order and no closed-batch restart."""
import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v995_sim_time_response';ROOT=R/'runs/sim_time_recovery_20261110'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def authorize(task=None,now=None):
    now=time.time()if now is None else now
    a=read(ROOT/'USER_AUTHORIZATION.json');w=read(ROOT/'ROUND_WINDOW.json');sw=read(O/'ROUND_WINDOW.json')
    assert a['maximum_root_s']==5400. and not(ROOT/'COMPLETION.json').exists(),'ROOT_CLOSED_OR_WRONG_SCOPE'
    assert abs(w['deadline_unix']-w['started_unix']-5400.)<1e-6 and w['started_unix']<=now<w['deadline_unix']-30,'ROOT_DEADLINE'
    assert sw['started_unix']==w['started_unix']and sw['deadline_unix']==min(w['deadline_unix'],w['started_unix']+1200.)
    assert now<sw['deadline_unix']-320 and not(O/'COMPLETION.json').exists(),'STAGE_CLOSED_OR_NO_FULL_TASK_RESERVE'
    assert w['source_freeze_sha256']==sha(C/'SOURCE_FREEZE.json')and w['user_authorization_sha256']==sha(ROOT/'USER_AUTHORIZATION.json')
    for rel,h in read(C/'SOURCE_FREEZE.json')['files'].items():assert sha(R/rel)==h,'FROZEN_SOURCE_CHANGED '+rel
    assert read(O/'QUALIFICATION.json')['passed']and read(O/'EXECUTION_QUALIFICATION.json')['passed']and read(O/'ENTRY_QUALIFICATION.json')['passed']
    for row in read(O/'RESTORE_RECEIPT.json')['files']:assert sha(R/row['path'])==row['sha256'],'SAVED_INPUT_CHANGED'
    if task is not None:
        assert task in read(C/'TASKS.json'),'UNREGISTERED_TASK'
        prior=read(O/'RESULTS.json')if(O/'RESULTS.json').exists()else[]
        assert len(prior)==task['slot']and all(x['passed']for x in prior),'TASK_ORDER_OR_DEPENDENCY_FAILED'
        if prior:assert prior[0]['audit']['bridge']['passed'],'CLOCK_EQUIVALENCE_NOT_PROVEN'
    return sw['deadline_unix']
