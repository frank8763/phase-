"""Frozen two-component prerequisite; never grants authority to later navigation."""
import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v1003_causal_recovery_execution';ROOT=R/'runs/input_consistent_overnight_20261110'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def validate_window(a,w,now):
    assert a['absolute_model_deadline_unix']==1794355200. and a['max_precondition_model_window_s']==5400.
    assert w['started_unix']<=now<w['deadline_unix']-30 and 0<w['deadline_unix']-w['started_unix']<=5400.+1e-6,'ROOT_DEADLINE'
    assert w['deadline_unix']<=1794355200.,'OVERNIGHT_HARD_STOP'
    assert now<w['deadline_unix']-440,'FULL_TASK_RESERVE'
    return w['deadline_unix']
def authorize(task=None,now=None):
    now=time.time()if now is None else now
    assert not(ROOT/'COMPLETION.json').exists()and not(O/'COMPLETION.json').exists(),'CLOSED_STAGE_OR_ROOT'
    a=read(ROOT/'USER_AUTHORIZATION.json');w=read(ROOT/'ROUND_WINDOW.json');end=validate_window(a,w,now)
    assert w['source_freeze_sha256']==sha(C/'SOURCE_FREEZE.json')and w['user_authorization_sha256']==sha(ROOT/'USER_AUTHORIZATION.json')
    for rel,h in read(C/'SOURCE_FREEZE.json')['files'].items():assert sha(R/rel)==h,'FROZEN_SOURCE_CHANGED '+rel
    assert read(O/'QUALIFICATION.json')['passed']and read(O/'ENTRY_QUALIFICATION.json')['passed']
    for row in read(O/'RESTORE_RECEIPT.json')['files']:assert sha(R/row['path'])==row['sha256'],'RESTORED_INPUT_CHANGED'
    if task is not None:
        assert task in read(C/'TASKS.json'),'UNREGISTERED_TASK'
        prior=read(O/'RESULTS_PHYSICAL.json')if(O/'RESULTS_PHYSICAL.json').exists()else[]
        assert len(prior)==task['slot']and all(x['passed']for x in prior),'TASK_ORDER_OR_DEPENDENCY'
    return end
