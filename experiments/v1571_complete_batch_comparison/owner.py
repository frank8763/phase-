"""Bounded CPU5 once supervisor, CPU2 run_phase analytical child only."""
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
s=importlib.util.spec_from_file_location('v1509_owner_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
P=c.R/'runs/v1382_weekend_campaign/LEDGER.json';REVIEW=c.R/'REVIEW_PENDING'

def parent_bytes(value,maximum=131072):
 raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()+b'\n';assert len(raw)<=maximum,'PARENT_CONTROL_SERIALIZED_CAP';return raw

def work_unknown(machine):
 if not isinstance(machine,dict):return True
 return (type(machine.get('CPP_analytical_native'))is not int or
  type(machine.get('Engine_constructions'))is not int or
  machine.get('CPP_inflight_unknown')is not False or
  'construction_inflight'not in machine or machine['construction_inflight']is not None)

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

def reserve_parent_budget(writer,original,limits):
 # Prepay all close controls before the child. Logs can never consume this hold.
 control_max=131072
 for _ in range(2):
  writer.reserve_control(P,control_max+8192);writer.reserve_control(P.with_suffix('.json.tmp'),control_max+8192)
 writer.reserve_control(REVIEW,len(original)+4096)
 prepaid={'NUMERIC_ONCE_CLAIM.json':4096,'ROUND_WINDOW.json':4096,'FULL_CPP_BATCH_ADMISSION.json':4096,'OWNED_CHILD.json':4096,'COMPLETION.json':32768,'RESULT.json':65536}
 for name,maximum in prepaid.items():writer.reserve(writer.output/name,maximum+8192)
 writer.reserve(writer.output/'numeric.console',limits['parent_stdout_bytes']+8192)
 return prepaid

def runtime_passed(returncode,machine,secondary):
 if type(returncode)is not int or returncode!=0 or not isinstance(machine,dict):return False
 if machine.get('closed')is not True or machine.get('passed')is not True:return False
 if 'first_error'not in machine or machine['first_error']is not None or machine.get('secondary_errors')!=[]or secondary:return False
 if work_unknown(machine):return False
 if type(machine.get('CPP_analytical_native'))is not int or machine['CPP_analytical_native']!=1263600:return False
 if type(machine.get('Engine_constructions'))is not int or machine['Engine_constructions']!=1:return False
 count=machine.get('accounting',{}).get('stages',{}).get('CPP_AUDIT',{})
 expected=dict(nominal_native=13600,witness_native=1250000,copy=562,batch_calls=562,batch_native=1235838,native=1263600)
 if any(type(count.get(k))is not int or count[k]!=v for k,v in expected.items()):return False
 if not machine.get('saved_reference_is_development_input'):return False
 return all(type(machine.get(k))is int and machine[k]==0 for k in ['python_generation_native','physical_native','replay_native','optimizer_calls','physical_capture_native'])

def launch():
 import fcntl
 assert sorted(os.sched_getaffinity(0))==[5]and time.time()+30<c.limits()['root_deadline_unix']
 assert not(c.O/'NUMERIC_ONCE_CLAIM.json').exists();qualified=c.read(c.O/'ENTRY_QUALIFICATION.json');assert qualified['passed'];source=c.sources();identity=c.digest(source);current,setup=c.inputs();limits=c.limits();recovery=c.read(c.O/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['source_freeze_sha256']==c.sha(c.O/'SOURCE_FREEZE.json')and recovery['all_frozen_members_remote_chain_covered']and recovery['uncovered_members']==[]
 parent=c.read(P);assert len(parent_bytes(parent))+8192<=131072,'PARENT_LEDGER_CLOSE_BOUND_REFUSED';assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']and len(parent['rounds'])<48 and parent['scientific_revisions']==10
 # The original compact parent denominator/authority fields are preserved.
 # Reserve the next round and its compact closing reference before claiming.
 parent_probe=json.loads(json.dumps(parent))
 parent_probe['rounds'].append(dict(id=C.name,scope=limits['scope'],started_unix=time.time(),
  status='CLOSED_REFUSED_OR_FAILED',models_actual_vehicle=0,physical_native=0,
  maximum_generation_native=0,success_only_maximum_audit_native=1263600,science_revision=10,
  result=dict(passed=False,CPP_native=1263600,model_work_unknown=True,Engine=1,
   result_path=str((c.O/'COMPLETION.json').relative_to(c.R)),physical_native=0)))
 assert len(parent_bytes(parent_probe))+8192<=131072,'CPP_COMPARISON_PARENT_CLOSE_RESERVE'
 original=REVIEW.read_bytes();assert c.sha(REVIEW)=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 before=c.usage();extra=sum(limits[k]for k in ['evidence_bytes','archive_bytes','download_bytes','root_reserve_bytes']);assert before+extra<10*1024**3,'CANONICAL_WITNESS_FULL_STORAGE_PEAK_REFUSED'
 writer_module=c.load('v1509_parent_original_budget',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');writer=writer_module.WriterBudget(c.O,role='SUPERVISOR_LOG',maximum_bytes=limits['parent_writer_bytes'],source_identity=identity)
 prepaid=reserve_parent_budget(writer,original,limits);control_max=131072
 def metadata(name,value):c.put(c.O/name,value,prepaid[name])
 def parent_put(value):
  raw=parent_bytes(value,control_max);temporary=P.with_suffix('.json.tmp');temporary.write_bytes(raw);temporary.replace(P)
 start=time.monotonic();unix=time.time();end=min(start+limits['round_s'],parent['hard_stop_monotonic'],start+limits['root_deadline_unix']-unix);wall=min(unix+limits['round_s'],limits['root_deadline_unix'])
 authority=dict(scope=limits['scope'],round_id=C.name,models_authorized=True,physical_authorized=False,optimizer_authorized=False,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),source_manifest_sha256=identity,current_input_sha256=current['response_method_sha256'],scientific_revision=10,absolute_deadline_unix=wall,hard_stop_monotonic=end)
 authority.update(generation_native_cap=0,success_only_CPP_audit_cap=limits['CPP_native'],model_writer_bytes=limits['model_writer_bytes'],parent_writer_bytes=limits['parent_writer_bytes'],source_freeze_sha256=c.sha(c.O/'SOURCE_FREEZE.json'),limits_sha256=c.sha(C/'LIMITS.json'),replay_authorized=False,initialization_deadline_unix=min(unix+limits['initialization_s'],wall-limits['closure_reserve_s']),initialization_deadline_monotonic=min(start+limits['initialization_s'],end-limits['closure_reserve_s']))
 reference=c.R/'runs/v1563_lzma_lossless_witness/model/generation'
 authority.update(CPP_native_cap=1263600,maximum_batch_calls=562,exact_zero_batch_native=2199,
  generation_authorized=False,live_reserve_authorized=False,
  saved_reference_sha256={name:c.sha(reference/name)for name in ['GENERATION.json','STREAM_SEAL.json','WITNESSES.bin']},
  audit_deadline_unix=min(unix+limits['audit_s'],wall-limits['closure_reserve_s']),
  audit_deadline_monotonic=min(start+limits['audit_s'],end-limits['closure_reserve_s']))
 # The audit deadline is conservatively measured from launch and includes
 # initialization; the CPP phase can never receive >2300seconds.
 with(c.O/'NUMERIC_ONCE_CLAIM.json').open('x')as file:json.dump(dict(started_unix=unix,models_physical=0,authority=authority),file)
 task=c.O/'model';proc=None;proc_identity=None;rc=None;first=None;secondary=[];total=0;machine=None
 try:
  metadata('ROUND_WINDOW.json',dict(scope=limits['scope'],started_unix=unix,started_monotonic=start,absolute_deadline_unix=wall,hard_stop_monotonic=end,allruns_before_bytes=before,full_reserved_peak_bytes=before+extra,storage_limit_bytes=10*1024**3,limits=limits));metadata('FULL_CPP_BATCH_ADMISSION.json',authority)
  task.mkdir()
  with(c.R/'runs/v648_static_unknown/execution.lock').open()as transition:
   fcntl.flock(transition,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=c.read(P);assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
   parent['active_round']=C.name;parent['models_now_authorized']=True;parent['rounds'].append(dict(id=C.name,scope=limits['scope'],started_unix=unix,status='ACTIVE',models_actual_vehicle=0,physical_native=0,maximum_generation_native=0,success_only_maximum_audit_native=limits['CPP_native'],science_revision=10));parent_put(parent)
  REVIEW.unlink();env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',PYTHONDONTWRITEBYTECODE='1')
  command=['ionice','-c','3','taskset','-c','2','nice','-n','19','./run_phase.sh',str((C/'driver.py').relative_to(c.R))]
  proc=subprocess.Popen(command,cwd=c.R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  proc_identity=owned_identity(proc);assert proc_identity['pgid']==proc.pid
  metadata('OWNED_CHILD.json',dict(**proc_identity,command=command,source_manifest_sha256=identity))
  os.set_blocking(proc.stdout.fileno(),False);selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ)
  with(c.O/'numeric.console').open('xb')as output:
   while selector.get_map():
    if time.monotonic()>=end or time.time()>=wall:raise TimeoutError('CANONICAL_WITNESS_OWNER_ROOT_OR_ROUND_EXPIRED')
    for key,_ in selector.select(.2):
     block=os.read(key.fileobj.fileno(),16384)
     if not block:selector.unregister(key.fileobj);continue
     assert total+len(block)<=limits['parent_stdout_bytes'],'CANONICAL_WITNESS_PARENT_STDOUT_CAP'
     output.write(block);output.flush();total+=len(block)
   rc=proc.wait(timeout=5)
  selector.close();proc.stdout.close()
  result_path=task/'RESULT.json'if(task/'RESULT.json').exists()else c.O/'RESULT.json';machine=c.read(result_path);assert machine['closed'];first=machine.get('first_error')
 except BaseException as error:first=first or repr(error);secondary.append(traceback.format_exc())
 finally:
  if proc and proc.poll()is None:
   try:
    assert proc_identity is not None,'CPP_OWNED_CHILD_IDENTITY_MISSING'
    rc=close_owned(proc,proc_identity)
   except BaseException as error:secondary.append('owned_child_close:'+repr(error))
  try:REVIEW.write_bytes(original);assert c.sha(REVIEW)=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  except BaseException as error:secondary.append('review_restore:'+repr(error))
  if machine is None:
   result_path=task/'RESULT.json'if(task/'RESULT.json').exists()else c.O/'RESULT.json'
   if result_path.exists():
    try:machine=c.read(result_path)
    except BaseException as error:secondary.append('machine_result_read:'+repr(error))
  closed=dict(passed=runtime_passed(rc,machine,secondary),closed=True,returncode=rc,
   scope=limits['scope'],first_error=first,secondary_errors=secondary,machine_result_present=machine is not None,
   CPP_analytical_native=machine.get('CPP_analytical_native')if machine else None,
   Engine_constructions=machine.get('Engine_constructions')if machine else None,
   model_work_unknown=work_unknown(machine),
   models_physical=0,physical_native=0,optimizer_calls=0,ownreplay_native=0,python_generation_native=0,
   stdout_bytes=total,review_original_restored=c.sha(REVIEW)=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66',
   closed_unix=time.time(),wall_s=time.monotonic()-start,whole_route_passed=False,
   saved_reference_is_development_input=True)
  parent=c.read(P);owned=parent['active_round']==C.name
  summary=dict(passed=closed['passed'],CPP_native=closed['CPP_analytical_native'],
   model_work_unknown=closed['model_work_unknown'],Engine=closed['Engine_constructions'],
   result_path=str((c.O/'COMPLETION.json').relative_to(c.R)),physical_native=0)
  if owned:
   parent['active_round']=None;parent['models_now_authorized']=False
   record=next(v for v in parent['rounds']if v['id']==C.name)
   record.update(status='CLOSED_PASS'if closed['passed']else'CLOSED_REFUSED_OR_FAILED',result=summary)
  try:metadata('COMPLETION.json',closed)
  except BaseException as error:print('CANONICAL_WITNESS_OWNER_COMPLETION_SAVE_GAP:'+repr(error),flush=True)
  if owned:
   try:parent_put(parent)
   except BaseException as error:print('CANONICAL_WITNESS_PARENT_CLOSE_SAVE_GAP:'+repr(error),flush=True)
  with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 return closed
if __name__=='__main__':
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert sys.argv[1:]==['--launch']
 try:answer=launch()
 except BaseException as error:
  answer=dict(passed=False,closed=True,prelaunch_refused=True,first_error=repr(error),traceback=traceback.format_exc(),
   numeric_once_claim_present=(c.O/'NUMERIC_ONCE_CLAIM.json').exists(),
   owned_child_record_present=(c.O/'OWNED_CHILD.json').exists(),models_started=None)
  c.put(c.O/'PRELAUNCH_REFUSAL.json',answer)
 print(json.dumps(answer,allow_nan=False))
 raise SystemExit(0 if answer.get('passed')else 1)
