"""Separate once-only initializer qualification owner. Does not admit a route."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;P=R/'runs/v1382_weekend_campaign/LEDGER.json'

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
contract=exact('v1445_once_initializer_contract',C/'contract.py')

def put(path,value):
 path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(path)

def claim_once(path):
 with Path(path).open('x')as stream:stream.write(json.dumps(dict(once=True,recorded_unix=time.time()))+'\n')

class BoundedConsole:
 def __init__(self,stream,maximum_bytes):
  assert type(maximum_bytes)is int and maximum_bytes>0
  self.stream=stream;self.maximum=maximum_bytes;self.charged=0
 def feed(self,block):
  assert isinstance(block,bytes)and self.charged+len(block)<=self.maximum,'INITIALIZER_CONSOLE_BYTE_CAP_EXHAUSTED'
  self.charged+=len(block);self.stream.write(block);self.stream.flush()

def prepare_admission():
 assert not(O/'INITIALIZER_ONLY_ADMISSION.json').exists()
 q=contract.read(O/'ENTRY_QUALIFICATION.json');assert q['passed']and q['models']==q['physical_native']==0
 assert all(q['entry_gates'].values())and q['actual_native_C_save_executed']is False
 assert q['entry_gates']['immutable_original_guard_scope_and_native_Mesa_cache']is True and q['entry_gates']['task_local_temp_and_torch_cache_write_path']is True and q['changed_runtime_source_checks_passed']is True
 assert q['reused_initializer_entry_qualification_SHA']==contract.sha(R/'runs/v1441_initializer_definition_import/ENTRY_QUALIFICATION.json')
 frozen=contract.read(O/'SOURCE_FREEZE.json')['files'];assert all(contract.sha(R/p)==h for p,h in frozen.items())
 put(O/'INITIALIZER_ONLY_ADMISSION.json',dict(initializer_only_admission=True,physical_route_admission=False,initializer_runtime_qualified=False,actual_native_C_save_executed=False,entry_gates=q['entry_gates'],entry_qualification_sha256=contract.sha(O/'ENTRY_QUALIFICATION.json'),limits=contract.read(C/'LIMITS.json'),source_hashes=frozen,prerequisite_qualification_SHA=contract.prerequisites(),prepared_unix=time.time()))

def launch():
 # A narrow initialization admission, its tested source and actual source
 # backup must exist before even the launch claim or parent ledger changes.
 q=contract.read(O/'INITIALIZER_ONLY_ADMISSION.json');assert q['initializer_only_admission']and not q['physical_route_admission']
 assert all(contract.sha(R/p)==h for p,h in q['source_hashes'].items())
 recovered=contract.read(R/'runs/v1443_task_local_initializer_cache/FULL_REMOTE_VERIFIED.json');assert recovered['passed']and recovered['every_member_SHA_and_link_text']
 index=contract.read(R/'runs/v1443_task_local_initializer_cache/ARCHIVE_INDEX.json');members={row['path']:row for row in index['files']}
 assert all(name in members and members[name]['sha256']==digest for name,digest in q['source_hashes'].items()if name.startswith('experiments/v1445_immutable_initializer_writeguard/')),'INITIALIZER_SOURCE_NOT_IN_VERIFIED_REMOTE_ARCHIVE'
 parent=contract.read(P);auth=contract.read(R/'experiments/v1382_weekend_campaign/AUTHORIZATION.json');assert parent['active_round']is None and not parent['models_now_authorized']
 assert len(parent['rounds'])<auth['maximum_rounds']and parent['vehicle_task_starts']<auth['maximum_vehicle_task_starts']and parent['scientific_revisions']==5
 assert min(parent['absolute_hard_stop_unix']-time.time(),parent['hard_stop_monotonic']-time.monotonic())>240
 storage=contract.storage_preflight();saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
 import fcntl
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 claim_once(O/'INITIALIZER_ONCE_CLAIM.json');out=O/'initializer_only';out.mkdir();(O/'REVIEW_PENDING.before').write_bytes(saved)
 task=contract.read(R/'experiments/v1439_actual_ros_startup_close/TASKS.json')[0];task.update(task_id='initializer_only',role='initializer_only',run_id=C.name+'_initializer_only',output=str(out),run_root=str(O))
 now=time.time();mono=time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+180,hard_stop_monotonic=mono+180,boot_id=parent['boot_id'])
 approval=dict(models_authorized=True,scope=q['limits']['scope'],qualification_sha256=contract.sha(O/'INITIALIZER_ONLY_ADMISSION.json'),round_id=C.name+'_initializer_only',allowed_task_ids=['initializer_only'],**{k:window[k]for k in ['absolute_deadline_unix','hard_stop_monotonic','boot_id']})
 for path,value in [(O/'TASK.json',task),(O/'APPROVAL.json',approval),(O/'INITIALIZER_WINDOW.json',window),(O/'STORAGE_PREFLIGHT.json',storage),(out/'CONSOLE_RESERVATION.json',dict(maximum_bytes=4*1024**2,owner_source_sha256=contract.sha(C/'owner.py'),entry_gate_qualified=q['entry_gates']['supervisor_console_bounded_pipe']))]:put(path,value)
 row=dict(id=approval['round_id'],kind='canonical_initializer_only_qualification_zero_integration',status='RUNNING',started_unix=now,hard_stop_unix=window['absolute_deadline_unix'],maximum_canonical_factory_calls=1,maximum_actual_native=0,maximum_analytical_native=0,maximum_replay_native=0,scientific_revision=5,not_navigation=True)
 parent['rounds'].append(row);parent.update(active_round=row['id'],models_now_authorized=True,status='INITIALIZER_ONLY_QUALIFICATION_RUNNING');parent['vehicle_task_starts']+=1;put(P,parent)
 job=None;result=dict(passed=False,closed=False,physical_route_admission=False);started=time.monotonic()
 try:
  (R/'REVIEW_PENDING').unlink();env=exact('v1445_frozen_CPU_environment',R/'experiments/v1439_actual_ros_startup_close/supervisor.py').env()
  with(out/'initializer.console').open('xb')as console:
   bounded=BoundedConsole(console,4*1024**2)
   job=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'entry.py').relative_to(R)),'--run'],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
   os.set_blocking(job.stdout.fileno(),False)
   def drain():
    for _ in range(64):
     try:block=os.read(job.stdout.fileno(),16384)
     except BlockingIOError:break
     if not block:break
     bounded.feed(block)
   while job.poll()is None:
    assert min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())>0,'INITIALIZER_OWNER_DUAL_CLOCK_EXHAUSTED'
    drain();time.sleep(.02)
   drain();result.update(returncode=job.wait(timeout=2),console_charged_bytes=bounded.charged)
   job.stdout.close()
  result['native']=contract.read(out/'RESULT.json');result['passed']=result['returncode']==0 and result['native']['passed']
 except BaseException as exc:result.update(error=repr(exc))
 finally:
  errors=[]
  if job is not None and job.poll()is None:
   try:
    os.killpg(job.pid,signal.SIGTERM)
    try:job.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(job.pid,signal.SIGKILL);job.wait(timeout=2)
   except BaseException as exc:errors.append(dict(stage='CLOSE_INITIALIZER_WORKER',error=repr(exc)))
  try:(R/'REVIEW_PENDING').write_bytes(saved)
  except BaseException as exc:errors.append(dict(stage='RESTORE_REVIEW',error=repr(exc)))
  restored=(R/'REVIEW_PENDING').read_bytes()==saved;result.update(closed=True,closed_unix=time.time(),wall_s=time.monotonic()-started,review_original_restored=restored,secondary_errors=errors)
  if errors or not restored:result['passed']=False
  try:put(O/'COMPLETION.json',result)
  except BaseException as exc:errors.append(dict(stage='SAVE_COMPLETION',error=repr(exc)));result['passed']=False
  parent=contract.read(P);item=next(x for x in parent['rounds']if x['id']==approval['round_id']);native=result.get('native',{})
  item.update(status='CLOSED',closed=True,passed=result['passed'],completion=str((O/'COMPLETION.json').relative_to(R)),canonical_factory_call_attempts=native.get('canonical_factory_call_attempts'),canonical_vehicle_initializations=native.get('canonical_vehicle_initializations'),internal_factory_model_constructions=None,actual_native=0,analytical_native=0,own_replay_native=0,initializer_inflight_unknown=native.get('initializer_inflight_unknown',True))
  parent.update(active_round=None,models_now_authorized=False,status='INITIALIZER_ONLY_QUALIFICATION_CLOSED')
  try:put(P,parent)
  except BaseException as exc:errors.append(dict(stage='CLOSE_PARENT',error=repr(exc)));result['passed']=False
  if errors:os.write(2,(json.dumps(dict(first_error=result.get('error')or result.get('native',{}).get('first_error'),secondary_errors=errors,evidence_gap=True),allow_nan=False)+'\n').encode())
 return result
