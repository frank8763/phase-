"""One offline analytical owner and one original-RPP mathematical peer."""
import fcntl
import hashlib
import importlib.util
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
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
io=load('analytical_owner_json',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
def native_env():
    env=dict(os.environ);env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('LD_PRELOAD',None);return env
def remaining(w):
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id']
    return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic(),1795395600-time.time())
def used():return int(subprocess.run(['du','-sx','--block-size=1',str(R/'runs')],capture_output=True,text=True,check=True,timeout=60).stdout.split()[0])
def terminate(p):
    if p is not None and p.poll() is None:
        os.killpg(p.pid,signal.SIGTERM)
        try:p.wait(timeout=8)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)
def launch():
    assert not (O/'ANALYSIS_LAUNCH.json').exists() and not (O/'ROUND_WINDOW.json').exists()
    q=read(O/'ANALYSIS_QUALIFICATION.json');assert q['passed'] and all(sha(R/p)==h for p,h in q['tested_source_hashes'].items())
    frozen=read(O/'ANALYSIS_SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in frozen.items())
    d=read(DAY/'LEDGER.json');a=read(R/'experiments/v1382_weekend_campaign/AUTHORIZATION.json');assert d['active_round'] is None and d['storage_ready'] and used()<10*1024**3-512*1024**2
    assert len(d['rounds'])<a['maximum_rounds'] and d['scientific_revisions']<a['maximum_scientific_revisions']
    assert d['absolute_hard_stop_unix']==1795395600 and d['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    assert min(1795395600-time.time(),d['hard_stop_monotonic']-time.monotonic())>2000
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(guard).hexdigest()==d['review_pending_original_bytes_sha256'];(O/'REVIEW_PENDING.before').write_bytes(guard)
    now,mono=time.time(),time.monotonic();end=min(now+5400,1795395600);window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=end,hard_stop_monotonic=min(mono+end-now,d['hard_stop_monotonic']),boot_id=d['boot_id']);io.atomic(O/'ROUND_WINDOW.json',window)
    io.atomic(O/'ANALYSIS_APPROVAL.json',dict(mode='ANALYTICAL_ONLY',maximum_steps=650000,maximum_analysis_s=1800,maximum_mujoco_initializations=0,physical_admission=False))
    d.update(active_round='v1393_analysis01',status='RUNNING_FULL9390_ANALYTICAL_PREPARATION',models_now_authorized=True);d['scientific_revisions']+=1;d['rounds'].append(dict(id='v1393_analysis01',kind='analytical_preparation',status='RUNNING',source_freeze_sha256=sha(O/'ANALYSIS_SOURCE_FREEZE.json'),started_unix=now,hard_stop_unix=end,maximum_analytical_steps=650000,maximum_vehicle_tasks=0));io.atomic(DAY/'LEDGER.json',d)
    with (O/'owner.console').open('x') as log:p=subprocess.Popen([sys.executable,'-B',str(C/'analysis_owner.py'),'--work'],cwd=R,env=native_env(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    io.atomic(O/'ANALYSIS_LAUNCH.json',dict(pid=p.pid,window=window,analytical_only=True,maximum_analytical_steps=650000,physical_native=0));print(json.dumps(dict(started=True,pid=p.pid,analytical_only=True)))
def work():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));window=read(O/'ROUND_WINDOW.json');guard=(O/'REVIEW_PENDING.before').read_bytes();peer=None;native=None;logs=[];result=dict(closed=False,passed=False,physical_native=0,canonical_vehicle_initializations=0)
    try:
        peer_out=O/'analysis_peer';peer_out.mkdir(exist_ok=False);env_helper=load('analysis_original_ros_environment',C/'qualify_peer_entry02.py');ros,env=env_helper.environment(peer_out)
        log=(peer_out/'peer.console').open('x');logs.append(log);peer=subprocess.Popen(ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'rpp_peer.py'),str(peer_out),'v1393-analysis01']),cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        until=time.monotonic()+10
        while not (peer_out/'peer.sock').exists():
            assert peer.poll() is None and time.monotonic()<until;time.sleep(.05)
        (R/'REVIEW_PENDING').unlink();log=(O/'analysis.console').open('x');logs.append(log)
        native=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'analysis.py').relative_to(R))],cwd=R,env=native_env(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        io.atomic(O/'ACTIVE.json',dict(phase='ORIGINAL_RPP_MODELED_RESPONSE',native_pid=native.pid,peer_pid=peer.pid,physical_native=0));until=time.monotonic()+1810;next_storage=0
        while native.poll() is None:
            assert remaining(window)>30 and time.monotonic()<until,'OWNER_MODEL_DEADLINE'
            if time.monotonic()>=next_storage:assert used()<10*1024**3-256*1024**2,'OWNER_STORAGE_RESERVE';next_storage=time.monotonic()+5
            time.sleep(.25)
        result.update(native_returncode=native.returncode,analysis=read(O/'ANALYSIS_RESULT.json') if (O/'ANALYSIS_RESULT.json').exists() else None);result['passed']=native.returncode==0 and bool(result['analysis'] and result['analysis']['passed'])
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        terminate(native);terminate(peer)
        for log in logs:log.close()
        (R/'REVIEW_PENDING').write_bytes(guard);io.atomic(O/'ANALYSIS_APPROVAL.json',dict(mode='CLOSED',physical_admission=False))
        result.update(closed=True,closed_unix=time.time(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==guard);io.atomic(O/'ANALYSIS_COMPLETION.json',result);(O/'ACTIVE.json').unlink(missing_ok=True)
        d=read(DAY/'LEDGER.json');d.update(active_round=None,models_now_authorized=False,status='FULL9390_ANALYSIS_CLOSED_REVIEW_REQUIRED');row=next(x for x in d['rounds'] if x['id']=='v1393_analysis01');a=result.get('analysis') or {};row.update(status='CLOSED',closed=True,passed=result['passed'],completion=str((O/'ANALYSIS_COMPLETION.json').relative_to(R)),analytical_native=a.get('analytical_native'),analytical_unknown=a.get('analytical_step_inflight_unknown',not bool(a)),physical_native=0);d['full9390_preparation_analytical_native']=a.get('analytical_native');io.atomic(DAY/'LEDGER.json',d)
    return 0 if result['passed'] else 1
if __name__=='__main__':
    if '--work' in sys.argv:raise SystemExit(work())
    launch()
