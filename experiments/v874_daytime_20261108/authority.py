"""Immutable task, selected-branch and fixed17:00 authority; no expired batch reuse."""
import hashlib,json,math
from pathlib import Path
from handshake import require
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v874_daytime_20261108';DEADLINE=1794128400.
def digest(task):return hashlib.sha256(json.dumps(task,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def read(p):return json.loads(p.read_text())
def resolve(template,selected=None):
 t=dict(template);variant=t['variant']
 if variant.startswith('SELECTED'):
  require(selected in ['A','B','C'],'SELECTED_BRANCH_REQUIRED');variant=variant.replace('SELECTED',selected)
 t['resolved_variant']=variant;t['nav2_params']=str(C/(variant+'.yaml'));return t

def authorized(task,receipt,now,freeze_sha):
 require(receipt.get('models_authorized')is True and receipt.get('scope')=='V874_DAYTIME_OFFLINE','MODELS_NOT_AUTHORIZED')
 require(receipt.get('source_freeze_sha256')==freeze_sha,'FREEZE_MISMATCH');root=read(O/'AUTHORIZATION.json');require(root['source_freeze_sha256']==freeze_sha and root['deadline_unix']==DEADLINE and receipt.get('deadline_unix')==DEADLINE,'ROOT_WINDOW_CHANGED');start=receipt.get('started_unix');require(isinstance(start,(int,float))and math.isfinite(start)and start==root['started_unix']and start<=now<DEADLINE-30,'EXPIRED_OR_RENEWED_WINDOW')
 templates=[t for t in read(C/'TASKS.json')if t['run_id']==task['run_id']];require(len(templates)==1,'UNREGISTERED_TASK');template=templates[0];selected=None
 if template['variant'].startswith('SELECTED'):
  selection=read(O/'SELECTED.json');require(selection['passed']is True and selection['source_freeze_sha256']==freeze_sha,'SELECTION_NOT_PASSED');selected=selection['variant']
 require(resolve(template,selected)==task,'TASK_CHANGED');require(receipt.get('run_id')==task['run_id']and receipt.get('task_sha256')==digest(task),'TASK_RECEIPT_CHANGED');require(task['wall_limit_s']==180 and task['brake_s']==2.,'NAVIGATION_BUDGET_CHANGED')
 role=task['role'];v=task['resolved_variant'];base=v.split('_')[0]
 if role=='development':
  gate=read(O/'software'/base/'QUALIFICATION.json');require(gate.get('passed')is True,'SOFTWARE_DEPENDENCY_NOT_PASSED')
  if task['dynamic']:require(read(O/(base+'_STATIC_GATE.json')).get('passed')is True,'STATIC_DEPENDENCY_NOT_PASSED')
 elif role in ['confirmation','confirmation_repeat']:require(read(O/'DEVELOPMENT_GATE.json').get('passed')is True,'DEVELOPMENT_NOT_PASSED')
 elif role in ['comparison','ablation']:
  require(read(O/'CONFIRMATION_GATE.json').get('passed')is True,'CONFIRMATION_NOT_PASSED')
  if v!='MPPI'and '_'not in v:pass
  else:require(read(O/'software'/v/'QUALIFICATION.json').get('passed')is True,'COMPARISON_SOFTWARE_NOT_PASSED')
 else:raise RuntimeError('UNKNOWN_ROLE')
 return DEADLINE
