"""One new 90-minute campaign, independent of all expired windows."""
import hashlib, json, sys
from pathlib import Path
C=Path(__file__).resolve().parent; R=C.parents[1]; O=R/'runs/v903_retained_exit_reference'
sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import require
SCOPE='V903_RETAINED_EXIT_DEVELOPMENT'
def read(p): return json.loads(Path(p).read_text())
def digest(t): return hashlib.sha256(json.dumps(t,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def authorized(task,receipt,now,freeze_sha):
    require(receipt.get('models_authorized') is True and receipt.get('scope')==SCOPE,'MODELS_NOT_AUTHORIZED')
    require(not(O/'COMPLETION.json').exists(),'WINDOW_ALREADY_CLOSED')
    root=read(O/'AUTHORIZATION.json'); window=read(R/'runs/v900_refuge_terminal_set/ROUND_WINDOW.json')
    require(root['models_authorized'] is True and root['deadline_unix']==window['deadline_unix'] and root['started_unix']==window['started_unix'],'ROOT_WINDOW_CHANGED')
    require(root['deadline_unix']-root['started_unix']==5400. and now<root['deadline_unix']-30,'EXPIRED_OR_CHANGED_DEADLINE')
    require(receipt['deadline_unix']==root['deadline_unix'],'TASK_DEADLINE_CHANGED')
    require(read(R/'runs/v896_overnight_20261108/platform_continuation_result.json')['passed'] is True,'PLATFORM_NOT_QUALIFIED')
    require(task in read(C/'TASKS.json'),'UNREGISTERED_OR_CHANGED_TASK')
    require(receipt.get('task_sha256')==digest(task) and receipt.get('run_id')==task['run_id'],'TASK_CHANGED')
    require(receipt.get('source_freeze_sha256')==freeze_sha==root['source_freeze_sha256'],'SOURCE_CHANGED')
    if task['role']!='dynamic_t0': require(read(O/'PREFLIGHTS.json')[task['case_id']]['passed'],'T0_NOT_PASSED')
    if task['role']=='dynamic_repeat': require(read(Path(task['output']).parent/('main_'+task['route'])/'INDEPENDENT_AUDIT.json')['passed'],'MAIN_NOT_PASSED')
    return root['deadline_unix']
