"""One registered original-WE task owner; no launch without complete admission."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;P=R/'runs/v1382_weekend_campaign/LEDGER.json'

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,value):
 p=Path(p);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)
def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
budget=exact('v1427_supervisor_exact_budget',C/'budget.py')
startup=exact('v1479_actual_ready_and_stop_control',C/'startup.py')
phase_module=exact('v1437_supervisor_shared_phase_runtime',R/'experiments/v1449_route_initializer_binding/phase_runtime.py')
def env():
 e=dict(os.environ);e.update(CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'));e.pop('LD_PRELOAD',None);return e

def process_identity(pid):
 text=Path('/proc/'+str(pid)+'/stat').read_text();tail=text[text.rfind(')')+2:].split()
 return dict(pid=pid,start_ticks=int(tail[19]),pgid=os.getpgid(pid))

def close_recorded_process(record):
 pid=record['pid']
 try:current=process_identity(pid)
 except FileNotFoundError:return
 assert current==record and current['pgid']==pid,'OWNED_PROCESS_IDENTITY_CHANGED'
 os.killpg(pid,signal.SIGTERM);end=time.monotonic()+3
 while time.monotonic()<end:
  try:current=process_identity(pid)
  except FileNotFoundError:return
  assert current==record,'OWNED_PROCESS_REUSED_DURING_CLOSE';time.sleep(.02)
 os.killpg(pid,signal.SIGKILL)

def owner_failure_account(parent,round_id,errors,*,child_completion_exists):
 import copy
 value=copy.deepcopy(parent);row=next(x for x in value['rounds']if x['id']==round_id)
 row.update(status='CLOSED_OWNER_FAILURE',closed=True,passed=False,owner_errors=list(errors))
 if not child_completion_exists:row.update(actual_native=None,own_replay_native=None,canonical_initializations=None,accounting_unknown=True)
 value.update(active_round=None,models_now_authorized=False)
 return value

def terminate(job):
 if job is not None and job.poll()is None:
  os.killpg(job.pid,signal.SIGTERM)
  try:job.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(job.pid,signal.SIGKILL);job.wait(timeout=3)

@contextmanager
def stage_alarm(seconds,window):
 old_handler=signal.getsignal(signal.SIGALRM)
 def expired(*_):raise TimeoutError('BOUNDED_RECORDED_AUDIT_STAGE_EXPIRED')
 signal.signal(signal.SIGALRM,expired)
 signal.setitimer(signal.ITIMER_REAL,max(.001,min(seconds,window['absolute_deadline_unix']-time.time()-5,window['hard_stop_monotonic']-time.monotonic()-5)))
 try:yield
 finally:
  signal.signal(signal.SIGALRM,old_handler)
  signal.setitimer(signal.ITIMER_REAL,max(.001,min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())-5))

def cleanup_attempt(errors,stage,fn):
 try:return fn()
 except BaseException as exc:
  errors.append(dict(stage=stage,error=repr(exc)))
  return None

def launch(role):
 assert role=='first_event';q=budget.complete_admission();limits=read(C/'LIMITS.json');budget.limits_check(limits)
 budget.contract.verify_source_recovery(q['tested_source_hashes'])
 parent=read(P);auth=read(R/'experiments/v1382_weekend_campaign/AUTHORIZATION.json');assert parent['active_round']is None and not parent['models_now_authorized']and len(parent['rounds'])<auth['maximum_rounds']and parent['vehicle_task_starts']<auth['maximum_vehicle_task_starts']and parent['scientific_revisions']==5
 assert min(parent['absolute_hard_stop_unix']-time.time(),parent['hard_stop_monotonic']-time.monotonic())>5500
 task=next(t for t in read(C/'TASKS.json')if t['task_id']==role);out=Path(task['output']);assert not out.exists(),'ORIGINAL_TASK_ALREADY_ATTEMPTED_NO_RELAUNCH'
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 storage=budget.storage_preflight(limits);saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
 out.mkdir();put(out/'LAUNCH_CLAIM.json',dict(once=True,unix=time.time(),original_task_role=role));put(out/'STORAGE_PREFLIGHT.json',storage);put(out/'TASK.json',task)
 if not(O/'REVIEW_PENDING.before').exists():(O/'REVIEW_PENDING.before').write_bytes(saved)
 else:assert(O/'REVIEW_PENDING.before').read_bytes()==saved
 now=time.time();mono=time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=min(now+5400,parent['absolute_hard_stop_unix']),hard_stop_monotonic=min(mono+5400,parent['hard_stop_monotonic']),boot_id=parent['boot_id']);put(O/'ROUND_WINDOW.json',window);put(out/'ROUND_WINDOW.json',window)
 round_id=C.name+'_'+role
 approval=dict(models_authorized=True,scope='LIVE_FIRST_EVENT_RUNTIME_QUALIFICATION',whole_route_admission=False,round_id=round_id,qualification_sha256=sha(O/'LIVE_FIRST_EVENT_ONLY_ADMISSION.json'),tested_source_hashes=q['tested_source_hashes'],allowed_task_ids=[role],**{k:window[k]for k in ['absolute_deadline_unix','hard_stop_monotonic','boot_id']});put(O/'APPROVAL.json',approval);put(out/'APPROVAL.json',approval)
 coverage=q['external_writer_hook_qualification'];assert set(coverage)=={'ACTUAL_ROS','MODELED_ROS','PLANNER','SUPERVISOR_LOG'}and all(coverage.values())
 caps=read(C/'WRITER_CAPS.json');assert sum(caps.values())<=64*1024**2
 put(out/'EXTERNAL_WRITER_RESERVATIONS.json',dict(source_identity=approval['qualification_sha256'],approval_sha256=sha(out/'APPROVAL.json'),whole_task_224MiB_storage_preflight=storage,writers={role:dict(maximum_bytes=cap,source_hook_coverage_qualified=coverage[role])for role,cap in caps.items()}))
 parent['rounds'].append(dict(id=round_id,kind='actual_original_WE_partial_navigation_first_event_runtime_qualification',status='RUNNING',started_unix=now,hard_stop_unix=window['absolute_deadline_unix'],maximum_actual_native=40000,maximum_own_replay_native=40000,maximum_generation_native=1005000,maximum_independent_model_audit_native=1005000,maximum_current_reserve_analytical_native=8000000,scientific_revision=5,role=role,source_qualification_sha256=sha(O/'LIVE_FIRST_EVENT_ONLY_ADMISSION.json')));parent.update(active_round=round_id,models_now_authorized=True,status='RUNNING_ORIGINAL_WE_CURRENT_EVENT_ROUTE');parent['vehicle_task_starts']+=1;parent['navigation_prefix_task_starts']=parent.get('navigation_prefix_task_starts',0)+1;put(P,parent)
 # The once owner drains the actual supervisor stdout through the same
 # already reserved SUPERVISOR_LOG role. No detached unbounded log writer.
 job=None;owner_errors=[]
 try:
  writer=exact('v1479_parent_stdout_writer',C/'writer_budget.py').WriterBudget(out,role='SUPERVISOR_LOG',maximum_bytes=caps['SUPERVISOR_LOG'],source_identity=approval['qualification_sha256'])
  with(out/'supervisor.console').open('xb')as log:
   pipe=BoundedConsole(log,writer,out/'supervisor.console')
   job=subprocess.Popen([sys.executable,'-B',str(C/'supervisor.py'),'--work',role],cwd=R,env=env(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
   os.set_blocking(job.stdout.fileno(),False);put(out/'SUPERVISOR_LAUNCH.json',dict(pid=job.pid,once=True,unix=now,models_in_supervisor=0,bounded_parent_pipe=True))
   def drain():
    for _ in range(64):
     try:block=os.read(job.stdout.fileno(),16384)
     except BlockingIOError:break
     if not block:break
     pipe.feed(block)
   while job.poll()is None:
    assert min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())>0,'LIVE_EVENT_PARENT_ROOT_DEADLINE'
    drain();time.sleep(.05)
   drain();job.stdout.close()
   completion=read(out/'COMPLETION.json');assert completion['closed']and read(P)['active_round']is None
   put(out/'ONCE_OWNER_COMPLETION.json',dict(closed=True,supervisor_returncode=job.returncode,completion_passed=completion['passed'],stdout_bytes=pipe.charged,models_in_owner=0))
   return completion
 except BaseException as exc:
  owner_errors.append(dict(stage='LIVE_EVENT_ONCE_OWNER',error=repr(exc)))
 finally:
  if job is not None and job.poll()is None:
   try:terminate(job)
   except BaseException as exc:owner_errors.append(dict(stage='CLOSE_SUPERVISOR',error=repr(exc)))
  if owner_errors:
   # Unknown child state is never replaced by zero counts. Preserve the first
   # owner exception, any actual child record, and restoration/close errors.
   try:(R/'REVIEW_PENDING').write_bytes(saved)
   except BaseException as exc:owner_errors.append(dict(stage='RESTORE_REVIEW',error=repr(exc)))
   try:
    active=out/'ACTIVE.json'
    if active.exists():
     for process in read(active)['owned_process_identities']:close_recorded_process(process)
    current=owner_failure_account(read(P),round_id,owner_errors,child_completion_exists=(out/'COMPLETION.json').exists());put(P,current)
    put(out/'ONCE_OWNER_ERROR.json',dict(closed=True,passed=False,errors=owner_errors,existing_child_completion=(out/'COMPLETION.json').exists(),unknown_without_child_completion=not(out/'COMPLETION.json').exists(),review_original_restored=(R/'REVIEW_PENDING').read_bytes()==saved))
   except BaseException as exc:os.write(2,(json.dumps(dict(first_error=owner_errors[0],secondary_owner_save_error=repr(exc),evidence_gap=True))+'\n').encode())
 if owner_errors:raise RuntimeError('LIVE_EVENT_ONCE_OWNER_FAILED:'+repr(owner_errors))

class BoundedConsole:
 def __init__(self,stream,writer,path):self.stream=stream;self.writer=writer;self.path=Path(path);self.charged=0
 def feed(self,block):
  assert isinstance(block,bytes)
  self.writer.reserve(self.path,len(block));self.stream.write(block);self.stream.flush();self.charged+=len(block)

def _work(role):
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));out=O/role;task=read(out/'TASK.json');window=read(out/'ROUND_WINDOW.json');limits=read(C/'LIMITS.json');saved=(O/'REVIEW_PENDING.before').read_bytes();native=None;rosjob=None;logs=[];result=dict(closed=False,passed=False,role=role,independent_audit_unexecuted=True,pair_unexecuted=True,scientific_source_identity=sha(O/'LIVE_FIRST_EVENT_ONLY_ADMISSION.json'))
 phases=phase_module.PhaseRuntime(window,limits,lambda value:put(out/'SUPERVISOR_PHASES.json',value))
 def stop(*_):raise TimeoutError('ROUTE_SUPERVISOR_HARD_STOP_SAVE_PREFIX')
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())-5))
 try:
  q=budget.complete_admission();assert all(sha(R/p)==h for p,h in q['tested_source_hashes'].items());budget.clocks(window,read(P),reserve_s=limits['finalization_reserve_s']);(R/'REVIEW_PENDING').unlink()
  log=(out/'native.console').open('x');logs.append(log);native=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'native_entry.py').relative_to(R)),str(out/'TASK.json')],cwd=R,env=dict(env(),PHASE_BOUNDED_TASK_OUTPUT=str(out),PHASE_BOUNDED_SOURCE_ID=read(O/'APPROVAL.json')['qualification_sha256']),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  put(out/'ACTIVE.json',dict(native_pid=native.pid,ros_wrapper_pid=None,owned_process_identities=[process_identity(native.pid)],scope='CANONICAL_INITIALIZER_ONLY_BEFORE_ROS',round_id=read(O/'APPROVAL.json')['round_id']))
  ready=startup.wait_ready(out,task,read(O/'APPROVAL.json')['qualification_sha256'],native,window,maximum_s=limits['canonical_initializer_wall_cap_s'],check=lambda:budget.clocks(window,read(P),reserve_s=limits['finalization_reserve_s']))
  put(out/'CANONICAL_STARTUP_HANDOFF.json',dict(passed=True,current_ready=ready,ROS_started_after_real_t0=True,original_ROS45s_wait_unchanged=True,root_window_not_reset=True))
  helper=exact('v1427_actual_ROS_namespace_env',R/'experiments/v1396_rpp_rpc_retirement/peer_environment.py');ros,rosenv=helper.environment(out);rosenv.update(PHASE_BOUNDED_TASK_OUTPUT=str(out),PHASE_BOUNDED_WRITER_ROLE='ACTUAL_ROS',PHASE_BOUNDED_SOURCE_ID=read(O/'APPROVAL.json')['qualification_sha256'])
  log=(out/'ros.console').open('x');logs.append(log);rosjob=subprocess.Popen(ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'route_ros.py'),str(out/'TASK.json')]),cwd=R,env=rosenv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  put(out/'ACTIVE.json',dict(native_pid=native.pid,ros_wrapper_pid=rosjob.pid,owned_process_identities=[process_identity(native.pid),process_identity(rosjob.pid)],scope='ONE_CANONICAL_PHYSICS_CPU2_PLUS_ISOLATED_ROS_CPU3',round_id=read(O/'APPROVAL.json')['round_id']))
  next_storage=0.
  while native.poll()is None:
   budget.clocks(window,read(P),reserve_s=5)
   if time.monotonic()>=next_storage:
    assert budget.allocated(R/'runs')+limits['remaining_archive_download_reserve_bytes']+limits['root_reserve_bytes']<limits['storage_limit_bytes'],'SUPERVISOR_ALL_RUNS_PEAK_STOP'
    assert budget.allocated(out)<limits['maximum_task_evidence_bytes'],'SUPERVISOR_TASK_EVIDENCE_CAP';next_storage=time.monotonic()+2
   failure=startup.unexpected_ROS_failure(out,task['run_id'])
   if failure is not None:
    put(out/'FIRST_SAVED_ROS_FAILURE.json',failure);raise RuntimeError('ACTUAL_ROS_FAILED_WITH_SAVED_RESULT:'+str(failure['first_saved_ROS_error']))
   if rosjob.poll()is not None and not(out/'ROS_RESULT.json').exists():raise RuntimeError('ACTUAL_ROS_EXIT_WITHOUT_COMPLETE_EVIDENCE')
   time.sleep(.2)
  result['native_returncode']=native.returncode;native=None
  # Native awaited cooperative ROS/controller close in the shared peer-close
  # stage before allocation/replay. Do not allocate a second120s close window.
  if rosjob.poll()is None:raise TimeoutError('ACTUAL_ROS_NOT_EXITED_AFTER_NATIVE_SHARED_CLOSE')
  result['ROS_returncode']=rosjob.returncode;rosjob=None;(R/'REVIEW_PENDING').write_bytes(saved)
  result['native']=read(out/'RESULT.json');result['ROS']=read(out/'ROS_RESULT.json')
  phases.budget.restore(read(out/'NATIVE_PHASES.json'))
  if result['native_returncode']==0 and result['native'].get('runtime_component_passed')and result['native'].get('replay',{}).get('passed'):
   # No new model/replay here: pure recorded geometry/control/source auditCPU5.
   audit=exact('v1479_current_event_component_audit',C/'audit.py');result['independent_audit_unexecuted']=False
   phases.transition('recorded_audit');proof=audit.audit(task);phases.check('recorded_audit')
   put(out/'INDEPENDENT_COMPLETE_AUDIT.json',proof);result['independent_audit']=proof
   result['passed']=proof['passed'];result.update(whole_route_navigation_passed=False,partial_navigation_attempt=True,pair_unexecuted=True)
 except BaseException as exc:
  result.update(error=repr(exc),traceback=traceback.format_exc())
  if native is not None and native.poll()is None:
   try:
    startup.request_native_stop(out,run_id=task['run_id'],source_identity=read(O/'APPROVAL.json')['qualification_sha256'],error=result['error'],atomic=put)
    startup.wait_native_close(native,window,maximum_s=limits['cooperative_native_stop_wall_s'],check=lambda:budget.clocks(window,read(P),reserve_s=5))
   except BaseException as closing:result['native_cooperative_close_error']=repr(closing)
 finally:
  # Preserve the first error even when child closure, review restoration or
  # evidence writes fail. Every secondary failure is durably exposed if possible.
  errors=[]
  cleanup_attempt(errors,'ENTER_FINAL_METADATA_PHASE',lambda:phases.transition('final_metadata'))
  cleanup_attempt(errors,'CLOSE_NATIVE',lambda:terminate(native))
  cleanup_attempt(errors,'CLOSE_ROS',lambda:terminate(rosjob))
  for index,log in enumerate(logs):cleanup_attempt(errors,'CLOSE_LOG_'+str(index),log.close)
  cleanup_attempt(errors,'RESTORE_REVIEW_PENDING',lambda:(R/'REVIEW_PENDING').write_bytes(saved))
  cleanup_attempt(errors,'REMOVE_ACTIVE',lambda:(out/'ACTIVE.json').unlink(missing_ok=True))
  if(out/'RESULT.json').exists():
   value=cleanup_attempt(errors,'READ_NATIVE_RESULT',lambda:read(out/'RESULT.json'))
   if value is not None:result['native']=value
  restored=cleanup_attempt(errors,'CHECK_REVIEW_RESTORED',lambda:(R/'REVIEW_PENDING').read_bytes()==saved)
  result.update(closed=True,closed_unix=time.time(),review_pending_original_restored=restored,secondary_closure_errors=errors)
  if errors or restored is not True:result['passed']=False
  cleanup_attempt(errors,'SAVE_COMPLETION',lambda:put(out/'COMPLETION.json',result))
  def close_parent():
   parent=read(P);row=next(x for x in parent['rounds']if x['id']==C.name+'_'+role);native_result=result.get('native')or{}
   row.update(status='CLOSED',closed=True,passed=result['passed']and not errors,completion=str((out/'COMPLETION.json').relative_to(R)),actual_native=native_result.get('new_actual_native'),actual_inflight_unknown=native_result.get('actual_inflight_unknown',True),canonical_initializations=native_result.get('canonical_vehicle_initializations'),internal_factory_model_constructions=None,own_replay_native=native_result.get('own_replay_native'),generation_and_independent_model_audit=native_result.get('model_generation_and_audit_accounting'),current_reserve_analytical=native_result.get('current_reserve_accounting'),independent_allocator=native_result.get('independent_allocation'))
   parent['live_first_event_runtime_counts']=dict(round_id=C.name+'_'+role,partial_navigation_attempt=True,whole_route_navigation_passed=False,actual_native=native_result.get('new_actual_native'),own_replay_native=native_result.get('own_replay_native'),canonical_initializations=native_result.get('canonical_vehicle_initializations'),internal_factory_model_constructions=None,model_generation_and_independent_audit=native_result.get('model_generation_and_audit_accounting'),current_reserve=native_result.get('current_reserve_accounting'),independent_allocator=native_result.get('independent_allocation'))
   for dst,src in [('actual_total_native','new_actual_native'),('own_replay_native','own_replay_native')]:
    amount=native_result.get(src)
    if amount is None:parent['live_event_'+dst+'_additional_unknown']=True
    else:parent[dst]+=amount
   parent.update(active_round=None,models_now_authorized=False,status='LIVE_FIRST_EVENT_RUNTIME_CLOSED_REVIEW_REQUIRED');put(P,parent)
  cleanup_attempt(errors,'SAVE_PARENT_CLOSURE',close_parent)
  if errors:
   result['passed']=False
   cleanup_attempt(errors,'RESAVE_COMPLETION_WITH_GAPS',lambda:put(out/'COMPLETION.json',result))
   os.write(2,(json.dumps(dict(first_error=result.get('error'),secondary_closure_errors=errors,evidence_gap=True),allow_nan=False)+'\n').encode())
  cleanup_attempt(errors,'SAVE_SUPERVISOR_PHASE_ACCOUNTING',phases.finish)

def work(role):
 out=O/role;registry=read(out/'EXTERNAL_WRITER_RESERVATIONS.json')
 os.environ.update(PHASE_BOUNDED_TASK_OUTPUT=str(out),PHASE_BOUNDED_WRITER_ROLE='SUPERVISOR_LOG',PHASE_BOUNDED_SOURCE_ID=registry['source_identity'])
 writer=exact('v1432_supervisor_output_writer',C/'writer_budget.py').WriterBudget.from_environment()
 boundary=exact('v1432_supervisor_bounded_log_pipes',C/'bounded_io.py').OutputBoundary
 control_paths={R/'REVIEW_PENDING',R/'runs/v1382_weekend_campaign/LEDGER.json',R/'runs/v1382_weekend_campaign/LEDGER.json.tmp'}
 control_renames={(R/'runs/v1382_weekend_campaign/LEDGER.json.tmp',R/'runs/v1382_weekend_campaign/LEDGER.json')}
 def charge(path,size):return writer.reserve(path,size)if path.is_relative_to(out)else writer.reserve_control(path,size)
 with boundary(out,charge,control_paths=control_paths,control_renames=control_renames):return _work(role)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--launch',choices=['first_event']);p.add_argument('--work',choices=['first_event']);p.add_argument('--prepare-admission',action='store_true');a=p.parse_args()
 if a.prepare_admission:budget.contract.prepare_admission()
 elif a.launch:launch(a.launch)
 elif a.work:work(a.work)
 else:raise SystemExit('Specify exactly one registered task; no implicit launch')
