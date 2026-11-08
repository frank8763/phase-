"""One explicit dynamic stage after verified static regression; old cutoff is immutable."""
import hashlib,json,math,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v892_dynamic_terminal_consistency'
sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import require
SCOPE='V892_DYNAMIC_TERMINAL_CONSISTENCY'
DURATION=json.loads((C/'WINDOW_POLICY.json').read_text())['maximum_duration_s']
def read(p):return json.loads(Path(p).read_text())
def digest(t):return hashlib.sha256(json.dumps(t,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def validate_static_anchor():
    for name,h in read(C/'STATIC_ANCHOR.json')['files'].items():
        p=R/name
        if not p.is_file()or hashlib.sha256(p.read_bytes()).hexdigest()!=h:return False
    for name,h in read(C/'PREPARATION_ANCHOR.json')['files'].items():
        p=R/name
        if not p.is_file()or hashlib.sha256(p.read_bytes()).hexdigest()!=h:return False
    return bool(read(R/'records/nav2_v885_20261108/COMBINED_THREE_ROUTE_GATE.json')['combined_three_route_static_development_passed']and read(R/'records/nav2_v887_20261108/QUALIFICATION.json')['passed']and read(R/'records/nav2_v886_20261108/COMPLETION.json')['closed']and read(R/'records/nav2_v890_20261108/COMPLETION.json')['closed']and read(R/'records/nav2_v891_20261108/CONTRACT_QUALIFICATION.json')['passed'])
def authorized(task,receipt,now,freeze_sha):
    require(receipt.get('models_authorized')is True and receipt.get('scope')==SCOPE,'MODELS_NOT_AUTHORIZED')
    require(not(O/'COMPLETION.json').exists(),'WINDOW_ALREADY_CLOSED')
    root=read(O/'AUTHORIZATION.json')
    require(root.get('models_authorized')is True and root.get('user_requested_dynamic_stage')is True and root.get('user_approved_new90min')is True and root.get('scope')==SCOPE,'DYNAMIC_STAGE_INSTRUCTION_REQUIRED')
    require(root.get('source_freeze_sha256')==freeze_sha==receipt.get('source_freeze_sha256'),'FREEZE_MISMATCH')
    start=root.get('started_unix');end=root.get('deadline_unix')
    require(type(start)in[int,float]and type(end)in[int,float]and math.isfinite(start)and math.isfinite(end),'ABSOLUTE_WINDOW_REQUIRED')
    require(end==start+DURATION and receipt.get('started_unix')==start and receipt.get('deadline_unix')==end,'NEW_FIXED_90MIN_WINDOW_CHANGED')
    require(start<=now<end-30 and start<end,'EXPIRED_OR_NOT_STARTED_WINDOW')
    require(validate_static_anchor(),'FROZEN_STATIC_ANCHOR_NOT_PASSED')
    require(task in read(C/'TASKS.json'),'UNREGISTERED_OR_CHANGED_TASK')
    require(receipt.get('run_id')==task['run_id']and receipt.get('task_sha256')==digest(task),'TASK_RECEIPT_CHANGED')
    require(task['case_id']=='WEST_EAST'and task['seed']==10010001 and task['dynamic']is True and task['wall_limit_s']==180 and task['brake_s']==2.,'TASK_SCOPE_CHANGED')
    if task['task_id']!='t0_we':require(read(O/'PREFLIGHTS.json').get('passed')is True,'DYNAMIC_T0_NOT_PASSED')
    if task['task_id']=='repeat_we':
        baseline=R/'runs/v858_nav2_verified/v892/main_we'
        require(read(baseline/'INDEPENDENT_AUDIT.json').get('passed')is True,'MAIN_NOT_PASSED')
        require(read(baseline/'RESULT.json').get('passed')is True,'MAIN_RUNTIME_NOT_PASSED')
    return float(end)
