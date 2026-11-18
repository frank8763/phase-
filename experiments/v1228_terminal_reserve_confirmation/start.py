from campaign_context import *
import subprocess,fcntl,signal
CEILING=1794832200.
def validate_authorization(a):
 assert a['authorized']is True and a['scope']=='ns_current_state_repair_and_regression_then_conditional_fixed24'
 assert a['user_instruction']=='下一步开始，然后运行到今天晚上八点半' and a['scientific_revisions']==1 and a['no_replacements']and a['repeat_slots']==[1,9,17]
 assert a['temporary_bytes']==2*1024**3 and a['absolute_ceiling_unix']==CEILING
 assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 return min(CEILING-time.time(),a['monotonic_ceiling']-time.monotonic())
def main():
 assert not(O/'ROUND_WINDOW.json').exists()and not(O/'LAUNCH_RECEIPT.json').exists()
 duration=validate_authorization(read(O/'AUTHORIZATION.json'));assert duration>1900 and source_ok()and sha(R/'REVIEW_PENDING')==GUARD
 assert read(O/'QUALIFICATION.json')['passed']and read(O/'ISOLATED_QUALIFICATION.json')['passed']
 assert read(R/'runs/v1222_exact_stop_confirmation/FINALIZED.json')['manifest_readback']and read(R/'CURRENT_EXPERIMENT.json')['active_run']is None
 assert read(O/'INHERITED_ROUTE_GATE.json')['passed']
 tasks=read(C/'TASKS.json');assert not any(Path(t['output']).exists()for t in tasks)
 f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
 check=read(R/'runs/v1208_runtime_launch_environment/QUALIFICATION.json');lib=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu';assert check['passed']and sha(lib/'libOSMesa.so.8.0.0')==check['mesa_sha256']
 env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(lib),PYOPENGL_PLATFORM='osmesa',MUJOCO_GL='osmesa',CUDA_VISIBLE_DEVICES='',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 guard=(R/'REVIEW_PENDING').read_bytes();(O/'GUARD.bin').write_bytes(guard);now=time.time();mono=time.monotonic();duration=min(CEILING-now,read(O/'AUTHORIZATION.json')['monotonic_ceiling']-mono)
 dump(O/'ROUND_WINDOW.json',dict(version='V1228',window_seconds=duration,started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+duration,hard_stop_monotonic=mono+duration,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),previous_windows_unchanged=True))
 dump(O/'APPROVAL.json',dict(models_authorized=True,version='V1228',window_seconds=duration,stop_on_safety_evidence=True,automatic_new24=False,absolute_deadline_unix=now+duration,allowed_task_ids=[t['task_id']for t in tasks]))
 j=read(R/'CURRENT_EXPERIMENT.json');j.update(status='RUNNING_V1228_EXACT_FIXED24',active_run=str(O.relative_to(R)),active_entrypoint=str((C/'campaign.py').relative_to(R)),active_window=str((O/'ROUND_WINDOW.json').relative_to(R)),next_physical_authorized=True,automatic_additional_simulation=False,next_scope='NS current-state source: slot9 and original NS main/repeat first; unchanged WE/EW gates inherited explicitly, then conditional fixed24 from slot1;20:30 hardstop/2GiB.');dump(R/'CURRENT_EXPERIMENT.json',j)
 child=None
 try:
  with(O/'campaign.console').open('x')as log:child=subprocess.Popen(['/usr/bin/taskset','-c','2','/usr/bin/nice','-n','19','/usr/bin/ionice','-c','3',sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
  receipt=dict(pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],absolute_deadline_unix=now+duration,offline_capable=True);dump(O/'LAUNCH_RECEIPT.json',receipt)
  with(O/'watchdog.console').open('x')as log:w=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py')],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
  dump(O/'WATCHDOG_LAUNCH.json',dict(pid=w.pid,proc_start=Path('/proc',str(w.pid),'stat').read_text().split()[21]));print(json.dumps(receipt))
 except BaseException as exc:
  if child and child.poll()is None:os.killpg(child.pid,signal.SIGTERM)
  (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'START_ERROR.json',dict(error=repr(exc),counts_unknown=child is not None));raise
if __name__=='__main__':main()
