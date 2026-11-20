"""One400-step analytical qualification, no physical or replay permission."""
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


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert not(O/'LAUNCH.json').exists() and not(O/'ROUND_WINDOW.json').exists()
    assert read(O/'ENTRY_CHECK.json')['passed']and read(R/'runs/v1413_current_reserve_qualification/FULL_REMOTE_VERIFIED.json')['passed']
    freeze=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in freeze.items())
    parent=read(P);root=read(R/'experiments/v1382_weekend_campaign/AUTHORIZATION.json')
    assert parent['scientific_revisions']<root['maximum_scientific_revisions']
    assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==3 and len(parent['rounds'])<root['maximum_rounds']
    assert parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    assert min(parent['hard_stop_monotonic']-time.monotonic(),1795395600-time.time())>1000
    allocated=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],text=True).split()[0]);assert allocated+(512+4+32+32)*1024**2<10*1024**3
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256'];(O/'REVIEW_PENDING.before').write_bytes(saved)
    now,mono=time.time(),time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=min(now+900,1795395600),hard_stop_monotonic=min(mono+900,parent['hard_stop_monotonic']),boot_id=parent['boot_id']);write(O/'ROUND_WINDOW.json',window)
    current=read(O/'FIXED_INPUTS.json')['current_input'];snapshot=current['causal_snapshot'];identity=hashlib.sha256(json.dumps(snapshot,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    approval=dict(scope='CURRENT_MEASURED_PACKET_RESERVE',models_authorized=True,physical_admission=False,round_id=C.name,maximum_analytical_native=400,maximum_predictor_constructions=2,tested_source_hashes=freeze,causal_snapshot_sha256=identity,current_input_sha256=current['input_sha256'],**{k:window[k]for k in ['absolute_deadline_unix','hard_stop_monotonic','boot_id']});write(O/'APPROVAL.json',approval)
    parent['scientific_revisions']=4
    parent['rounds'].append(dict(id=C.name,kind='current_causal_timed_reserve_analytical_qualification',status='RUNNING',started_unix=now,hard_stop_unix=window['absolute_deadline_unix'],maximum_analytical_native=400,maximum_vehicle_tasks=0,scientific_revision=4,source_freeze_sha256=sha(O/'SOURCE_FREEZE.json')));parent.update(active_round=C.name,models_now_authorized=True,status='RUNNING_CURRENT_RESERVE_400_QUALIFICATION');write(P,parent)
    write(O/'LAUNCH.json',dict(started_unix=now,one_launch=True,maximum_analytical_native=400,physical_native=0,allocated_all_runs_bytes=allocated))
    env=dict(os.environ);env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('LD_PRELOAD',None)
    job=None
    result=dict(passed=False,physical_native=0,replay_native=0,mujoco_models=0,vehicle_starts=0)
    def stop(*_):raise TimeoutError('CURRENT_RESERVE_OWNER_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,100)
    try:
        (R/'REVIEW_PENDING').unlink()
        with(O/'numeric.console').open('x')as log:
            job=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'entry.py').relative_to(R))],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            write(O/'ACTIVE.json',dict(native_pid=job.pid,physical_native=0,maximum_analytical_native=400))
            code=job.wait(timeout=75)
        proof=read(O/'RESULT.json')if(O/'RESULT.json').exists()else None
        result.update(returncode=code,qualification=proof,passed=bool(code==0 and proof and proof['passed']))
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        if job is not None and job.poll()is None:
            os.killpg(job.pid,signal.SIGTERM)
            try:job.wait(timeout=8)
            except subprocess.TimeoutExpired:os.killpg(job.pid,signal.SIGKILL);job.wait(timeout=3)
        if result.get('qualification')is None and (O/'RESULT.json').exists():result['qualification']=read(O/'RESULT.json')
        (O/'ACTIVE.json').unlink(missing_ok=True)
        signal.setitimer(signal.ITIMER_REAL,0);(R/'REVIEW_PENDING').write_bytes(saved);result.update(closed=True,closed_unix=time.time(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==saved);write(O/'COMPLETION.json',result)
        parent=read(P);row=next(v for v in parent['rounds']if v['id']==C.name);q=result.get('qualification')or{}
        row.update(closed=True,status='CLOSED',passed=result['passed'],analytical_native=q.get('analytical_native'),analytical_unknown=q.get('analytical_inflight_unknown',True),physical_native=0,completion=str((O/'COMPLETION.json').relative_to(R)));parent.update(active_round=None,models_now_authorized=False,status='CURRENT_RESERVE_QUALIFICATION_CLOSED',current_timed_reserve_qualification_analytical_native=q.get('analytical_native'));write(P,parent)
    print(json.dumps(result));return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
