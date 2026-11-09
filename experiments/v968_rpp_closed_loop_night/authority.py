"""One new fixed08:00 window, never reads old failed windows as authority."""
import hashlib,json,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v968_rpp_closed_loop_night'
SCOPE='V968_CLOSED_LOOP_RPP_NIGHT'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def root_authorized(now=None,freeze_sha=None):
    now=time.time()if now is None else now
    assert not(O/'COMPLETION.json').exists(),'ROUND_CLOSED'
    a=read(O/'AUTHORIZATION.json');w=read(O/'ROUND_WINDOW.json')
    assert a['models_authorized']is True and a['scope']==SCOPE
    assert a['started_unix']==w['started_unix']and a['deadline_unix']==w['deadline_unix']==read(C/'NIGHT_PLAN.json')['deadline_unix']
    assert 0<a['deadline_unix']-a['started_unix']<=43200. and a['started_unix']<=now<a['deadline_unix']-30
    assert sha(C/'SOURCE_FREEZE.json')==a['source_freeze_sha256']
    if freeze_sha is not None:assert freeze_sha==a['source_freeze_sha256']
    for p,h in read(C/'SOURCE_FREEZE.json')['files'].items():
        q=R/p;assert q.resolve().is_relative_to(R)and q.is_file()and sha(q)==h,'FROZEN_SOURCE_CHANGED '+p
    for name in ['ZERO_MODEL_QUALIFICATION.json','FULL_STARTUP_QUALIFICATION.json','FULL_COMPONENT_SOFTWARE_QUALIFICATION.json']:assert read(O/name)['passed'],name
    assert read(R/'records/nav2_v955_v960_20261109/v960_hold_response_closure_FINAL_INDEPENDENT_AUDIT.json')['passed']
    return a
def ready_for_navigation():
    # Exact task-specific phase authority is enforced immediately by authorized.
    return None
def authorized(task,receipt,now,freeze_sha,preflight=False):
    a=root_authorized(now,freeze_sha)
    assert task in read(C/'TASKS.json')and receipt==dict(a,run_id=task['run_id'],task_sha256=digest(task))
    if task['stage']!='component':assert read(O/'COMPONENT_GATE.json')['passed'],'CLOSED_LOOP_COMPONENT_NOT_PASSED'
    if task['stage']=='regression':assert read(O/'WE_GATE.json')['passed'],'WE_MAIN_REPEAT_NOT_PASSED'
    if task['stage']in{'confirmation','confirmation_repeat'}:assert read(O/'REGRESSION_GATE.json')['passed'],'THREE_ROUTE_NOT_PASSED'
    if not preflight and task.get('preflight_output'):assert read(O/(task['phase_group']+'_PREFLIGHT_AUDIT.json'))['passed']
    if task['role']=='dynamic_repeat':
        assert read(Path(task['baseline_output'])/'INDEPENDENT_AUDIT.json')['passed']
        if task['stage']=='confirmation_repeat':assert read(O/'CONFIRMATION_MAIN_GATE.json')['passed']
    return a['deadline_unix']
