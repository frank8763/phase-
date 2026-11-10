"""New checker/valid-path candidate; closed roots cannot authorize this one."""
import hashlib,json,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1014_atomic_handoff_navigation';ROOT=R/'runs/atomic_handoff_night_20261110'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def root_authorized(now=None,freeze_sha=None):
    approval=read(ROOT/'APPROVAL.json');assert approval['models_authorized']is True,'NEW_BOUNDED_CANDIDATE_NOT_AUTHORIZED'
    now=time.time()if now is None else now
    assert not(ROOT/'COMPLETION.json').exists()and not(O/'COMPLETION.json').exists(),'ENTRY_ALREADY_CLOSED'
    w=read(ROOT/'ROUND_WINDOW.json');assert w['deadline_unix']==min(w['started_unix']+5400.,1794355200.)and w['started_unix']<=now
    assert now<1794355200.-30 and read(R/'records/nav2_v1003_20261110/FINAL_INDEPENDENT_AUDIT.json')['component_passed']
    f=sha(C/'SOURCE_FREEZE.json');assert approval['source_freeze_sha256']==f
    assert read(O/'ZERO_MODEL_QUALIFICATION.json')['passed']and read(R/'records/nav2_v1010_20261110/FINAL_INDEPENDENT_AUDIT.json')['passed']
    assert read(R/'records/nav2_v1013_20261110/HANDOFF_QUALIFICATION.json')['passed']and read(O/'SAVED_AUDIT_QUALIFICATION.json')['passed']
    for rel,h in read(C/'SOURCE_FREEZE.json')['files'].items():assert sha(R/rel)==h,'SOURCE_CHANGED '+rel
    if freeze_sha is not None:assert freeze_sha==f
    return dict(models_authorized=True,scope='V1014_CHECKER_VALID_PATH_NAVIGATION',started_unix=w['started_unix'],deadline_unix=1794355200.,precondition_deadline_unix=w['deadline_unix'],source_freeze_sha256=f,conditional_overnight=approval['conditional_overnight'])
def authorized(task,receipt,now,freeze_sha,preflight=False):
    a=root_authorized(now,freeze_sha);assert task in read(C/'TASKS.json')and task['origin_native_tick']==0 and task['origin_sim_time']==0.
    expected=dict(a,run_id=task['run_id'],task_sha256=digest(task))
    if'task_clock_sha256'in receipt:expected['task_clock_sha256']=sha(Path(task['output'])/'TASK_CLOCK.json')
    assert receipt==expected,'TASK_CHANGED'
    rows=read(O/'RESULTS.json')if(O/'RESULTS.json').exists()else[]
    if task['slot']<2 or(preflight and task['slot']<6):end=a['precondition_deadline_unix'];assert now<end-365
    else:
        assert a['conditional_overnight']is True,'CONDITIONAL_OVERNIGHT_NOT_AUTHORIZED'
        assert len(rows)>=2 and all(x['passed']for x in rows[:2]);night=read(O/'NIGHT_WINDOW.json');assert night['deadline_unix']==1794355200. and night['source_freeze_sha256']==freeze_sha;end=1794355200.
    if task['slot']>=6:assert len(rows)>=6 and all(x['passed']for x in rows[:6])
    if not preflight:assert len(rows)==task['slot']
    return end
def ready_for_navigation():return root_authorized()
