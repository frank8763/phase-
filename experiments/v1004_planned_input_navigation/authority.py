"""Conditional gates and immutable original precondition/overnight deadlines."""
import hashlib,json,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1004_planned_input_navigation';ROOT=R/'runs/input_consistent_overnight_20261110'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def root_authorized(now=None,freeze_sha=None):
    now=time.time()if now is None else now
    assert not(ROOT/'COMPLETION.json').exists()and not(ROOT/'MODEL_STOP.json').exists()and not(O/'COMPLETION.json').exists(),'CAMPAIGN_ALREADY_CLOSED'
    a=read(ROOT/'USER_AUTHORIZATION.json');w=read(ROOT/'ROUND_WINDOW.json');f=sha(C/'SOURCE_FREEZE.json')
    assert a['absolute_model_deadline_unix']==1794355200. and now<1794355200.-30
    assert read(R/'runs/v1003_causal_recovery_execution/COMPLETION.json')['passed'],'TWO_ACTUAL_COMPONENTS_REQUIRED'
    assert read(O/'ZERO_MODEL_QUALIFICATION.json')['passed']and read(O/'SOFTWARE_QUALIFICATION.json')['passed'],'NAVIGATOR_SOFTWARE_GATE'
    for rel,h in read(C/'SOURCE_FREEZE.json')['files'].items():assert sha(R/rel)==h,'SOURCE_CHANGED '+rel
    if freeze_sha is not None:assert f==freeze_sha
    return dict(models_authorized=True,scope='V1004_CONDITIONAL_INPUT_CONSISTENT_OVERNIGHT',started_unix=w['started_unix'],deadline_unix=1794355200.,precondition_deadline_unix=w['deadline_unix'],source_freeze_sha256=f)
def authorized(task,receipt,now,freeze_sha,preflight=False):
    a=root_authorized(now,freeze_sha);tasks=read(C/'TASKS.json');assert task in tasks
    expected=dict(a,run_id=task['run_id'],task_sha256=digest(task))
    if 'task_clock_sha256'in receipt:
        expected['task_clock_sha256']=sha(Path(task['output'])/'TASK_CLOCK.json')
    assert receipt==expected,'TASK_OR_AUTHORITY_CHANGED'
    assert task['wall_limit_s']==180 and task['brake_s']==2. and task['dynamic']is True
    rows=read(O/'RESULTS.json')if(O/'RESULTS.json').exists()else[]
    if task['slot']<2 or (preflight and task['slot']<6):
        end=a['precondition_deadline_unix'];assert now<end-365,'PRECONDITION_DEADLINE'
    else:
        assert len(rows)>=2 and all(x['passed']for x in rows[:2]),'WEST_EAST_MAIN_AND_REPEAT_REQUIRED';end=a['deadline_unix']
        night=read(O/'NIGHT_WINDOW.json');assert night['deadline_unix']==1794355200. and night['source_freeze_sha256']==freeze_sha
    if task['slot']>=6:assert len(rows)>=6 and all(x['passed']for x in rows[:6]),'SAME_VERSION_THREE_ROUTE_GATE'
    if not preflight:assert len(rows)==task['slot'],'TASK_ORDER'
    return end
def ready_for_navigation():return root_authorized()
