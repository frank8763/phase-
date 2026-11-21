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

def reserve_parent_budget(writer,original,limits):
 # Prepay all close controls before the child. Logs can never consume this hold.
 control_max=131072
 for _ in range(2):
  writer.reserve_control(P,control_max+8192);writer.reserve_control(P.with_suffix('.json.tmp'),control_max+8192)
 writer.reserve_control(REVIEW,len(original)+4096)
 prepaid={'NUMERIC_ONCE_CLAIM.json':4096,'ROUND_WINDOW.json':4096,'STOP_COMPONENT_ADMISSION.json':4096,'OWNED_CHILD.json':4096,'COMPLETION.json':32768,'RESULT.json':65536}
 for name,maximum in prepaid.items():writer.reserve(writer.output/name,maximum+8192)
 writer.reserve(writer.output/'numeric.console',limits['parent_stdout_bytes']+8192)
 return prepaid

def runtime_passed(returncode,machine,secondary):
 if type(returncode)is not int or returncode!=0 or not isinstance(machine,dict):return False
 if machine.get('closed')is not True or machine.get('passed')is not True:return False
 if 'first_error'not in machine or machine['first_error']is not None or machine.get('secondary_errors')!=[]or secondary:return False
 if any(machine.get(k)is not False for k in ['generation_inflight_unknown','audit_inflight_unknown']):return False
 if any(type(machine.get(k))is not int or machine[k]!=200 for k in ['generation_analytical_native','audit_analytical_native']):return False
 if any(type(machine.get(k))is not int or machine[k]!=1 for k in ['cpp_engine_constructions','python_predictor_constructions']):return False
 return all(type(machine.get(k))is int and machine[k]==0 for k in ['physical_native','ownreplay_native','optimizer_calls','nominal_native'])

def launch():
 import fcntl
 assert sorted(os.sched_getaffinity(0))==[5]and time.time()+30<c.limits()['root_deadline_unix']
 assert not(c.O/'NUMERIC_ONCE_CLAIM.json').exists();qualified=c.read(c.O/'ENTRY_QUALIFICATION.json');assert qualified['passed'];source=c.sources();identity=c.digest(source);current,setup=c.inputs();limits=c.limits();recovery=c.read(c.O/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['source_freeze_sha256']==c.sha(c.O/'SOURCE_FREEZE.json')and recovery['all_frozen_members_remote_chain_covered']and recovery['uncovered_members']==[]
 parent=c.read(P);assert len(parent_bytes(parent))+8192<=131072,'PARENT_LEDGER_CLOSE_BOUND_REFUSED';assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']and len(parent['rounds'])<48 and parent['scientific_revisions']==8
 original=REVIEW.read_bytes();assert c.sha(REVIEW)=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 before=c.usage();extra=sum(limits[k]for k in ['evidence_bytes','archive_bytes','download_bytes','root_reserve_bytes']);assert before+extra<10*1024**3,'STOP_COMPONENT_FULL_STORAGE_PEAK_REFUSED'
 writer_module=c.load('v1509_parent_original_budget',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');writer=writer_module.WriterBudget(c.O,role='SUPERVISOR_LOG',maximum_bytes=limits['parent_writer_bytes'],source_identity=identity)
 prepaid=reserve_parent_budget(writer,original,limits);control_max=131072
 def metadata(name,value):c.put(c.O/name,value,prepaid[name])
 def parent_put(value):
  raw=parent_bytes(value,control_max);temporary=P.with_suffix('.json.tmp');temporary.write_bytes(raw);temporary.replace(P)
 start=time.monotonic();unix=time.time();end=min(start+limits['round_s'],parent['hard_stop_monotonic'],start+limits['root_deadline_unix']-unix);wall=min(unix+limits['round_s'],limits['root_deadline_unix'])
 authority=dict(scope=limits['scope'],round_id=C.name,models_authorized=True,physical_authorized=False,optimizer_authorized=False,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),source_manifest_sha256=identity,current_input_sha256=current['method_input_sha256'],scientific_revision=8,absolute_deadline_unix=wall,hard_stop_monotonic=end)
 for key in ['maximum_nominal_native','generation_native','success_only_audit_native','model_writer_bytes','parent_writer_bytes']:authority[key]=limits[key]
 with(c.O/'NUMERIC_ONCE_CLAIM.json').open('x')as file:json.dump(dict(started_unix=unix,models_physical=0,authority=authority),file)
 task=c.O/'model';proc=None;rc=None;first=None;secondary=[];total=0;machine=None
 try:
  metadata('ROUND_WINDOW.json',dict(scope=limits['scope'],started_unix=unix,started_monotonic=start,absolute_deadline_unix=wall,hard_stop_monotonic=end,allruns_before_bytes=before,full_reserved_peak_bytes=before+extra,storage_limit_bytes=10*1024**3,limits=limits));metadata('STOP_COMPONENT_ADMISSION.json',authority)
  task.mkdir()
  with(c.R/'runs/v648_static_unknown/execution.lock').open()as transition:
   fcntl.flock(transition,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=c.read(P);assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
   parent['active_round']=C.name;parent['models_now_authorized']=True;parent['rounds'].append(dict(id=C.name,scope=limits['scope'],started_unix=unix,status='ACTIVE',models_actual_vehicle=0,physical_native=0,maximum_generation_native=limits['generation_native'],success_only_maximum_audit_native=limits['success_only_audit_native'],science_revision=8));parent_put(parent)
  REVIEW.unlink();env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',PYTHONDONTWRITEBYTECODE='1')
  command=['ionice','-c','3','taskset','-c','2','nice','-n','19','./run_phase.sh',str((C/'driver.py').relative_to(c.R))]
  proc=subprocess.Popen(command,cwd=c.R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True);metadata('OWNED_CHILD.json',dict(pid=proc.pid,pgid=proc.pid,command=command,source_manifest_sha256=identity,boot_id=authority['boot_id']))
  os.set_blocking(proc.stdout.fileno(),False);selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ)
  with(c.O/'numeric.console').open('xb')as output:
   while selector.get_map():
    if time.monotonic()>=end or time.time()>=wall:raise TimeoutError('STOP_COMPONENT_OWNER_ROOT_OR_ROUND_EXPIRED')
    for key,_ in selector.select(.2):
     block=os.read(key.fileobj.fileno(),16384)
     if not block:selector.unregister(key.fileobj);continue
     assert total+len(block)<=limits['parent_stdout_bytes'],'STOP_COMPONENT_PARENT_STDOUT_CAP'
     output.write(block);output.flush();total+=len(block)
   rc=proc.wait(timeout=5)
  selector.close();proc.stdout.close()
  result_path=task/'RESULT.json'if(task/'RESULT.json').exists()else c.O/'RESULT.json';machine=c.read(result_path);assert machine['closed'];first=machine.get('first_error')
 except BaseException as error:first=first or repr(error);secondary.append(traceback.format_exc())
 finally:
  if proc and proc.poll()is None:
   try:
    os.killpg(proc.pid,signal.SIGTERM)
    try:rc=proc.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);rc=proc.wait(timeout=5)
   except BaseException as error:secondary.append('owned_child_close:'+repr(error))
  try:REVIEW.write_bytes(original);assert c.sha(REVIEW)=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  except BaseException as error:secondary.append('review_restore:'+repr(error))
  if machine is None:
   result_path=task/'RESULT.json'if(task/'RESULT.json').exists()else c.O/'RESULT.json'
   if result_path.exists():
    try:machine=c.read(result_path)
    except BaseException as error:secondary.append('machine_result_read:'+repr(error))
  closed=dict(passed=runtime_passed(rc,machine,secondary),closed=True,returncode=rc,scope=limits['scope'],first_error=first,secondary_errors=secondary,machine_result_present=machine is not None,generation_analytical_native=machine.get('generation_analytical_native')if machine else None,audit_analytical_native=machine.get('audit_analytical_native')if machine else None,model_work_unknown=machine is None or bool(machine.get('generation_inflight_unknown')or machine.get('audit_inflight_unknown')or machine.get('cpp_engine_constructions')is None or machine.get('python_predictor_constructions')is None),models_physical=0,physical_native=0,optimizer_calls=0,ownreplay_native=0,stdout_bytes=total,review_original_restored=c.sha(REVIEW)=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66',closed_unix=time.time(),wall_s=time.monotonic()-start,whole_route_passed=False)
  closed['cpp_engine_constructions']=machine.get('cpp_engine_constructions')if machine else None;closed['python_predictor_constructions']=machine.get('python_predictor_constructions')if machine else None
  parent=c.read(P);owned=parent['active_round']==C.name
  summary={k:v for k,v in closed.items()if k not in {'first_error','secondary_errors'}};summary['first_error_excerpt']=None if first is None else str(first)[:1024];summary['full_result_path']=str((c.O/'COMPLETION.json').relative_to(c.R))
  if owned:
   parent['active_round']=None;parent['models_now_authorized']=False;record=next(v for v in parent['rounds']if v['id']==C.name);record.update(status='CLOSED_PASS'if closed['passed']else'CLOSED_REFUSED_OR_FAILED',result=summary);parent['latest_WE_current_origin_stop_component']=summary
  try:metadata('COMPLETION.json',closed)
  except BaseException as error:print('STOP_COMPONENT_OWNER_COMPLETION_SAVE_GAP:'+repr(error),flush=True)
  if owned:
   try:parent_put(parent)
   except BaseException as error:print('STOP_COMPONENT_PARENT_CLOSE_SAVE_GAP:'+repr(error),flush=True)
  with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 return closed
if __name__=='__main__':
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert sys.argv[1:]==['--launch'];print(json.dumps(launch(),allow_nan=False))
