"""Immutable task and fixed-root authority; no model imports."""
import hashlib,json,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1064_cpu_backend_entry_20261111';HARD_END=1794445200.
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def authorized(task,receipt):
 assert task in json.loads((C/'TASKS.json').read_text()),'UNREGISTERED_TASK'
 assert receipt['task_id']==task['task_id']and receipt['task_sha256']==sha(C/('TASK_'+task['task_id']+'.json'))and receipt['source_sha256']==sha(C/'SOURCE_FREEZE.json')and receipt['window_sha256']==sha(O/'ROUND_WINDOW.json'),'RECEIPT_BINDING'
 window=json.loads((O/'ROUND_WINDOW.json').read_text());approval=json.loads((O/'APPROVAL.json').read_text());assert approval['models_authorized']and task['task_id']in approval['allowed_task_ids'],'NO_MODEL_AUTHORITY';assert window['absolute_deadline_unix']==approval['absolute_deadline_unix']==HARD_END and time.time()<HARD_END-180 and time.monotonic()<window['hard_stop_monotonic']-180,'FIXED_ROOT_EXPIRED'
 assert Path(task['output']).resolve()==R/'runs/v858_nav2_verified/v1064'/task['task_id'],'OUTPUT_NAMESPACE'
 assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items()),'SOURCE_CHANGED'
 if task['kind'].startswith('confirm')or task['task_id'].startswith('t0_confirm'):
  gate=json.loads((O/'THREE_ROUTE_GATE.json').read_text());assert gate['passed']and gate['selected_branch_id']==receipt['branch_id'],'MISSING_FULL_THREE_ROUTE_GATE'
  assert receipt['gate_sha256']==sha(O/'THREE_ROUTE_GATE.json'),'THREE_ROUTE_GATE_CHANGED'
 return min(HARD_END-30,receipt['task_deadline_unix'])
