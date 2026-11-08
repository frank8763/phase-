"""Only the five immutable static tasks are authorized; original time limit is inherited."""
import hashlib,json,math
from pathlib import Path
from handshake import require
C=Path(__file__).resolve().parent;R=C.parents[1];DEADLINE=1794062038.6753576
def digest(task):return hashlib.sha256(json.dumps(task,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def authorized(task,receipt,now,freeze_sha):
 require(receipt.get('models_authorized')is True,'MODELS_NOT_AUTHORIZED')
 require(receipt.get('scope')=='V864_FIVE_FIXED_STATIC_RPP_RUNS','WRONG_SCOPE')
 require(receipt.get('source_freeze_sha256')==freeze_sha,'FREEZE_MISMATCH')
 rows=json.loads((C/'TASKS.json').read_text());registered=[row for row in rows if row['run_id']==task['run_id']]
 require(len(registered)==1 and registered[0]==task,'UNREGISTERED_TASK')
 require(receipt.get('run_id')==task['run_id']and receipt.get('task_sha256')==digest(task),'TASK_AUTHORITY_MISMATCH')
 require(receipt.get('deadline_unix')==DEADLINE,'ORIGINAL_DEADLINE_CHANGED')
 start=receipt.get('started_unix');require(isinstance(start,(int,float))and math.isfinite(start)and start<=now<DEADLINE-30,'EXPIRED_OR_NOT_STARTED')
 require(task['dynamic']is False and task['wall_limit_s']==180 and task['brake_s']==2.,'SCOPE_OR_BUDGET_CHANGED')
 return DEADLINE
