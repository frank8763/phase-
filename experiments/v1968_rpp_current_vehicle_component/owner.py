"""Once fresh canonical actual/replay component, original bounded closure."""
import fcntl,hashlib,json,os,selectors,signal,subprocess,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;SOURCE=R/'runs'/C.name;O=SOURCE
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def put(p,v):
 raw=json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(raw)<=1024**2
 p=Path(p);t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)

def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 ownerlock=(R/'runs/v1643_formal_parent_metadata/OWNER.lock').open();fcntl.flock(ownerlock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 started=time.monotonic();now=time.time()
 assert read(O/'SOURCE_QUALIFICATION.json')['passed']and read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 prior_closed=read(O/'PRIOR_CLOSED_BARRIERS.json');assert prior_closed['passed']
 for path,h in prior_closed['proof_paths_SHA256'].items():assert sha(R/path)==h
 assert not(O/'PILOT_ONCE_CLAIM.json').exists()and not(O/'COMPLETION.json').exists()
 review=R/'REVIEW_PENDING';original=review.read_bytes();assert sha(review)=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
 assert read(R/'runs/v1691_dwa_receding_navigation/POST_ROUND_STORAGE_BARRIER.json')['passed']
 assert read(R/'runs/v1834_teb_common_entry_gate/POST_ROUND_STORAGE_BARRIER.json')['passed']
 assert read(O/'SOURCE_QUALIFICATION.json')['passed']and read(O/'SOURCE_OUTER_CLOSED.json')['passed']
 recovery=read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and not recovery['uncovered_members']
 assert sha(R/recovery['full_remote_proof_path'])==recovery['full_remote_proof_sha256']and read(R/recovery['full_remote_proof_path'])['passed']
 frozen=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 usage=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);peak=usage+(224+240+32+512+4+2)*1024**2;assert peak<15*1024**3
 task=read(O/'PILOT_TASK.json');assert task['component_not_navigation']and task['maximum_control_native']==10 and task['native_limit']==60000
 original_task=read(R/'runs/v1639_original_evidence_stages/PILOT_TASK.json')
 for key in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction']:assert task[key]==original_task[key]
 out=Path(task['output']);out.mkdir(exist_ok=False)
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();window=dict(started_unix=now,started_monotonic=started,absolute_deadline_unix=now+5400,hard_stop_monotonic=started+5400,normal_end_unix=now+4200,boot_id=boot)
 put(O/'PILOT_ONCE_CLAIM.json',dict(unix=now,owner_pid=os.getpid(),development_navigation=False,component_only=True,common_method='RPP',common_task=None,not_formal_ablation_task=True,allruns_bytes=usage,full_reserved_peak_bytes=peak))
 put(O/'PILOT_WINDOW.json',window)
 admission=dict(scope='RPP_CURRENT_ORIGINAL_VEHICLE_INTERFACE_COMPONENT',models_authorized=True,assignment=task,source_freeze_sha256=sha(O/'SOURCE_FREEZE.json'),pilot_entry_sha256=sha(C/'pilot_entry.py'),pilot_owner_sha256=sha(C/'owner.py'),model_work_counter_scope='q1159 recovery subset only; full normal/static/FFI totals unknown',formal_results=False,common_algorithm_results=False,common_registry_sha256=sha(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json'),exposed_development_not_independent_benchmark=True)
 put(O/'PILOT_ADMISSION.json',admission);put(O/'APPROVAL.json',dict(models_authorized=True,absolute_deadline_unix=now+5400,allowed_task_ids=[task['task_id']],scope=admission['scope']))
 current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_RPP_CURRENT_INTERFACE_COMPONENT',models_now_authorized=True,active_round=C.name,active_run=str(out.relative_to(R)));put(R/'CURRENT_EXPERIMENT.json',current)
 result=dict(passed=False,closed=False,canonical_vehicle_initializations=None,actual_native=None,own_replay_native=None,first_error=None,secondary_errors=[],whole_navigation_passed=False,formal_assignments_executed=0)
 child=None;console=bytearray();restored=False;identity=None
 try:
  review.unlink();env=os.environ.copy();lib=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'
  env.update(LD_LIBRARY_PATH=str(lib),PYOPENGL_PLATFORM='osmesa',MUJOCO_GL='osmesa',CUDA_VISIBLE_DEVICES='',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',MESA_SHADER_CACHE_DISABLE='true')
  child=subprocess.Popen(['taskset','-c','2','nice','-n','19','ionice','-c','3','./run_phase.sh',str((C/'pilot_entry.py').relative_to(R))],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  stat=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split();identity=dict(pid=child.pid,pgid=os.getpgid(child.pid),start_ticks=stat[19],boot_id=boot,command=str((C/'pilot_entry.py').relative_to(R)));put(O/'OWNED_CHILD.json',identity)
  selector=selectors.DefaultSelector();selector.register(child.stdout,selectors.EVENT_READ)
  with(O/'pilot.console').open('xb')as log:
   while selector.get_map():
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<window['absolute_deadline_unix']and time.monotonic()<window['hard_stop_monotonic'],'OWNER_DUAL_CLOCK_ROOT_STOP'
    for key,_ in selector.select(.5):
     block=os.read(key.fileobj.fileno(),16384)
     if not block:selector.unregister(key.fileobj);continue
     assert len(console)+len(block)<=4*1024**2;console.extend(block);log.write(block);log.flush()
  child.wait(timeout=5);machine=read(out/'RESULT.json');allsource=all(sha(R/n)==h for n,h in frozen.items())
  result.update(machine_result_sha256=sha(out/'RESULT.json'),machine_passed=machine['passed'],whole_navigation_passed=machine['whole_navigation_passed'],canonical_vehicle_initializations=machine['canonical_vehicle_initializations'],actual_native=machine['new_actual_native'],own_replay_native=machine['own_replay_native'],machine_first_error=machine['first_error'],all_source_SHA_verified_after_child_exit=allsource,full_model_work_total_native=None,tracked_recovery_model_work=machine.get('model_work'),passed=bool(child.returncode==0 and machine['passed']and machine['closed']and machine['first_error']is None and not machine['secondary_errors']and machine['source_unchanged']and allsource))
 except BaseException as e:result['first_error']=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  if child is not None and child.poll()is None:
   try:
    stat=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split();assert stat[19]==identity['start_ticks']and os.getpgid(child.pid)==identity['pgid']
    os.killpg(identity['pgid'],signal.SIGTERM)
    try:child.wait(timeout=15)
    except subprocess.TimeoutExpired:os.killpg(identity['pgid'],signal.SIGKILL);child.wait(timeout=5)
   except BaseException as e:result['secondary_errors'].append(dict(stage='CHILD_CLOSE',error=repr(e)))
  idle=False
  try:
   with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);idle=True
  except BaseException as e:result['secondary_errors'].append(dict(stage='LOCK_NOT_IDLE',error=repr(e)))
  if(child is None or child.poll()is not None)and idle:
   try:
    review.write_bytes(original);assert review.read_bytes()==original;restored=True
    put(O/'APPROVAL.json',dict(models_authorized=False,closed=True));current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='RPP_CURRENT_INTERFACE_COMPONENT_CLOSED',models_now_authorized=False,active_round=None,active_run=None);put(R/'CURRENT_EXPERIMENT.json',current)
   except BaseException as e:result['secondary_errors'].append(dict(stage='RESTORE',error=repr(e)))
  if child is not None:result['returncode']=child.returncode
  result.update(closed=True,review_restored=restored,lock_idle=idle,wall_s=time.monotonic()-started)
  if result['first_error']or result['secondary_errors']or not restored:result['passed']=False
  put(O/'COMPLETION.json',result)
 print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
