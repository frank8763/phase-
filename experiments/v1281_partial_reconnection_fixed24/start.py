"""One independent3h root for fresh24 and fixed3 complete repeats."""
from campaign_context import *
from parent_gate import verify_parent

import subprocess,fcntl,signal

def validate_authorization(a):
 assert a['authorized']is True and a['scope']=='partial_reconnection_fixed24'
 assert a.get('user_approved')is True and a['scientific_revisions']==0 and a['window_seconds']==10800
 assert a['temporary_bytes']==8*1024**3 and a['previous_failed_windows_unchanged']
 assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 return 10800

def main():
 assert not(O/'ROUND_WINDOW.json').exists()and not(O/'LAUNCH_RECEIPT.json').exists()
 auth=read(O/'AUTHORIZATION.json');duration=validate_authorization(auth)
 assert auth.get('root_not_locked_yet',True)and source_ok()and sha(R/'REVIEW_PENDING')==GUARD
 assert read(O/'QUALIFICATION.json')['passed']and read(O/'ISOLATED_QUALIFICATION.json')['passed']
 assert read(R/'CURRENT_EXPERIMENT.json')['active_run']is None
 assert read(O/'NS_SOURCE_QUALIFICATION.json')['passed']and read(O/'EW_SOURCE_QUALIFICATION.json')['passed']
 parent=verify_parent();assert parent['passed']
 dump(O/'PARENT_GATE_AT_LAUNCH.json',parent)
 tasks=read(C/'TASKS.json');assert not any(Path(t['output']).exists()for t in tasks)
 f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
 assert used()+256*1024**2<LIMIT
 check=read(R/'runs/v1208_runtime_launch_environment/QUALIFICATION.json');lib=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu';assert check['passed']and sha(lib/'libOSMesa.so.8.0.0')==check['mesa_sha256']
 env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(lib),PYOPENGL_PLATFORM='osmesa',MUJOCO_GL='osmesa',CUDA_VISIBLE_DEVICES='',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 assert time.time()+duration<=1794963600.,'NIGHT_09_HARD_CEILING'
 guard=(R/'REVIEW_PENDING').read_bytes();(O/'GUARD.bin').write_bytes(guard);now=time.time();mono=time.monotonic()
 auth.update(root_not_locked_yet=False,absolute_ceiling_unix=now+duration,monotonic_ceiling=mono+duration,locked_unix=now);dump(O/'AUTHORIZATION.json',auth)
 dump(O/'ROUND_WINDOW.json',dict(version='V1281',window_seconds=duration,started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+duration,hard_stop_monotonic=mono+duration,boot_id=auth['boot_id'],previous_windows_unchanged=True,new_independent_window=True,parent_closed_run='V1280'))
 dump(O/'APPROVAL.json',dict(models_authorized=True,version='V1281',window_seconds=duration,stop_on_safety_evidence=True,automatic_new24=False,absolute_deadline_unix=now+duration,allowed_task_ids=[t['task_id']for t in tasks]))
 j=read(R/'CURRENT_EXPERIMENT.json');j.update(status='RUNNING_V1281_FRESH_FIXED24',active_run=str(O.relative_to(R)),active_entrypoint=str((C/'campaign.py').relative_to(R)),active_window=str((O/'ROUND_WINDOW.json').relative_to(R)),next_physical_authorized=True,automatic_additional_simulation=False,next_scope='Frozen WE V1218/NS V1246/EW V1271 temporal fallback science, fresh original24 t0 then all24main and fixed1/9/17 full repeats. No old confirmation or development imported. New independent3h;temporary8GiB;CPU2idle;no runtime tuning.');dump(R/'CURRENT_EXPERIMENT.json',j)
 child=None
 try:
  with(O/'campaign.console').open('x')as log:child=subprocess.Popen(['/usr/bin/taskset','-c','2','/usr/bin/nice','-n','19','/usr/bin/ionice','-c','3',sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
  receipt=dict(pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],absolute_deadline_unix=now+duration,offline_capable=True,new_independent_window=True);dump(O/'LAUNCH_RECEIPT.json',receipt)
  with(O/'watchdog.console').open('x')as log:w=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py')],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
  dump(O/'WATCHDOG_LAUNCH.json',dict(pid=w.pid,proc_start=Path('/proc',str(w.pid),'stat').read_text().split()[21]));print(json.dumps(receipt))
 except BaseException as exc:
  if child and child.poll()is None:os.killpg(child.pid,signal.SIGTERM)
  (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'START_ERROR.json',dict(error=repr(exc),counts_unknown=child is not None));raise
if __name__=='__main__':main()
