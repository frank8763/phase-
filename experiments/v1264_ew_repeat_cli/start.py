"""Lock a fresh bounded physical root once, after all zero-model gates."""
from campaign_context import *
import fcntl,subprocess,signal
def validate_authorization(a):
    assert a['authorized']is True and a['scope']=='EW_slot17_main_repeat_only'and a['user_approved']is True
    assert type(a['window_seconds'])is int and a['window_seconds']==5400 and a['scientific_revisions']==0
    assert a['temporary_bytes']==2*1024**3 and a['previous_failed_windows_unchanged']and a['automatic_new24']is False and a['stop_on_first_failure']is True
    assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    return 5400
def main():
    assert not(O/'ROUND_WINDOW.json').exists()and not(O/'LAUNCH_RECEIPT.json').exists()
    auth=read(O/'AUTHORIZATION.json');duration=validate_authorization(auth)
    assert auth['root_not_locked_yet']and source_ok()and sha(R/'REVIEW_PENDING')==GUARD
    assert all(read(O/name)['passed']for name in ['QUALIFICATION.json','ISOLATED_QUALIFICATION.json','LIVE_ADAPTER_QUALIFICATION.json','EW_SOURCE_QUALIFICATION.json','NATIVE_AUDIT_QUALIFICATION.json'])
    from inherited_gate import verify_parent_main
    verify_parent_main()
    assert read(R/'CURRENT_EXPERIMENT.json')['active_run']is None and used()+256*1024**2<LIMIT
    tasks=read(C/'TASKS.json');assert len(tasks)==1 and not any(Path(t['output']).exists()for t in tasks)
    for t in tasks:task_contract(t)
    f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
    check=read(R/'runs/v1208_runtime_launch_environment/QUALIFICATION.json');lib=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'
    assert check['passed']and sha(lib/'libOSMesa.so.8.0.0')==check['mesa_sha256']
    env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(lib),PYOPENGL_PLATFORM='osmesa',MUJOCO_GL='osmesa',CUDA_VISIBLE_DEVICES='',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'GUARD.bin').write_bytes(guard)
    parent_window=read(R/'runs/v1261_ew_reserved_validation/ROUND_WINDOW.json');now=parent_window['started_unix'];mono=parent_window['started_monotonic']
    assert min(now+duration-time.time(),mono+duration-time.monotonic())>1900,'ORIGINAL_ROOT_REMAINING_REQUIRED'
    auth.update(root_not_locked_yet=False,absolute_ceiling_unix=now+duration,monotonic_ceiling=mono+duration,locked_unix=now);dump(O/'AUTHORIZATION.json',auth)
    dump(O/'ROUND_WINDOW.json',dict(version='V1264',window_seconds=duration,started_unix=now,started_monotonic=mono,
        absolute_deadline_unix=now+duration,hard_stop_monotonic=mono+duration,boot_id=auth['boot_id'],previous_windows_unchanged=True,new_independent_window=False,inherits_original_V1261_deadline=True))
    dump(O/'APPROVAL.json',dict(models_authorized=True,version='V1264',window_seconds=duration,stop_on_safety_evidence=True,automatic_new24=False,
        absolute_deadline_unix=now+duration,allowed_task_ids=[t['task_id']for t in tasks]))
    current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_V1264_EW_OBSERVATION_DEVELOPMENT',active_run=str(O.relative_to(R)),active_entrypoint=str((C/'campaign.py').relative_to(R)),active_window=str((O/'ROUND_WINDOW.json').relative_to(R)),next_physical_authorized=True,automatic_additional_simulation=False,
        next_scope='Only unexecuted slot17 complete repeat, successful parent main inherited explicitly; safe observation handoff, actual causal rays refresh then whole-source admission; original V1261 root ceiling unchanged, first failure stop, no automatic24.')
    dump(R/'CURRENT_EXPERIMENT.json',current);child=None
    try:
        with(O/'campaign.console').open('x')as log:child=subprocess.Popen(['/usr/bin/taskset','-c','2','/usr/bin/nice','-n','19','/usr/bin/ionice','-c','3',sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
        receipt=dict(pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],absolute_deadline_unix=now+duration,offline_capable=True,new_independent_window=False,inherits_original_V1261_deadline=True);dump(O/'LAUNCH_RECEIPT.json',receipt)
        with(O/'watchdog.console').open('x')as log:w=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py')],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
        dump(O/'WATCHDOG_LAUNCH.json',dict(pid=w.pid,proc_start=Path('/proc',str(w.pid),'stat').read_text().split()[21]));print(json.dumps(receipt))
    except BaseException as exc:
        if child and child.poll()is None:os.killpg(child.pid,signal.SIGTERM)
        (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'START_ERROR.json',dict(error=repr(exc),counts_unknown=child is not None));raise
if __name__=='__main__':main()
