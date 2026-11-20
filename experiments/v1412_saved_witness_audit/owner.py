"""One separate registered saved-evidence audit; no generation or peer."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;P=R/'runs/v1382_weekend_campaign/LEDGER.json'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def write(p,v):
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)


def used(path):return int(subprocess.check_output(['du','-sx','-B1',str(path)],text=True).split()[0])


def environment():
    e=dict(os.environ);e.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');e.pop('LD_PRELOAD',None);return e


def launch():
    assert not(O/'LAUNCH.json').exists() and not(O/'ROUND_WINDOW.json').exists()
    assert read(O/'QUALIFICATION.json')['passed']
    assert read(R/'runs/v1410_scalar_feedback_witness/FULL_REMOTE_VERIFIED.json')['passed']
    assert read(R/'runs/v1410_scalar_feedback_witness/TRANSPORT_CLEANUP.json')['passed']
    hashes=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in hashes.items())
    parent=read(P);auth=read(R/'experiments/v1382_weekend_campaign/AUTHORIZATION.json')
    assert parent['active_round'] is None and not parent['models_now_authorized'] and parent['scientific_revisions']==3
    assert len(parent['rounds'])<auth['maximum_rounds']
    assert parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    assert min(parent['hard_stop_monotonic']-time.monotonic(),1795395600-time.time())>5500
    allocated=used(R/'runs');assert allocated+(16+32+32+512)*1024**2<10*1024**3
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256'];(O/'REVIEW_PENDING.before').write_bytes(saved)
    now,mono=time.time(),time.monotonic();end=min(now+5400,1795395600)
    window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=end,hard_stop_monotonic=min(mono+end-now,parent['hard_stop_monotonic']),boot_id=parent['boot_id']);write(O/'ROUND_WINDOW.json',window)
    write(O/'STORAGE_PREFLIGHT.json',dict(passed=True,allocated_all_runs_bytes=allocated,new_output_cap_bytes=16*1024**2,archive_reserve_bytes=32*1024**2,download_reserve_bytes=32*1024**2,root_reserve_bytes=512*1024**2))
    current=read(R/'runs/v1410_scalar_feedback_witness/model/CURRENT_INPUT.json')
    approval=dict(mode='CURRENT_WITNESS_INDEPENDENT_AUDIT',round_id=C.name,input_sha256=current['input_sha256'],maximum_steps=791940,source_hashes=hashes,source_generation='runs/v1410_scalar_feedback_witness/model',**{k:window[k]for k in ['absolute_deadline_unix','hard_stop_monotonic','boot_id']});write(O/'model/AUDIT_APPROVAL.json',approval)
    parent['rounds'].append(dict(id=C.name,kind='saved_generation_independent_model_audit',status='RUNNING',started_unix=now,hard_stop_unix=end,source_generation='v1410_scalar_feedback_witness',scientific_revision=3,maximum_generation_analytical=0,maximum_audit_analytical=791940,maximum_vehicle_tasks=0,source_freeze_sha256=sha(O/'SOURCE_FREEZE.json')))
    parent.update(active_round=C.name,models_now_authorized=True,status='RUNNING_SEPARATE_SAVED_MODEL_AUDIT');write(P,parent)
    state=read(R/'CURRENT_EXPERIMENT.json');state.update(active_run=str(O.relative_to(R)),active_zero_model_diagnostic=None,next_physical=False);write(R/'CURRENT_EXPERIMENT.json',state)
    with(O/'owner.console').open('x')as log:job=subprocess.Popen([sys.executable,'-B',str(C/'owner.py'),'--work'],cwd=R,env=environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    write(O/'LAUNCH.json',dict(pid=job.pid,started_unix=now,one_launch=True,maximum_generation_steps=0,maximum_audit_steps=791940,physical_native=0));print(json.dumps(dict(started=True,pid=job.pid)))


def work():
    window=read(O/'ROUND_WINDOW.json');saved=(O/'REVIEW_PENDING.before').read_bytes();job=None
    result=dict(passed=False,closed=False,generation_analytical_native=0,physical_native=0,replay_native=0,vehicle_starts=0,mujoco_models=0)
    def stop(*_):raise TimeoutError('SAVED_AUDIT_OWNER_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,window['hard_stop_monotonic']-time.monotonic()-5))
    try:
        assert all(sha(R/p)==h for p,h in read(O/'SOURCE_FREEZE.json')['files'].items())
        (R/'REVIEW_PENDING').unlink()
        with(O/'audit.console').open('x')as log:
            job=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'audit_entry.py').relative_to(R))],cwd=R,env=environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            write(O/'ACTIVE.json',dict(native_pid=job.pid,phase='SAVED_COMPLETE_INDEPENDENT_AUDIT',physical_native=0))
            until=min(time.monotonic()+1810,window['hard_stop_monotonic']-30);next_storage=0
            while job.poll()is None:
                assert time.monotonic()<until and time.time()<window['absolute_deadline_unix']-30
                assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==window['boot_id']
                if time.monotonic()>=next_storage:
                    assert used(R/'runs')<10*1024**3-512*1024**2 and used(O)<16*1024**2;next_storage=time.monotonic()+5
                time.sleep(.3)
            audit=read(O/'model/INDEPENDENT_AUDIT.json')if(O/'model/INDEPENDENT_AUDIT.json').exists()else None
            result.update(audit_returncode=job.returncode,audit=audit,passed=bool(job.returncode==0 and audit and audit['passed']))
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        if job is not None and job.poll()is None:
            os.killpg(job.pid,signal.SIGTERM)
            try:job.wait(timeout=8)
            except subprocess.TimeoutExpired:os.killpg(job.pid,signal.SIGKILL);job.wait(timeout=3)
        (R/'REVIEW_PENDING').write_bytes(saved);signal.setitimer(signal.ITIMER_REAL,0)
        result.update(closed=True,closed_unix=time.time(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==saved);write(O/'COMPLETION.json',result);(O/'ACTIVE.json').unlink(missing_ok=True)
        parent=read(P);row=next(x for x in parent['rounds']if x['id']==C.name);a=result.get('audit')or{}
        row.update(closed=True,status='CLOSED',passed=result['passed'],completion=str((O/'COMPLETION.json').relative_to(R)),generation_analytical_native=0,audit_analytical_native=a.get('audit_analytical_native'),audit_unknown=a.get('audit_inflight_unknown',True),physical_native=0)
        parent.update(active_round=None,models_now_authorized=False,status='SAVED_MODEL_AUDIT_CLOSED_REVIEW_REQUIRED',scalar_feedback_saved_generation_independent_audit_native=row['audit_analytical_native']);write(P,parent)
        state=read(R/'CURRENT_EXPERIMENT.json');state.update(active_run=None,next_physical=False,active_zero_model_diagnostic=str((O/'COMPLETION.json').relative_to(R)));write(R/'CURRENT_EXPERIMENT.json',state)
    return 0 if result['passed']else 1


if __name__=='__main__':
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    if '--work'in sys.argv:raise SystemExit(work())
    launch()
