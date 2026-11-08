"""A future, separately approved90min window; immutable originalNS task, no model imports."""
import hashlib,json,math
from pathlib import Path
import sys
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import require
O=R/'runs/v884_feasible_rpp'
SCOPE='V884_ONE_STATIC_NS_FEASIBLE_RPP'
def read(path):return json.loads(Path(path).read_text())
def digest(task):return hashlib.sha256(json.dumps(task,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def authorized(task,receipt,now,freeze_sha):
    require(receipt.get('models_authorized')is True and receipt.get('scope')==SCOPE,'MODELS_NOT_AUTHORIZED')
    require(not(O/'COMPLETION.json').exists(),'WINDOW_ALREADY_CLOSED')
    root=read(O/'AUTHORIZATION.json')
    require(root.get('models_authorized')is True and root.get('user_approved_new90min')is True and root.get('scope')==SCOPE,'NEW_EXPLICIT_WINDOW_REQUIRED')
    require(root.get('source_freeze_sha256')==freeze_sha==receipt.get('source_freeze_sha256'),'FREEZE_MISMATCH')
    start=root.get('started_unix');end=root.get('deadline_unix')
    require(type(start)in[int,float]and type(end)in[int,float]and math.isfinite(start)and math.isfinite(end),'ABSOLUTE_WINDOW_REQUIRED')
    require(abs(end-start-5400.)<1e-6 and receipt.get('started_unix')==start and receipt.get('deadline_unix')==end,'WINDOW_CHANGED')
    require(start<=now<end-30,'EXPIRED_OR_NOT_STARTED_WINDOW')
    require(task in read(C/'TASKS.json'),'UNREGISTERED_OR_CHANGED_TASK')
    require(receipt.get('run_id')==task['run_id']and receipt.get('task_sha256')==digest(task),'TASK_RECEIPT_CHANGED')
    require(task['case_id']=='NORTH_SOUTH'and task['seed']==10010002 and task['dynamic']is False and task['wall_limit_s']==180 and task['brake_s']==2.,'TASK_SCOPE_CHANGED')
    if task['task_id']=='repeat_ns':
        baseline=read(R/'runs/v858_nav2_verified/v884/main_ns/INDEPENDENT_AUDIT.json')
        require(baseline.get('passed')is True,'MAIN_NOT_PASSED')
        require(read(R/'runs/v858_nav2_verified/v884/main_ns/RESULT.json').get('passed')is True,'MAIN_RUNTIME_NOT_PASSED')
    return float(end)
