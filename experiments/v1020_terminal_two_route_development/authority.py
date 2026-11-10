"""New user-authorized night root; old V1014 window remains closed."""
import hashlib,json,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1020_terminal_two_route_development';ROOT=R/'runs/terminal_two_route_20261110'
HARD_END=1794358800.  # 2026-11-11 09:00+08, fixed before any new model

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def root_authorized(now=None,freeze_sha=None):
    approval=read(ROOT/'APPROVAL.json');assert approval['models_authorized']is True,'NEW_BOUNDED_CANDIDATE_NOT_AUTHORIZED'
    now=time.time()if now is None else now
    assert not(ROOT/'COMPLETION.json').exists()and not(O/'COMPLETION.json').exists(),'ENTRY_ALREADY_CLOSED'
    w=read(ROOT/'ROUND_WINDOW.json');assert w['deadline_unix']==HARD_END and w['started_unix']<=now<HARD_END-30,'ABSOLUTE_NIGHT_WINDOW'
    assert read(R/'runs/atomic_handoff_night_20261110/COMPLETION.json')['closed']is True
    assert approval['new_night_authorized']is True and approval['independent_route_branches']is True
    assert read(ROOT/'PARENT_WINDOW.json')['deadline_unix']==HARD_END,'PARENT_ABSOLUTE_END_CHANGED'
    assert read(R/'records/nav2_v1003_20261110/FINAL_INDEPENDENT_AUDIT.json')['component_passed']
    f=sha(C/'SOURCE_FREEZE.json');assert approval['source_freeze_sha256']==f
    for name in ['ZERO_MODEL_QUALIFICATION.json','SAVED_AUDIT_QUALIFICATION.json','BACKEND_ENTRY_QUALIFICATION.json','AUTHORITY_QUALIFICATION.json','SCIENTIFIC_ENTRY_QUALIFICATION.json','INITIAL_ZERO_QUALIFICATION.json']:
        assert read(O/name)['passed'],name
    assert read(R/'records/nav2_v1019_20261110/ZERO_MODEL_QUALIFICATION.json')['passed']
    assert {t['route']for t in read(C/'TASKS.json')}=={'we','ns'},'UNQUALIFIED_ROUTE_NOT_REGISTERED'
    assert read(R/'records/nav2_v1010_20261110/FINAL_INDEPENDENT_AUDIT.json')['passed']
    assert read(R/'records/nav2_v1013_20261110/HANDOFF_QUALIFICATION.json')['passed']
    for rel,h in read(C/'SOURCE_FREEZE.json')['files'].items():assert sha(R/rel)==h,'SOURCE_CHANGED '+rel
    if freeze_sha is not None:assert freeze_sha==f
    return dict(models_authorized=True,scope='V1020_EXACT_ENTRY_THREE_ROUTE_NIGHT',started_unix=w['started_unix'],deadline_unix=HARD_END,
        precondition_deadline_unix=HARD_END,source_freeze_sha256=f,conditional_overnight=True)
def authorized(task,receipt,now,freeze_sha,preflight=False):
    a=root_authorized(now,freeze_sha);assert task in read(C/'TASKS.json')and task['origin_native_tick']==0 and task['origin_sim_time']==0.
    expected=dict(a,run_id=task['run_id'],task_sha256=digest(task))
    if'task_clock_sha256'in receipt:expected['task_clock_sha256']=sha(Path(task['output'])/'TASK_CLOCK.json')
    assert receipt==expected,'TASK_CHANGED'
    rows=read(O/'RESULTS.json')if(O/'RESULTS.json').exists()else[]
    if task['slot']>=4:assert len(rows)>=4 and all(x['passed']and x.get('executed',True)for x in rows[:4]),'TWO_ROUTE_GATE_NOT_PASSED'
    if not preflight:
        assert len(rows)==task['slot'],'TASK_ORDER_CHANGED'
        if task['slot']<4 and task['slot']%2:assert rows[-1]['passed'],'REPEAT_REQUIRES_SUCCESSFUL_MAIN'
    assert now<HARD_END-485,'INSUFFICIENT_FULL_TASK_RESERVE'
    return HARD_END
def ready_for_navigation():return root_authorized()
