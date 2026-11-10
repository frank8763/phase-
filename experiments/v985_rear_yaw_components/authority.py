"""One immutable90minute physical window, exact fixed order, fail-closed gates."""
import hashlib,json,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v985_rear_yaw_components'
SCOPE='V985_TWO_FIXED_RECOVERY_COMPONENTS_ONLY'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def root_authorized(now=None,freeze_sha=None):
    now=time.time()if now is None else now
    if not(O/'USER_APPROVAL.json').exists():raise PermissionError('V985_NEW_90MIN_PHYSICAL_APPROVAL_REQUIRED')
    approval=read(O/'USER_APPROVAL.json')
    assert approval['explicit_user_approval']is True and approval['scope']==SCOPE and approval['maximum_root_s']==5400.
    assert approval['source_freeze_sha256']==sha(C/'SOURCE_FREEZE.json')
    assert not(O/'COMPLETION.json').exists(),'BATCH_ALREADY_CLOSED'
    a=read(O/'AUTHORIZATION.json');w=read(O/'ROUND_WINDOW.json')
    assert a['models_authorized']is True and a['scope']==SCOPE
    assert a['started_unix']==w['started_unix'] and a['deadline_unix']==w['deadline_unix']
    assert abs(a['deadline_unix']-a['started_unix']-5400.)<1e-6 and a['started_unix']<=now<a['deadline_unix']-30
    assert sha(C/'SOURCE_FREEZE.json')==a['source_freeze_sha256']
    if freeze_sha is not None:assert freeze_sha==a['source_freeze_sha256']
    for rel,h in read(C/'SOURCE_FREEZE.json')['files'].items():assert sha(R/rel)==h,'FROZEN_SOURCE_CHANGED '+rel
    assert read(O/'ZERO_MODEL_ENTRY_QUALIFICATION.json')['passed']
    assert read(O/'SOFTWARE_QUALIFICATION.json')['passed']
    inputs=read(O/'RESTORE_RECEIPT.json');assert inputs['passed']and len(inputs['files'])==13
    required=read(C/'RESTORE_REQUIREMENTS.json')['files'];assert inputs['files']==required,'RESTORED_INPUT_SELECTION_CHANGED'
    for row in inputs['files']:assert sha(R/row['path'])==row['sha256'],'RESTORED_INPUT_CHANGED'
    return a
def ready_for_navigation():return root_authorized()
def authorized(task,receipt,now,freeze_sha):
    a=root_authorized(now,freeze_sha);tasks=read(C/'TASKS.json');assert task in tasks
    assert receipt==dict(a,run_id=task['run_id'],task_sha256=digest(task))
    prior=read(O/'RESULTS.json')if(O/'RESULTS.json').exists()else[]
    assert len(prior)==task['slot'] and all(x['passed']for x in prior),'DEPENDENCY_GATE_OR_TASK_ORDER_FAILED'
    assert task['stage']=='component'and task['wall_limit_s']==40.0 and task['brake_s']==2.0
    return a['deadline_unix']
