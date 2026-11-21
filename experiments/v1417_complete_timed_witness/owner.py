"""Once-only complete finite timed model generation and success-only audit."""
import ast
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
METHOD='ORIGINAL_BOUNDED_STEERING_THEN_GEAR_RELEASE_TIMED_REVERSE'


def write(p,v):
    temporary=p.with_suffix(p.suffix+'.tmp');temporary.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temporary.replace(p)


def used(path):return int(subprocess.check_output(['du','-sx','-B1',str(path)],text=True).split()[0])


def window_valid(w,parent):
    assert w['boot_id']==parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'BOOT_CHANGED'
    assert w['absolute_deadline_unix']<=1795395600 and w['hard_stop_monotonic']<=parent['hard_stop_monotonic'],'ROOT_WINDOW_EXPANDED'
    assert time.time()<w['absolute_deadline_unix'] and time.monotonic()<w['hard_stop_monotonic'],'DUAL_CLOCK_EXPIRED'


def storage_valid(allocated,evidence):
    assert allocated<10*1024**3-512*1024**2 and evidence<64*1024**2,'COMPLETE_TIMED_EVIDENCE_STORAGE_STOP'


def preflight(hashes):
    parent=read(P);auth=read(R/'experiments/v1382_weekend_campaign/AUTHORIZATION.json')
    assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==4
    assert len(parent['rounds'])<auth['maximum_rounds']and parent['scientific_revisions']<=auth['maximum_scientific_revisions']
    assert read(O/'ENTRY_QUALIFICATION.json')['passed']and read(O/'model/ENTRY_CHECK.json')['passed']
    assert read(R/'runs/v1416_timed_reserve_qualification/FULL_REMOTE_VERIFIED.json')['passed']and read(R/'runs/v1416_timed_reserve_qualification/TRANSPORT_CLEANUP.json')['passed']
    assert hashes and all(sha(R/p)==h for p,h in hashes.items())
    current=read(O/'model/CURRENT_INPUT.json');value=dict(current);identity=value.pop('input_sha256')
    assert hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==identity
    assert identity==read(O/'FIXED_INPUTS.json')['model_input_sha256']
    assert current['method_spec']['method']==METHOD and current['geometry_kind']=='ORIGINAL_CAUSAL_TIME_POLYGONS'and current['physical_admission']is False
    assert min(1795395600-time.time(),parent['hard_stop_monotonic']-time.monotonic())>5500
    assert parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    allocated=used(R/'runs');assert allocated+(64+64+32+512)*1024**2<10*1024**3,'GENERATION_ARCHIVE_DOWNLOAD_ROOT_RESERVE'
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
    return parent,current,allocated,saved


def entry_check():
    assert not(O/'OWNER_ENTRY_CHECK.json').exists()and not(O/'LAUNCH_CLAIM.json').exists()
    hashes=read(O/'INPUT_ENTRY_SOURCE_FREEZE.json')['files'];parent,current,allocated,saved=preflight(hashes)
    for p in [Path(__file__),C/'production_entry.py',C/'audit_entry.py']:ast.parse(p.read_text())
    w=dict(boot_id=parent['boot_id'],absolute_deadline_unix=time.time()+60,hard_stop_monotonic=time.monotonic()+60);window_valid(w,parent)
    negatives=[]
    for name,changed in [('boot',dict(w,boot_id='invalid')),('root',dict(w,absolute_deadline_unix=1795395601)),('clock',dict(w,hard_stop_monotonic=time.monotonic()-1))]:
        try:window_valid(changed,parent)
        except AssertionError:negatives.append(name)
        else:raise AssertionError('OWNER_WINDOW_NEGATIVE_ACCEPTED:'+name)
    try:storage_valid(10*1024**3,0)
    except AssertionError:negatives.append('storage')
    else:raise AssertionError('OWNER_STORAGE_NEGATIVE_ACCEPTED')
    value=dict(passed=True,models=0,analytical_native=0,physical_native=0,source_identity_verified=True,negative_guards=negatives,allocated_all_runs_bytes=allocated,maximum_nominal_native=2000,maximum_generation_native=402000,maximum_audit_native=402000,owner_source_sha256=sha(Path(__file__)))
    write(O/'OWNER_ENTRY_CHECK.json',value)
    for p in [Path(__file__),O/'OWNER_ENTRY_CHECK.json']:hashes[str(p.relative_to(R))]=sha(p)
    write(O/'NUMERIC_SOURCE_FREEZE.json',dict(files=hashes,owner_source_sha256=sha(Path(__file__)),entry_qualification='runs/v1417_complete_timed_witness/ENTRY_QUALIFICATION.json',owner_qualification='runs/v1417_complete_timed_witness/OWNER_ENTRY_CHECK.json',maximum_nominal_native=2000,maximum_generation_steps=402000,maximum_audit_steps=402000,physical_admission=False))
    print(json.dumps(value))


def environment():
    e=dict(os.environ);e.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');e.pop('LD_PRELOAD',None);return e


def launch():
    assert not(O/'LAUNCH_CLAIM.json').exists()and not(O/'ROUND_WINDOW.json').exists()
    assert read(O/'OWNER_ENTRY_CHECK.json')['passed']
    hashes=read(O/'NUMERIC_SOURCE_FREEZE.json')['files'];parent,current,allocated,saved=preflight(hashes)
    with(O/'LAUNCH_CLAIM.json').open('x')as stream:json.dump(dict(unix=time.time(),one_launch=True,models=0),stream)
    (O/'REVIEW_PENDING.before').write_bytes(saved)
    now,mono=time.time(),time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=min(now+5400,1795395600),hard_stop_monotonic=min(mono+5400,parent['hard_stop_monotonic']),boot_id=parent['boot_id']);write(O/'ROUND_WINDOW.json',window)
    write(O/'STORAGE_PREFLIGHT.json',dict(passed=True,allocated_all_runs_bytes=allocated,evidence_cap_bytes=64*1024**2,archive_reserve_bytes=64*1024**2,download_reserve_bytes=32*1024**2,root_reserve_bytes=512*1024**2))
    write(O/'LAUNCH_SOURCE_FREEZE.json',dict(files={str(p.relative_to(R)):sha(p)for p in [Path(__file__),O/'NUMERIC_SOURCE_FREEZE.json',O/'OWNER_ENTRY_CHECK.json']}))
    approval=dict(models_authorized=True,physical_admission=False,scope='CURRENT_EVENT_COMPLETE_MODEL_WITNESS',round_id=C.name,current_input_sha256=current['input_sha256'],maximum_nominal_native=2000,maximum_analytical_native=402000,tested_source_hashes=hashes,run_id='v1417-original-saved32210-complete-timed-model',**{k:window[k]for k in ['absolute_deadline_unix','hard_stop_monotonic','boot_id']});write(O/'model/APPROVAL.json',approval)
    parent['rounds'].append(dict(id=C.name,kind='complete_saved_current_causal_timed_method_model_qualification',status='RUNNING',started_unix=now,hard_stop_unix=window['absolute_deadline_unix'],maximum_generation_analytical=402000,maximum_audit_analytical=402000,maximum_vehicle_tasks=0,scientific_revision=4,source_freeze_sha256=sha(O/'NUMERIC_SOURCE_FREEZE.json')))
    parent.update(active_round=C.name,models_now_authorized=True,status='RUNNING_COMPLETE_TIMED_METHOD_MODEL');write(P,parent)
    state=read(R/'CURRENT_EXPERIMENT.json');state.update(active_run=str(O.relative_to(R)),active_zero_model_diagnostic=None,next_physical=False);write(R/'CURRENT_EXPERIMENT.json',state)
    try:
        with(O/'owner.console').open('x')as log:job=subprocess.Popen([sys.executable,'-B',str(C/'owner.py'),'--work'],cwd=R,env=environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    except BaseException as exc:
        parent=read(P);row=parent['rounds'][-1];row.update(closed=True,passed=False,status='CLOSED_LAUNCH_ERROR',error=repr(exc));parent.update(active_round=None,models_now_authorized=False);write(P,parent);raise
    write(O/'LAUNCH.json',dict(pid=job.pid,started_unix=now,one_launch=True,maximum_generation_steps=402000,maximum_audit_steps=402000,physical_native=0,ROS_peer_starts=0));print(json.dumps(dict(started=True,pid=job.pid)))


def terminate(job):
    if job is not None and job.poll()is None:
        os.killpg(job.pid,signal.SIGTERM)
        try:job.wait(timeout=10)
        except subprocess.TimeoutExpired:os.killpg(job.pid,signal.SIGKILL);job.wait(timeout=3)


def work():
    window=read(O/'ROUND_WINDOW.json');parent=read(P);saved=(O/'REVIEW_PENDING.before').read_bytes();job=None;logs=[];out=O/'model';hashes=read(O/'NUMERIC_SOURCE_FREEZE.json')['files']
    result=dict(passed=False,closed=False,independent_audit_unexecuted=True,physical_native=0,replay_native=0,mujoco_models=0,vehicle_starts=0,ROS_peer_starts=0)
    def stop(*_):raise TimeoutError('COMPLETE_TIMED_OWNER_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,min(window['hard_stop_monotonic']-time.monotonic(),window['absolute_deadline_unix']-time.time())-5))
    def run_stage(name,args):
        nonlocal job
        log=(out/(name+'.console')).open('x');logs.append(log)
        job=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),*args],cwd=R,env=environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write(O/'ACTIVE.json',dict(phase=name,native_pid=job.pid,physical_native=0,ROS_peer_starts=0));end=min(time.monotonic()+1810,window['hard_stop_monotonic']-30);next_storage=0
        while job.poll()is None:
            window_valid(window,parent);assert time.monotonic()<end,'MODEL_STAGE_WALL_LIMIT'
            if time.monotonic()>=next_storage:storage_valid(used(R/'runs'),used(out));next_storage=time.monotonic()+5
            time.sleep(.3)
        code=job.returncode;job=None;return code
    try:
        assert all(sha(R/p)==h for p,h in hashes.items())and all(sha(R/p)==h for p,h in read(O/'LAUNCH_SOURCE_FREEZE.json')['files'].items())
        window_valid(window,parent);(R/'REVIEW_PENDING').unlink()
        code=run_stage('generation',[str((C/'production_entry.py').relative_to(R)),str(out)]);(R/'REVIEW_PENDING').write_bytes(saved)
        generated=read(out/'RESULT.json')if(out/'RESULT.json').exists()else None;result.update(generation_returncode=code,generation=generated)
        if code==0 and generated and generated['passed']:
            assert generated['qualified_method']==METHOD and generated['geometry_kind']=='ORIGINAL_CAUSAL_TIME_POLYGONS'and generated['original_RPP_nominal_native']==0
            assert not read(out/'MODELED_SENT.json')and not read(out/'MODELED_ACCEPTED.json'),'UNEXPECTED_RPP_IN_DECLARED_FINITE_TIMED_METHOD'
            paths=[out/name for name in ['CURRENT_INPUT.json','SETUP.json','RESULT.json','NOMINAL.npz','JOURNAL.json','MEMORY.json','MODES.json','MODELED_SENT.json','MODELED_ACCEPTED.json','MODELED_RETIRED.json','branches/INDEX.json','branches/ROWS.jsonl','branches/branches.xor.gz']]
            data_hashes={str(p.relative_to(R)):sha(p)for p in paths}
            write(out/'AUDIT_APPROVAL.json',dict(mode='CURRENT_WITNESS_INDEPENDENT_AUDIT',round_id=C.name,input_sha256=generated['input_sha256'],maximum_steps=402000,source_hashes=hashes,source_generation=str(out.relative_to(R)),generated_data_hashes=data_hashes,**{k:window[k]for k in ['absolute_deadline_unix','hard_stop_monotonic','boot_id']}))
            result['independent_audit_unexecuted']=False;(R/'REVIEW_PENDING').unlink();code=run_stage('audit',[str((C/'audit_entry.py').relative_to(R))]);(R/'REVIEW_PENDING').write_bytes(saved)
            audit=read(out/'INDEPENDENT_AUDIT.json')if(out/'INDEPENDENT_AUDIT.json').exists()else None;result.update(audit_returncode=code,audit=audit,passed=bool(code==0 and audit and audit['passed']))
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        terminate(job)
        for log in logs:log.close()
        (R/'REVIEW_PENDING').write_bytes(saved);signal.setitimer(signal.ITIMER_REAL,0)
        for key,name in [('generation','RESULT.json'),('audit','INDEPENDENT_AUDIT.json')]:
            if result.get(key)is None and(out/name).exists():result[key]=read(out/name)
        unchanged=all(sha(R/p)==h for p,h in hashes.items());result.update(passed=result['passed']and unchanged,closed=True,closed_unix=time.time(),source_unchanged=unchanged,review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==saved);write(O/'COMPLETION.json',result);write(O/'CLOSED_APPROVAL.json',dict(models_authorized=False,physical_admission=False));(O/'ACTIVE.json').unlink(missing_ok=True)
        parent=read(P);row=next(v for v in parent['rounds']if v['id']==C.name);g=result.get('generation')or{};a=result.get('audit')or{}
        row.update(closed=True,status='CLOSED',passed=result['passed'],completion=str((O/'COMPLETION.json').relative_to(R)),generation_analytical_native=g.get('analytical_native'),generation_unknown=g.get('analytical_inflight_unknown',not bool(g)),audit_analytical_native=a.get('audit_analytical_native',0 if result['independent_audit_unexecuted']else None),audit_unknown=a.get('audit_inflight_unknown',not result['independent_audit_unexecuted']),physical_native=0)
        parent.update(active_round=None,models_now_authorized=False,status='COMPLETE_TIMED_METHOD_CLOSED_REVIEW_REQUIRED',complete_timed_method_generation_native=row['generation_analytical_native'],complete_timed_method_independent_audit_native=row['audit_analytical_native']);write(P,parent)
        state=read(R/'CURRENT_EXPERIMENT.json');state.update(active_run=None,active_zero_model_diagnostic=str((O/'COMPLETION.json').relative_to(R)),next_physical=False);write(R/'CURRENT_EXPERIMENT.json',state)
    return 0 if result['passed']else 1


if __name__=='__main__':
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    if '--entry-check'in sys.argv:entry_check()
    elif '--work'in sys.argv:raise SystemExit(work())
    else:launch()
