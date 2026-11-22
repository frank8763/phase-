"""CPU5 once actual/ROS owner; root/source/storage gates before any claim.

No old window is reopened. Missing native evidence remains unknown, and only
exact owned process groups may be terminated. No modeled ROS peer is started.
"""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time
import traceback
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1607_owner_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
P=c.R/'runs/v1382_weekend_campaign/LEDGER.json';REVIEW=c.R/'REVIEW_PENDING'

def parent_bytes(value,maximum=131072):
 raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()+b'\n';assert len(raw)<=maximum,'PARENT_CONTROL_SERIALIZED_CAP';return raw

def owned_identity(process):
 stat=Path('/proc/'+str(process.pid)+'/stat').read_text().rsplit(')',1)[1].split()
 return dict(pid=process.pid,pgid=os.getpgid(process.pid),start_ticks=int(stat[19]),
  boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())

def close_owned(process,identity):
 if process.poll()is not None:return process.returncode
 assert owned_identity(process)==identity and identity['pgid']==process.pid,'CPP_OWNED_CHILD_IDENTITY_CHANGED'
 os.killpg(process.pid,signal.SIGTERM)
 try:return process.wait(timeout=5)
 except subprocess.TimeoutExpired:
  assert owned_identity(process)==identity,'CPP_OWNED_CHILD_IDENTITY_CHANGED_BEFORE_KILL'
  os.killpg(process.pid,signal.SIGKILL);return process.wait(timeout=5)


def runtime_passed(rc,machine,errors):
 if rc!=0 or not isinstance(machine,dict)or errors:return False
 if machine.get('passed')is not True or machine.get('closed')is not True:return False
 if machine.get('first_error')is not None or machine.get('secondary_errors')!=[]:return False
 if type(machine.get('actual_native'))is not int or machine.get('actual_inflight_unknown')is not False:return False
 if machine.get('canonical_vehicle_initializations')!=1 or machine.get('own_replay_inflight_unknown')is not False:return False
 n=machine['actual_native'];replay=machine.get('replay',{});allocation=machine.get('independent_allocation',{})
 return (0<n<=40000 and machine.get('own_replay_native')==n and replay.get('passed')is True and replay.get('replay_native')==n
  and replay.get('maximum_qpos_qvel_ctrl_mocap_error',float('inf'))<=1e-8 and replay.get('contact_mismatched_ticks')==0
  and allocation.get('passed')is True and allocation.get('allocator_recomputations')==n
  and allocation.get('maximum_memory_control_error',float('inf'))<=1e-8
  and machine.get('integrated_audit',{}).get('passed')is True and machine.get('source_unchanged')is True)


def launch():
 assert sorted(os.sched_getaffinity(0))==[5]
 q=c.read(c.O/'ENTRY_QUALIFICATION.json');assert q.get('complete_actual_source_target_passed') is True,'COMPLETE_ACTUAL_SOURCE_TARGET_NOT_QUALIFIED'
 assert q['passed']and q['closed']and q['models']==q['physical_native']==0
 assert all(q['source_gates'].values())
 source=c.sources();recovery=c.read(c.O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')
 assert recovery['passed']and recovery['source_freeze_sha256']==c.sha(c.O/'SOURCE_FREEZE.json')
 assert recovery['all_frozen_members_remote_chain_covered']and recovery['uncovered_members']==[]
 parent=c.read(P);auth=c.read(c.R/'experiments/v1382_weekend_campaign/AUTHORIZATION.json')
 assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
 assert parent['storage_limit_bytes']==15*1024**3
 assert parent['scientific_revisions']==12 and len(parent['rounds'])<auth['maximum_rounds']and parent['vehicle_task_starts']<auth['maximum_vehicle_task_starts']
 assert min(parent['absolute_hard_stop_unix']-time.time(),parent['hard_stop_monotonic']-time.monotonic())>5500
 barrier=c.load('v1607_single_round_remote_cleanup_barrier',C/'round_barrier.py')
 barrier_proof=barrier.before_next(parent,current_round=C.name)
 budget=c.load('v1607_full_budget',C/'budget.py');limits=budget.limits();storage=budget.preflight()
 storage['prior_round_upload_cleanup_barrier']=barrier_proof
 assert not(c.O/'ACTUAL_ONCE_CLAIM.json').exists()and not(c.O/'ROUND_WINDOW.json').exists()
 task=c.read(C/'TASKS.json')[0];out=Path(task['output']);assert not out.exists()
 saved=REVIEW.read_bytes();assert hashlib.sha256(saved).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 probe=json.loads(json.dumps(parent));probe['rounds'].append(dict(id=C.name,science=12,status='CLOSED_REFUSED_OR_FAILED',result='runs/'+C.name+'/first_event/COMPLETION.json'))
 assert len(parent_bytes(probe))+8192<=131072,'GOAL_BOUND_PARENT_CLOSE_HEADROOM'
 writers=c.load('v1607_owner_bounded_writes',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
 control=writers.WriterBudget(c.O,role='SUPERVISOR_LOG',maximum_bytes=2*1024**2,source_identity=c.digest(source))
 for _ in range(2):
  control.reserve_control(P,131072+8192);control.reserve_control(P.with_suffix('.json.tmp'),131072+8192)
 control.reserve_control(REVIEW,len(saved)+4096)
 control.reserve(c.O/'COMPLETION.json',131072)
 c.put(c.O/'REVIEW_PENDING.before.json',dict(hex=saved.hex(),sha256=hashlib.sha256(saved).hexdigest()))
 now=time.time();mono=time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+5400,hard_stop_monotonic=mono+5400,boot_id=parent['boot_id'])
 phase=c.load('v1607_original_stage_caps',c.R/'experiments/v1449_route_initializer_binding/phase_budget.py').PhaseBudget(window,limits)
 end=phase.boundary('normal')
 out.mkdir();c.put(c.O/'TASK.json',task,maximum=128*1024);c.put(out/'TASK.json',task,maximum=128*1024);c.put(c.O/'ROUND_WINDOW.json',window)
 claim=c.O/'ACTUAL_ONCE_CLAIM.json'
 with claim.open('x')as f:json.dump(dict(round_id=C.name,unix=now,storage=storage),f)
 a=dict(scope=limits['scope'],scientific_revision=12,round_id=C.name,physical_authorized=True,models_authorized=True,ROS_authorized=True,
  optimizer_authorized=False,whole_route_admission=False,repeat_authorized=False,window=window,limits=limits,
  boot_id=window['boot_id'],absolute_deadline_unix=window['absolute_deadline_unix'],hard_stop_monotonic=window['hard_stop_monotonic'],
  execution_deadline_unix=end['absolute_deadline_unix'],execution_deadline_monotonic=end['hard_stop_monotonic'],
  source_qualification_path=str((c.O/'ENTRY_QUALIFICATION.json').relative_to(c.R)),qualification_sha256=c.sha(c.O/'ENTRY_QUALIFICATION.json'),
  source_freeze_path=str((c.O/'SOURCE_FREEZE.json').relative_to(c.R)),source_freeze_sha256=c.sha(c.O/'SOURCE_FREEZE.json'),
  source_recovery_path=str((c.O/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(c.R)),once_claim_sha256=c.sha(claim),maximum_current_reserve_calls=8200)
 bootstrap=c.load('v1607_canonical_socket_source',C/'bootstrap_contract.py')
 a=bootstrap.factory_authority(a,task=task,output=out)
 c.put(c.O/'ACTUAL_ADMISSION.json',a);c.put(c.O/'APPROVAL.json',a);c.put(out/'APPROVAL.json',a);caps=c.read(C/'WRITER_CAPS.json')
 coverage=q['writer_source_coverage'];assert all(coverage[k]for k in caps)
 c.put(out/'EXTERNAL_WRITER_RESERVATIONS.json',dict(source_identity=a['qualification_sha256'],approval_sha256=c.sha(out/'APPROVAL.json'),
  writers={k:dict(maximum_bytes=v,source_hook_coverage_qualified=coverage[k])for k,v in caps.items()}))
 parent['rounds'].append(dict(id=C.name,science=12,status='RUNNING',started_unix=now,result=str((out/'COMPLETION.json').relative_to(c.R))))
 parent.update(active_round=C.name,models_now_authorized=True);parent['vehicle_task_starts']+=1;parent['navigation_prefix_task_starts']=parent.get('navigation_prefix_task_starts',0)+1
 # The activation write is inside the guarded lifecycle below.
 native=None;rosjob=None;identities={};streams={};children={};logs={};machine=None;rc=None;errors=[];first=None
 def metadata(path,value,maximum=65536):
  raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(raw)<=maximum
  control.reserve(path,2*len(raw)+16384);temporary=path.with_name(path.name+'.tmp');temporary.write_bytes(raw);temporary.replace(path)
 logwriter=None;poll=None
 def register(label,job):
  children[label]=dict(process=job,identity=None)
  identities[label]=owned_identity(job);children[label]['identity']=identities[label];os.set_blocking(job.stdout.fileno(),False)
  logs[label]=(out/(label+'.console')).open('xb');streams[label]=job
  poll.register(job.stdout,selectors.EVENT_READ,label)
  metadata(out/'OWNED_CHILDREN.json',identities)
 def drain(timeout=.05):
  for key,_ in poll.select(timeout):
   block=os.read(key.fileobj.fileno(),16384);label=key.data
   if not block:poll.unregister(key.fileobj);continue
   logwriter.reserve(out/(label+'.console'),len(block));logs[label].write(block);logs[label].flush()
 def check():
  assert time.time()<window['absolute_deadline_unix']and time.monotonic()<window['hard_stop_monotonic'],'ACTUAL_OWNER_ROOT_STOP'
 closer=c.load('v1607_explicit_close_transaction',C/'close.py')
 accounting=c.load('v1607_exact_unknown_accounting',C/'accounting.py')
 try:
  temporary=P.with_suffix('.json.tmp');temporary.write_bytes(parent_bytes(parent));temporary.replace(P)
  logwriter=writers.WriterBudget(out,role='SUPERVISOR_LOG',maximum_bytes=caps['SUPERVISOR_LOG'],source_identity=a['qualification_sha256'])
  poll=selectors.DefaultSelector()
  REVIEW.unlink()
  e=bootstrap.environment(source)
  native=subprocess.Popen(['ionice','-c','3','taskset','-c','2',str(c.R/'run_phase.sh'),str((C/'native_entry.py').relative_to(c.R)),str(out/'TASK.json')],cwd=c.R,env=e,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True);register('native',native)
  startup=c.load('v1607_exact_ready_close',c.R/'experiments/v1479_retirement_scope_binding/startup.py')
  ready_end=time.monotonic()+180
  while not(out/'CANONICAL_T0_READY.json').exists():
   check();drain();assert native.poll()is None and time.monotonic()<ready_end,'CANONICAL_READY_MISSING'
  startup.verify_ready(out,run_id=task['run_id'],source_identity=a['qualification_sha256'])
  helper=c.load('v1607_exact_ROS_network',c.R/'experiments/v1396_rpp_rpc_retirement/peer_environment.py')
  ros,rosenv=helper.environment(out);rosenv.update(PHASE_BOUNDED_TASK_OUTPUT=str(out),PHASE_BOUNDED_WRITER_ROLE='ACTUAL_ROS',PHASE_BOUNDED_SOURCE_ID=a['qualification_sha256'])
  rosjob=subprocess.Popen(ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'route_ros.py'),str(out/'TASK.json')]),cwd=c.R,env=rosenv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True);register('ros',rosjob)
  while native.poll()is None:
   check();drain()
   failure=startup.unexpected_ROS_failure(out,task['run_id'])
   if failure is not None:raise RuntimeError('ACTUAL_ROS_FAILED:'+str(failure))
   if rosjob.poll()is not None and not(out/'ROS_RESULT.json').exists():raise RuntimeError('ACTUAL_ROS_EXITED_WITHOUT_RESULT')
  rc=native.returncode;drain(0);machine=c.read(out/'RESULT.json')
  assert rosjob.poll()is not None,'ROS_NOT_CLOSED_AFTER_NATIVE'
 except BaseException as error:
  first=repr(error);errors.append(dict(stage='ONCE_OWNER',first_error=first,traceback=traceback.format_exc()))
  if native is not None and native.poll()is None:
   try:
    startup=c.load('v1607_cooperative_native_stop',c.R/'experiments/v1479_retirement_scope_binding/startup.py')
    startup.request_native_stop(out,run_id=task['run_id'],source_identity=a['qualification_sha256'],error=first,atomic=lambda p,v:c.put(p,v))
    stop_end=min(time.monotonic()+200,window['hard_stop_monotonic'])
    while native.poll()is None and time.monotonic()<stop_end:drain();check()
   except BaseException as close:errors.append(dict(stage='COOPERATIVE_NATIVE_CLOSE',error=repr(close)))
 finally:
  def close_child(item):
   job=item['process']
   if job.poll()is not None:return job.returncode
   identity=item['identity']
   if identity is None:
    identity=owned_identity(job);assert identity['pgid']==job.pid
    item['identity']=identity
   return close_owned(job,identity)
  def child_closed(item):
   job=item['process']
   if job.poll()is None:return False
   identity=item['identity']
   pgid=job.pid if identity is None else identity['pgid']
   try:os.killpg(pgid,0)
   except ProcessLookupError:return True
   return False
  def drain_closed():
   if poll is None:return
   # Every drain() already limits one read to16KiB and charges the original
   # writer. Bound closure independently of a missing EOF or broken selector.
   for _ in range(1024):
    if not poll.get_map():return
    drain(0)
   raise RuntimeError('OWNER_CLOSE_PIPE_EOF_OR_BYTE_CAP_UNPROVEN')
  def close_logs():
   failures=[]
   for label,stream in logs.items():
    try:stream.close()
    except BaseException as error:failures.append(dict(label=label,error=repr(error)))
   if poll is not None:
    try:poll.close()
    except BaseException as error:failures.append(dict(selector=repr(error)))
   if failures:raise RuntimeError(failures)
  def idle():
   with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   return True
  def restore():
   assert hashlib.sha256(saved).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
   REVIEW.write_bytes(saved)
  def close_parent(snapshot):
   latest=c.read(P)
   updated,counts=accounting.apply_closed(latest,round_id=C.name,machine=snapshot['machine'],
    result_path=str((out/'COMPLETION.json').relative_to(c.R)),close_errors=snapshot['errors'])
   # Snapshot and candidate are bounded before either parent byte is changed.
   assert len(parent_bytes(updated))+8192<=131072,'CLOSING_PARENT_HEADROOM'
   temporary=P.with_suffix('.json.tmp');temporary.write_bytes(parent_bytes(updated));temporary.replace(P)
   return True
  def save_close(kind,value):
   metadata(out/('OWNER_CLOSE_'+kind+'.json'),value,maximum=128*1024)
  result=closer.close_owner(children=children,close_child=close_child,child_closed=child_closed,
   drain=drain_closed,close_logs=close_logs,read_machine=lambda:c.read(out/'RESULT.json')if(out/'RESULT.json').exists()else None,
   restore_review=restore,verify_review=lambda:REVIEW.read_bytes()==saved,verify_lock_idle=idle,
   save_receipt=save_close,close_parent=close_parent,first_error=first,prior_errors=errors)
  machine=result['machine'];rc=None if native is None else native.returncode
  closed=dict(passed=False,closed=result['closed'],runtime_candidate_passed=runtime_passed(rc,machine,result['errors'])and result['close_complete'],
   scientific_acceptance_pending_closed_review=True,first_error=result['first_error'],secondary_errors=result['errors'],
   native_returncode=rc,native_counts=accounting.summary(machine),native_counts_unknown=result['machine_counts_unknown'],
   whole_route_passed=False,pair_unexecuted=True,review_original_restored=result['review_original_restored'],
   owner_close_complete=result['close_complete'],result_path=str((out/'RESULT.json').relative_to(c.R)))
  try:metadata(out/'COMPLETION.json',closed,maximum=128*1024)
  except BaseException as error:
   closed['owner_close_complete']=False
   closed['secondary_errors'].append(dict(stage='SAVE_COMPLETION',error=repr(error),traceback=traceback.format_exc()))
   if closed['first_error']is None:closed['first_error']=repr(error)
   # A distinct bounded stderr record is the final fallback. Never change
   # the primary error or claim a failed metadata write was persisted.
   raw=json.dumps(closed,allow_nan=False).encode()
   if len(raw)>65500:
    raw=json.dumps(dict(owner_completion_save_gap=True,unpersisted_json_sha256=hashlib.sha256(raw).hexdigest(),
     first_error_prefix=repr(closed['first_error'])[:4000],first_error_complete_in_fallback=False,
     secondary_error_count=len(closed['secondary_errors']),passed=False,models_not_restarted=True),allow_nan=False).encode()
   os.write(2,raw+b'\n')

 return closed


if __name__=='__main__':
 assert sys.argv[1:]==['--launch'];print(json.dumps(launch(),allow_nan=False))
