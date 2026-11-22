"""Once CPU2 original-contract pilot with bounded pipe and independent closure."""
import fcntl,hashlib,json,os,selectors,signal,subprocess,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
O=R/'runs'/C.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def put(p,v):
 raw=json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(raw)<=1024**2
 t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)

def main():
 started=time.monotonic();now=time.time();root=now+5400
 assert read(R/'runs/v1620_mechanism_boundary/UNATTENDED_CONTINUATION_AUTHORIZATION_20261123.json')['overall_calendar_deadline_unix'] is None
 assert not(O/'PILOT_ONCE_CLAIM.json').exists()and not(O/'PILOT_WINDOW.json').exists()
 review=R/'REVIEW_PENDING';original=review.read_bytes();assert sha(review)=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']
 assert read(O/'SOURCE_QUALIFICATION.json')['passed']
 assert read(R/'runs/v1634_original_compiler_refusal_recovery/FULL_REMOTE_VERIFIED.json')['passed']and read(R/'runs/v1634_original_compiler_refusal_recovery/TRANSPORT_CLEANUP.json')['passed']
 barrier=read(R/'runs/v1632_original_pilot_resources/POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']
 for a,b in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:assert sha(R/barrier[a])==barrier[b]
 recovery=read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and not recovery['uncovered_members']
 freeze=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in freeze.items())
 delivery=R/'runs/v1637_cached_original_source_recovery';remote=read(delivery/'FULL_REMOTE_VERIFIED.json');assert remote['passed']and read(delivery/'TRANSPORT_CLEANUP.json')['passed']
 index=read(delivery/'ARCHIVE_INDEX.json');members={r['path']:r for r in index['files']}
 for p in [C/'owner.py',C/'pilot_entry.py']:assert members[str(p.relative_to(R))]['sha256']==sha(p)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 usage=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);peak=usage+(224+240+32+512+4)*1024**2
 assert peak<15*1024**3
 task=read(O/'PILOT_TASK.json');out=Path(task['output']);out.mkdir(exist_ok=False)
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 window=dict(started_unix=now,started_monotonic=started,absolute_deadline_unix=now+5400,hard_stop_monotonic=started+5400,normal_end_unix=now+4200,boot_id=boot)
 put(O/'PILOT_ONCE_CLAIM.json',dict(unix=now,owner_pid=os.getpid(),pilot=True,not_formal_task=True,allruns_bytes=usage,full_reserved_peak_bytes=peak))
 put(O/'PILOT_WINDOW.json',window)
 admission=dict(scope='ORIGINAL_V1281_CONTRACT_WE_PILOT',models_authorized=True,assignment=task,source_freeze_sha256=sha(O/'SOURCE_FREEZE.json'),pilot_entry_sha256=sha(C/'pilot_entry.py'),pilot_owner_sha256=sha(C/'owner.py'),model_work_counter_scope='q1159 recovery subset only; full normal/static/FFI totals unknown, not0',full_model_work_native_cap_known=False,all_model_work_wall_root_bounded=True,formal_results=False)
 put(O/'PILOT_ADMISSION.json',admission)
 put(O/'APPROVAL.json',dict(models_authorized=True,absolute_deadline_unix=now+5400,allowed_task_ids=[task['task_id']],scope='ORIGINAL_V1281_CONTRACT_WE_PILOT'))
 put(O/'EVALUATION_LEDGER.json',dict(status='ACTIVE_EXPOSED_OPERATIONAL_PILOT',active_round='pilot_WE_full',models_now_authorized=True,vehicle_start_attempts=1,formal_assignments_executed=0,source_recovery=str((delivery/'FULL_REMOTE_VERIFIED.json').relative_to(R)),root_stop_unix=root))
 current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_ORIGINAL_CONTRACT_WE_PILOT',models_now_authorized=True,active_round='v1636_pilot_WE_full',active_run=str(out.relative_to(R)),active_entrypoint=str((C/'pilot_entry.py').relative_to(R)));put(R/'CURRENT_EXPERIMENT.json',current)
 result=dict(passed=False,closed=False,canonical_vehicle_initializations=None,actual_native=None,own_replay_native=None,first_error=None,secondary_errors=[],formal_assignments_executed=0,original_contract=True)
 child=None;console=bytearray();cleared=False
 try:
  review.unlink();env=os.environ.copy();lib=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'
  env.update(LD_LIBRARY_PATH=str(lib),PYOPENGL_PLATFORM='osmesa',MUJOCO_GL='osmesa',CUDA_VISIBLE_DEVICES='',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',MESA_SHADER_CACHE_DISABLE='true')
  child=subprocess.Popen(['taskset','-c','2','nice','-n','19','ionice','-c','3','./run_phase.sh',str((C/'pilot_entry.py').relative_to(R))],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  identity=dict(pid=child.pid,pgid=os.getpgid(child.pid),start_ticks=Path('/proc',str(child.pid),'stat').read_text().split()[21],boot_id=boot,command=str((C/'pilot_entry.py').relative_to(R)))
  put(O/'OWNED_CHILD.json',identity);print(json.dumps(dict(started=True,owned_child=identity,window=window)),flush=True)
  selector=selectors.DefaultSelector();selector.register(child.stdout,selectors.EVENT_READ)
  with(O/'pilot.console').open('xb')as log:
   while selector.get_map():
    assert time.time()<window['absolute_deadline_unix']and time.monotonic()<window['hard_stop_monotonic'],'OWNER_DUAL_CLOCK_ROOT_STOP'
    for key,_ in selector.select(.5):
     block=os.read(key.fileobj.fileno(),16384)
     if not block:selector.unregister(key.fileobj);continue
     assert len(console)+len(block)<=4*1024**2,'OWNER_CONSOLE_CAP'
     console.extend(block);log.write(block);log.flush()
  child.wait(timeout=5);result['returncode']=child.returncode
  machine=read(out/'RESULT.json');allsource=all(sha(R/n)==h for n,h in freeze.items());result['all_source_SHA_verified_after_child_exit']=allsource;result.update(canonical_vehicle_initializations=machine['canonical_vehicle_initializations'],actual_native=machine['new_actual_native'],own_replay_native=machine['own_replay_native'],machine_result_sha256=sha(out/'RESULT.json'),machine_passed=machine['passed'],full_model_work_total_native=None,tracked_recovery_model_work=machine.get('model_work'),complete_runtime_qualified=bool(machine['passed']),passed=bool(child.returncode==0 and machine['passed']and machine['closed']and machine['first_error']is None and not machine['secondary_errors']and machine['source_unchanged']and allsource))
 except BaseException as error:result['first_error']=dict(error=repr(error),traceback=traceback.format_exc())
 finally:
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
    put(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
    put(O/'EVALUATION_LEDGER.json',dict(status='CLOSED_PILOT_REVIEW_AND_REMOTE_BACKUP_REQUIRED',active_round=None,models_now_authorized=False,vehicle_start_attempts=1,formal_assignments_executed=0))
    current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='ORIGINAL_CONTRACT_PILOT_CLOSED_REVIEW',models_now_authorized=False,active_round=None,active_run=None);put(R/'CURRENT_EXPERIMENT.json',current)
   except BaseException as error:result['secondary_errors'].append(dict(stage='RESTORE_AND_CLEAR',error=repr(error)))
  result.update(closed=True,review_restored=cleared,lock_idle=idle,wall_s=time.monotonic()-started,closed_unix=time.time())
  if child is not None:result['returncode']=child.returncode
  if result['first_error']or result['secondary_errors']or not cleared:result['passed']=False
  try:put(O/'COMPLETION.json',result)
  except BaseException:os.write(2,(json.dumps(result)+'\n').encode())
 print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
