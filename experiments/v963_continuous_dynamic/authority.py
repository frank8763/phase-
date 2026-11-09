"""A new immutable component-to-route window; no authority from closed rounds."""
import hashlib
import json
import time
from pathlib import Path

C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v963_continuous_dynamic'
SCOPE='V963_STEERING_CONTINUOUS_DYNAMIC_COURSE'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def root_authorized(now=None,freeze_sha=None,night=False):
    now=time.time()if now is None else now
    prefix='NIGHT_'if night else''
    assert not(O/(prefix+'COMPLETION.json')).exists(),'ROUND_CLOSED'
    a=read(O/(prefix+'AUTHORIZATION.json'));w=read(O/(prefix+'ROUND_WINDOW.json'))
    assert a['scope']==(SCOPE+'_NIGHT'if night else SCOPE)and a['models_authorized']is True
    assert a['started_unix']==w['started_unix']and a['deadline_unix']==w['deadline_unix']
    if night:
        assert read(O/'COMPLETION.json')['status']=='ORIGINAL_WE_DEVELOPMENT_AND_REPEAT_PASSED','CURRENT_ROUND_NOT_PASSED'
        assert a['deadline_unix']==read(C/'NIGHT_PLAN.json')['deadline_unix']
        assert 0<a['deadline_unix']-a['started_unix']<=43200.
    else:assert abs(a['deadline_unix']-a['started_unix']-5400.)<1e-6
    assert a['started_unix']<=now<a['deadline_unix']-30,'WINDOW_EXPIRED'
    assert sha(C/'SOURCE_FREEZE.json')==a['source_freeze_sha256']
    if freeze_sha is not None:assert freeze_sha==a['source_freeze_sha256']
    for rel,expected in read(C/'SOURCE_FREEZE.json')['files'].items():
        p=R/rel;assert p.resolve().is_relative_to(R)and p.is_file()and sha(p)==expected,'FROZEN_SOURCE_CHANGED '+rel
    for name in ['ZERO_MODEL_QUALIFICATION.json','FULL_STARTUP_QUALIFICATION.json']:
        assert read(O/name)['passed'],name
    assert read(R/'records/nav2_v955_v960_20261109/v960_hold_response_closure_FINAL_INDEPENDENT_AUDIT.json')['passed']
    return a
def component_authorized():
    a=root_authorized()
    assert not(O/'HANDOFF_CLAIM.json').exists(),'HANDOFF_ALREADY_CLAIMED'
    assert not(O/'HANDOFF_AUDIT.json').exists(),'HANDOFF_ALREADY_CLOSED'
    return a
def ready_for_navigation():
    assert read(O/'HANDOFF_AUDIT.json')['passed'],'HANDOFF_NOT_QUALIFIED'
    assert read(O/'HANDOFF_RESULT.json')['passed'],'HANDOFF_FAILED'
def authorized(task,receipt,now,freeze_sha,preflight=False):
    night=task.get('campaign')=='night'
    a=root_authorized(now,freeze_sha,night=night);ready_for_navigation()
    assert task in read(C/('NIGHT_TASKS.json'if night else'TASKS.json')),'UNREGISTERED_TASK'
    assert receipt==dict(a,run_id=task['run_id'],task_sha256=digest(task)),'CHANGED_RECEIPT'
    if task.get('stage')in{'confirmation','confirmation_repeat'}:
        assert read(O/'NIGHT_REGRESSION_GATE.json')['passed'],'THREE_ROUTE_REGRESSION_NOT_PASSED'
    if not preflight and night:assert read(O/(task['phase_group']+'_PREFLIGHT_AUDIT.json'))['passed'],'REAL_T0_PREFLIGHT_NOT_PASSED'
    if task['role']=='dynamic_repeat':
        baseline=Path(task.get('baseline_output',str(Path(task['output']).parent/'main_we')))
        assert read(baseline/'INDEPENDENT_AUDIT.json')['passed'],'MAIN_FAILED'
        if task.get('stage')=='confirmation_repeat':assert read(O/'CONFIRMATION_MAIN_GATE.json')['passed'],'MAIN_DENOMINATOR_GATE_NOT_PASSED'
    return a['deadline_unix']
