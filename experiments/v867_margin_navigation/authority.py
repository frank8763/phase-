"""Only preregistered12 tasks, one separately user-authorized90min window, no renewal."""
import hashlib,json,math
from pathlib import Path
from handshake import require
C=Path(__file__).resolve().parent;R=C.parents[1]
def digest(task):return hashlib.sha256(json.dumps(task,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def authorized(task,receipt,now,freeze_sha):
 require(receipt.get('models_authorized')is True,'MODELS_NOT_AUTHORIZED')
 require(receipt.get('scope')=='V867_STATIC_THEN_CONDITIONAL_DYNAMIC','WRONG_SCOPE')
 require(receipt.get('source_freeze_sha256')==freeze_sha,'FREEZE_MISMATCH')
 tasks=json.loads((C/'TASKS.json').read_text());registered=[t for t in tasks if t['run_id']==task['run_id']];require(len(registered)==1 and registered[0]==task,'UNREGISTERED_TASK')
 require(receipt.get('run_id')==task['run_id']and receipt.get('task_sha256')==digest(task),'TASK_AUTHORITY_MISMATCH')
 start=receipt.get('started_unix');deadline=receipt.get('deadline_unix');require(all(isinstance(v,(int,float))and math.isfinite(v)for v in [start,deadline]),'ABSOLUTE_WINDOW_REQUIRED');require(abs(deadline-start-5400)<1e-6,'90MIN_WINDOW_CHANGED');require(start<=now<deadline-30,'EXPIRED_OR_NOT_STARTED')
 root=json.loads((R/'runs/v867_margin_navigation/AUTHORIZATION.json').read_text());require(root['started_unix']==start and root['deadline_unix']==deadline and root['source_freeze_sha256']==freeze_sha,'ROOT_AUTHORITY_CHANGED')
 require(task['wall_limit_s']==180 and task['brake_s']==2.,'BUDGET_CHANGED')
 if task['dynamic']:
  gate=R/'runs/v867_margin_navigation/STATIC_GATE.json';require(gate.is_file()and json.loads(gate.read_text()).get('passed')is True,'STATIC_DEPENDENCY_NOT_PASSED')
 return float(deadline)
