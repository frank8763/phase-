"""New90min daytime, exactly one original WE dynamic navigation, no automatic followup."""
import hashlib,json,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v974_daytime_binding_gate';SCOPE='V974_ONE_DYNAMIC_ROUTE_BINDING_GATE'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def root_authorized(now=None,freeze_sha=None):
 now=time.time()if now is None else now
 assert not(O/'COMPLETION.json').exists(),'DAY_GATE_ALREADY_CLOSED'
 a=read(O/'AUTHORIZATION.json');w=read(O/'ROUND_WINDOW.json')
 assert a['models_authorized']is True and a['scope']==SCOPE
 assert a['started_unix']==w['started_unix']and a['deadline_unix']==w['deadline_unix']and abs(a['deadline_unix']-a['started_unix']-5400.)<1e-6
 assert a['started_unix']<=now<a['deadline_unix']-30
 assert sha(C/'SOURCE_FREEZE.json')==a['source_freeze_sha256']
 if freeze_sha is not None:assert freeze_sha==a['source_freeze_sha256']
 for rel,h in read(C/'SOURCE_FREEZE.json')['files'].items():
  p=R/rel;assert p.resolve().is_relative_to(R)and p.is_file()and sha(p)==h,'FROZEN_SOURCE_CHANGED '+rel
 for entry in read(C/'MODULE_BINDINGS.json')['aliases']:
  assert (R/entry['alias']).resolve()==(R/entry['source']).resolve(),'MODULE_ALIAS_TARGET_CHANGED'
 for name in ['ZERO_MODEL_QUALIFICATION.json','FULL_PLANNER_FLOW_QUALIFICATION.json']:assert read(O/name)['passed'],name
 return a
def ready_for_navigation():return None
def authorized(task,receipt,now,freeze_sha):
 a=root_authorized(now,freeze_sha);assert task in read(C/'TASKS.json')and receipt==dict(a,run_id=task['run_id'],task_sha256=digest(task))
 assert task['task_id']=='main_we'and task['seed']==10010001 and task['wall_limit_s']==180
 return a['deadline_unix']
