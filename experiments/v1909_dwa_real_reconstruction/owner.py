"""Once CPU5 owner of a 600s, CPU2 analytical-only qualification."""
import fcntl,hashlib,json,os,selectors,signal,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
    raw=(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    assert len(raw)<8*1024**2
    t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def identity(pid):
    s=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
    return dict(pid=pid,pgid=os.getpgid(pid),startticks=int(s[19]),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
def main():
    assert sorted(os.sched_getaffinity(0))==[5]
    for n in ['OWNER_ONCE_CLAIM.json','COMPLETION.json','OWNED_CHILD.json','RESULT.json']:assert not(O/n).exists(),'NO_RESTART:'+n
    auth=read(R/'runs/v1908_night_plan_review/OVERNIGHT_AUTHORIZATION_20261124.json')
    assert auth['authorized'] and auth['deadline_local']=='2026-11-25T09:00:00+08:00'
    assert time.time()+600<min(auth['deadline_unix'],auth['engineering_deadline_unix'])
    original=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(original).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    study=(R/'runs/v1643_formal_parent_metadata/OWNER.lock').open();fcntl.flock(study,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    current=read(R/'CURRENT_EXPERIMENT.json');assert current['active_round']is None and not current['models_now_authorized']
    files=read(O/'SOURCE_IDENTITY.json')['files'];assert all(sha(R/n)==h for n,h in files.items())
    used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(1015+16+32)*1024**2<15*1024**3
    start=time.time();mono=time.monotonic();me=identity(os.getpid())
    window=dict(start_unix=start,start_monotonic=mono,boot_id=me['boot_id'],normal_stop_unix=start+480,normal_stop_monotonic=mono+480,hard_stop_unix=start+600,hard_stop_monotonic=mono+600)
    with(O/'OWNER_ONCE_CLAIM.json').open('x')as f:json.dump(me,f)
    put(O/'WINDOW.json',window);put(O/'OWNER_IDENTITY.json',me)
    put(O/'ADMISSION.json',dict(scope='EXACT_ANALYTICAL_RECONSTRUCTION_ONLY',analytical_models_authorized=True,plant_authorized=False,maximum_python_native=19860,source_identity_sha256=sha(O/'SOURCE_IDENTITY.json')))
    current.update(active_round='v1909_analytical_reconstruction_only',models_now_authorized=True,status='ANALYTICAL_RECONSTRUCTION_QUALIFICATION_ACTIVE',navigation_models_authorized=False)
    put(R/'CURRENT_EXPERIMENT.json',current)
    p=None;owned=None;raw=bytearray();error=None;last=0
    try:
        (R/'REVIEW_PENDING').unlink()
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MUJOCO_GL='osmesa')
        p=subprocess.Popen(['taskset','-c','2','nice','-n','19','./run_phase.sh',str((C/'target.py').relative_to(R))],cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
        owned=identity(p.pid);put(O/'OWNED_CHILD.json',owned)
        sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
        while sel.get_map():
            assert me['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            assert min(window['hard_stop_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())>0
            if time.monotonic()-last>15:
                put(O/'RUNNING_CHECKPOINT.json',dict(stage='REAL_ANALYTICAL_REBUILD',owned=owned,elapsed_s=time.monotonic()-mono,physical_native=0,partial_not_pass=True,unix=time.time()));last=time.monotonic()
            for key,_ in sel.select(.2):
                b=os.read(key.fileobj.fileno(),16384)
                if not b:sel.unregister(key.fileobj);continue
                assert len(raw)+len(b)<=256*1024;raw.extend(b)
        p.wait(timeout=5)
        assert p.returncode==0 and read(O/'RESULT.json')['passed'],'REAL_REBUILD_QUALIFICATION_FAILED'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if p is not None and p.poll()is None:
            assert identity(p.pid)==owned
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=8)
            except subprocess.TimeoutExpired:
                assert identity(p.pid)==owned;os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
        (O/'CONSOLE.log').write_bytes(raw);(R/'REVIEW_PENDING').write_bytes(original)
        verified=all(sha(R/n)==h for n,h in files.items())
        result=dict(closed=True,passed=error is None and verified,first_error=error,source_SHA_after_exit=verified,child_returncode=None if p is None else p.returncode,child_exited=p is None or p.poll()is not None,review_restored=sha(R/'REVIEW_PENDING')==hashlib.sha256(original).hexdigest(),wall_s=time.monotonic()-mono,physical_native=0,navigation_admitted=False,remote_recovered=False)
        put(O/'COMPLETION.json',result)
        current=read(R/'CURRENT_EXPERIMENT.json');current.update(active_round=None,models_now_authorized=False,navigation_models_authorized=False,status='REAL_RECONSTRUCTION_CLOSED_NAVIGATION_NOT_ADMITTED',last_check=str((O/'COMPLETION.json').relative_to(R)));put(R/'CURRENT_EXPERIMENT.json',current)
        study.close()
    print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
