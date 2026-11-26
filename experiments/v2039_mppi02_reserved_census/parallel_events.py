"""Append-only per-method claims avoid racing the frozen RPP ledger writer."""
from pathlib import Path
import copy,hashlib,json,os,time
from context import R,O,read,sha
EVENTS=R/'runs/v1805_common_algorithm_registry/PARALLEL_METHOD_EVENTS'
def write_once(path,value):
 raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(raw)<256*1024
 with path.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
def register(task,*,source_freeze_sha256):
 assert task['method']=='MPPI'and task['common_task_id']=='common_02'
 assert read(O/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
 base=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json');slot=next(x for x in base['slots']if x['method']=='MPPI'and x['task_id']==task['common_task_id']);assert not slot['registered']and not slot['closed']
 EVENTS.mkdir(exist_ok=True);path=EVENTS/(task['task_id']+'.REGISTERED.json');assert not path.exists()
 value=dict(registered=True,closed=False,method='MPPI',task_id=task['common_task_id'],round_id=task['task_id'],root=str(O.relative_to(R)),task_sha256=sha(O/'PILOT_TASK.json'),source_freeze_sha256=source_freeze_sha256,original_common_registry_sha256=sha(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json'),unix=time.time(),shared_120_denominator_unchanged=True,base_ledger_not_mutated_while_RPP_active=True)
 write_once(path,value);write_once(O/'FORMAL_REGISTERED.json',dict(event_path=str(path.relative_to(R)),event_sha256=sha(path),**value))
def close(result):
 task=read(O/'PILOT_TASK.json');p=EVENTS/(task['task_id']+'.REGISTERED.json');assert read(p)['root']==str(O.relative_to(R));path=EVENTS/(task['task_id']+'.CLOSED.json');assert not path.exists()
 first=result.get('machine_first_error')or result.get('first_error');audit=result.get('independent_audit')or{};message=first.get('error','')if isinstance(first,dict)else str(first)
 names=['MPPI_RAW_COMMAND_GEAR_REFUSED','MPPI_RAW_COMMAND_DOMAIN_REFUSED','MPPI_CURRENT_CYCLE_COMPLETE_STOP_REFUSED','MPPI_ORIGINAL_COMPLETE_STOP_REFUSED','MPPI_NATIVE_LIMIT_NO_WHOLE_GOAL','MPPI_NOMINAL_PATH_NOT_FOUND','MPPI_CURRENT_PATH_REVALIDATION_REFUSED','MPPI_MEASURED_CUSP_CAPTURE_REFUSED']
 valid=bool(first and any(x in message for x in names)and audit.get('passed')and result.get('actual_native',0)>0 and result.get('actual_native')==result.get('own_replay_native'))
 value=dict(registered=True,closed=True,method='MPPI',task_id=task['common_task_id'],round_id=task['task_id'],root=str(O.relative_to(R)),qualified_success=bool(result['passed']),valid_finite_method_refusal=valid,technical_censor=not result['passed']and not valid,first_error=first,actual_native=result.get('actual_native'),own_replay_native=result.get('own_replay_native'),internal_total_modelwork=None,result_path=str((O/'COMPLETION.json').relative_to(R)),result_sha256=sha(O/'COMPLETION.json'),registration_sha256=sha(p),unix=time.time())
 write_once(path,value);write_once(O/'FORMAL_CLOSED_EVENT.json',dict(event_path=str(path.relative_to(R)),event_sha256=sha(path),**value))
def combined():
 base=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json');slots=copy.deepcopy(base['slots'])
 if EVENTS.exists():
  for p in sorted(EVENTS.glob('*.REGISTERED.json')):
   event=read(p);slot=next(x for x in slots if x['method']==event['method']and x['task_id']==event['task_id']);assert not slot['registered'],'DUPLICATE_BASE_AND_PARALLEL_REGISTRATION';slot.update(event)
   q=p.with_name(p.name.replace('.REGISTERED.json','.CLOSED.json'))
   if q.exists():assert read(q)['registration_sha256']==sha(p);slot.update(read(q))
 assert len(slots)==120
 return dict(denominator=120,registered=sum(bool(x['registered'])for x in slots),closed=sum(bool(x['closed'])for x in slots),unexecuted=sum(not x['registered']for x in slots),qualified_success=sum(bool(x.get('qualified_success'))for x in slots),parallel_events_authoritative_until_base_consolidation=True,base_ledger_not_mutated=True)
