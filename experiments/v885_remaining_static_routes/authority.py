"""Remaining fixed static routes only, original V884 hard cutoff inherited without reset."""
import hashlib,json,math,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v885_remaining_static_routes'
sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import require
SCOPE='V885_REMAINING_STATIC_ROUTES'
DEADLINE=json.loads((C/'WINDOW_POLICY.json').read_text())['deadline_unix']
def read(p):return json.loads(Path(p).read_text())
def digest(t):return hashlib.sha256(json.dumps(t,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def validate_ns_anchor():
    proof=read(C/'NS_ANCHOR.json')
    for name,h in proof['files'].items():
        p=R/name
        if not p.is_file()or hashlib.sha256(p.read_bytes()).hexdigest()!=h:return False
    return bool(read(R/'records/nav2_v884_20261108/RESULT_SUMMARY.json')['passed']and read(R/'records/nav2_v884_20261108/REMOTE_VERIFIED.json')['passed']and read(R/'records/nav2_v884_20261108/REPEAT_COMPARISON.json')['passed'])
def authorized(task,receipt,now,freeze_sha):
    require(receipt.get('models_authorized')is True and receipt.get('scope')==SCOPE,'MODELS_NOT_AUTHORIZED')
    require(not(O/'COMPLETION.json').exists(),'WINDOW_ALREADY_CLOSED')
    root=read(O/'AUTHORIZATION.json')
    require(root.get('models_authorized')is True and root.get('user_requested_next_static_stage')is True and root.get('scope')==SCOPE,'NEXT_STATIC_STAGE_INSTRUCTION_REQUIRED')
    require(root.get('source_freeze_sha256')==freeze_sha==receipt.get('source_freeze_sha256'),'FREEZE_MISMATCH')
    start=root.get('started_unix');end=root.get('deadline_unix')
    require(type(start)in[int,float]and type(end)in[int,float]and math.isfinite(start)and math.isfinite(end),'ABSOLUTE_WINDOW_REQUIRED')
    require(end==DEADLINE and receipt.get('started_unix')==start and receipt.get('deadline_unix')==DEADLINE,'INHERITED_DEADLINE_CHANGED')
    require(start<=now<end-30 and start<end,'EXPIRED_OR_NOT_STARTED_WINDOW')
    require(validate_ns_anchor(),'FROZEN_NS_ANCHOR_NOT_PASSED')
    require(task in read(C/'TASKS.json'),'UNREGISTERED_OR_CHANGED_TASK')
    require(receipt.get('run_id')==task['run_id']and receipt.get('task_sha256')==digest(task),'TASK_RECEIPT_CHANGED')
    require((task['case_id'],task['seed'])in [('WEST_EAST',10010001),('EAST_WEST',10010003)]and task['dynamic']is False and task['wall_limit_s']==180 and task['brake_s']==2.,'TASK_SCOPE_CHANGED')
    if task['case_id']=='EAST_WEST':require(read(O/'WEST_EAST_REPEAT_COMPARISON.json').get('passed')is True,'WEST_EAST_PAIR_NOT_PASSED')
    if task['task_id'].startswith('repeat_'):
        baseline=R/'runs/v858_nav2_verified/v885'/task['task_id'].replace('repeat_','main_',1)
        require(read(baseline/'INDEPENDENT_AUDIT.json').get('passed')is True,'MAIN_NOT_PASSED')
        require(read(baseline/'RESULT.json').get('passed')is True,'MAIN_RUNTIME_NOT_PASSED')
    return float(end)
