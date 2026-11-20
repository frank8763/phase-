"""At most one804-step numerical qualification after storage/source gates."""
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

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;DAY=R/'runs/v1382_weekend_campaign'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    p=Path(p);temporary=p.with_suffix(p.suffix+'.tmp');temporary.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temporary.replace(p)
def used():return int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],text=True).split()[0])
def env():
    value=dict(os.environ);value.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');value.pop('LD_PRELOAD',None);return value
def stop_job(p):
    if p is not None and p.poll()is None:
        os.killpg(p.pid,signal.SIGTERM)
        try:p.wait(timeout=8)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)


def launch():
    assert not(O/'LAUNCH.json').exists()and not(O/'ROUND_WINDOW.json').exists(), 'MODEL_QUALIFICATION_ALREADY_CLAIMED'
    # Closed-stream transport recovery and its old-hardlink cleanup are both
    # required. An earlier FINALIZED alone cannot bypass unfinished cleanup.
    assert read(R/'runs/v1400_archive_link_schema/FINALIZED.json')['passed']
    assert read(R/'runs/v1400_archive_link_schema/PRIOR_FAILED_TRANSPORT_LINK_CLEANUP.json')['passed']
    assert read(O/'ENTRY_CHECK02.json')['passed'] and read(O/'PRELAUNCH_QUALIFICATION02.json')['passed']
    freeze=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in freeze.items())
    parent=read(DAY/'LEDGER.json');authority=read(R/'experiments/v1382_weekend_campaign/AUTHORIZATION.json')
    assert parent['active_round']is None and not parent['models_now_authorized']and len(parent['rounds'])<authority['maximum_rounds']
    assert parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    assert used()+4*1024**2+32*1024**2<10*1024**3-512*1024**2, 'MODEL_QUALIFICATION_STORAGE_RESERVE'
    assert min(1795395600-time.time(),parent['hard_stop_monotonic']-time.monotonic())>1000
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256'];(O/'REVIEW_PENDING.before').write_bytes(saved)
    now,mono=time.time(),time.monotonic();end=min(now+900,1795395600)
    window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=end,hard_stop_monotonic=min(mono+end-now,parent['hard_stop_monotonic']),boot_id=parent['boot_id']);write(O/'ROUND_WINDOW.json',window)
    write(O/'APPROVAL.json',dict(mode='MODEL_ORIGIN_QUALIFICATION',maximum_analytical_native=804,maximum_predictor_constructions=6,maximum_branch_copies=2,maximum_vehicle_initializations=0,physical_admission=False))
    parent['rounds'].append(dict(id=C.name,kind='analytical_origin_qualification',status='RUNNING',started_unix=now,hard_stop_unix=end,maximum_analytical_native=804,maximum_vehicle_tasks=0,source_freeze_sha256=sha(O/'SOURCE_FREEZE.json')))
    parent.update(active_round=C.name,models_now_authorized=True,status='RUNNING_CURRENT_MODEL_ORIGIN_QUALIFICATION');write(DAY/'LEDGER.json',parent)
    with(O/'owner.console').open('x')as log:
        p=subprocess.Popen([sys.executable,'-B',str(C/'owner.py'),'--work'],cwd=R,env=env(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    write(O/'LAUNCH.json',dict(pid=p.pid,started_unix=now,one_launch=True,maximum_analytical_native=804,physical_native=0));print(json.dumps(dict(started=True,pid=p.pid)))


def work():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    window=read(O/'ROUND_WINDOW.json');saved=(O/'REVIEW_PENDING.before').read_bytes();p=None
    result=dict(closed=False,passed=False,physical_native=0,replay_native=0,vehicle_initializations=0)
    def stop(*_):raise TimeoutError('ORIGIN_QUALIFICATION_OWNER_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,window['hard_stop_monotonic']-time.monotonic()-5))
    try:
        assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==window['boot_id']
        (R/'REVIEW_PENDING').unlink()
        with(O/'entry.console').open('x')as log:
            p=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'entry02.py').relative_to(R))],cwd=R,env=env(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            deadline=min(time.monotonic()+310,window['hard_stop_monotonic']-15)
            while p.poll()is None:
                assert time.monotonic()<deadline and time.time()<window['absolute_deadline_unix']-15
                assert used()<10*1024**3-512*1024**2, 'MODEL_QUALIFICATION_STORAGE_STOP'
                time.sleep(.5)
        native=read(O/'RESULT.json')if(O/'RESULT.json').exists()else None
        result.update(returncode=p.returncode,result=native,passed=bool(p.returncode==0 and native and native['passed']));p=None
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        stop_job(p);(R/'REVIEW_PENDING').write_bytes(saved);signal.setitimer(signal.ITIMER_REAL,0)
        result.update(closed=True,closed_unix=time.time(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==saved)
        write(O/'COMPLETION.json',result);write(O/'APPROVAL_CLOSED.json',dict(models_authorized=False,physical_admission=False))
        d=read(DAY/'LEDGER.json');record=next(x for x in d['rounds']if x['id']==C.name);n=result.get('result')or{}
        record.update(closed=True,status='CLOSED',passed=result['passed'],analytical_native=n.get('analytical_native'),analytical_inflight_unknown=n.get('analytical_inflight_unknown',not bool(n)),explicit_predictor_constructions=n.get('explicit_predictor_constructions'),physical_native=0,completion=str((O/'COMPLETION.json').relative_to(R)))
        d.update(active_round=None,models_now_authorized=False,status='MODEL_ORIGIN_QUALIFICATION_CLOSED_REVIEW_REQUIRED');d['model_origin_qualification_analytical_native']=n.get('analytical_native');write(DAY/'LEDGER.json',d)
    return 0 if result['passed']else 1


if __name__=='__main__':
    if '--work'in sys.argv:raise SystemExit(work())
    launch()
