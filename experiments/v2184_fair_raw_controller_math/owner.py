"""One double-locked CPU2 mathematical scope, original plant permanently denied."""
import datetime,fcntl,hashlib,json,os,secrets,selectors,signal,subprocess,time,traceback
from pathlib import Path
from context import R,C,S,read,put,sha,source_files,REVIEW_SHA
from budget import check
def identity(pid):
    return dict(pid=pid,pgid=os.getpgid(pid),start_ticks=Path('/proc',str(pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
def same(value):
    p=Path('/proc',str(value['pid']),'stat')
    return value['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and p.exists()and p.read_text().split(') ',1)[1].split()[19]==value['start_ticks']
def main():
    assert os.sched_getaffinity(0)=={5}
    assert not any((S/n).exists()for n in ['RUNTIME_ONCE.json','COMPLETION.json','OWNED_CHILD.json'])
    assert read(S/'SOURCE_QUALIFICATION.json')['passed']and read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
    check('runtime');source=source_files();assert 'REVIEW_PENDING'not in source and all(sha(R/n)==h for n,h in source.items())
    handles=[]
    for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
        h=(R/n).open();fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);handles.append(h)
    review=R/'REVIEW_PENDING';assert sha(review)==REVIEW_SHA
    now=datetime.datetime.now().astimezone();assert now.isoformat()<'2026-11-29T07:00:00+08:00','WEEKEND_NO_NEW_NATIVE_AFTER07'
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();start=time.monotonic();wall=time.time();nonce=secrets.token_hex(24)
    window=dict(started_unix=wall,started_monotonic=start,normal_end_unix=wall+4200,absolute_deadline_unix=wall+5400,hard_stop_monotonic=start+5400,boot_id=boot,native_math_watchdog_seconds=180)
    put(S/'RUNTIME_ONCE.json',dict(owner_identity=identity(os.getpid()),controller_math_only=True,original_plant_allowed=False))
    put(S/'ROUND_WINDOW.json',window)
    put(S/'NUMERICAL_ADMISSION.json',dict(scope='FIXED_SAVED_COMMON_INPUT_RAW_CONTROLLER_MATH',original_plant_allowed=False,controller_math_allowed=True,allowed_queries={'DWA':1,'RPP':1},source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'),host_child_nonce=nonce))
    out=S/'RUNTIME';out.mkdir();backup=S/'REVIEW_HELD.original';assert not backup.exists()
    child=None;child_id=None;first=None;secondary=[];machine=None;stdout=bytearray()
    try:
        os.replace(review,backup);assert sha(backup)==REVIEW_SHA
        env=dict(os.environ,PHASE_REPO=str(R),PHASE_NATIVE_MATH_NONCE=nonce,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa')
        child=subprocess.Popen(['taskset','-c','2','nice','-n','19','/usr/bin/python3','-B',str(C/'run_phase.py')],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
        child_id=identity(child.pid);put(S/'OWNED_CHILD.json',dict(**child_id,CPU=2,original_plant_allowed=False))
        sel=selectors.DefaultSelector();sel.register(child.stdout,selectors.EVENT_READ)
        while sel.get_map():
            assert time.monotonic()-start<180 and time.time()<window['absolute_deadline_unix']and boot==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'MATH_OWNER_WATCHDOG_OR_BOOT'
            for key,_ in sel.select(.1):
                b=os.read(key.fileobj.fileno(),4096)
                if not b:sel.unregister(key.fileobj);continue
                stdout.extend(b);assert len(stdout)<=16*1024,'MATH_OWNER_CONSOLE16KIB'
        child.wait(timeout=3);machine=read(out/'RESULT.json')
        assert all(sha(R/n)==h for n,h in source.items()),'FROZEN_SOURCE_CHANGED_AFTER_MATH'
    except BaseException as e:first=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            if same(child_id):
                try:
                    os.killpg(child_id['pgid'],signal.SIGTERM)
                    try:child.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(child_id['pgid'],signal.SIGKILL);child.wait(timeout=5)
                except BaseException as e:secondary.append('OWNED_CHILD_TERMINATION_ERROR:'+repr(e))
            else:secondary.append('CHILD_IDENTITY_CHANGED_NOT_SIGNALED')
        if backup.exists():
            assert sha(backup)==REVIEW_SHA
            if review.exists():
                if sha(review)!=REVIEW_SHA:secondary.append('REVIEW_CHANGED_EXTERNALLY_NOT_OVERWRITTEN')
            else:os.replace(backup,review)
        restored=review.is_file()and sha(review)==REVIEW_SHA
        # Parent keeps both locks through child death and REVIEW restoration.
        value=dict(closed=True,passed=restored and not secondary and first is None and machine is not None and machine['passed']and child.returncode==0,first_error=first,secondary_errors=secondary,machine_result_sha256=sha(out/'RESULT.json')if(out/'RESULT.json').exists()else None,machine_passed=None if machine is None else machine['passed'],controller_math_only=True,original_plant_factory_calls=0,original_actual_native=0,original_replay_native=0,formal_assignments_executed=0,whole_navigation_passed=False,child_returncode=None if child is None else child.returncode,real_child_identity=child_id,child_identity_gone_or_changed=child_id is None or not same(child_id),original_REVIEW_exact_restored=restored,source_unchanged_after_exit=all(sha(R/n)==h for n,h in source.items()),native_controller_counts_unknown_if_capsule_absent=not(out/'EVIDENCE.json.gz').exists(),owner_console_lossless_hex=bytes(stdout).hex(),wall_s=time.monotonic()-start)
        assert len(json.dumps(value))<32*1024
        put(S/'COMPLETION.json',value);check('closed')
    print(json.dumps(read(S/'COMPLETION.json')),flush=True)
    return 0 if value['passed']and restored else 1
if __name__=='__main__':raise SystemExit(main())
