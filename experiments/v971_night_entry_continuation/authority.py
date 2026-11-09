"""Post-stop user-authorized route development; original V968 deadline/source retained."""
import hashlib,json,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v971_night_entry_continuation'
SCOPE='V971_USER_POSTSTOP_REMAINING_ROUTE_ENTRY'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def root_authorized(now=None,freeze_sha=None):
 now=time.time()if now is None else now
 assert not(O/'COMPLETION.json').exists(),'ENTRY_CLOSED_NO_RESTART'
 a=read(O/'AUTHORIZATION.json');w=read(O/'ROUND_WINDOW.json');old=read(R/'records/nav2_v968_20261109/AUTHORIZATION.before_close.json')
 assert a['models_authorized']is True and a['scope']==SCOPE
 assert a['started_unix']==old['started_unix']==w['started_unix'] and a['deadline_unix']==old['deadline_unix']==w['deadline_unix']==1794268800.
 assert a['started_unix']<=now<a['deadline_unix']-30
 assert read(O/'USER_POSTSTOP_INSTRUCTION.json')['authorizes_remaining_route_development']is True
 assert read(O/'SAVED_HANDOFF_ANCHOR.json')['saved_second_stage_passed']is True
 assert read(O/'SAVED_HANDOFF_ANCHOR.json')['original_full_component_passed']is False
 assert read(O/'ZERO_MODEL_QUALIFICATION.json')['passed']
 assert sha(C/'SOURCE_FREEZE.json')==a['source_freeze_sha256']
 if freeze_sha is not None:assert freeze_sha==a['source_freeze_sha256']
 for rel,h in read(C/'SOURCE_FREEZE.json')['files'].items():
  p=R/rel;assert p.resolve().is_relative_to(R)and p.is_file()and sha(p)==h,'FROZEN_SOURCE_CHANGED '+rel
 return a
def ready_for_navigation():
 assert read(O/'SAVED_HANDOFF_ANCHOR.json')['saved_second_stage_passed']
def authorized(task,receipt,now,freeze_sha,preflight=False):
 a=root_authorized(now,freeze_sha)
 assert task in read(C/'TASKS.json')and receipt==dict(a,run_id=task['run_id'],task_sha256=digest(task))
 assert task['stage']!='component','COMPONENT_RERUN_FORBIDDEN'
 if task['stage']=='regression':assert read(O/'WE_GATE.json')['passed']
 if task['stage']in{'confirmation','confirmation_repeat'}:assert read(O/'REGRESSION_GATE.json')['passed']
 if not preflight and task.get('preflight_output'):assert read(O/(task['phase_group']+'_PREFLIGHT_AUDIT.json'))['passed']
 if task['role']=='dynamic_repeat':
  assert read(Path(task['baseline_output'])/'INDEPENDENT_AUDIT.json')['passed']
  if task['stage']=='confirmation_repeat':assert read(O/'CONFIRMATION_MAIN_GATE.json')['passed']
 return a['deadline_unix']
