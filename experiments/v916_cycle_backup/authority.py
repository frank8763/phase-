"""Single new finite round. Closed previous windows are never consulted as authority."""
import hashlib,json,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v916_cycle_backup'
sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import require
SCOPE='V916_DECLARED_PERIODIC_COURSE'
def read(p):return json.loads(Path(p).read_text())
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def root_authorized(now,freeze_sha):
    root=read(O/'AUTHORIZATION.json');window=read(O/'ROUND_WINDOW.json')
    require(not(O/'COMPLETION.json').exists(),'ROUND_ALREADY_CLOSED')
    require(root['scope']==SCOPE and root['models_authorized'] is True,'NO_NEW_AUTHORITY')
    require(root['started_unix']==window['started_unix'] and root['deadline_unix']==window['deadline_unix'],'WINDOW_CHANGED')
    require(0<root['deadline_unix']-root['started_unix']<=5400. and root['started_unix']<=now<root['deadline_unix']-30,'INVALID_OR_EXPIRED_WINDOW')
    require(root['source_freeze_sha256']==freeze_sha,'SOURCE_AUTHORITY_MISMATCH')
    require(all(read(O/name)['passed'] for name in ['ZERO_MODEL_QUALIFICATION.json','RELEASE_QUALIFICATION.json','ROS_SOFTWARE_QUALIFICATION.json','FULL_STARTUP_QUALIFICATION.json','CONDITIONAL_RESPONSE_QUALIFICATION.json','PLANNING_QUALIFICATION.json','NATIVE_SEAM_QUALIFICATION.json','AUDIT_QUALIFICATION.json']),'ZERO_MODEL_QUALIFICATION_FAILED')
    return root
def authorized(task,receipt,now,freeze_sha):
    root=root_authorized(now,freeze_sha)
    require(receipt==dict(root,run_id=task['run_id'],task_sha256=digest(task)),'RECEIPT_CHANGED')
    require(task in read(C/'TASKS.json'),'UNREGISTERED_TASK')
    require(read(O/'PLATFORM_RESULT.json')['passed'],'PLATFORM_FAILED')
    if task['role']=='dynamic_repeat':require(read(Path(task['output']).parent/'main_we/INDEPENDENT_AUDIT.json')['passed'],'MAIN_FAILED')
    return root['deadline_unix']
