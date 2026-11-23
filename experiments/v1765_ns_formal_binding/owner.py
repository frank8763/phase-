"""Once registered original-contract phase assignment with bounded ownership."""
import fcntl,hashlib,json,os,selectors,signal,subprocess,time,traceback,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
SOURCE=R/'runs'/C.name
ROOT=R/'runs/v1643_formal_parent_metadata'
O=SOURCE
PARENT_USED=0
PARENT_CLOSED_USED=0
PARENT_CLOSING=False
PARENT_LIMIT=2*1024**2
PARENT_CLOSE_RESERVE=1024**2
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def put(p,v):
 global PARENT_USED,PARENT_CLOSED_USED
 raw=json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(raw)<=1024**2
 charge=2*len(raw)+8192
 if PARENT_CLOSING:
  assert PARENT_CLOSED_USED+charge<=PARENT_CLOSE_RESERVE,'FORMAL_PARENT_CLOSE_METADATA_CAP';PARENT_CLOSED_USED+=charge
 else:
  assert PARENT_USED+charge<=PARENT_LIMIT-PARENT_CLOSE_RESERVE,'FORMAL_PARENT_START_METADATA_CAP';PARENT_USED+=charge
 t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)

def main(assignment_id):
 global O,PARENT_CLOSING
 assert 'PHASE_FORMAL_ASSIGNMENT'not in os.environ
 spec=importlib.util.spec_from_file_location('v1642_pure_registry',C/'phase_contract.py');registry=importlib.util.module_from_spec(spec);spec.loader.exec_module(registry)
 selected=registry.select(read(ROOT/'TASKS_LOCKED.json'),assignment_id,ROOT);task=selected['task']
 scope_spec=importlib.util.spec_from_file_location('v1765_route_scope',C/'route_scope.py');route_scope=importlib.util.module_from_spec(scope_spec);scope_spec.loader.exec_module(route_scope)
 assert route_scope.qualified(task,selected['variant'])
 O=ROOT/'rounds'/assignment_id;O.mkdir(parents=True,exist_ok=True)
 assert not(O/'actual').exists()
 # Fixed registered order: every earlier assignment must close, upload, verify,
 # and perform exact eligible cleanup, including failed scientific outcomes.
 for previous in selected['registered_order'][:task['formal_order_index']]:
  barrier=read(ROOT/'rounds'/previous/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']
  for a,b in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:assert sha(R/barrier[a])==barrier[b]
 started=time.monotonic();now=time.time();root=now+5400
 assert read(R/'runs/v1620_mechanism_boundary/UNATTENDED_CONTINUATION_AUTHORIZATION_20261123.json')['overall_calendar_deadline_unix'] is None
 assert not(O/'ROUND_ONCE_CLAIM.json').exists()and not(O/'ROUND_WINDOW.json').exists()
 review=R/'REVIEW_PENDING';original=review.read_bytes();assert sha(review)=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']
 assert read(SOURCE/'SOURCE_QUALIFICATION.json')['passed']
 pilot=read(R/'runs/v1639_original_evidence_stages/COMPLETION.json');assert pilot['passed']and pilot['closed']and pilot['all_source_SHA_verified_after_child_exit']
 assert read(R/'runs/v1639_original_evidence_stages/RUNTIME_CLOSED_REVIEW.json')['independent_original_numeric_audit_passed']
 assert read(R/'runs/v1641_original_evidence_pilot_recovery/FULL_REMOTE_VERIFIED.json')['passed']and read(R/'runs/v1641_original_evidence_pilot_recovery/TRANSPORT_CLEANUP.json')['passed']
 barrier=read(R/'runs/v1639_original_evidence_stages/POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']
 for a,b in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:assert sha(R/barrier[a])==barrier[b]
 recovery=read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and not recovery['uncovered_members']
 freeze=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in freeze.items())
 remote=read(R/recovery['full_remote_proof_path']);assert sha(R/recovery['full_remote_proof_path'])==recovery['full_remote_proof_sha256']and remote['passed']
 assert sha(R/recovery['index_path'])==recovery['index_sha256'];index=read(R/recovery['index_path']);members={row['path']:row for row in index['files']}
 for p in [C/'owner.py',C/'entry.py']:assert members[str(p.relative_to(R))]['sha256']==sha(p)
 current_before=read(R/'CURRENT_EXPERIMENT.json');assert current_before.get('active_round')is None and not current_before['models_now_authorized']
 assert 4*len(json.dumps(current_before,sort_keys=True,separators=(',',':')).encode())+256*1024<PARENT_LIMIT,'PARENT_PRECHARGE_REFUSED'
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 usage=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);peak=usage+(224+240+32+512+4+2)*1024**2
 assert peak<15*1024**3
 result=dict(passed=False,closed=False,canonical_vehicle_initializations=None,actual_native=None,own_replay_native=None,first_error=None,secondary_errors=[],formal_assignments_executed=0,original_contract=True)
 child=None;console=bytearray();cleared=False
 try:
  put(O/'FORMAL_TASK.json',task);out=Path(task['output']);out.mkdir(exist_ok=False)
  boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  clock_spec=importlib.util.spec_from_file_location('v1744_conservative_clock',C/'clock_window.py');clock_module=importlib.util.module_from_spec(clock_spec);clock_spec.loader.exec_module(clock_module)
  window=clock_module.make_window(now,started,boot);root=window['absolute_deadline_unix']
  put(O/'ROUND_ONCE_CLAIM.json',dict(unix=now,owner_pid=os.getpid(),pilot=False,formal_assignment=True,assignment_id=assignment_id,allruns_bytes=usage,full_reserved_peak_bytes=peak))
  result['formal_assignments_executed']=1
  put(O/'ROUND_WINDOW.json',window)
  admission=dict(source_version_root=str(SOURCE.relative_to(R)),scope='ORIGINAL_V1281_NS_NEW_PHASE_FULL',models_authorized=True,assignment=task,source_freeze_sha256=sha(SOURCE/'SOURCE_FREEZE.json'),entry_sha256=sha(C/'entry.py'),owner_sha256=sha(C/'owner.py'),scientific_task_sha256=selected['scientific_task_sha256'],model_work_counter_scope='q1159 recovery subset only; full normal/static/FFI totals unknown, not0',full_model_work_native_cap_known=False,all_model_work_wall_root_bounded=True,formal_results=True)
  put(O/'FORMAL_ADMISSION.json',admission)
  put(O/'APPROVAL.json',dict(models_authorized=True,absolute_deadline_unix=now+5400,allowed_task_ids=[task['task_id']],scope='ORIGINAL_V1281_NS_NEW_PHASE_FULL'))
  put(O/'EVALUATION_LEDGER.json',dict(status='ACTIVE_REGISTERED_PHASE_COMPARISON',active_round=assignment_id,models_now_authorized=True,vehicle_start_attempts=1,formal_assignments_executed=1,source_recovery=recovery['full_remote_proof_path'],root_stop_unix=root))
  current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_REGISTERED_PHASE_COMPARISON',models_now_authorized=True,active_round='v1642_'+assignment_id,active_run=str(out.relative_to(R)),active_entrypoint=str((C/'entry.py').relative_to(R)));put(R/'CURRENT_EXPERIMENT.json',current)
  review.unlink();env=os.environ.copy();env['PHASE_FORMAL_ASSIGNMENT']=assignment_id;lib=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'
  env.update(LD_LIBRARY_PATH=str(lib),PYOPENGL_PLATFORM='osmesa',MUJOCO_GL='osmesa',CUDA_VISIBLE_DEVICES='',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',MESA_SHADER_CACHE_DISABLE='true')
  child=subprocess.Popen(['taskset','-c','2','nice','-n','19','ionice','-c','3','./run_phase.sh',str((C/'entry.py').relative_to(R))],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  identity=dict(pid=child.pid,pgid=os.getpgid(child.pid),start_ticks=Path('/proc',str(child.pid),'stat').read_text().split()[21],boot_id=boot,command=str((C/'entry.py').relative_to(R)))
  put(O/'OWNED_CHILD.json',identity);print(json.dumps(dict(started=True,owned_child=identity,window=window)),flush=True)
  selector=selectors.DefaultSelector();selector.register(child.stdout,selectors.EVENT_READ)
  with(O/'formal.console').open('xb')as log:
   while selector.get_map():
    assert time.time()<window['absolute_deadline_unix']and time.monotonic()<window['hard_stop_monotonic'],'OWNER_DUAL_CLOCK_ROOT_STOP'
    for key,_ in selector.select(.5):
     block=os.read(key.fileobj.fileno(),16384)
     if not block:selector.unregister(key.fileobj);continue
     assert len(console)+len(block)<=4*1024**2,'OWNER_CONSOLE_CAP'
     console.extend(block);log.write(block);log.flush()
  child.wait(timeout=5);result['returncode']=child.returncode
  allsource=all(sha(R/n)==h for n,h in freeze.items());result['all_source_SHA_verified_after_child_exit']=allsource
  machine=read(out/'RESULT.json');result.update(canonical_vehicle_initializations=machine['canonical_vehicle_initializations'],actual_native=machine['new_actual_native'],own_replay_native=machine['own_replay_native'],machine_result_sha256=sha(out/'RESULT.json'),machine_passed=machine['passed'],full_model_work_total_native=None,tracked_recovery_model_work=machine.get('model_work'),complete_runtime_qualified=bool(machine['passed']),passed=bool(child.returncode==0 and machine['passed']and machine['closed']and machine['first_error']is None and not machine['secondary_errors']and machine['source_unchanged']and allsource))
 except BaseException as error:result['first_error']=dict(error=repr(error),traceback=traceback.format_exc())
 finally:
  PARENT_CLOSING=True
  if child is not None and child.poll()is None:
   try:
    stat=Path('/proc',str(child.pid),'stat').read_text().split();assert stat[21]==identity['start_ticks']and os.getpgid(child.pid)==identity['pgid'];os.killpg(identity['pgid'],signal.SIGTERM)
    try:child.wait(timeout=15)
    except subprocess.TimeoutExpired:os.killpg(identity['pgid'],signal.SIGKILL);child.wait(timeout=5)
   except BaseException as error:result['secondary_errors'].append(dict(stage='OWNED_CHILD_CLOSE',error=repr(error)))
  idle=False
  try:
   with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);idle=True
  except BaseException as error:result['secondary_errors'].append(dict(stage='LOCK_NOT_IDLE',error=repr(error)))
  if (child is None or child.poll()is not None)and idle:
   try:
    review.write_bytes(original);assert review.read_bytes()==original;cleared=True
   except BaseException as error:result['secondary_errors'].append(dict(stage='RESTORE_REVIEW',error=repr(error)))
   try:put(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
   except BaseException as error:result['secondary_errors'].append(dict(stage='REVOKE_APPROVAL',error=repr(error)))
   try:put(O/'EVALUATION_LEDGER.json',dict(status='CLOSED_FORMAL_ASSIGNMENT_REVIEW_AND_REMOTE_BACKUP_REQUIRED',active_round=None,models_now_authorized=False,vehicle_start_attempts=int(child is not None),formal_assignments_executed=result['formal_assignments_executed']))
   except BaseException as error:result['secondary_errors'].append(dict(stage='CLOSE_ASSIGNMENT_LEDGER',error=repr(error)))
   try:
    current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REGISTERED_PHASE_ASSIGNMENT_CLOSED_REVIEW',models_now_authorized=False,active_round=None,active_run=None);put(R/'CURRENT_EXPERIMENT.json',current)
   except BaseException as error:result['secondary_errors'].append(dict(stage='CLEAR_CURRENT_AUTHORITY',error=repr(error)))
  result.update(closed=True,review_restored=cleared,lock_idle=idle,wall_s=time.monotonic()-started,closed_unix=time.time())
  if child is not None:result['returncode']=child.returncode
  if result['first_error']or result['secondary_errors']or not cleared:result['passed']=False
  try:put(O/'COMPLETION.json',result)
  except BaseException:os.write(2,(json.dumps(result)+'\n').encode())
 print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--assignment',required=True);args=parser.parse_args()
 with(ROOT/'OWNER.lock').open('a+')as owner_lock:
  fcntl.flock(owner_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  raise SystemExit(main(args.assignment))
