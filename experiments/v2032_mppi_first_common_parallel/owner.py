"""Independent prospective CPU6 vehicle component; never mutates RPP owner."""
from context import R,C,O,read,put,sha
from pathlib import Path
import fcntl,json,os,selectors,signal,subprocess,time,traceback
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 lock=(O/'owner.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(O/'PILOT_ONCE_CLAIM.json').exists() and not(O/'OWNED_CHILD.json').exists() and not(O/'COMPLETION.json').exists()
 assert read(O/'SOURCE_QUALIFICATION.json')['passed'] and read(O/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
 recovery=read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed'] and recovery['all_frozen_members_remote_chain_covered']
 source=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in source.items())
 with(O/'execution.lock').open() as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 reserve=read(O/'JOINT_RESOURCE_RESERVATION.json');assert reserve['passed'] and reserve['joint_peak_bytes']<15*1024**3
 pre=R/reserve['RPP_prelaunch_path'];assert sha(pre)==reserve['RPP_prelaunch_sha256']
 extras=sum(p.lstat().st_blocks*512 for root in (R/'runs').glob('v20*') if root.name[:5]>='v2006' for p in root.rglob('*'))
 credit=read(R/'runs/v2030_closed_dwa_derived_cache_cleanup/RESULT.json');assert credit['passed']and credit['all_source_SHA_after'];freed=credit['freed_allocated_bytes'];assert read(pre)['complete_future_peak']+extras-freed+502*1024**2<15*1024**3,'PARALLEL_COMPONENT_JOINT_PEAK_REFUSED'
 task=read(O/'PILOT_TASK.json');assert not task['component_not_navigation'] and task['maximum_control_native']==57600 and task['stop_native']==2200
 registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');original=next(x['task']for x in registry['tasks']if x['task']['task_id']=='common_01')
 for key in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id']:assert task[key]==original[key]
 from parallel_events import register
 register(task,source_freeze_sha256=sha(O/'SOURCE_FREEZE.json'));out=Path(task['output']);out.mkdir(exist_ok=False)
 now=time.time();start=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 window=dict(started_unix=now,started_monotonic=start,absolute_deadline_unix=now+5400,hard_stop_monotonic=start+5400,normal_end_unix=now+4200,boot_id=boot)
 put(O/'PILOT_ONCE_CLAIM.json',dict(owner_pid=os.getpid(),unix=now,models=1,CPU=6,component_only=False,formal_tasks=1,joint_peak_bytes=read(pre)['complete_future_peak']+extras-freed+502*1024**2))
 put(O/'PILOT_WINDOW.json',window)
 put(O/'PILOT_ADMISSION.json',dict(scope='MPPI_CURRENT_COMMON_FULL_TASK',models_authorized=True,independent_parallel_owner=True,assignment=task,source_freeze_sha256=sha(O/'SOURCE_FREEZE.json'),pilot_entry_sha256=sha(C/'pilot_entry.py')))
 put(O/'APPROVAL.json',dict(models_authorized=True,allowed_task_ids=[task['task_id']],absolute_deadline_unix=now+5400,scope='MPPI_CURRENT_COMMON_FULL_TASK'))
 result=dict(passed=False,closed=False,first_error=None,secondary_errors=[],actual_native=None,own_replay_native=None,canonical_vehicle_initializations=None,whole_navigation_passed=False,formal_assignments_executed=1,internal_factory_model_constructions=None)
 child=None;identity=None;console=0
 try:
  env=dict(os.environ,LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',MESA_SHADER_CACHE_DISABLE='true')
  child=subprocess.Popen(['taskset','-c','6','nice','-n','19','ionice','-c','3','/usr/bin/python3','-B',str(C/'run_phase.py')],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  identity=dict(pid=child.pid,pgid=os.getpgid(child.pid),start_ticks=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=boot,CPU=6)
  put(O/'OWNED_CHILD.json',identity);sel=selectors.DefaultSelector();sel.register(child.stdout,selectors.EVENT_READ)
  with(O/'pilot.console').open('xb') as log:
   while sel.get_map():
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<window['absolute_deadline_unix'] and time.monotonic()<window['hard_stop_monotonic'],'COMPONENT_OWNER_DUAL_CLOCK_STOP'
    for key,_ in sel.select(.2):
     data=os.read(key.fileobj.fileno(),16384)
     if not data:sel.unregister(key.fileobj);continue
     console+=len(data);assert console<=4*1024**2,'COMPONENT_OWNER_CONSOLE_4MIB_CAP';log.write(data);log.flush()
  child.wait(timeout=5);m=read(out/'RESULT.json');all_source=all(sha(R/n)==h for n,h in source.items())
  result.update(machine_result_sha256=sha(out/'RESULT.json'),machine_first_error=m['first_error'],machine_secondary_errors=m['secondary_errors'],machine_passed=m['passed'],actual_native=m['new_actual_native'],own_replay_native=m['own_replay_native'],canonical_vehicle_initializations=m['canonical_vehicle_initializations'],all_source_SHA_after_child=all_source,independent_audit=m.get('independent_audit'),modelwork_subset=m.get('model_work'),parallel_resource_report=m.get('parallel_resource_report'),whole_navigation_passed=bool(m['whole_navigation_passed']),passed=bool(child.returncode==0 and m['passed'] and all_source))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if child is not None and child.poll()is None:
   assert Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19]==identity['start_ticks']
   os.killpg(identity['pgid'],signal.SIGTERM)
   try:child.wait(timeout=15)
   except subprocess.TimeoutExpired:os.killpg(identity['pgid'],signal.SIGKILL);child.wait(timeout=5)
  if child is not None:result['returncode']=child.returncode
  with(O/'execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  put(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
  result.update(closed=True,wall_s=time.monotonic()-start,independent_lock_idle=True,global_RPP_REVIEW_owner_lock_and_CURRENT_not_modified=True)
  put(O/'COMPLETION.json',result)
  from parallel_events import close
  close(result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
