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
phase_module=exact('v1437_supervisor_shared_phase_runtime',R/'experiments/v1449_route_initializer_binding/phase_runtime.py')
def env():
 e=dict(os.environ);e.update(CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'));e.pop('LD_PRELOAD',None);return e

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
 assert role in {'main','repeat'};q=budget.complete_admission();limits=read(C/'LIMITS.json');budget.limits_check(limits)
 parent=read(P);auth=read(R/'experiments/v1382_weekend_campaign/AUTHORIZATION.json');assert parent['active_round']is None and not parent['models_now_authorized']and len(parent['rounds'])<auth['maximum_rounds']and parent['vehicle_task_starts']<auth['maximum_vehicle_task_starts']and parent['scientific_revisions']==5
 assert min(parent['absolute_hard_stop_unix']-time.time(),parent['hard_stop_monotonic']-time.monotonic())>5500
 if role=='repeat':
  main=read(O/'main/COMPLETION.json');assert main['passed']and read(O/'main/INDEPENDENT_COMPLETE_AUDIT.json')['passed']and read(O/'main/FULL_REMOTE_VERIFIED.json')['passed']
  assert main['scientific_source_identity']==sha(O/'COMPLETE_INTEGRATED_ROUTE_QUALIFICATION.json')
 task=next(t for t in read(C/'TASKS.json')if t['task_id']==role);out=Path(task['output']);assert not out.exists(),'ORIGINAL_TASK_ALREADY_ATTEMPTED_NO_RELAUNCH'
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 storage=budget.storage_preflight(limits);saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
 out.mkdir();put(out/'LAUNCH_CLAIM.json',dict(once=True,unix=time.time(),original_task_role=role));put(out/'STORAGE_PREFLIGHT.json',storage);put(out/'TASK.json',task)
 if not(O/'REVIEW_PENDING.before').exists():(O/'REVIEW_PENDING.before').write_bytes(saved)
 else:assert(O/'REVIEW_PENDING.before').read_bytes()==saved
 now=time.time();mono=time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=min(now+5400,parent['absolute_hard_stop_unix']),hard_stop_monotonic=min(mono+5400,parent['hard_stop_monotonic']),boot_id=parent['boot_id']);put(O/'ROUND_WINDOW.json',window);put(out/'ROUND_WINDOW.json',window)
 round_id=C.name+'_'+role
 approval=dict(models_authorized=True,scope='ACTUAL_ROUTE_EVENT_WITNESS',round_id=round_id,qualification_sha256=sha(O/'COMPLETE_INTEGRATED_ROUTE_QUALIFICATION.json'),tested_source_hashes=q['tested_source_hashes'],allowed_task_ids=[role],**{k:window[k]for k in ['absolute_deadline_unix','hard_stop_monotonic','boot_id']});put(O/'APPROVAL.json',approval);put(out/'APPROVAL.json',approval)
 coverage=q['external_writer_hook_qualification'];assert set(coverage)=={'ACTUAL_ROS','MODELED_ROS','PLANNER','SUPERVISOR_LOG'}and all(coverage.values())
 caps=read(C/'WRITER_CAPS.json');assert sum(caps.values())<=64*1024**2
 put(out/'EXTERNAL_WRITER_RESERVATIONS.json',dict(source_identity=approval['qualification_sha256'],approval_sha256=sha(out/'APPROVAL.json'),whole_task_224MiB_storage_preflight=storage,writers={role:dict(maximum_bytes=cap,source_hook_coverage_qualified=coverage[role])for role,cap in caps.items()}))
 parent['rounds'].append(dict(id=round_id,kind='actual_original_WE_current_event_main_or_full_repeat',status='RUNNING',started_unix=now,hard_stop_unix=window['absolute_deadline_unix'],maximum_actual_native=40000,maximum_own_replay_native=40000,maximum_generation_native=8040000,maximum_independent_model_audit_native=8040000,maximum_current_reserve_analytical_native=8000000,scientific_revision=5,role=role,source_qualification_sha256=sha(O/'COMPLETE_INTEGRATED_ROUTE_QUALIFICATION.json')));parent.update(active_round=round_id,models_now_authorized=True,status='RUNNING_ORIGINAL_WE_CURRENT_EVENT_ROUTE');parent['vehicle_task_starts']+=1;put(P,parent)
 try:
  log=(out/'supervisor.console').open('x');job=subprocess.Popen([sys.executable,'-B',str(C/'supervisor.py'),'--work',role],cwd=R,env=env(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close();put(out/'SUPERVISOR_LAUNCH.json',dict(pid=job.pid,once=True,unix=now,models_in_supervisor=0))
 except BaseException as exc:
  parent=read(P);parent['rounds'][-1].update(status='CLOSED_LAUNCH_FAILURE',closed=True,passed=False,error=repr(exc),canonical_initializations=0,actual_native=0);parent.update(active_round=None,models_now_authorized=False);put(P,parent);raise
 print(json.dumps(dict(started=True,role=role,pid=job.pid)))

def _work(role):
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));out=O/role;task=read(out/'TASK.json');window=read(out/'ROUND_WINDOW.json');limits=read(C/'LIMITS.json');saved=(O/'REVIEW_PENDING.before').read_bytes();native=None;rosjob=None;logs=[];result=dict(closed=False,passed=False,role=role,independent_audit_unexecuted=True,pair_unexecuted=True,scientific_source_identity=sha(O/'COMPLETE_INTEGRATED_ROUTE_QUALIFICATION.json'))
 phases=phase_module.PhaseRuntime(window,limits,lambda value:put(out/'SUPERVISOR_PHASES.json',value))
 def stop(*_):raise TimeoutError('ROUTE_SUPERVISOR_HARD_STOP_SAVE_PREFIX')
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())-5))
 try:
  q=budget.complete_admission();assert all(sha(R/p)==h for p,h in q['tested_source_hashes'].items());budget.clocks(window,read(P),reserve_s=limits['finalization_reserve_s']);(R/'REVIEW_PENDING').unlink()
  log=(out/'native.console').open('x');logs.append(log);native=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'native_entry.py').relative_to(R)),str(out/'TASK.json')],cwd=R,env=dict(env(),PHASE_BOUNDED_TASK_OUTPUT=str(out),PHASE_BOUNDED_SOURCE_ID=read(O/'APPROVAL.json')['qualification_sha256']),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  helper=exact('v1427_actual_ROS_namespace_env',R/'experiments/v1396_rpp_rpc_retirement/peer_environment.py');ros,rosenv=helper.environment(out);rosenv.update(PHASE_BOUNDED_TASK_OUTPUT=str(out),PHASE_BOUNDED_WRITER_ROLE='ACTUAL_ROS',PHASE_BOUNDED_SOURCE_ID=read(O/'APPROVAL.json')['qualification_sha256'])
  log=(out/'ros.console').open('x');logs.append(log);rosjob=subprocess.Popen(ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'route_ros.py'),str(out/'TASK.json')]),cwd=R,env=rosenv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  put(out/'ACTIVE.json',dict(native_pid=native.pid,ros_wrapper_pid=rosjob.pid,scope='ONE_CANONICAL_PHYSICS_CPU2_PLUS_ISOLATED_ROS_CPU3',round_id=read(O/'APPROVAL.json')['round_id']))
  next_storage=0.
  while native.poll()is None:
   budget.clocks(window,read(P),reserve_s=5)
   if time.monotonic()>=next_storage:
    assert budget.allocated(R/'runs')+limits['remaining_archive_download_reserve_bytes']+limits['root_reserve_bytes']<limits['storage_limit_bytes'],'SUPERVISOR_ALL_RUNS_PEAK_STOP'
    assert budget.allocated(out)<limits['maximum_task_evidence_bytes'],'SUPERVISOR_TASK_EVIDENCE_CAP';next_storage=time.monotonic()+2
   if rosjob.poll()is not None and not(out/'ROS_RESULT.json').exists():raise RuntimeError('ACTUAL_ROS_EXIT_WITHOUT_COMPLETE_EVIDENCE')
   time.sleep(.2)
  result['native_returncode']=native.returncode;native=None
  # Native awaited cooperative ROS/controller close in the shared peer-close
  # stage before allocation/replay. Do not allocate a second120s close window.
  if rosjob.poll()is None:raise TimeoutError('ACTUAL_ROS_NOT_EXITED_AFTER_NATIVE_SHARED_CLOSE')
  result['ROS_returncode']=rosjob.returncode;rosjob=None;(R/'REVIEW_PENDING').write_bytes(saved)
  result['native']=read(out/'RESULT.json');result['ROS']=read(out/'ROS_RESULT.json')
  phases.budget.restore(read(out/'NATIVE_PHASES.json'))
  if result['native_returncode']==0 and result['native'].get('functional_passed')and result['native'].get('replay',{}).get('passed'):
   # No new model/replay here: pure recorded geometry/control/source auditCPU5.
   audit=exact('v1427_complete_recorded_route_audit',C/'audit.py');result['independent_audit_unexecuted']=False
   phases.transition('recorded_audit');proof=audit.audit(task);phases.check('recorded_audit')
   put(out/'INDEPENDENT_COMPLETE_AUDIT.json',proof);result['independent_audit']=proof
   if proof['passed']and role=='repeat':
    result['pair_unexecuted']=False
    phases.transition('main_repeat_pair');pair=audit.pair(O/'main',out);phases.check('main_repeat_pair')
    put(out/'COMPLETE_PAIR.json',pair);result['pair']=pair
   result['passed']=proof['passed']and(role=='main'or result.get('pair',{}).get('passed')is True)
 except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
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
   parent.update(active_round=None,models_now_authorized=False,status='ORIGINAL_WE_CURRENT_EVENT_TASK_CLOSED_REVIEW_REQUIRED');put(P,parent)
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
 p=argparse.ArgumentParser();p.add_argument('--launch',choices=['main','repeat']);p.add_argument('--work',choices=['main','repeat']);a=p.parse_args()
 if a.launch:launch(a.launch)
 elif a.work:work(a.work)
 else:raise SystemExit('Specify exactly one registered task; no implicit launch')
