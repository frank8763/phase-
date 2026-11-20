"""One saved-input complete method generation and success-only model audit."""
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
def write(p,v):
    p=Path(p);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)
def exact(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def used():return int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],text=True).split()[0])
def folder_bytes(p):return int(subprocess.check_output(['du','-sx','-B1',str(p)],text=True).split()[0])
def env():
    e=dict(os.environ);e.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');e.pop('LD_PRELOAD',None);return e
def terminate(p):
    if p is not None and p.poll()is None:
        os.killpg(p.pid,signal.SIGTERM)
        try:p.wait(timeout=8)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)


def launch():
    assert not(O/'LAUNCH.json').exists()and not(O/'ROUND_WINDOW.json').exists()
    assert read(O/'QUALIFICATION.json')['passed']and read(O/'model/AUDIT_ENTRY_CHECK.json')['passed']
    assert read(R/'runs/v1408_saved_capture_witness/FULL_REMOTE_VERIFIED.json')['passed']and read(R/'runs/v1408_saved_capture_witness/TRANSPORT_CLEANUP.json')['passed']
    assert read(R/'runs/v1401_model_origin_qualification/FULL_REMOTE_VERIFIED.json')['passed']and read(R/'runs/v1407_lossless_branch_stream/QUALIFICATION.json')['passed']
    hashes=read(O/'NUMERIC_SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in hashes.items())
    parent=read(DAY/'LEDGER.json');a=read(R/'experiments/v1382_weekend_campaign/AUTHORIZATION.json')
    assert parent['active_round']is None and not parent['models_now_authorized']and len(parent['rounds'])<a['maximum_rounds']and parent['scientific_revisions']<a['maximum_scientific_revisions']
    assert parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    assert used()+288*1024**2<10*1024**3-512*1024**2,'COMPLETE_METHOD_GENERATION_ARCHIVE_READBACK_RESERVE'
    assert min(1795395600-time.time(),parent['hard_stop_monotonic']-time.monotonic())>5500
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256'];(O/'REVIEW_PENDING.before').write_bytes(saved)
    write(O/'STORAGE_PREFLIGHT.json',dict(allocated_all_runs_bytes=used(),new_evidence_cap_bytes=128*1024**2,archive_reserve_bytes=128*1024**2,download_reserve_bytes=32*1024**2,root_reserve_bytes=512*1024**2,storage_limit_bytes=10*1024**3,passed=used()+800*1024**2<10*1024**3,physical_admission=False))
    now,mono=time.time(),time.monotonic();end=min(now+5400,1795395600)
    w=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=end,hard_stop_monotonic=min(mono+end-now,parent['hard_stop_monotonic']),boot_id=parent['boot_id']);write(O/'ROUND_WINDOW.json',w)
    launch_sources=dict(files={str(p.relative_to(R)):sha(p)for p in [Path(__file__),O/'NUMERIC_SOURCE_FREEZE.json']},generation_source_hashes=hashes,maximum_generation_steps=904500,maximum_audit_steps=904500,maximum_evidence_allocated_bytes=128*1024**2)
    write(O/'LAUNCH_SOURCE_FREEZE.json',launch_sources)
    current=read(O/'model/CURRENT_INPUT.json')
    approval=dict(models_authorized=True,round_id=C.name,scope='CURRENT_EVENT_COMPLETE_MODEL_WITNESS',current_input_sha256=current['input_sha256'],boot_id=parent['boot_id'],maximum_nominal_native=4500,maximum_analytical_native=904500,tested_source_hashes=hashes,run_id='v1410-saved9390-scalar-feedback-complete-model',absolute_deadline_unix=end,hard_stop_monotonic=w['hard_stop_monotonic'])
    write(O/'model/APPROVAL.json',approval)
    assert parent['scientific_revisions']==2, 'SCIENTIFIC_REVISION_PRECONDITION_CHANGED'
    parent['scientific_revisions']+=1
    parent['rounds'].append(dict(id=C.name,kind='complete_saved_input_finite_method_model_qualification',started_unix=now,hard_stop_unix=end,status='RUNNING',scientific_revision=parent['scientific_revisions'],maximum_generation_analytical=904500,maximum_audit_analytical=904500,maximum_vehicle_tasks=0,source_freeze_sha256=sha(O/'NUMERIC_SOURCE_FREEZE.json')))
    parent.update(active_round=C.name,models_now_authorized=True,status='RUNNING_SCALAR_FEEDBACK_CAPTURE_PLUS_RPP_MODEL_WITNESS');write(DAY/'LEDGER.json',parent)
    state=read(R/'CURRENT_EXPERIMENT.json');state.update(active_run=str(O.relative_to(R)),active_zero_model_diagnostic=None,next_physical=False);write(R/'CURRENT_EXPERIMENT.json',state)
    with(O/'owner.console').open('x')as log:p=subprocess.Popen([sys.executable,'-B',str(C/'owner.py'),'--work'],cwd=R,env=env(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    write(O/'LAUNCH.json',dict(pid=p.pid,started_unix=now,one_launch=True,physical_native=0,maximum_generation_steps=904500,maximum_audit_steps=904500));print(json.dumps(dict(started=True,pid=p.pid,physical_native=0)))


def work():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));w=read(O/'ROUND_WINDOW.json');saved=(O/'REVIEW_PENDING.before').read_bytes();peer=None;native=None;logs=[];out=O/'model'
    result=dict(passed=False,closed=False,physical_native=0,replay_native=0,mujoco_models=0,vehicle_starts=0,independent_audit_unexecuted=True)
    def stop(*_):raise TimeoutError('COMPLETE_MODEL_WITNESS_OWNER_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,w['hard_stop_monotonic']-time.monotonic()-5))
    def monitor(p,limit):
        end=min(time.monotonic()+limit,w['hard_stop_monotonic']-30);next_storage=0
        while p.poll()is None:
            assert time.monotonic()<end and time.time()<w['absolute_deadline_unix']-30 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id']
            if time.monotonic()>=next_storage:
                assert used()<10*1024**3-512*1024**2 and folder_bytes(out)<128*1024**2,'COMPLETE_MODEL_EVIDENCE_STORAGE_STOP';next_storage=time.monotonic()+5
            time.sleep(.3)
    try:
        freeze=read(O/'LAUNCH_SOURCE_FREEZE.json');assert all(sha(R/p)==h for p,h in freeze['files'].items())
        helper=exact('v1410_original_peer_env',R/'experiments/v1396_rpp_rpc_retirement/peer_environment.py');ros,peer_env=helper.environment(out)
        log=(out/'peer.console').open('x');logs.append(log);peer=subprocess.Popen(ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'modeled_peer.py'),str(out),read(out/'APPROVAL.json')['run_id']]),cwd=R,env=peer_env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        until=time.monotonic()+10
        while not(out/'peer.sock').exists():assert peer.poll()is None and time.monotonic()<until;time.sleep(.02)
        (R/'REVIEW_PENDING').unlink();log=(out/'production.console').open('x');logs.append(log)
        native=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'production_entry.py').relative_to(R)),str(out)],cwd=R,env=env(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write(O/'ACTIVE.json',dict(phase='COMPLETE_CAPTURE_PLUS_ORIGINAL_RPP_GENERATION',native_pid=native.pid,peer_pid=peer.pid,physical_native=0));monitor(native,1810)
        code=native.returncode;native=None;(R/'REVIEW_PENDING').write_bytes(saved);terminate(peer);peer=None
        generated=read(out/'RESULT.json')if(out/'RESULT.json').exists()else None;result.update(generation_returncode=code,generation=generated)
        if code==0 and generated and generated['passed']:
            approval=read(out/'APPROVAL.json');write(out/'AUDIT_APPROVAL.json',dict(mode='CURRENT_WITNESS_INDEPENDENT_AUDIT',round_id=C.name,input_sha256=approval['current_input_sha256'],maximum_steps=904500,boot_id=w['boot_id'],absolute_deadline_unix=w['absolute_deadline_unix'],hard_stop_monotonic=w['hard_stop_monotonic'],source_hashes=approval['tested_source_hashes']))
            result['independent_audit_unexecuted']=False;(R/'REVIEW_PENDING').unlink();log=(out/'audit.console').open('x');logs.append(log)
            native=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'audit_entry.py').relative_to(R))],cwd=R,env=env(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            write(O/'ACTIVE.json',dict(phase='INDEPENDENT_COMPLETE_METHOD_AUDIT',native_pid=native.pid,physical_native=0));monitor(native,1810)
            audit=read(out/'INDEPENDENT_AUDIT.json')if(out/'INDEPENDENT_AUDIT.json').exists()else None;result.update(audit_returncode=native.returncode,audit=audit,passed=bool(native.returncode==0 and audit and audit['passed']));native=None
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        terminate(native);terminate(peer)
        for log in logs:log.close()
        (R/'REVIEW_PENDING').write_bytes(saved);signal.setitimer(signal.ITIMER_REAL,0)
        result.update(closed=True,closed_unix=time.time(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==saved);write(O/'COMPLETION.json',result);write(O/'CLOSED_APPROVAL.json',dict(models_authorized=False,physical_admission=False));(O/'ACTIVE.json').unlink(missing_ok=True)
        d=read(DAY/'LEDGER.json');rr=next(x for x in d['rounds']if x['id']==C.name);g=result.get('generation')or{};a=result.get('audit')or{}
        rr.update(closed=True,status='CLOSED',passed=result['passed'],completion=str((O/'COMPLETION.json').relative_to(R)),generation_analytical_native=g.get('analytical_native'),generation_unknown=g.get('analytical_inflight_unknown',not bool(g)),audit_analytical_native=a.get('audit_analytical_native',0 if result['independent_audit_unexecuted']else None),audit_unknown=a.get('audit_inflight_unknown',not result['independent_audit_unexecuted']),physical_native=0)
        d.update(active_round=None,models_now_authorized=False,status='COMPLETE_SAVED_CAPTURE_MODEL_WITNESS_CLOSED_REVIEW_REQUIRED');d['complete_scalar_feedback_model_generation_native']=g.get('analytical_native');d['complete_scalar_feedback_model_audit_native']=rr['audit_analytical_native'];write(DAY/'LEDGER.json',d)
        state=read(R/'CURRENT_EXPERIMENT.json');state.update(active_run=None,next_physical=False,active_zero_model_diagnostic=str((O/'COMPLETION.json').relative_to(R)));write(R/'CURRENT_EXPERIMENT.json',state)
    return 0 if result['passed']else 1


if __name__=='__main__':
    if '--work'in sys.argv:raise SystemExit(work())
    launch()
